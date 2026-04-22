from __future__ import annotations

import time
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple, Dict, Any, List

# === 下位机协议模块 ===
from robot_state_machine.utils.robot_protocol import (
    create_robot_controller, RobotController,
)  # :contentReference[oaicite:1]{index=1}
# --- 头身协同 ---
from robot_state_machine.utils.gazeShifting_mechanism_simulation import (
    HeadBodyPolicyConfig,
    HeadBodyPolicyState,
    compute_head_body_targets,
    vision_pos_to_yaw_delta_deg,
)

# ============================================================
# 0. 枚举：你 C++ 里用到的 UserRole / InteractionStatus / UserEvent
#    （枚举取值你可以按你项目实际再细化，但类型必须存在）
# ============================================================
class UserRole(Enum):
    ADMIN = auto()
    FAMILY = auto()
    GUEST = auto()


class InteractionStatus(Enum):
    Blind = auto()      # 盲交
    TRACKING = auto()   # 追踪
    LOST = auto()       # 丢失用户


class UserEvent(Enum):
    WAVE = auto()
    LEAVE = auto()
    CALL_NAME = auto()
    NONE = auto()       # 建议加一个默认值，避免未初始化


# ============================================================
# 基础坐标与向量定义
# ============================================================
@dataclass
class Point3D:
    x: float
    y: float
    z: float


@dataclass
class Embedding:
    data: List[float]
    updated_at: int  # uint64_t in C++，这里用 int 表示（你统一毫秒/微秒即可）


# ============================================================
# 单个用户的完整状态结构
# ============================================================
@dataclass
class UserState:
    # --- 【核心身份层】 ---
    user_id: int                # 0: 主用户, 1-5: 家庭, 6-10: 访客
    name: str                   # 注册名或 "Guest_n"
    role: UserRole              # ADMIN, FAMILY, GUEST
    is_registered: bool         # 是否为已持久化存储的用户
    face_feat: Embedding        # 临时的/注册的人脸特征向量
    voice_feat: Embedding       # 临时的/注册的声纹特征向量

    # --- 【实时视觉感知 (Vision)】 ---
    is_in_fov: bool             # 当前是否在视野内
    vision_pos: Point3D         # 当前用户在视野中坐标
    face_distance: float        # 脸部距离
    gaze_angle: float           # 注视角度（判断是否在看机器人）
    gaze_frequency: float       # 注视统计（统计用户的注视次数和注视频率）
    is_lip_moving: bool         # 唇动检测（辅助判断是否正在发声）
    facial_emotion: str         # 面部情绪分类（如：HAPPY, SAD, ANGRY, NEUTRAL等）
    last_seen_ts: int           # 最后一次视觉检测到该用户的时间戳
    last_follow_pos: Point3D    # 丢失前的最后一帧坐标（用于盲寻）

    # --- 【实时听觉感知 (Audio)】 ---
    is_speaking: bool           # VAD检测当前是否正在说话
    doa_angle: float            # 声音来源方向 (Degree)
    voice_emotion: str          # 声音情绪分类（如：HAPPY, SAD, ANGRY, NEUTRAL等）
    voice_confidence: float     # 声纹识别匹配度

    # --- 【交互与逻辑层 (Logic)】 ---
    is_waked_up: bool               # 是否是该用户触发了当前的唤醒
    engagement_score: float         # 交互意图分 (0.0-1.0，综合距离、眼神、唤醒、动作)
    is_wakeup_confirmed: bool       # 确认唤醒事件（经过多模态对齐、意图校验后的有效唤醒标记）
    has_scheduled_event: bool       # 该用户当前是否有预设或预约的事件（如：吃药提醒、日程播报）
    scheduled_event_id: str         # 预设/预约事件的唯一ID（用于关联业务数据库提取具体事件内容）
    is_interaction: bool            # 是否正在交互流程中
    status: InteractionStatus       # 交互中的状态Blind(盲交), TRACKING(追踪), LOST(丢失用户)
    session_start_ts: int           # 本次会话开始时间
    last_event: UserEvent           # 用户最近事件：WAVE(挥手), LEAVE(离开), CALL_NAME(喊名字)

    # --- 【动态权重/置信度】 ---
    identity_consistency: float     # 身份对齐置信度（视觉ID与声纹ID的匹配程度）


# ============================================================
# 全局管理容器
# ============================================================
@dataclass
class UserStateManager:
    slots: Dict[int, UserState]  # 1+5+5 映射表
    primary_user_id: int         # 当前机器人主要关注的 ID (Focus ID)


# ============================================================
# 一些“保持结构不变”的辅助初始化方法
# ============================================================
def now_ts_ms() -> int:
    return int(time.time() * 1000)


def make_empty_embedding(dim: int = 0) -> Embedding:
    return Embedding(data=[0.0] * dim, updated_at=now_ts_ms())


def make_zero_point() -> Point3D:
    return Point3D(0.0, 0.0, 0.0)


# =========================
# 电机/板号映射与参数
# =========================
@dataclass
class YawBoardConfig:
    """
    每个 yaw 由哪个板控制，以及用板上的哪个通道(A01/B01)来表示。
    协议是双电机板：send_single_motor_angles(board_id, angle_a01, angle_b01)
    """
    neck_board_id: int
    waist_board_id: int

    # 该板上 A01/B01 哪个对应 yaw，另一个电机角度保持不动
    neck_use_a01: bool = True
    waist_use_a01: bool = True

    # 另一个电机的“保持角”（根据你的机构实际填）
    neck_other_hold_angle: float = 180.0
    waist_other_hold_angle: float = 180.0

    # 机械/安全限制（deg）
    neck_yaw_min: float = -90.0
    neck_yaw_max: float = 90.0
    waist_yaw_min: float = -60.0
    waist_yaw_max: float = 60.0

    # 角度零点偏置（标定用，deg）
    neck_yaw_offset: float = 0.0
    waist_yaw_offset: float = 0.0

    # 发送频率/三次插值
    interp_points: int = 10         # 插值点数量
    cmd_interval_s: float = 0.01   # 控制周期（100 Hz）


# =========================
# 搜寻与跟随控制器
# =========================
class SearchAndFollowController:
    def __init__(
        self,
        robot: RobotController,
        yaw_cfg: YawBoardConfig,
        logger=None,
    ):
        self.robot = robot
        self.cfg = yaw_cfg
        self.logger = logger

        # 记录当前 yaw 目标/估计
        self._neck_yaw_deg = 0.0
        self._waist_yaw_deg = 0.0

        # 跟随/搜寻运行标记
        self._following = False
        self._searching = False

        # 头身协同运动初始化
        self._hb_cfg = HeadBodyPolicyConfig(
            head_only_deg=45.0,             # 小范围阈值：<45° 头先动
            body_align_delay_s=0.8,         # 小范围：头保持偏转超过多久才开始带身体
            body_catchup_gain_small=0.6,    # 身体追赶强度（0~1），越大身体越快追上目标
            body_catchup_gain_large=0.8,    # 身体追赶强度（0~1），越大身体越快追上目标
        )
        self._hb_state = HeadBodyPolicyState()

        # 获取上一时刻用户所在视野中的坐标
        self._last_vision_pos: Optional[Point3D] = None

    # ---------------------------------------------------------
    # 顶层：触发条件判断
    # ---------------------------------------------------------
    def update_robot_behavior(self, user_state: UserState, need_follow: bool = True) -> None:
        if not need_follow:
            return

        # 触发条件 A：被唤醒
        if user_state.is_waked_up:
            self.execute_search_and_follow(user_state, trigger_type="WAKEUP")
            return

        # 触发条件 B：交互中丢失（可能是遮挡，也可能是因为特殊动作导致）
        if user_state.is_interaction and user_state.status == InteractionStatus.LOST:
            self.execute_search_and_follow(user_state, trigger_type="LOST")
            return
    def get_current_yaw_deg(self) -> Tuple[float, float]:
        """返回 (neck_yaw_deg, waist_yaw_deg)。

        注意：当前实现使用控制器内部维护的“估计值”（每次下发命令后更新）。
        如果你后续接入下位机回读角度/编码器反馈，可以在这里改成返回真实反馈。
        """
        return self._neck_yaw_deg, self._waist_yaw_deg

    def get_current_neck_yaw_deg(self) -> float:
        return self._neck_yaw_deg

    def get_current_waist_yaw_deg(self) -> float:
        return self._waist_yaw_deg
    
    # ---------------------------------------------------------
    # 核心：搜寻与跟随
    # ---------------------------------------------------------
    def execute_search_and_follow(self, user_state: UserState, trigger_type: str) -> None:
        # 2. 视野内：直接跟随
        if user_state.is_in_fov:
            self.start_visual_servo_following(user_state)
            user_state.status = InteractionStatus.TRACKING
            return

        # 3. 提取位置信息
        has_location_info = False
        target_location = None  # 可以是 doa_angle(deg) 或 Point3D

        if trigger_type == "WAKEUP" and self._is_valid_doa(user_state.doa_angle):
            has_location_info = True
            target_location = float(user_state.doa_angle)  # deg
        elif trigger_type == "LOST" and self._is_valid_point(user_state.last_follow_pos):
            has_location_info = True
            target_location = user_state.last_follow_pos

        # 4. 决策树
        if has_location_info:
            # A: 携带位置信息
            self.move_to(target_location)

            if self.check_user_in_fov(user_state):
                self.start_visual_servo_following(user_state)
                user_state.status = InteractionStatus.TRACKING
                return

            self.execute_saccade_search(user_state)

            if self.check_user_in_fov(user_state):
                self.start_visual_servo_following(user_state)
                user_state.status = InteractionStatus.TRACKING
                return

            # 还找不到：回到线索位置结束
            self.move_to(target_location)
            self.end_process(user_state)
        else:
            # B: 没有位置信息：直接扫视
            self.execute_saccade_search(user_state)

            if self.check_user_in_fov(user_state):
                self.start_visual_servo_following(user_state)
                user_state.status = InteractionStatus.TRACKING
                return

            self.reset_to_home_position()
            self.end_process(user_state)

    # =========================================================
    # (1) MoveTo：把“线索位置”转成 yaw 并驱动 neck/waist
    # =========================================================
    def move_to(self, target_location) -> None:
        if isinstance(target_location, (float, int)):
            target_yaw = float(target_location)
        elif isinstance(target_location, Point3D):
            target_yaw = vision_pos_to_yaw_delta_deg(
            target_location=target_location,
            ref_pos=self._last_vision_pos
        )
        else:
            return

        neck_target, waist_target = compute_head_body_targets(
            target_yaw_deg=target_yaw,
            neck_cur_deg=self._neck_yaw_deg,
            waist_cur_deg=self._waist_yaw_deg,
            neck_min_deg=self.cfg.neck_yaw_min,
            neck_max_deg=self.cfg.neck_yaw_max,
            waist_min_deg=self.cfg.waist_yaw_min,
            waist_max_deg=self.cfg.waist_yaw_max,
            cfg=self._hb_cfg,
            st=self._hb_state,
        )

        self._move_yaw_split(neck_target=neck_target, waist_target=waist_target)

    def _move_yaw_split(self, neck_target: float, waist_target: float) -> None:
        """
        将目标 yaw 分配给腰/颈，并按步进发送到下位机。
        """
        # 限制目标角度
        neck_target = self._clamp(neck_target, self.cfg.neck_yaw_min, self.cfg.neck_yaw_max)
        waist_target = self._clamp(waist_target, self.cfg.waist_yaw_min, self.cfg.waist_yaw_max)

        # 加 offset（标定）
        neck_target = neck_target + self.cfg.neck_yaw_offset
        waist_target = waist_target + self.cfg.waist_yaw_offset

        # 做步进：对起始点->目标点做三次插值，生成 1~3 个中间点，逐点下发
        neck_seq = self._step_towards(self._neck_yaw_deg, neck_target, self.cfg.interp_points)
        waist_seq = self._step_towards(self._waist_yaw_deg, waist_target, self.cfg.interp_points)

        n_steps = max(len(neck_seq), len(waist_seq))
        for i in range(n_steps):
            neck_cmd = neck_seq[i] if i < len(neck_seq) else neck_seq[-1]
            waist_cmd = waist_seq[i] if i < len(waist_seq) else waist_seq[-1]

            self._send_neck_yaw(neck_cmd)
            self._send_waist_yaw(waist_cmd)

            # 更新内部“当前位置估计”
            self._neck_yaw_deg = neck_cmd
            self._waist_yaw_deg = waist_cmd

            time.sleep(self.cfg.cmd_interval_s)

    def _send_neck_yaw(self, angle_0_360: float) -> Optional[Dict[str, Any]]:
        if self.cfg.neck_use_a01:
            a01, b01 = angle_0_360, self.cfg.neck_other_hold_angle
        else:
            a01, b01 = self.cfg.neck_other_hold_angle, angle_0_360

        return self.robot.send_single_motor_angles(self.cfg.neck_board_id, a01, b01, retry=False)

    def _send_waist_yaw(self, angle_0_360: float) -> Optional[Dict[str, Any]]:
        if self.cfg.waist_use_a01:
            a01, b01 = angle_0_360, self.cfg.waist_other_hold_angle
        else:
            a01, b01 = self.cfg.waist_other_hold_angle, angle_0_360

        return self.robot.send_single_motor_angles(self.cfg.waist_board_id, a01, b01, retry=False)

    # =========================================================
    # (2) StartVisualServoFollowing：视野内跟随闭环框架
    # =========================================================
    def start_visual_servo_following(self, user_state: UserState) -> None:
        """
        视野内跟随：根据 vision_pos 不断更新 yaw，让用户尽量居中。
        后续可以把控制律换成更稳定的 PID/LQR。
        """
        self._following = True
        start_ts = time.time()

        # 跟随最长持续时间，防止卡死
        MAX_FOLLOW_TIME_S = 10.0

        while self._following:
            # 如果用户已经不在视野，退出交给上层搜寻
            if not user_state.is_in_fov or not self._is_valid_point(user_state.vision_pos):
                break

            # vision_pos -> yaw 误差（需要你按相机坐标定义）
            target_yaw = vision_pos_to_yaw_delta_deg(
            target_location=user_state.vision_pos,
            ref_pos=self._last_vision_pos
            )

            # 简单控制：让 neck/waist 朝 target_yaw 靠拢
            self._move_yaw_split(neck_target=target_yaw * 0.6, waist_target=target_yaw * 0.4)

            # 退出条件
            if time.time() - start_ts > MAX_FOLLOW_TIME_S:
                break

        self._following = False

    # =========================================================
    # 下面这些：你没提供数据/接口，我按要求留“可替换接口”
    # =========================================================
    def check_user_in_fov(self, user_state: UserState) -> bool:
        """
        TODO: 你需要接你的视觉模块实时更新 user_state.is_in_fov
        这里先直接返回当前字段值。
        """
        return bool(user_state.is_in_fov)

    def execute_saccade_search(self, user_state: UserState) -> None:
        """
        扫视搜寻：脖子左右扫，必要时腰也跟着小角度扫。
        这里给一个简单实现：neck 在 [-45, 45] 来回，腰在 [-20, 20] 慢扫。
        """
        self._searching = True

        neck_seq = [-45, 0, 45, 0]
        waist_seq = [-20, 0, 20, 0]
        
        neck_seq = neck_seq + self.cfg.neck_yaw_offset
        waist_seq = waist_seq + self.cfg.waist_yaw_offset

        for i in range(len(neck_seq)):
            if self.check_user_in_fov(user_state):
                break
            self._move_yaw_split(neck_target=neck_seq[i], waist_target=waist_seq[i])
            time.sleep(0.15)

        self._searching = False

    def reset_to_home_position(self) -> None:
        """复位：回到 0 yaw。"""
        self._move_yaw_split(neck_target=0.0, waist_target=0.0)

    def end_process(self, user_state: UserState) -> None:
        user_state.is_waked_up = False
        user_state.status = InteractionStatus.LOST
    #     self.stop_all_motors()

    # def stop_all_motors(self) -> None:
    #     """
    #     TODO: 你下位机协议里目前是“角度控制”，没有显式 stop。
    #     一个常见做法是：保持当前位置/发当前角度，或发送电流=0 的模式（如果协议支持）。
    #     这里先留空，避免误动作。
    #     """
    #     pass

    def on_vision_update(self, user_state: UserState) -> None:
        """
        这个在获取vision_pos前调用?
        """
        if user_state.is_in_fov and self._is_valid_point(user_state.vision_pos):
            # 把“上一时刻”保存下来
            self._last_vision_pos = user_state.vision_pos
    # =========================
    # utils
    # =========================
    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, x))

    @staticmethod
    def _step_towards(self, curr: float, target: float, num_points: int):
        """
        三次方插值：从 curr 到 target 生成 num_points 个“后续点”（不包含 curr，包含 target）。
        """
        if num_points <= 1:
            return [target]

        def smoothstep(t: float) -> float:
            return 3.0 * t * t - 2.0 * t * t * t  # cubic

        pts = []
        for i in range(1, num_points + 1):
            t = i / num_points  # (0,1]
            y = curr + (target - curr) * smoothstep(t)
            pts.append(y)
        return pts

    @staticmethod
    def _is_valid_doa(doa: Optional[float]) -> bool:
        return doa is not None and (not math.isnan(doa)) and (-180.0 <= doa <= 180.0)

    @staticmethod
    def _is_valid_point(p: Optional[Point3D]) -> bool:
        if p is None:
            return False
        return all(not math.isnan(v) for v in (p.x, p.y, p.z))


# =========================
# 使用示例
# =========================
if __name__ == "__main__":
    # 1) 创建下位机控制器
    robot = create_robot_controller(port="/dev/ttyUSB0", baudrate=115200)  # :contentReference[oaicite:2]{index=2}
    robot.open_serial()

    # 2) 配置板号映射（你把实际 neck/waist 的板号填上）
    yaw_cfg = YawBoardConfig(
        neck_board_id=2,   # TODO: 改成你的 neck yaw 板号
        waist_board_id=3,  # TODO: 改成你的 waist yaw 板号
        neck_use_a01=True,
        waist_use_a01=True,
        neck_other_hold_angle=180.0,
        waist_other_hold_angle=180.0,
    )

    ctrl = SearchAndFollowController(robot=robot, yaw_cfg=yaw_cfg)

    # 3) 模拟一个用户状态：被唤醒但不在视野内，有 doa_angle 线索
    user = UserState(
        user_id=0,
        is_in_fov=False,
        doa_angle=30.0,
        is_waked_up=True,
        is_interaction=False,
        status=InteractionStatus.LOST
    )

    try:
        ctrl.update_robot_behavior(user, need_follow=True)
    finally:
        robot.close_serial()