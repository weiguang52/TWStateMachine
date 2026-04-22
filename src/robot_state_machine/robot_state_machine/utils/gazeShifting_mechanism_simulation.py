# head_body_policy.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
import time
import math


@dataclass
class HeadBodyPolicyConfig:
    # 小范围阈值：<45° 头先动
    head_only_deg: float = 45.0

    # 小范围：头保持偏转超过多久才开始带身体
    body_align_delay_s: float = 0.8

    # 身体追赶强度（0~1），越大身体越快追上目标
    body_catchup_gain_small: float = 0.6
    body_catchup_gain_large: float = 0.8

    # 跟随死区/迟滞（用于跟随环可选）
    follow_deadzone_deg: float = 5.0
    follow_hysteresis_deg: float = 1.0


@dataclass
class HeadBodyPolicyState:
    """跨周期状态：用于实现‘头先转一段时间再带身’这类逻辑"""
    head_hold_since_s: Optional[float] = None
    follow_active: bool = False


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def apply_deadzone_hysteresis(
    yaw_err: float,
    cfg: HeadBodyPolicyConfig,
    st: HeadBodyPolicyState,
) -> float:
    """±deadzone 的迟滞：避免跟随时抖动频繁抽搐。"""
    dz = cfg.follow_deadzone_deg
    hy = cfg.follow_hysteresis_deg

    if (not st.follow_active) and abs(yaw_err) >= (dz + hy):
        st.follow_active = True
    if st.follow_active and abs(yaw_err) <= dz:
        st.follow_active = False

    return yaw_err if st.follow_active else 0.0


def compute_head_body_targets(
    target_yaw_deg: float,
    neck_cur_deg: float,
    waist_cur_deg: float,
    neck_min_deg: float,
    neck_max_deg: float,
    waist_min_deg: float,
    waist_max_deg: float,
    cfg: HeadBodyPolicyConfig,
    st: HeadBodyPolicyState,
    now_s: Optional[float] = None,
) -> Tuple[float, float]:
    """
    头身解耦协同策略（按你描述）：
    - 小范围(<head_only_deg)：头先转，身体不动；若头偏转保持超过 delay，则身体追赶并让头回正
    - 大范围(>=head_only_deg)：头继续盯目标，同时身体更快追赶；最终 waist 对齐目标、neck 回正
    """
    if now_s is None:
        now_s = time.time()

    # 身体最终希望对齐的方向（在腰限位内）
    waist_goal = clamp(target_yaw_deg, waist_min_deg, waist_max_deg)

    # ========= 小范围：头先转 =========
    if abs(target_yaw_deg) < cfg.head_only_deg:
        # 头先转到目标（相对身体）
        neck_goal = clamp(target_yaw_deg - waist_cur_deg, neck_min_deg, neck_max_deg)

        # 记录“头保持偏转”的起始时间
        if abs(neck_goal) > 1e-3:
            if st.head_hold_since_s is None:
                st.head_hold_since_s = now_s
        else:
            st.head_hold_since_s = None

        # 到时间后带身体回正
        if st.head_hold_since_s is not None and (now_s - st.head_hold_since_s) > cfg.body_align_delay_s:
            waist_cmd = waist_cur_deg + (waist_goal - waist_cur_deg) * cfg.body_catchup_gain_small
            waist_cmd = clamp(waist_cmd, waist_min_deg, waist_max_deg)
            neck_cmd = clamp(target_yaw_deg - waist_cmd, neck_min_deg, neck_max_deg)
            return neck_cmd, waist_cmd

        # 时间未到：只动头
        return neck_goal, waist_cur_deg

    # ========= 大范围：身体开始跟随 =========
    st.head_hold_since_s = None  # 大范围时不需要这个计时
    waist_cmd = waist_cur_deg + (waist_goal - waist_cur_deg) * cfg.body_catchup_gain_large
    waist_cmd = clamp(waist_cmd, waist_min_deg, waist_max_deg)
    neck_cmd = clamp(target_yaw_deg - waist_cmd, neck_min_deg, neck_max_deg)
    return neck_cmd, waist_cmd

def wrap_to_180(deg: float) -> float:
    """把角度归一化到 [-180, 180)"""
    x = (deg + 180.0) % 360.0 - 180.0
    return x

def bearing_yaw_deg(p) -> float:
    """
    把一个 3D 点转成水平面方位角 yaw（deg）。
    约定：x=右，z=前；yaw=atan2(x, z)
    """
    return math.degrees(math.atan2(p.x, max(p.z, 1e-6)))

def vision_pos_to_yaw_delta_deg(
    target_location,
    ref_pos: Optional[object] = None,
    current_yaw_deg: Optional[float] = None,
) -> float:
    """
    输出“需要转多少 yaw（deg）”的 Δyaw。

    - 若提供 ref_pos：Δyaw = yaw(target) - yaw(ref_pos)   (做法B：相对上一帧视线)
    - 否则若提供 current_yaw_deg：Δyaw = yaw(target) - current_yaw_deg  (做法A：相对当前头+腰)
    - 两者都不提供：直接返回 yaw(target)（退化为绝对目标 yaw）
    """
    yaw_tgt = bearing_yaw_deg(target_location)

    if ref_pos is not None:
        yaw_ref = bearing_yaw_deg(ref_pos)
        return wrap_to_180(yaw_tgt - yaw_ref)

    if current_yaw_deg is not None:
        return wrap_to_180(yaw_tgt - current_yaw_deg)

    return wrap_to_180(yaw_tgt)