#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
功能：
1. 订阅 /robot/base_pose，计算 base 在 x/y 平面的相邻帧平移量，以及 roll/pitch
2. 订阅 /imu/raw：
   - 调用 ImuVibrationEstimator 直接计算 p_high
   - 对 linear_acceleration.z 积分，得到 z 方向速度
3. 订阅关节命令与关节反馈，计算关节位置误差
    self.declare_parameter("base_pose_topic", "/robot/base_pose")
    self.declare_parameter("imu_topic", "/imu/raw")
    self.declare_parameter("joint_cmd_topic", "/joint_command")
    self.declare_parameter("joint_fb_topic", "/robot_feedback")
4. 根据规则状态机判断：
   - VIBRATION
   - BASE_PUSH
   - BASE_LIFT
   - JOINT_DISTURB
   - TIPPING
   - FALLING
5. 发布当前状态与调试信息

注意：
- “平移量”定义为 base_pose 相邻两帧在 x/y 平面上的位移模长，不包含 z
- z方向速度由 imu/raw 的 linear_acceleration.z 直接积分得到
- 若 imu 安装方向与机器人 base z 不一致，需要先做轴向转换
"""

import math
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from scipy.spatial.transform import Rotation

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from std_msgs.msg import String
from sensor_msgs.msg import Imu, JointState
from geometry_msgs.msg import PoseStamped
from diagnostic_msgs.msg import KeyValue, DiagnosticArray, DiagnosticStatus

from robot_state_machine.robot_state_machine.utils.imu_vibration_monitor import ImuVibrationEstimator


# =============================================================================
# 数据结构
# =============================================================================

class ExternalForceState(Enum):
    NORMAL = auto()
    VIBRATION = auto()
    BASE_PUSH = auto()
    BASE_LIFT = auto()
    JOINT_DISTURB = auto()
    TIPPING = auto()
    FALLING = auto()


@dataclass
class ThresholdConfig:
    # base x/y 平移量（相邻帧位移模长）
    base_translation_low: float = 0.003
    base_translation_high: float = 0.015

    # 高频能量
    p_high_low: float = 0.15
    p_high_high: float = 0.60

    # z方向速度
    z_vel_low: float = 0.03
    z_vel_high: float = 0.12

    # roll / pitch 超限阈值（弧度）
    roll_pitch_limit: float = math.radians(20.0)

    # 关节误差阈值
    joint_error_low: float = 0.05
    joint_error_high: float = 0.18

    disturbed_joint_count_min: int = 1

    # z速度积分相关
    z_acc_deadband: float = 0.08
    z_vel_damping: float = 0.995
    z_vel_clip: float = 0.8
    z_acc_lpf_alpha: float = 0.25

    # 状态确认与释放时间
    confirm_time: float = 0.12
    release_time: float = 0.25

    # 振动估计参数
    vibration_fs: float = 100.0
    vibration_bpf_low: float = 8.0
    vibration_bpf_high: float = 30.0
    vibration_filter_order: int = 4
    vibration_rms_window_sec: float = 0.5


@dataclass
class RuntimeData:
    # 来自 /robot/base_pose
    base_translation_xy: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0

    # 来自 /imu/raw 内部计算
    p_high: float = 0.0
    mag_high: float = 0.0
    z_acc: float = 0.0
    z_velocity: float = 0.0

    # 来自 joint cmd / fb
    joint_errors: List[float] = field(default_factory=list)


# =============================================================================
# 状态机
# =============================================================================

class ExternalForceStateMachine:
    def __init__(self, cfg: ThresholdConfig):
        self.cfg = cfg
        self.state = ExternalForceState.NORMAL

        self._candidate_state: Optional[ExternalForceState] = None
        self._candidate_since: float = 0.0
        self._release_since: Optional[float] = None

        self.last_debug: Dict = {}

    def _translation_level(self, value: float) -> str:
        if value < self.cfg.base_translation_low:
            return "low"
        elif value < self.cfg.base_translation_high:
            return "medium"
        else:
            return "high"

    def _p_high_level(self, value: float) -> str:
        if value < self.cfg.p_high_low:
            return "low"
        elif value < self.cfg.p_high_high:
            return "medium"
        else:
            return "high"

    def _z_vel_level(self, value: float) -> str:
        v = abs(value)
        if v < self.cfg.z_vel_low:
            return "low"
        elif v < self.cfg.z_vel_high:
            return "medium"
        else:
            return "high"

    def _joint_error_max(self, errs: List[float]) -> float:
        if not errs:
            return 0.0
        return max(abs(e) for e in errs)

    def _joint_error_level(self, errs: List[float]) -> str:
        emax = self._joint_error_max(errs)
        if emax < self.cfg.joint_error_low:
            return "low"
        elif emax < self.cfg.joint_error_high:
            return "medium"
        else:
            return "high"

    def _disturbed_joint_count(self, errs: List[float]) -> int:
        return sum(1 for e in errs if abs(e) > self.cfg.joint_error_high)

    def _roll_pitch_exceeded(self, roll: float, pitch: float) -> bool:
        return abs(roll) > self.cfg.roll_pitch_limit or abs(pitch) > self.cfg.roll_pitch_limit

    def _classify_once(self, data: RuntimeData) -> ExternalForceState:
        trans_level = self._translation_level(data.base_translation_xy)
        p_level = self._p_high_level(data.p_high)
        z_level = self._z_vel_level(data.z_velocity)
        rp_exceeded = self._roll_pitch_exceeded(data.roll, data.pitch)
        joint_level = self._joint_error_level(data.joint_errors)
        disturbed_count = self._disturbed_joint_count(data.joint_errors)

        self.last_debug = {
            "translation_xy": data.base_translation_xy,
            "translation_level": trans_level,
            "mag_high": data.mag_high,
            "p_high": data.p_high,
            "p_level": p_level,
            "z_acc": data.z_acc,
            "z_velocity": data.z_velocity,
            "z_level": z_level,
            "roll_deg": math.degrees(data.roll),
            "pitch_deg": math.degrees(data.pitch),
            "roll_pitch_exceeded": rp_exceeded,
            "joint_error_max": self._joint_error_max(data.joint_errors),
            "joint_error_level": joint_level,
            "disturbed_joint_count": disturbed_count,
        }

        # 5. 倾倒
        if (
            trans_level in ("low", "medium") and
            p_level == "low" and
            z_level == "low" and
            rp_exceeded and
            joint_level == "medium"
        ):
            return ExternalForceState.TIPPING

        # 6. 坠落
        if (
            trans_level in ("medium", "high") and
            p_level == "medium" and
            z_level == "high" and
            rp_exceeded and
            joint_level == "medium"
        ):
            return ExternalForceState.FALLING

        # 3. 拿起
        if (
            trans_level == "high" and
            p_level == "medium" and
            z_level == "high" and
            (not rp_exceeded) and
            joint_level == "low"
        ):
            return ExternalForceState.BASE_LIFT

        # 2. 推移
        if (
            trans_level == "high" and
            p_level in ("medium", "low") and
            z_level == "low" and
            (not rp_exceeded) and
            joint_level == "low"
        ):
            return ExternalForceState.BASE_PUSH

        # 4. 关节扰动
        if (
            trans_level == "low" and
            p_level == "low" and
            z_level == "low" and
            (not rp_exceeded) and
            joint_level == "high" and
            disturbed_count >= self.cfg.disturbed_joint_count_min
        ):
            return ExternalForceState.JOINT_DISTURB

        # 1. 振动
        if (
            trans_level == "low" and
            p_level == "high" and
            z_level == "low" and
            (not rp_exceeded) and
            joint_level == "low"
        ):
            return ExternalForceState.VIBRATION

        return ExternalForceState.NORMAL

    def update(self, data: RuntimeData) -> ExternalForceState:
        now = time.monotonic()
        new_state = self._classify_once(data)

        if new_state == self.state:
            self._candidate_state = None
            self._candidate_since = 0.0
            self._release_since = None
            return self.state

        if new_state == ExternalForceState.NORMAL:
            if self._release_since is None:
                self._release_since = now
            elif now - self._release_since >= self.cfg.release_time:
                self.state = ExternalForceState.NORMAL
                self._candidate_state = None
                self._candidate_since = 0.0
                self._release_since = None
            return self.state

        self._release_since = None

        if self._candidate_state != new_state:
            self._candidate_state = new_state
            self._candidate_since = now
            return self.state

        if now - self._candidate_since >= self.cfg.confirm_time:
            self.state = new_state
            self._candidate_state = None
            self._candidate_since = 0.0

        return self.state

    def get_debug_info(self) -> Dict:
        out = dict(self.last_debug)
        out["current_state"] = self.state.name
        out["candidate_state"] = self._candidate_state.name if self._candidate_state else None
        return out


# =============================================================================
# ROS2 节点
# =============================================================================

class ExternalForceNode(Node):
    def __init__(self):
        super().__init__("r10007_external_force")

        # 参数
        self.declare_parameter("base_pose_topic", "/robot/base_pose")
        self.declare_parameter("imu_topic", "/imu/raw")
        self.declare_parameter("joint_cmd_topic", "/joint_command")
        self.declare_parameter("joint_fb_topic", "/robot_feedback")

        self.declare_parameter("base_translation_low", 0.003)
        self.declare_parameter("base_translation_high", 0.015)
        self.declare_parameter("p_high_low", 0.15)
        self.declare_parameter("p_high_high", 0.60)
        self.declare_parameter("z_vel_low", 0.03)
        self.declare_parameter("z_vel_high", 0.12)
        self.declare_parameter("roll_pitch_limit_deg", 20.0)
        self.declare_parameter("joint_error_low", 0.05)
        self.declare_parameter("joint_error_high", 0.18)
        self.declare_parameter("disturbed_joint_count_min", 1)
        self.declare_parameter("z_acc_deadband", 0.08)
        self.declare_parameter("z_vel_damping", 0.995)
        self.declare_parameter("z_vel_clip", 0.8)
        self.declare_parameter("z_acc_lpf_alpha", 0.25)
        self.declare_parameter("confirm_time", 0.12)
        self.declare_parameter("release_time", 0.25)

        self.declare_parameter("vibration_fs", 100.0)
        self.declare_parameter("vibration_bpf_low", 8.0)
        self.declare_parameter("vibration_bpf_high", 30.0)
        self.declare_parameter("vibration_filter_order", 4)
        self.declare_parameter("vibration_rms_window_sec", 0.5)

        base_pose_topic = self.get_parameter("base_pose_topic").value
        imu_topic = self.get_parameter("imu_topic").value
        joint_cmd_topic = self.get_parameter("joint_cmd_topic").value
        joint_fb_topic = self.get_parameter("joint_fb_topic").value

        cfg = ThresholdConfig(
            base_translation_low=float(self.get_parameter("base_translation_low").value),
            base_translation_high=float(self.get_parameter("base_translation_high").value),
            p_high_low=float(self.get_parameter("p_high_low").value),
            p_high_high=float(self.get_parameter("p_high_high").value),
            z_vel_low=float(self.get_parameter("z_vel_low").value),
            z_vel_high=float(self.get_parameter("z_vel_high").value),
            roll_pitch_limit=math.radians(float(self.get_parameter("roll_pitch_limit_deg").value)),
            joint_error_low=float(self.get_parameter("joint_error_low").value),
            joint_error_high=float(self.get_parameter("joint_error_high").value),
            disturbed_joint_count_min=int(self.get_parameter("disturbed_joint_count_min").value),
            z_acc_deadband=float(self.get_parameter("z_acc_deadband").value),
            z_vel_damping=float(self.get_parameter("z_vel_damping").value),
            z_vel_clip=float(self.get_parameter("z_vel_clip").value),
            z_acc_lpf_alpha=float(self.get_parameter("z_acc_lpf_alpha").value),
            confirm_time=float(self.get_parameter("confirm_time").value),
            release_time=float(self.get_parameter("release_time").value),
            vibration_fs=float(self.get_parameter("vibration_fs").value),
            vibration_bpf_low=float(self.get_parameter("vibration_bpf_low").value),
            vibration_bpf_high=float(self.get_parameter("vibration_bpf_high").value),
            vibration_filter_order=int(self.get_parameter("vibration_filter_order").value),
            vibration_rms_window_sec=float(self.get_parameter("vibration_rms_window_sec").value),
        )

        self.cfg = cfg
        self.fsm = ExternalForceStateMachine(cfg)
        self.data = RuntimeData()

        # 复用振动估计器
        self.vibration_estimator = ImuVibrationEstimator(
            fs=cfg.vibration_fs,
            bpf_low=cfg.vibration_bpf_low,
            bpf_high=cfg.vibration_bpf_high,
            filter_order=cfg.vibration_filter_order,
            rms_window_sec=cfg.vibration_rms_window_sec,
        )

        # 内部缓存
        self._last_base_pose_xy: Optional[np.ndarray] = None
        self._last_imu_ts: Optional[float] = None
        self._z_acc_lpf: float = 0.0

        self._joint_cmd: Dict[str, float] = {}
        self._joint_fb: Dict[str, float] = {}

        # QoS
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # 订阅
        self.sub_base_pose = self.create_subscription(
            PoseStamped, base_pose_topic, self._base_pose_cb, reliable_qos
        )
        self.sub_imu = self.create_subscription(
            Imu, imu_topic, self._imu_cb, sensor_qos
        )
        self.sub_joint_cmd = self.create_subscription(
            JointState, joint_cmd_topic, self._joint_cmd_cb, reliable_qos
        )
        self.sub_joint_fb = self.create_subscription(
            JointState, joint_fb_topic, self._joint_fb_cb, reliable_qos
        )

        # 发布
        self.pub_state = self.create_publisher(String, "/external_force/state", reliable_qos)
        self.pub_diag = self.create_publisher(DiagnosticArray, "/external_force/diagnostics", reliable_qos)

        # 50Hz
        self.timer = self.create_timer(0.02, self._timer_cb)

        self.get_logger().info("R10007-External_Force 节点已启动")
        self.get_logger().info(f"base_pose_topic  : {base_pose_topic}")
        self.get_logger().info(f"imu_topic        : {imu_topic}")
        self.get_logger().info(f"joint_cmd_topic  : {joint_cmd_topic}")
        self.get_logger().info(f"joint_fb_topic   : {joint_fb_topic}")
        self.get_logger().info(
            f"vibration estimator: fs={cfg.vibration_fs}, "
            f"BPF=[{cfg.vibration_bpf_low}, {cfg.vibration_bpf_high}]Hz, "
            f"window={cfg.vibration_rms_window_sec}s"
        )

    def _base_pose_cb(self, msg: PoseStamped):
        x = float(msg.pose.position.x)
        y = float(msg.pose.position.y)

        cur_xy = np.array([x, y], dtype=np.float64)
        if self._last_base_pose_xy is None:
            self.data.base_translation_xy = 0.0
        else:
            dxy = cur_xy - self._last_base_pose_xy
            self.data.base_translation_xy = float(np.linalg.norm(dxy))
        self._last_base_pose_xy = cur_xy

        qx = float(msg.pose.orientation.x)
        qy = float(msg.pose.orientation.y)
        qz = float(msg.pose.orientation.z)
        qw = float(msg.pose.orientation.w)

        try:
            r = Rotation.from_quat([qx, qy, qz, qw])
            roll, pitch, _ = r.as_euler("xyz", degrees=False)
            self.data.roll = float(roll)
            self.data.pitch = float(pitch)
        except Exception as e:
            self.get_logger().warn(f"base_pose 四元数转欧拉失败: {e}", throttle_duration_sec=1.0)

    def _imu_cb(self, msg: Imu):
        ts = float(msg.header.stamp.sec) + float(msg.header.stamp.nanosec) * 1e-9

        # 1) 直接复用振动估计器
        mag_high, p_high = self.vibration_estimator.update_from_imu_msg(msg)
        self.data.mag_high = mag_high
        self.data.p_high = p_high

        # 2) z加速度积分 -> z速度
        az = float(msg.linear_acceleration.z)
        self.data.z_acc = az

        if self._last_imu_ts is None:
            self._last_imu_ts = ts
            return

        dt = ts - self._last_imu_ts
        self._last_imu_ts = ts

        if dt <= 0.0 or dt > 0.2:
            return

        alpha = self.cfg.z_acc_lpf_alpha
        self._z_acc_lpf = alpha * az + (1.0 - alpha) * self._z_acc_lpf

        acc_use = self._z_acc_lpf
        if abs(acc_use) < self.cfg.z_acc_deadband:
            acc_use = 0.0

        vz = self.data.z_velocity + acc_use * dt
        vz *= self.cfg.z_vel_damping
        vz = float(np.clip(vz, -self.cfg.z_vel_clip, self.cfg.z_vel_clip))
        self.data.z_velocity = vz

    def _joint_cmd_cb(self, msg: JointState):
        for name, pos in zip(msg.name, msg.position):
            self._joint_cmd[name] = float(pos)
        self._update_joint_errors()

    def _joint_fb_cb(self, msg: JointState):
        for name, pos in zip(msg.name, msg.position):
            self._joint_fb[name] = float(pos)
        self._update_joint_errors()

    def _update_joint_errors(self):
        joint_errors: List[float] = []
        common = set(self._joint_cmd.keys()) & set(self._joint_fb.keys())
        for jn in common:
            joint_errors.append(self._joint_cmd[jn] - self._joint_fb[jn])
        self.data.joint_errors = joint_errors

    def _timer_cb(self):
        state = self.fsm.update(self.data)
        self._publish_state(state)
        self._publish_diag()

    def _publish_state(self, state: ExternalForceState):
        msg = String()
        msg.data = state.name
        self.pub_state.publish(msg)

    def _publish_diag(self):
        dbg = self.fsm.get_debug_info()

        status = DiagnosticStatus()
        status.name = "External_Force"
        status.hardware_id = "robot_external_force"
        status.level = DiagnosticStatus.OK
        status.message = dbg.get("current_state", "UNKNOWN")

        kvs = []
        for k, v in dbg.items():
            kv = KeyValue()
            kv.key = str(k)
            kv.value = str(v)
            kvs.append(kv)
        status.values = kvs

        arr = DiagnosticArray()
        arr.header.stamp = self.get_clock().now().to_msg()
        arr.status = [status]
        self.pub_diag.publish(arr)


def main(args=None):
    rclpy.init(args=args)
    node = ExternalForceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()