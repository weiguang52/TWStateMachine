#!/usr/bin/env python3
"""
跟随模块 - 完整实现
支持视觉锁定、演讲者模式、动作输出时的智能跟随策略
"""
import json
import time
from enum import Enum
from typing import Optional, Dict, List, Tuple

from utils.gazeShifting_mechanism_simulation import HeadBodyCoordinator

class FollowMode(Enum):
    """跟随模式"""
    VISUAL_LOCK = "visual_lock"            # 情况1：视觉锁定跟随
    SPEAKER_MODE = "speaker_mode"          # 情况2：演讲者模式
    MOTION_OUTPUT = "motion_output"        # 情况3：动作输出时跟随


class MotionPriority(Enum):
    """动作优先级"""
    LOW = "low"          # 低优先级：可随时打断
    MEDIUM = "medium"    # 中优先级：视野边缘时打断
    HIGH = "high"        # 高优先级：完全丢失时才打断


class FollowModule:
    def __init__(self, parent_node):
        self.parent_node = parent_node
        self.logger = parent_node.get_logger()

        # ========== 添加头身协同控制器 ==========
        self.head_body_coordinator = HeadBodyCoordinator(
            dead_zone_deg=5.0,
            small_turn_threshold_deg=45.0,
            head_timeout_sec=2.0,
            control_frequency_hz=100.0
        )
        # =======================================
        
        # ========== 跟随状态 ==========
        self.target_lost = False
        self.lost_count = 0
        self.lost_threshold = 30  # 3秒（假设10Hz更新）
        self.follow_count = 0
        
        # ========== 跟随模式 ==========
        self.current_mode = FollowMode.VISUAL_LOCK
        
        # ========== 目标用户信息 ==========
        self.primary_user_id = None          # 主交互用户ID
        self.primary_user_position = None    # 主交互用户位置
        self.last_primary_seen_time = None   # 上次看到主用户的时间
        
        # ========== 演讲者模式相关 ==========
        self.speaker_mode_active = False
        self.other_users = []                 # 其他用户列表
        self.gaze_target = None               # 当前注视目标
        self.gaze_switch_time = None          # 上次切换注视的时间
        self.gaze_duration_primary = 4.0      # 注视主用户时长（秒）
        self.gaze_duration_others = 1.0       # 注视其他用户时长（秒）
        self.attention_ratio = 0.8            # 80/20分配比例
        
        # ========== 动作输出模式相关 ==========
        self.is_outputting_motion = False     # 是否正在输出动作
        self.current_motion_priority = MotionPriority.LOW
        self.motion_start_time = None
        self.motion_expected_duration = 0.0
        self.motion_can_interrupt = True
        
        # ========== 视野边缘检测 ==========
        self.view_center_threshold = 15.0     # 视野中心范围（度）
        self.view_edge_threshold = 45.0       # 视野边缘阈值（度）
        self.view_lost_threshold = 60.0       # 视野完全丢失阈值（度）
        
        # ========== 用户位置追踪 ==========
        self.user_last_position = None        # 用户最后位置
        self.user_movement_velocity = 0.0     # 用户移动速度
        
        self.logger.info('[跟随模块] 初始化完成')
    
    def reset(self):
        """重置跟随模块"""
        self.logger.info('[跟随模块] 重置')
        self.target_lost = False
        self.lost_count = 0
        self.follow_count = 0
        
        # 重置模式
        self.current_mode = FollowMode.VISUAL_LOCK
        
        # 重置用户信息
        self.primary_user_id = None
        self.primary_user_position = None
        self.last_primary_seen_time = None
        
        # 重置演讲者模式
        self.speaker_mode_active = False
        self.other_users = []
        self.gaze_target = None
        self.gaze_switch_time = None
        
        # 重置动作输出状态
        self.is_outputting_motion = False
        self.motion_start_time = None
    
    def set_primary_user(self, user_id: str):
        """
        设置主交互用户
        
        Args:
            user_id: 主用户ID
        """
        self.primary_user_id = user_id
        self.logger.info(f'[跟随模块] 设置主用户: {user_id}')
    
    def set_follow_mode(self, mode: FollowMode):
        """
        设置跟随模式
        
        Args:
            mode: 跟随模式
        """
        if self.current_mode != mode:
            self.logger.info(f'[跟随模块] 切换模式: {self.current_mode.value} -> {mode.value}')
            self.current_mode = mode
    
    def start_motion_output(self, motion_name: str, duration: float, 
                           priority: MotionPriority = MotionPriority.MEDIUM):
        """
        开始输出动作
        
        Args:
            motion_name: 动作名称
            duration: 动作预期时长（秒）
            priority: 动作优先级
        """
        self.is_outputting_motion = True
        self.current_motion_priority = priority
        self.motion_start_time = time.time()
        self.motion_expected_duration = duration
        
        # 根据优先级设置是否可打断
        self.motion_can_interrupt = (priority == MotionPriority.LOW)
        
        # 切换到动作输出模式
        self.set_follow_mode(FollowMode.MOTION_OUTPUT)
        
        self.logger.info(f'[跟随模块] 开始输出动作: {motion_name}, '
                        f'时长: {duration}s, 优先级: {priority.value}')
    
    def stop_motion_output(self):
        """停止动作输出"""
        if self.is_outputting_motion:
            self.logger.info('[跟随模块] 动作输出完成')
            self.is_outputting_motion = False
            self.motion_start_time = None
            
            # 恢复到视觉锁定模式
            self.set_follow_mode(FollowMode.VISUAL_LOCK)
    
    def enable_speaker_mode(self, other_users: List[str] = None):
        """
        启用演讲者模式
        
        Args:
            other_users: 其他用户ID列表
        """
        self.speaker_mode_active = True
        self.other_users = other_users or []
        self.gaze_target = self.primary_user_id
        self.gaze_switch_time = time.time()
        
        self.set_follow_mode(FollowMode.SPEAKER_MODE)
        
        self.logger.info(f'[跟随模块] 启用演讲者模式, 其他用户: {len(self.other_users)}人')
    
    def disable_speaker_mode(self):
        """禁用演讲者模式"""
        if self.speaker_mode_active:
            self.logger.info('[跟随模块] 禁用演讲者模式')
            self.speaker_mode_active = False
            self.set_follow_mode(FollowMode.VISUAL_LOCK)
    
    def execute(self, vision_info, audio_info=None, motion_status=None):
        """
        执行跟随逻辑
        
        Args:
            vision_info: 视觉信息（包含多人检测）
            audio_info: 声觉信息（可选）
            motion_status: 动作输出状态（可选）
        
        Returns:
            bool: 目标是否丢失
        """
        self.follow_count += 1
        current_time = time.time()
        
        # 解析传感器数据
        vision_data = self._parse_vision_info(vision_info)
        audio_data = self._parse_audio_info(audio_info) if audio_info else {}
        
        # 更新动作状态
        if motion_status:
            self._update_motion_status(motion_status)
        
        # 根据当前模式执行相应策略
        if self.current_mode == FollowMode.VISUAL_LOCK:
            # 情况1：视觉锁定跟随
            result = self._execute_visual_lock(vision_data, current_time)
            
        elif self.current_mode == FollowMode.SPEAKER_MODE:
            # 情况2：演讲者模式
            result = self._execute_speaker_mode(vision_data, current_time)
            
        elif self.current_mode == FollowMode.MOTION_OUTPUT:
            # 情况3：动作输出时跟随
            result = self._execute_motion_output_follow(vision_data, current_time)
            
        else:
            result = False
        
        self.target_lost = not result
        return self.target_lost
    
    # ========================================================================
    # 情况1：视觉锁定跟随
    # ========================================================================
    def _execute_visual_lock(self, vision_data: Dict, current_time: float) -> bool:
        """
        执行视觉锁定跟随
        
        策略：保持目标用户在视觉中心位置
        
        Returns:
            bool: 是否成功跟随（True=成功，False=丢失）
        """
        # 查找主用户
        primary_user = self._find_user_in_vision(vision_data, self.primary_user_id)
        
        if primary_user:
            # 找到主用户
            self.lost_count = 0
            self.last_primary_seen_time = current_time
            
            position = primary_user.get("position")
            angle = position.get("angle", 0) if position else 0
            distance = position.get("distance", 0) if position else 0
            
            # 更新用户位置
            self._update_user_position(position, current_time)
            
            # 计算是否在视野中心
            in_center = abs(angle) < self.view_center_threshold
            
            if self.follow_count % 10 == 0 or not in_center:
                self.logger.info(f'[视觉锁定] 跟随主用户: 角度={angle:.1f}°, '
                                f'距离={distance:.2f}m, {"中心" if in_center else "偏离"}')
            
            # 生成跟随控制指令
            self._generate_visual_lock_control(angle, distance)
            
            return True
        
        else:
            # 未找到主用户
            self.lost_count += 1
            
            if self.lost_count >= self.lost_threshold:
                self.logger.warning(f'[视觉锁定] 目标丢失超过{self.lost_threshold}次')
                return False
            else:
                if self.lost_count % 10 == 0:
                    self.logger.info(f'[视觉锁定] 目标暂时丢失 ({self.lost_count}/{self.lost_threshold})')
                
                # 尝试预测位置或保持最后姿态
                self._handle_temporary_loss()
                
                return True  # 暂时丢失不算完全失败
    
    def _generate_visual_lock_control(self, angle: float, distance: float):
        """
        生成视觉锁定控制指令
        
        Args:
            angle: 目标相对角度（度）
            distance: 目标距离（米）
        """
        # TODO: 调用头身协同控制器
        # 策略：保持用户在视野中心
        
        # 如果偏离中心，转向用户
        if abs(angle) > self.view_center_threshold:
            self._turn_to_user(angle)
        
        # 如果距离过远或过近，调整底盘
        # TODO: 调用底盘控制接口
        # self._adjust_distance(distance)
    
    # ========================================================================
    # 情况2：演讲者模式
    # ========================================================================
    def _execute_speaker_mode(self, vision_data: Dict, current_time: float) -> bool:
        """
        执行演讲者模式
        
        策略：80%看主用户，20%扫视其他用户
        
        Returns:
            bool: 是否成功跟随
        """
        # 查找所有用户
        all_users = vision_data.get("users", [])
        
        if not all_users:
            self.lost_count += 1
            if self.lost_count >= self.lost_threshold:
                self.logger.warning('[演讲者模式] 所有用户丢失')
                return False
            return True
        
        self.lost_count = 0
        
        # 检查是否需要切换注视目标
        if self._should_switch_gaze(current_time):
            self._switch_gaze_target(all_users)
        
        # 找到当前注视目标
        gaze_user = self._find_user_in_vision(vision_data, self.gaze_target)
        
        if gaze_user:
            position = gaze_user.get("position")
            angle = position.get("angle", 0) if position else 0
            
            if self.follow_count % 10 == 0:
                is_primary = (self.gaze_target == self.primary_user_id)
                self.logger.info(f'[演讲者模式] 注视{"主用户" if is_primary else "其他用户"}: '
                                f'角度={angle:.1f}°')
            
            # 平滑转向注视目标
            self._turn_to_user(angle, smooth=True)
        
        return True
    
    def _should_switch_gaze(self, current_time: float) -> bool:
        """
        判断是否应该切换注视目标
        
        Returns:
            bool: 是否应该切换
        """
        if self.gaze_switch_time is None:
            return True
        
        elapsed = current_time - self.gaze_switch_time
        
        # 如果当前注视主用户，持续时间更长
        if self.gaze_target == self.primary_user_id:
            return elapsed > self.gaze_duration_primary
        else:
            return elapsed > self.gaze_duration_others
    
    def _switch_gaze_target(self, all_users: List[Dict]):
        """
        切换注视目标
        
        实现80/20分配策略
        
        Args:
            all_users: 视野中所有用户列表
        """
        import random
        
        # 80%概率看主用户，20%概率看其他用户
        if random.random() < self.attention_ratio:
            # 看主用户
            self.gaze_target = self.primary_user_id
            self.logger.info('[演讲者模式] 切换注视 -> 主用户')
        else:
            # 看其他用户
            other_users_in_view = [
                u for u in all_users 
                if u.get("user_id") != self.primary_user_id
            ]
            
            if other_users_in_view:
                # 随机选择一个其他用户
                target_user = random.choice(other_users_in_view)
                self.gaze_target = target_user.get("user_id")
                self.logger.info(f'[演讲者模式] 切换注视 -> 其他用户: {self.gaze_target}')
            else:
                # 没有其他用户，继续看主用户
                self.gaze_target = self.primary_user_id
        
        self.gaze_switch_time = time.time()
    
    # ========================================================================
    # 情况3：动作输出时跟随策略
    # ========================================================================
    def _execute_motion_output_follow(self, vision_data: Dict, current_time: float) -> bool:
        """
        执行动作输出时的跟随策略
        
        核心矛盾：动作完整性 vs 用户跟随
        
        策略：
        1. 用户在视野中心 -> 继续输出动作
        2. 用户到达视野边缘 -> 支架带动转向
        3. 用户完全消失 -> 逐渐停止动作（接口）
        
        Returns:
            bool: 是否成功跟随
        """
        # 检查动作是否完成
        if self._is_motion_completed(current_time):
            self.logger.info('[动作输出] 动作已完成，恢复正常跟随')
            self.stop_motion_output()
            
            # 快速对准用户最新位置
            primary_user = self._find_user_in_vision(vision_data, self.primary_user_id)
            if primary_user:
                position = primary_user.get("position")
                angle = position.get("angle", 0) if position else 0
                self.logger.info(f'[动作输出] 动作完成后快速对准: {angle:.1f}°')
                self._turn_to_user(angle, fast=True)
            
            return True
        
        # 动作进行中，检查用户位置
        primary_user = self._find_user_in_vision(vision_data, self.primary_user_id)
        
        if primary_user:
            position = primary_user.get("position")
            angle = position.get("angle", 0) if position else 0
            
            # 判断用户在视野中的位置
            if abs(angle) < self.view_center_threshold:
                # 流程1：用户在视野中心，继续输出动作
                if self.follow_count % 20 == 0:
                    self.logger.info(f'[动作输出] 用户在视野中心，继续输出动作')
                return True
                
            elif abs(angle) < self.view_edge_threshold:
                # 流程2：用户在视野边缘，支架带动转向
                self.logger.info(f'[动作输出] 用户到达边缘({angle:.1f}°)，支架带动转向')
                self._base_driven_turn(angle)
                return True
                
            else:
                # 流程3：用户接近完全丢失
                self.logger.warning(f'[动作输出] 用户接近丢失({angle:.1f}°)')
                
                # TODO: 调用逐渐停止动作接口
                self._gradually_stop_motion()
                
                return True  # 暂时还算跟随
        
        else:
            # 用户完全消失
            self.lost_count += 1
            
            if self.lost_count > 5:  # 快速判断（0.5秒）
                self.logger.warning('[动作输出] 用户完全消失，停止动作')
                
                # TODO: 调用逐渐停止动作接口
                self._gradually_stop_motion()
                
            if self.lost_count >= self.lost_threshold:
                return False
            
            return True
    
    def _is_motion_completed(self, current_time: float) -> bool:
        """
        判断动作是否完成
        
        Returns:
            bool: 是否完成
        """
        if not self.is_outputting_motion or self.motion_start_time is None:
            return True
        
        elapsed = current_time - self.motion_start_time
        return elapsed >= self.motion_expected_duration
    
    def _base_driven_turn(self, angle: float):
        """
        支架带动转向（底盘缓慢转向，不破坏动作）
        
        策略：在输出动作的同时，底盘缓慢转向用户方向
        
        Args:
            angle: 转向角度（度）
        """
        self.logger.info(f'[动作输出] 底盘缓慢转向: {angle:.1f}°')
        
        # 计算非常慢的转向速度（不破坏上半身动作）
        # 目标：1秒内转动约5度
        max_angular_velocity_deg_per_sec = 5.0  # 度/秒（很慢）
        
        # 根据角度大小调整速度
        if abs(angle) < 30:
            angular_velocity = angle * 0.1  # 10%的速度
        else:
            angular_velocity = angle * 0.05  # 5%的速度
        
        # 限制最大速度
        angular_velocity = min(
            abs(angular_velocity), 
            max_angular_velocity_deg_per_sec
        ) * (1 if angle > 0 else -1)
        
        # TODO: 发送底盘控制指令
        # 方法1: 直接控制底盘
        # self.parent_node.base_controller.set_angular_velocity(angular_velocity)
        
        # 方法2: 发布ROS Twist消息
        # from geometry_msgs.msg import Twist
        # twist = Twist()
        # twist.angular.z = math.radians(angular_velocity)
        # self.parent_node.cmd_vel_pub.publish(twist)
        
        self.logger.debug(f'[动作输出] 底盘角速度: {angular_velocity:.2f}°/s')
    
    def _gradually_stop_motion(self):
        """
        逐渐停止当前动作
        
        策略：平滑过渡到停止姿态，不是突然停止
        """
        self.logger.info('[动作输出] 逐渐停止动作')
        
        # TODO: 调用动作插值器或运动控制器
        # 
        # 方法1: 使用MotionInterpolator过渡到idle姿态
        # if hasattr(self.parent_node, 'motion_interpolator'):
        #     current_motion = self.parent_node.get_current_motion()
        #     idle_pose = self.parent_node.get_idle_pose()
        #     
        #     transition = self.parent_node.motion_interpolator.run(
        #         action_A=current_motion,
        #         action_B=idle_pose,
        #         is_smooth=True,
        #         target_fps=20,
        #         index_A=self.parent_node.current_frame_index,
        #         index_B=0
        #     )
        #     self.parent_node.execute_transition(transition)
        
        # 方法2: 调用运动控制器平滑停止
        # if hasattr(self.parent_node, 'motion_controller'):
        #     self.parent_node.motion_controller.stop_smoothly(duration=0.5)
        
        # 方法3: 简化版 - 线性插值到idle姿态
        # current_angles = self._get_current_joint_angles()
        # idle_angles = self._get_idle_joint_angles()
        # self._interpolate_to_pose(current_angles, idle_angles, duration=0.5)
        
        # 标记动作已停止
        self.is_outputting_motion = False
        
        self.logger.debug('[动作输出] 动作停止完成')
    
    # ========================================================================
    # 辅助功能
    # ========================================================================
    
    def _find_user_in_vision(self, vision_data: Dict, user_id: str) -> Optional[Dict]:
        """
        在视觉数据中查找指定用户
        
        Args:
            vision_data: 视觉数据
            user_id: 用户ID
        
        Returns:
            Dict: 用户信息，未找到返回None
        """
        users = vision_data.get("users", [])
        
        for user in users:
            if user.get("user_id") == user_id or user.get("face_id") == user_id:
                return user
        
        return None
    
    def _update_user_position(self, position: Dict, current_time: float):
        """
        更新用户位置，计算移动速度
        
        Args:
            position: 用户位置
            current_time: 当前时间
        """
        if self.user_last_position and position:
            # 计算移动速度（简化）
            dx = position.get("x", 0) - self.user_last_position.get("x", 0)
            dy = position.get("y", 0) - self.user_last_position.get("y", 0)
            distance = (dx**2 + dy**2)**0.5
            
            time_delta = current_time - getattr(self, 'last_position_update_time', current_time)
            if time_delta > 0:
                self.user_movement_velocity = distance / time_delta
        
        self.user_last_position = position
        self.last_position_update_time = current_time
    
    def _handle_temporary_loss(self):
        """
        处理目标暂时丢失的情况
        
        策略：
        - 短时间丢失：保持当前姿态，等待重新出现
        - 有运动趋势：预测方向并转向
        """
        if self.user_last_position:
            # 保持最后姿态
            self.logger.debug('[跟随] 保持最后姿态，等待目标重新出现')
            
            # TODO: 可以加入运动预测
            # if self.user_movement_velocity > threshold:
            #     predicted_angle = self._predict_user_direction()
            #     self._turn_to_user(predicted_angle)
    
    def _turn_to_user(self, angle: float, smooth: bool = False, fast: bool = False):
        """
        转向用户（使用头身协同控制器）
        
        Args:
            angle: 转向角度（度）
            smooth: 是否平滑转向（演讲者模式）
            fast: 是否快速转向（动作完成后）
        """
        mode_str = "平滑" if smooth else ("快速" if fast else "正常")
        self.logger.debug(f'[控制] {mode_str}转向: {angle:.1f}°')
        
        try:
            # 获取当前角度
            current_head_angle = self._get_current_head_angle()
            current_body_angle = self._get_current_body_angle()
            
            # 调用头身协同控制器
            self.head_body_coordinator.update(
                desired_head_direction=angle,
                current_head_angle=current_head_angle,
                current_body_angle=current_body_angle
            )
            
            # 注意：smooth和fast参数在当前HeadBodyCoordinator中没有实现
            # 如果需要，可以在HeadBodyCoordinator中添加速度控制参数
            
        except Exception as e:
            self.logger.error(f'[控制] 转向失败: {e}')

    def _get_current_head_angle(self) -> float:
        """
        获取当前头部角度
        
        Returns:
            float: 头部角度（度），相对于身体中线
        """
        # TODO: 从实际传感器读取
        # 方法1: 从parent_node读取
        # if hasattr(self.parent_node, 'current_head_angle'):
        #     return self.parent_node.current_head_angle
        
        # 方法2: 从头身协同控制器获取
        return self.head_body_coordinator.current_head_angle

    def _get_current_body_angle(self) -> float:
        """
        获取当前身体角度
        
        Returns:
            float: 身体角度（度），绝对角度
        """
        # TODO: 从实际传感器读取
        # 方法1: 从parent_node读取
        # if hasattr(self.parent_node, 'current_body_angle'):
        #     return self.parent_node.current_body_angle
        
        # 方法2: 从头身协同控制器获取
        return self.head_body_coordinator.current_body_angle
    
    def _update_motion_status(self, motion_status: Dict):
        """
        更新动作状态（外部传入）
        
        Args:
            motion_status: 动作状态字典
                {
                    "is_playing": bool,
                    "motion_name": str,
                    "progress": float,  # 0.0~1.0
                    "can_interrupt": bool
                }
        """
        is_playing = motion_status.get("is_playing", False)
        
        if is_playing and not self.is_outputting_motion:
            # 外部开始了新动作
            motion_name = motion_status.get("motion_name", "unknown")
            self.logger.info(f'[跟随模块] 检测到外部动作: {motion_name}')
            # 可以自动切换到动作输出模式
            
        elif not is_playing and self.is_outputting_motion:
            # 动作已结束
            self.stop_motion_output()
    
    # ========================================================================
    # 数据解析
    # ========================================================================
    
    def _parse_vision_info(self, vision_info) -> Dict:
        """
        解析视觉信息（支持多人检测）
        
        Returns:
            {
                "users": [
                    {
                        "user_id": "user_123",
                        "face_id": "face_456",
                        "position": {"x": 1.0, "y": 0.5, "angle": 30.0, "distance": 1.5},
                        "confidence": 0.95
                    },
                    ...
                ],
                "primary_user_detected": bool
            }
        """
        if vision_info is None:
            return {"users": [], "primary_user_detected": False}
        
        try:
            data = json.loads(vision_info) if isinstance(vision_info, str) else vision_info
            
            # 支持两种格式：
            # 格式1：单用户检测 (向后兼容)
            if "target_detected" in data or "face_detected" in data:
                detected = data.get("target_detected") or data.get("face_detected", False)
                if detected:
                    user_id = data.get("user_id") or data.get("face_id")
                    users = [{
                        "user_id": user_id,
                        "face_id": user_id,
                        "position": data.get("position") or data.get("target_position"),
                        "confidence": data.get("confidence", 0.0)
                    }]
                else:
                    users = []
            
            # 格式2：多用户检测
            elif "users" in data:
                users = data.get("users", [])
            else:
                users = []
            
            # 检查主用户是否在视野中
            primary_detected = any(
                u.get("user_id") == self.primary_user_id or 
                u.get("face_id") == self.primary_user_id
                for u in users
            )
            
            return {
                "users": users,
                "primary_user_detected": primary_detected
            }
        
        except Exception as e:
            self.logger.error(f'[跟随模块] 解析视觉信息失败: {e}')
            return {"users": [], "primary_user_detected": False}
    
    def _parse_audio_info(self, audio_info) -> Dict:
        """解析声觉信息"""
        if audio_info is None:
            return {
                "sound_detected": False,
                "direction": None,
                "voice_id": None
            }
        
        try:
            data = json.loads(audio_info) if isinstance(audio_info, str) else audio_info
            return {
                "sound_detected": data.get("sound_detected", False),
                "direction": data.get("direction"),
                "voice_id": data.get("voice_id")
            }
        except:
            return {
                "sound_detected": False,
                "direction": None,
                "voice_id": None
            }