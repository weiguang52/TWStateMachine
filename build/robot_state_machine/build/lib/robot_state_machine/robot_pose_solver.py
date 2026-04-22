#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROS2 节点：融合 IMU 与关节编码器，实时解算人形机器人全局位姿。

话题
----
订阅：/imu/raw          (sensor_msgs/msg/Imu)        ← 来自 mpu_imu_publisher
订阅：/joint_states     (sensor_msgs/msg/JointState) ← 来自编码器驱动节点
发布：/robot/base_pose      (geometry_msgs/msg/PoseStamped)   base 位姿
发布：/robot/com_position   (geometry_msgs/msg/PointStamped)  质心位置（base系）
发布：/robot/displacement   (geometry_msgs/msg/Vector3Stamped) 累积位移向量
发布：/robot/end_effectors  (geometry_msgs/msg/PoseArray)      末端位姿数组
  PoseArray 顺序固定：[left_foot, right_foot, left_hand, right_hand, head]

功能
----
  1. 基坐标系姿态估计（IMU → Madgwick 滤波器）
  2. 各肢体末端在基坐标系中的 3D 位置（pinocchio 正运动学）
  3. 机器人质心位置（基坐标系）
  4. 基坐标系位移检测（被推动检测 + 量级估计）

机器人：Assembly.urdf（28 自由度人形）
  base_link 固定于空间，不估计平移。
  IMU 安装于腰部（waist 附近）。

"""

import math
import time
import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.spatial.transform import Rotation

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import Imu, JointState
from geometry_msgs.msg import (
    PoseStamped, PointStamped, Vector3Stamped,
    PoseArray, Pose, Point, Quaternion, Vector3,
)
from std_msgs.msg import Header
import pinocchio as pin

# ══════════════════════════════════════════════════════════════════════════════
# URDF 路径（写死在代码中，无需启动时传参）
# ══════════════════════════════════════════════════════════════════════════════

URDF_PATH = "/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data/Assembly/Assembly.SLDASM.urdf" 

# ══════════════════════════════════════════════════════════════════════════════
# 内部数据结构
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class IMUData:
    """从 ROS2 Imu 消息解包后的内部表示（SI 单位）"""
    timestamp: float           # Unix 时间戳 [s]
    accel: np.ndarray          # [ax, ay, az]  m/s²
    gyro: np.ndarray           # [wx, wy, wz]  rad/s


@dataclass
class DisplacementResult:
    """位移检测结果"""
    state: str                          # "static" / "moving" / "settling"
    is_moving: bool
    current_displacement: np.ndarray    # 本次运动位移向量 [m]（世界系）
    total_displacement: np.ndarray      # 自上次 reset() 起累积位移 [m]
    total_distance: float               # 累积位移模 [m]
    dynamic_accel_norm: float           # 当前动态加速度大小 [m/s²]（调试用）
    recent_events: list                 # 最近几次运动事件


@dataclass
class RobotState:
    """解算输出：机器人全局状态"""
    timestamp: float = 0.0

    # ── 基坐标系姿态，三种形式的数据 ──────────────────────────────────────────────
    base_orientation_quat: np.ndarray = field(default_factory=lambda: np.array([0., 0., 0., 1.]))
    base_rotation_matrix: np.ndarray  = field(default_factory=lambda: np.eye(3))
    base_euler_zyx: np.ndarray        = field(default_factory=lambda: np.zeros(3))

    # ── 末端执行器（基坐标系） ────────────────────────────────────
    end_effector_positions: Dict[str, np.ndarray] = field(default_factory=dict)
    end_effector_poses: Dict[str, np.ndarray]     = field(default_factory=dict)

    # ── 质心（基坐标系） ──────────────────────────────────────────
    com_position: np.ndarray = field(default_factory=lambda: np.zeros(3))

    # ── 位移检测 ──────────────────────────────────────────────────
    displacement: Optional[DisplacementResult] = None

    # ── 诊断 ──────────────────────────────────────────────────────
    imu_valid: bool = False
    fk_valid: bool  = False


# ══════════════════════════════════════════════════════════════════════════════
# Madgwick 姿态滤波器
# ══════════════════════════════════════════════════════════════════════════════

class MadgwickFilter:
    """
    Madgwick 互补滤波器（加速度计 + 陀螺仪）

    参考：S. Madgwick, "An efficient orientation filter for inertial and
    inertial/magnetic sensor arrays", 2010.

    约定：内部四元数 [qw, qx, qy, qz]，对外输出 [x,y,z,w]（scipy 约定）

    注意：无磁力计，偏航角（yaw）长期存在陀螺漂移，不可观。
    Roll / Pitch 由加速度计持续校正，精度较好。
    """

    def __init__(self, beta: float = 0.1, sample_freq: float = 100.0):
        self.beta        = beta                                             # 滤波增益，数值越大越信加速度计
        self.sample_freq = sample_freq                                      # 采样频率
        self._q          = np.array([1.0, 0.0, 0.0, 0.0])
        self._last_ts: Optional[float] = None

    def reset(self):
        self._q       = np.array([1.0, 0.0, 0.0, 0.0])
        self._last_ts = None

    def update(self, imu: IMUData) -> np.ndarray:
        """输入一帧 IMU，返回更新后的四元数 [x, y, z, w]（scipy 约定）"""
        # -------------- 时间差 dt 计算 ------------
        if self._last_ts is not None:
            dt = imu.timestamp - self._last_ts
            if dt <= 0 or dt > 0.5:
                dt = 1.0 / self.sample_freq
        else:
            dt = 1.0 / self.sample_freq
        self._last_ts = imu.timestamp

        # -------------- 取出当前的四元数、加速度、陀螺仪读数 -----------------
        q = self._q
        gx, gy, gz = imu.gyro
        ax, ay, az = imu.accel

        # ------------ 加速度归一化，只取方向，不取大小 ----------------
        a_norm = np.linalg.norm([ax, ay, az])
        if a_norm < 1e-6:
            self._integrate_gyro(gx, gy, gz, dt)
            return self._to_xyzw()
        ax /= a_norm; ay /= a_norm; az /= a_norm

        qw, qx, qy, qz = q

        # 估计重力方向（由当前四元数推算）
        vx = 2*(qx*qz - qw*qy)
        vy = 2*(qw*qx + qy*qz)
        vz = qw*qw - qx*qx - qy*qy + qz*qz

        # 目标函数梯度（计算加速度计观测与预测的误差）
        ex = ay*vz - az*vy
        ey = az*vx - ax*vz
        ez = ax*vy - ay*vx

        # 梯度校正陀螺
        gx += self.beta * ex
        gy += self.beta * ey
        gz += self.beta * ez

        # 四元数积分（一阶欧拉积分）
        dqw = 0.5*(-qx*gx - qy*gy - qz*gz)
        dqx = 0.5*( qw*gx + qy*gz - qz*gy)
        dqy = 0.5*( qw*gy - qx*gz + qz*gx)
        dqz = 0.5*( qw*gz + qx*gy - qy*gx)

        # 更新四元数并归一化
        qw += dqw*dt; qx += dqx*dt
        qy += dqy*dt; qz += dqz*dt

        norm = math.sqrt(qw*qw + qx*qx + qy*qy + qz*qz)
        self._q = np.array([qw, qx, qy, qz]) / norm
        return self._to_xyzw()

    # 纯陀螺积分，没有加速度时使用
    def _integrate_gyro(self, gx, gy, gz, dt):
        qw, qx, qy, qz = self._q
        dqw = 0.5*(-qx*gx - qy*gy - qz*gz)
        dqx = 0.5*( qw*gx + qy*gz - qz*gy)
        dqy = 0.5*( qw*gy - qx*gz + qz*gx)
        dqz = 0.5*( qw*gz + qx*gy - qy*gx)
        qw += dqw*dt; qx += dqx*dt
        qy += dqy*dt; qz += dqz*dt
        norm = math.sqrt(qw**2 + qx**2 + qy**2 + qz**2)
        self._q = np.array([qw, qx, qy, qz]) / norm

    # 四元数格式转换：[w, x, y, z] -> [x, y, z, w]， scipy 标准
    def _to_xyzw(self) -> np.ndarray:
        qw, qx, qy, qz = self._q
        return np.array([qx, qy, qz, qw])

    def get_rotation_matrix(self) -> np.ndarray:
        return Rotation.from_quat(self._to_xyzw()).as_matrix()


# ══════════════════════════════════════════════════════════════════════════════
# IMU → base_link 外参变换
# ══════════════════════════════════════════════════════════════════════════════

class IMUExtrinsics:
    """
    IMU 相对于 base_link 的安装外参。

    waist_yaw_joint origin 相对 base_link 为 [0, 0, 0.0225]。z轴方向上的偏移量 0.0225m
    默认假设 IMU 轴与 base_link 对齐（R = I）。

    约定：R_world_base = R_world_imu @ R_base_imu.T
    """

    def __init__(
        self,
        R_base_imu: Optional[np.ndarray] = None,
        t_base_imu: Optional[np.ndarray] = None,
    ):
        self.R = R_base_imu if R_base_imu is not None else np.eye(3)
        self.t = t_base_imu if t_base_imu is not None else np.array([0.0, 0.0, 0.0225])

    def imu_orientation_to_base(self, R_world_imu: np.ndarray) -> np.ndarray:
        return R_world_imu @ self.R.T


# ══════════════════════════════════════════════════════════════════════════════
# 基坐标系位移检测器
# ══════════════════════════════════════════════════════════════════════════════

class BaseDisplacementDetector:
    """
    拨动事件检测器：
    - 只关心“单次拨动事件”的位移量级
    - 事件结束（重新静止）后自动清空内部累计
    - 不做长期累计，避免越积越漂
    """

    STATE_STILL    = "static"
    STATE_MOVING   = "moving"
    STATE_SETTLING = "settling"

    def __init__(
        self,
        accel_enter_threshold: float = 0.80,   # 进入运动阈值
        accel_exit_threshold: float  = 0.25,   # 退出运动阈值（低一些，做迟滞）
        still_timeout: float         = 0.50,   # 持续静止多久才认为结束
        lpf_alpha: float             = 0.15,   # 更平滑一点
        accel_deadband: float        = 0.08,   # 小动态加速度直接归零
        max_velocity: float          = 0.30,   # 速度上限，防止积分爆掉
    ):
        self.enter_threshold = accel_enter_threshold
        self.exit_threshold  = accel_exit_threshold
        self.still_timeout   = still_timeout
        self.alpha           = lpf_alpha
        self.accel_deadband  = accel_deadband
        self.max_velocity    = max_velocity

        self._velocity      = np.zeros(3)
        self._displacement  = np.zeros(3)
        self._accel_dyn_lpf = np.zeros(3)

        self._state         = self.STATE_STILL
        self._still_timer   = 0.0
        self._motion_start: Optional[float] = None
        self._events: list  = []
        self._peak_accel    = 0.0
        self._last_ts: Optional[float] = None

        # 最近一次完成的事件结果（给外部发布/日志用）
        self._last_event_disp = np.zeros(3)
        # don't care z
        self.enable_z_displacement = False

    def reset(self):
        self._velocity         = np.zeros(3)
        self._displacement     = np.zeros(3)
        self._accel_dyn_lpf    = np.zeros(3)
        self._state            = self.STATE_STILL
        self._still_timer      = 0.0
        self._motion_start     = None
        self._events.clear()
        self._peak_accel       = 0.0
        self._last_ts          = None
        self._last_event_disp  = np.zeros(3)

    def update(self, imu: IMUData, R_world_base: np.ndarray) -> DisplacementResult:
        ts = imu.timestamp
        if self._last_ts is None:
            self._last_ts = ts
            return self._make_result()

        dt = ts - self._last_ts
        if dt <= 0 or dt > 0.2:
            self._last_ts = ts
            self._velocity = np.zeros(3)
            return self._make_result()

        self._last_ts = ts

        # 1) 去重力
        accel_world   = R_world_base @ imu.accel
        gravity_world = np.array([0.0, 0.0, 9.80665])
        accel_dyn     = accel_world - gravity_world

        if not self.enable_z_displacement:
            accel_dyn[2] = 0.0

        # 2) 低通
        self._accel_dyn_lpf = (
            self.alpha * accel_dyn + (1.0 - self.alpha) * self._accel_dyn_lpf
        )

        # 3) 死区
        for i in range(3):
            if abs(self._accel_dyn_lpf[i]) < self.accel_deadband:
                self._accel_dyn_lpf[i] = 0.0

        a_norm = float(np.linalg.norm(self._accel_dyn_lpf))

        # 4) 状态机
        # 静止 → 动
        if self._state == self.STATE_STILL:
            if a_norm > self.enter_threshold:
                self._state        = self.STATE_MOVING
                self._motion_start = ts
                self._still_timer  = 0.0
                self._displacement = np.zeros(3)
                self._velocity     = np.zeros(3)
                self._peak_accel   = a_norm
        # 运动中
        elif self._state == self.STATE_MOVING:
            self._peak_accel = max(self._peak_accel, a_norm)

            if a_norm < self.exit_threshold:
                self._state = self.STATE_SETTLING
                self._still_timer = 0.0
            else:
                self._integrate(dt)
        # 稳定中
        elif self._state == self.STATE_SETTLING:
            if a_norm > self.enter_threshold:
                self._state = self.STATE_MOVING
                self._integrate(dt)
            else:
                self._still_timer += dt

                # settling 阶段不再继续积分，只做强制刹车
                self._velocity *= 0.5
                if np.linalg.norm(self._velocity) < 0.02:
                    self._velocity[:] = 0.0
                # 静止够久 → 结束事件，保存位移，清零
                if self._still_timer >= self.still_timeout:
                    event_disp = self._displacement.copy()
                    self._last_event_disp = event_disp.copy()

                    self._events.append({
                        "start":        self._motion_start,
                        "end":          ts,
                        "duration":     ts - self._motion_start if self._motion_start is not None else 0.0,
                        "displacement": event_disp,
                        "distance":     float(np.linalg.norm(event_disp)),
                        "peak_accel":   self._peak_accel,
                    })

                    # 事件结束后自动清空
                    self._velocity[:]      = 0.0
                    self._displacement[:]  = 0.0
                    self._accel_dyn_lpf[:] = 0.0
                    self._state            = self.STATE_STILL
                    self._still_timer      = 0.0
                    self._motion_start     = None
                    self._peak_accel       = 0.0

        return self._make_result()

    # 积分：加速度 -> 速度 -> 位移
    def _integrate(self, dt: float):
        self._velocity += self._accel_dyn_lpf * dt

        if not self.enable_z_displacement:
            self._velocity[2] = 0.0

        v_norm = np.linalg.norm(self._velocity)
        if v_norm > self.max_velocity:
            self._velocity *= (self.max_velocity / v_norm)

        self._displacement += self._velocity * dt
        if not self.enable_z_displacement:
            self._displacement[2] = 0.0

    # 构造输出结果
    def _make_result(self) -> DisplacementResult:
        # 这里 total_displacement 不再表示历史累计
        # moving / settling 时显示当前事件位移
        # static 时显示最近一次完成事件的位移
        if self._state == self.STATE_STILL:
            disp = self._last_event_disp.copy()
        else:
            disp = self._displacement.copy()

        return DisplacementResult(
            state                = self._state,
            is_moving            = self._state != self.STATE_STILL,
            current_displacement = disp.copy(),
            total_displacement   = disp.copy(),
            total_distance       = float(np.linalg.norm(disp)),
            dynamic_accel_norm   = float(np.linalg.norm(self._accel_dyn_lpf)),
            recent_events        = list(self._events[-5:]),
        )

    def get_recent_events(self) -> list:
        return list(self._events)


# ══════════════════════════════════════════════════════════════════════════════
# 正运动学后端（pinocchio）
# ══════════════════════════════════════════════════════════════════════════════

class PinocchioFK:
    """基于 pinocchio 的正运动学 + 质心计算"""

    END_EFFECTOR_LINKS = ["left_foot", "right_foot", "left_hand", "right_hand", "head"]

    def __init__(self, urdf_path: str):
        self.model = pin.buildModelFromUrdf(urdf_path, pin.JointModelFreeFlyer())
        self.data  = self.model.createData()

        self.joint_names = [
            self.model.names[i]
            for i in range(1, self.model.njoints)
            if self.model.names[i] not in ("universe", "root_joint")
        ]

        self._frame_ids: Dict[str, int] = {}
        for name in self.END_EFFECTOR_LINKS:
            try:
                self._frame_ids[name] = self.model.getFrameId(name)
            except Exception:
                warnings.warn(f"URDF 中未找到 link: {name}")

    def update(
        self,
        base_rotation: np.ndarray,
        joint_angles: Dict[str, float],
    ) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
        # 构造 pinocchino 状态 q: [x, y, z, qx, qy, qz, qw, 关节1, 关节2, ...]
        q = pin.neutral(self.model)
        q[0:3] = 0.0
        q[3:7] = Rotation.from_matrix(base_rotation).as_quat()  # [x,y,z,w]

        # 关节角
        for jname, angle in joint_angles.items():
            if self.model.existJointName(jname):
                jid      = self.model.getJointId(jname)
                q[self.model.joints[jid].idx_q] = angle

        # 正运动学求解
        pin.forwardKinematics(self.model, self.data, q)
        pin.updateFramePlacements(self.model, self.data)
        
        base_fid     = self.model.getFrameId("base_link")
        T_world_base = self._se3_to_mat(self.data.oMf[base_fid])
        T_base_world = np.linalg.inv(T_world_base)

        ee_poses: Dict[str, np.ndarray] = {}
        for name, fid in self._frame_ids.items():
            ee_poses[name] = T_base_world @ self._se3_to_mat(self.data.oMf[fid])

        pin.centerOfMass(self.model, self.data, q)
        com_world = np.array(self.data.com[0])
        com_base  = T_base_world[:3, :3] @ com_world + T_base_world[:3, 3]

        return ee_poses, com_base

    @staticmethod
    def _se3_to_mat(oMf) -> np.ndarray:
        T = np.eye(4)
        T[:3, :3] = oMf.rotation
        T[:3,  3] = oMf.translation
        return T

# ══════════════════════════════════════════════════════════════════════════════
# 核心解算器（纯算法，无 ROS 依赖）
# ══════════════════════════════════════════════════════════════════════════════

class RobotPoseSolver:
    """
    位姿解算算法核心，不含任何 ROS 代码。
    由 ROS2 节点持有并在 IMU 回调中驱动。
    """

    def __init__(
        self,
        urdf_path: str,
        imu_extrinsics: Optional[IMUExtrinsics] = None,
        madgwick_beta: float   = 0.1,
        imu_freq_hz: float     = 100.0,
        accel_threshold: float = 0.5,
    ):
        self.extrinsics    = imu_extrinsics or IMUExtrinsics()
        self.madgwick      = MadgwickFilter(beta=madgwick_beta, sample_freq=imu_freq_hz)
        self.disp_detector = BaseDisplacementDetector(
            accel_enter_threshold=max(0.8, accel_threshold),
            accel_exit_threshold=0.25,
            still_timeout=0.5,
            lpf_alpha=0.15,
            accel_deadband=0.08,
            max_velocity=0.30,
        )

        self._fk = PinocchioFK(urdf_path)
        self._use_pinocchio = True

    @property
    def joint_names(self) -> List[str]:
        return self._fk.joint_names

    def step(self, imu: IMUData, joint_angles: Dict[str, float]) -> RobotState:
        """
        执行一步解算。由 ROS2 IMU 回调驱动，每收到一帧 IMU 调用一次。

        参数
        ----
        imu          : 当前帧 IMU 数据（m/s²，rad/s），来自 /imu/raw 解包
        joint_angles : {joint_name: angle_rad}，来自 /joint_states 缓存

        返回
        ----
        RobotState
        """
        state = RobotState(timestamp=imu.timestamp)

        # 1. 姿态估计（Madgwick）
        quat_xyzw    = self.madgwick.update(imu)
        R_world_imu  = Rotation.from_quat(quat_xyzw).as_matrix()
        R_world_base = self.extrinsics.imu_orientation_to_base(R_world_imu)

        state.base_rotation_matrix  = R_world_base
        state.base_orientation_quat = Rotation.from_matrix(R_world_base).as_quat()
        state.base_euler_zyx        = Rotation.from_matrix(R_world_base).as_euler("ZYX")
        state.imu_valid             = True

        # 2. 位移检测
        state.displacement = self.disp_detector.update(imu, R_world_base)

        # 3. 正运动学 + 质心
        try:
            ee_poses, com    = self._fk.update(R_world_base, joint_angles)
            state.end_effector_poses     = ee_poses
            state.end_effector_positions = {n: T[:3, 3] for n, T in ee_poses.items()}
            state.com_position           = com
            state.fk_valid               = True
        except Exception as e:
            warnings.warn(f"FK 失败: {e}")
            state.fk_valid = False

        return state

    def reset_imu(self):
        self.madgwick.reset()

    def reset_displacement(self):
        self.disp_detector.reset()


# ══════════════════════════════════════════════════════════════════════════════
# ROS2 节点
# ══════════════════════════════════════════════════════════════════════════════

class PoseSolverNode(Node):
    """
    ROS2 节点：订阅 /imu/raw + /joint_states，解算后发布位姿相关话题。

    参数（ros2 param）
    -----------------
    urdf_path        : str   URDF 文件绝对路径（必填）
    madgwick_beta    : float Madgwick 增益（默认 0.1）
    imu_freq_hz      : float IMU 采样率，用于初始 dt 估计（默认 100.0）
    accel_threshold  : float 位移检测加速度阈值 m/s²（默认 0.5）
    imu_R_base_imu   : list  IMU 外参旋转矩阵，9 元素行优先展开（默认单位阵）
    imu_timeout_sec  : float IMU 话题超时告警时长（默认 0.5s）
    """

    END_EFFECTOR_LINKS = ["left_foot", "right_foot", "left_hand", "right_hand", "head"]

    def __init__(self):
        super().__init__("robot_pose_solver")

        # ── 声明 ROS2 参数 ────────────────────────────────────────
        self.declare_parameter("urdf_path",       URDF_PATH)   # 默认使用写死路径
        self.declare_parameter("madgwick_beta",   0.1)
        self.declare_parameter("imu_freq_hz",     100.0)
        self.declare_parameter("accel_threshold", 0.5)
        self.declare_parameter("imu_R_base_imu",  [1.,0.,0., 0.,1.,0., 0.,0.,1.])
        self.declare_parameter("imu_timeout_sec", 0.5)

        urdf_path        = self.get_parameter("urdf_path").value
        madgwick_beta    = self.get_parameter("madgwick_beta").value
        imu_freq_hz      = self.get_parameter("imu_freq_hz").value
        accel_threshold  = self.get_parameter("accel_threshold").value
        R_flat           = self.get_parameter("imu_R_base_imu").value
        self._imu_timeout = self.get_parameter("imu_timeout_sec").value

        R_base_imu = np.array(R_flat, dtype=float).reshape(3, 3)

        # ── 解算器 ────────────────────────────────────────────────
        self.get_logger().info(f"加载 URDF: {urdf_path}")
        self._solver = RobotPoseSolver(
            urdf_path       = urdf_path,
            imu_extrinsics  = IMUExtrinsics(R_base_imu=R_base_imu),
            madgwick_beta   = madgwick_beta,
            imu_freq_hz     = imu_freq_hz,
            accel_threshold = accel_threshold,
        )
        self.get_logger().info(
            f"  关节数={len(self._solver.joint_names)}"
        )

        # ── 内部缓存 ──────────────────────────────────────────────
        # 关节角由 /joint_states 异步更新，解算时直接使用最新值
        self._joint_angles: Dict[str, float] = {}
        self._last_imu_wall: float = 0.0      # 用于超时检查（wall time）

        # ── QoS ───────────────────────────────────────────────────
        # IMU 话题：sensor_msgs 惯例用 BEST_EFFORT，depth=1 只保最新帧
        sensor_qos = QoSProfile(
            reliability = ReliabilityPolicy.BEST_EFFORT,
            history     = HistoryPolicy.KEEP_LAST,
            depth       = 1,
        )
        # 关节角 / 输出话题：RELIABLE，depth=10
        reliable_qos = QoSProfile(
            reliability = ReliabilityPolicy.RELIABLE,
            history     = HistoryPolicy.KEEP_LAST,
            depth       = 10,
        )

        # ── 订阅 ──────────────────────────────────────────────────
        self._sub_imu = self.create_subscription(
            Imu, "/imu/raw", self._imu_cb, sensor_qos,
        )
        self._sub_joint = self.create_subscription(
            JointState, "/joint_states", self._joint_cb, reliable_qos,
        )

        # ── 发布 ──────────────────────────────────────────────────
        self._pub_base_pose = self.create_publisher(
            PoseStamped,    "/robot/base_pose",    reliable_qos)
        self._pub_com = self.create_publisher(
            PointStamped,   "/robot/com_position", reliable_qos)
        self._pub_disp = self.create_publisher(
            Vector3Stamped, "/robot/displacement", reliable_qos)
        self._pub_ee = self.create_publisher(
            PoseArray,      "/robot/end_effectors",reliable_qos)

        # ── IMU 超时检查（1Hz 定时器）────────────────────────────
        self.create_timer(1.0, self._check_imu_timeout)

        self.get_logger().info(
            "节点启动完成，等待 /imu/raw 和 /joint_states ..."
        )

    # ── 回调：IMU（解算主驱动）───────────────────────────────────────────────

    def _imu_cb(self, msg: Imu):
        """
        收到 /imu/raw（来自 mpu_imu_publisher）：
          - 数据已是 SI 单位（m/s²，rad/s），直接解包
          - 与关节角缓存一起驱动解算器 step()
          - 将结果发布到各话题
        """
        self._last_imu_wall = time.time()

        # 解包：话题时间戳 → Unix 浮点秒
        stamp = msg.header.stamp
        ts    = stamp.sec + stamp.nanosec * 1e-9

        imu = IMUData(
            timestamp = ts,
            accel     = np.array([
                msg.linear_acceleration.x,
                msg.linear_acceleration.y,
                msg.linear_acceleration.z,
            ]),
            gyro      = np.array([
                msg.angular_velocity.x,
                msg.angular_velocity.y,
                msg.angular_velocity.z,
            ]),
        )

        # 解算
        state = self._solver.step(imu, self._joint_angles)

        # 发布
        self._publish(state, stamp)

    # ── 回调：关节角（异步缓存，不触发解算）─────────────────────────────────

    def _joint_cb(self, msg: JointState):
        """
        收到 /joint_states，更新关节角缓存。
        单位：rad（JointState 标准）。
        解算在 IMU 回调中进行，此处仅更新缓存。
        """
        for name, pos in zip(msg.name, msg.position):
            self._joint_angles[name] = float(pos)

    # ── 发布解算结果 ──────────────────────────────────────────────────────────

    def _publish(self, state: RobotState, stamp):
        header          = Header()
        header.stamp    = stamp
        header.frame_id = "base_link"

        # 1. base 姿态（仅旋转，position 全零，因为 base 固定不平移）
        q  = state.base_orientation_quat   # [x, y, z, w]
        ps = PoseStamped()
        ps.header             = header

        if state.displacement is not None:
            disp = state.displacement.current_displacement
            ps.pose.position.x = float(disp[0])
            ps.pose.position.y = float(disp[1])
            ps.pose.position.z = float(disp[2])
            
        ps.pose.orientation.x = float(q[0])
        ps.pose.orientation.y = float(q[1])
        ps.pose.orientation.z = float(q[2])
        ps.pose.orientation.w = float(q[3])
        self._pub_base_pose.publish(ps)

        # 2. 质心位置（base 坐标系）
        if state.fk_valid:
            pt        = PointStamped()
            pt.header = header
            pt.point.x = float(state.com_position[0])
            pt.point.y = float(state.com_position[1])
            pt.point.z = float(state.com_position[2])
            self._pub_com.publish(pt)

        # 3. 累积位移向量（world 坐标系）
        if state.displacement is not None:
            d  = state.displacement
            disp = d.current_displacement
            vs        = Vector3Stamped()
            vs.header = header
            vs.vector.x = float(disp[0])
            vs.vector.y = float(disp[1])
            vs.vector.z = float(disp[2])
            self._pub_disp.publish(vs)

            if d.state == BaseDisplacementDetector.STATE_MOVING:
                self.get_logger().warn(
                    f"[位移告警] 检测到推动！"
                    f" 动态加速度={d.dynamic_accel_norm:.2f}m/s²"
                    f" 当前事件位移=({disp[0]:+.3f},{disp[1]:+.3f},{disp[2]:+.3f})m"
                    f" |d|={d.total_distance*100:.1f}cm",
                    throttle_duration_sec=0.3,
                )

            elif d.state == BaseDisplacementDetector.STATE_STILL and d.total_distance > 0.01:
                self.get_logger().info(
                    f"[位移事件结束]"
                    f" 单次位移=({disp[0]:+.3f},{disp[1]:+.3f},{disp[2]:+.3f})m"
                    f" |d|={d.total_distance*100:.1f}cm",
                    throttle_duration_sec=1.0,
                )

        # 4. 末端执行器位姿数组
        #    顺序固定：left_foot, right_foot, left_hand, right_hand, head
        if state.fk_valid:
            pa        = PoseArray()
            pa.header = header
            for name in self.END_EFFECTOR_LINKS:
                T = state.end_effector_poses.get(name)
                p = Pose()
                if T is not None:
                    p.position.x = float(T[0, 3])
                    p.position.y = float(T[1, 3])
                    p.position.z = float(T[2, 3])
                    eq = Rotation.from_matrix(T[:3, :3]).as_quat()  # [x,y,z,w]
                    p.orientation.x = float(eq[0])
                    p.orientation.y = float(eq[1])
                    p.orientation.z = float(eq[2])
                    p.orientation.w = float(eq[3])
                pa.poses.append(p)
            self._pub_ee.publish(pa)

    # ── IMU 超时检查 ──────────────────────────────────────────────────────────

    def _check_imu_timeout(self):
        if self._last_imu_wall == 0.0:
            return   # 还未收到过任何帧，不告警
        elapsed = time.time() - self._last_imu_wall
        if elapsed > self._imu_timeout:
            self.get_logger().warn(
                f"IMU 话题超时！已 {elapsed:.1f}s 未收到 /imu/raw",
                throttle_duration_sec=2.0,
            )


# ══════════════════════════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════════════════════════

def main(args=None):
    rclpy.init(args=args)
    node = PoseSolverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()