#!/usr/bin/env python3
"""
搜索模块 - 完整实现
支持多路径搜寻策略，包括声源定位、视觉定位、触觉传感器引导
"""
import json
import time
from enum import Enum
from typing import Optional, Dict, Any

from utils.gazeShifting_mechanism_simulation import HeadBodyCoordinator


class WakeupType(Enum):
    """唤醒类型"""
    VOICE_ONLY = "voice_only"           # 仅语音唤醒（模糊唤醒词）
    VOICE_VISION = "voice_vision"       # 视听融合唤醒
    VISION_ONLY = "vision_only"         # 视觉唤醒
    TOUCH = "touch"                     # 触觉唤醒（物理接触）
    MOVED = "moved"                     # 被移动
    NONE = "none"                       # 无唤醒


class UserType(Enum):
    """用户类型"""
    REGISTERED = "registered"    # 注册用户
    GUEST = "guest"             # 陌生访客（临时用户）
    UNKNOWN = "unknown"         # 未知


class SearchPath(Enum):
    """搜寻路径"""
    AUDIO_GUIDED = "audio_guided"       # 路径一：声源定位引导
    VISION_GUIDED = "vision_guided"     # 路径二：视觉定位引导
    TOUCH_GUIDED = "touch_guided"       # 路径三：触觉传感器引导
    GUEST_MODE = "guest_mode"           # 陌生访客模式
    IDLE = "idle"                       # 空闲


class SearchModule:
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
        
        # ========== 搜索状态 ==========
        self.target_found = False
        self.search_count = 0
        self.current_search_path = SearchPath.IDLE
        
        # ========== 唤醒信息 ==========
        self.wakeup_type = WakeupType.NONE
        self.wakeup_user_id = None          # 唤醒用户的ID（声纹ID或视觉ID）
        self.wakeup_source = None           # 唤醒源信息（方向、传感器位置等）
        
        # ========== 用户身份信息 ==========
        self.target_user_type = UserType.UNKNOWN
        self.target_user_id = None
        self.target_user_nickname = None
        
        # ========== 搜寻状态机 ==========
        self.audio_search_state = "init"    # 声源搜寻状态：init, turning, verifying, reverse_scan
        self.audio_search_start_time = None
        self.audio_initial_direction = None
        self.audio_reverse_searched = False
        
        # ========== 触觉搜寻状态 ==========
        self.touch_sensor_position = None   # 被触摸的传感器位置
        self.is_being_moved = False
        self.movement_stable_time = None
        
        # ========== 身份校验 ==========
        self.detected_face_id = None
        self.detected_voice_id = None
        self.identity_conflict = False
        
        self.logger.info('[搜索模块] 初始化完成')
    
    def reset(self):
        """重置搜索模块"""
        self.logger.info('[搜索模块] 重置')
        self.target_found = False
        self.search_count = 0
        self.current_search_path = SearchPath.IDLE
        
        # 重置唤醒信息
        self.wakeup_type = WakeupType.NONE
        self.wakeup_user_id = None
        self.wakeup_source = None
        
        # 重置搜寻状态
        self.audio_search_state = "init"
        self.audio_search_start_time = None
        self.audio_initial_direction = None
        self.audio_reverse_searched = False
        
        self.touch_sensor_position = None
        self.is_being_moved = False
        self.movement_stable_time = None
        
        # 重置身份信息
        self.detected_face_id = None
        self.detected_voice_id = None
        self.identity_conflict = False
    
    def set_wakeup_context(self, wakeup_type: WakeupType, user_id: Optional[str] = None, 
                          source_info: Optional[Dict] = None):
        """
        设置唤醒上下文信息
        
        Args:
            wakeup_type: 唤醒类型
            user_id: 唤醒用户ID（可选）
            source_info: 唤醒源信息（如DOA方向、传感器位置等）
        """
        self.wakeup_type = wakeup_type
        self.wakeup_user_id = user_id
        self.wakeup_source = source_info
        
        self.logger.info(f'[搜索模块] 设置唤醒上下文: 类型={wakeup_type.value}, 用户={user_id}')
        
        # 根据唤醒类型选择搜寻路径
        self._determine_search_path()
    
    def _determine_search_path(self):
        """根据唤醒类型确定搜寻路径"""
        if self.wakeup_type == WakeupType.VOICE_ONLY:
            # 路径一：仅语音唤醒，声源定位引导
            self.current_search_path = SearchPath.AUDIO_GUIDED
            self.logger.info('[搜索模块] 选择路径一：声源定位引导搜寻')
            
        elif self.wakeup_type in [WakeupType.VOICE_VISION, WakeupType.VISION_ONLY]:
            # 路径二：视听融合或视觉唤醒，视觉定位引导
            self.current_search_path = SearchPath.VISION_GUIDED
            self.logger.info('[搜索模块] 选择路径二：视觉定位引导搜寻')
            
        elif self.wakeup_type in [WakeupType.TOUCH, WakeupType.MOVED]:
            # 路径三：物理唤醒，触觉传感器引导
            self.current_search_path = SearchPath.TOUCH_GUIDED
            self.logger.info('[搜索模块] 选择路径三：触觉传感器引导搜寻')
            
        else:
            self.current_search_path = SearchPath.IDLE
    
    def execute(self, vision_info, audio_info, touch_info=None, imu_info=None):
        """
        执行搜索逻辑
        
        Args:
            vision_info: 视觉信息
            audio_info: 声觉信息
            touch_info: 触觉传感器信息（可选）
            imu_info: IMU信息（检测移动，可选）
        
        Returns:
            bool: 是否找到目标
        """
        self.search_count += 1
        
        # 解析传感器数据
        vision_data = self._parse_vision_info(vision_info)
        audio_data = self._parse_audio_info(audio_info)
        touch_data = self._parse_touch_info(touch_info) if touch_info else None
        imu_data = self._parse_imu_info(imu_info) if imu_info else None
        
        # 根据当前搜寻路径执行相应策略
        if self.current_search_path == SearchPath.AUDIO_GUIDED:
            result = self._execute_audio_guided_search(vision_data, audio_data)
            
        elif self.current_search_path == SearchPath.VISION_GUIDED:
            result = self._execute_vision_guided_search(vision_data, audio_data)
            
        elif self.current_search_path == SearchPath.TOUCH_GUIDED:
            result = self._execute_touch_guided_search(vision_data, audio_data, touch_data, imu_data)
            
        elif self.current_search_path == SearchPath.GUEST_MODE:
            result = self._execute_guest_mode_search(vision_data)
            
        else:
            # IDLE状态，不执行搜索
            result = False
        
        self.target_found = result
        return result
    
    # ========================================================================
    # 路径一：声源定位引导搜寻
    # ========================================================================
    def _execute_audio_guided_search(self, vision_data: Dict, audio_data: Dict) -> bool:
        """
        执行声源定位引导搜寻
        
        策略：
        1. 快速转向声源方向
        2. 检测人脸并验证身份
        3. 若失败，执行反方向扫视
        """
        current_time = time.time()
        
        # ========== 状态：初始化 ==========
        if self.audio_search_state == "init":
            # 获取DOA方向
            doa_direction = audio_data.get("doa_direction")
            if doa_direction is None and self.wakeup_source:
                doa_direction = self.wakeup_source.get("doa_direction")
            
            if doa_direction is not None:
                self.audio_initial_direction = doa_direction
                self.audio_search_start_time = current_time
                self.audio_search_state = "turning"
                
                self.logger.info(f'[路径一] 检测到声源方向: {doa_direction:.1f}°，开始转向')
                
                # TODO: 调用头身协同控制器转向
                self._turn_to_direction(doa_direction)
            else:
                self.logger.warning('[路径一] 未获取到DOA方向信息')
                return False
        
        # ========== 状态：转向中 ==========
        elif self.audio_search_state == "turning":
            # 检查是否转向完成（简化：假设1秒完成转向）
            if current_time - self.audio_search_start_time > 1.0:
                self.audio_search_state = "verifying"
                self.logger.info('[路径一] 转向完成，开始身份验证')
        
        # ========== 状态：身份验证 ==========
        elif self.audio_search_state == "verifying":
            # 检查是否捕获到人脸
            if vision_data.get("face_detected"):
                face_id = vision_data.get("face_id")
                voice_id = self.wakeup_user_id  # 声纹ID
                
                self.detected_face_id = face_id
                self.detected_voice_id = voice_id
                
                # 验证身份是否匹配
                if self._verify_identity(face_id, voice_id):
                    self.logger.info(f'[路径一] ✓ 身份验证成功: {face_id}')
                    return True  # 找到目标
                else:
                    # 场景A：发现他人
                    self.logger.warning(f'[路径一] ✗ 身份冲突: 看到{face_id}，但声纹是{voice_id}')
                    self._handle_identity_conflict_scenario_a(face_id, voice_id)
                    
                    # 转入反方向搜寻
                    self.audio_search_state = "reverse_scan"
            else:
                # 等待一段时间后转入反方向搜寻
                if current_time - self.audio_search_start_time > 3.0:
                    self.logger.info('[路径一] 原方向未发现用户，开始反方向搜寻')
                    self.audio_search_state = "reverse_scan"
        
        # ========== 状态：反方向扫视 ==========
        elif self.audio_search_state == "reverse_scan":
            if not self.audio_reverse_searched:
                # 转向相反方向
                reverse_direction = (self.audio_initial_direction + 180) % 360 - 180
                self.logger.info(f'[路径一] 反方向扫视: {reverse_direction:.1f}°')
                
                # TODO: 调用头身协同控制器转向
                self._turn_to_direction(reverse_direction)
                
                self.audio_reverse_searched = True
                self.audio_search_start_time = current_time
            else:
                # 等待转向完成
                if current_time - self.audio_search_start_time > 1.5:
                    # 检查是否找到
                    if vision_data.get("face_detected"):
                        face_id = vision_data.get("face_id")
                        if self._verify_identity(face_id, self.wakeup_user_id):
                            self.logger.info(f'[路径一] ✓ 反方向找到目标: {face_id}')
                            return True
                    
                    # 场景B：未发现任何人
                    self.logger.warning('[路径一] 反方向扫视后仍未发现用户')
                    self._handle_identity_conflict_scenario_b()
                    
                    # 搜寻失败
                    return False
        
        return False
    
    # ========================================================================
    # 路径二：视觉定位引导搜寻
    # ========================================================================
    def _execute_vision_guided_search(self, vision_data: Dict, audio_data: Dict) -> bool:
        """
        执行视觉定位引导搜寻
        
        策略：
        依据视觉中目标用户坐标直接锁定
        """
        if vision_data.get("face_detected"):
            face_id = vision_data.get("face_id")
            position = vision_data.get("position")
            
            self.logger.info(f'[路径二] 检测到人脸: {face_id}, 位置: {position}')
            
            # 转向目标位置
            if position:
                angle = position.get("angle", 0)
                # TODO: 调用头身协同控制器转向
                self._turn_to_direction(angle)
            
            # 身份校验
            voice_id = audio_data.get("voice_id") or self.wakeup_user_id
            
            if voice_id and face_id != voice_id:
                # 场景：人脸ID和声纹ID不匹配
                self.logger.warning(f'[路径二] 身份冲突: 人脸={face_id}, 声纹={voice_id}')
                self._handle_identity_conflict_vision_path(face_id, voice_id)
            
            # 即使有冲突，也锁定视觉目标
            self.detected_face_id = face_id
            return True
        
        else:
            # 未检测到人脸，等待或扫描
            if self.search_count % 10 == 0:
                self.logger.info('[路径二] 等待视觉检测...')
            return False
    
    # ========================================================================
    # 路径三：触觉传感器引导搜寻
    # ========================================================================
    def _execute_touch_guided_search(self, vision_data: Dict, audio_data: Dict, 
                                     touch_data: Optional[Dict], imu_data: Optional[Dict]) -> bool:
        """
        执行触觉传感器引导搜寻
        
        策略：
        1. 检测是否被移动，若被移动则等待稳定
        2. 根据触摸传感器位置转向
        3. 捕获人脸并验证
        """
        # 检测是否被移动
        if imu_data and imu_data.get("is_moving"):
            if not self.is_being_moved:
                self.logger.info('[路径三] 检测到机器人被移动，等待稳定...')
                self.is_being_moved = True
                self.movement_stable_time = None
            return False
        else:
            if self.is_being_moved:
                # 刚停止移动
                if self.movement_stable_time is None:
                    self.movement_stable_time = time.time()
                else:
                    # 等待稳定（如1秒）
                    if time.time() - self.movement_stable_time < 1.0:
                        return False
                    else:
                        self.logger.info('[路径三] 机器人已稳定，开始搜寻')
                        self.is_being_moved = False
        
        # 获取触摸传感器位置
        if self.touch_sensor_position is None and touch_data:
            self.touch_sensor_position = touch_data.get("sensor_position")
            self.logger.info(f'[路径三] 触摸传感器位置: {self.touch_sensor_position}')
        
        if self.touch_sensor_position:
            # 根据传感器位置确定转向方向
            turn_direction = self._get_direction_from_sensor(self.touch_sensor_position)
            
            # TODO: 调用头身协同控制器转向
            self._turn_to_direction(turn_direction)
            
            # 检测人脸
            if vision_data.get("face_detected"):
                face_id = vision_data.get("face_id")
                voice_id = audio_data.get("voice_id")
                
                self.detected_face_id = face_id
                self.detected_voice_id = voice_id
                
                # 身份校验
                if voice_id and face_id != voice_id:
                    # 场景：触觉触发位置与语音不一致
                    self.logger.warning(f'[路径三] 身份冲突: 人脸={face_id}, 声纹={voice_id}')
                    self._handle_identity_conflict_touch_path(face_id, voice_id)
                
                self.logger.info(f'[路径三] ✓ 找到目标: {face_id}')
                return True
        
        return False
    
    # ========================================================================
    # 陌生访客模式
    # ========================================================================
    def _execute_guest_mode_search(self, vision_data: Dict) -> bool:
        """
        执行陌生访客搜寻策略
        
        策略：
        1. 不处理视线外的模糊唤醒词
        2. 视野内有陌生用户则分配临时槽位并跟随
        3. 丢失则直接结束
        """
        if vision_data.get("face_detected"):
            face_id = vision_data.get("face_id")
            
            # 检查是否为陌生用户
            is_stranger = self._check_if_stranger(face_id)
            
            if is_stranger:
                self.logger.info(f'[陌生访客] 检测到陌生用户: {face_id}')
                
                # TODO: 调用用户注册接口，分配临时槽位
                temp_user_id = self._register_temporary_user(face_id, vision_data)
                
                self.target_user_type = UserType.GUEST
                self.target_user_id = temp_user_id
                
                self.logger.info(f'[陌生访客] 分配临时ID: {temp_user_id}，开始跟随')
                return True
        
        return False
    
    # ========================================================================
    # 身份冲突处理
    # ========================================================================
    def _handle_identity_conflict_scenario_a(self, face_id: str, voice_id: str):
        """
        场景A：看到他人B，但声纹是A
        
        策略：向B询问："你看到【A】了吗？我听到他和我讲话，但是我没有看到他？"
        """
        self.identity_conflict = True
        
        voice_nickname = self._get_user_nickname(voice_id)
        
        message = f"你看到{voice_nickname}了吗？我听到他和我讲话，但是我没有看到他？"
        self.logger.info(f'[身份冲突-A] 向{face_id}询问: {message}')
        
        # TODO: 调用TTS接口播放
        self._speak(message)
    
    def _handle_identity_conflict_scenario_b(self):
        """
        场景B：扫视后没有发现任何人
        
        策略：先回答唤醒问题，随后询问："你在哪呀，我都没有看见你？"
        """
        self.identity_conflict = True
        
        # TODO: 先回答唤醒问题（这部分逻辑在对话模块）
        
        message = "你在哪呀，我都没有看见你？"
        self.logger.info(f'[身份冲突-B] {message}')
        
        # TODO: 调用TTS接口播放
        self._speak(message)
        
        # TODO: 执行复位动作
        self._reset_pose()
    
    def _handle_identity_conflict_vision_path(self, face_id: str, voice_id: str):
        """
        视觉路径的身份冲突处理
        
        策略：询问"【人脸ID昵称】，是你在和我说话不，我怎么没听出来是你。"
        """
        self.identity_conflict = True
        
        face_nickname = self._get_user_nickname(face_id)
        voice_nickname = self._get_user_nickname(voice_id)
        
        message = f"{face_nickname}，是你在和我说话不，我怎么没听出来是你。我还以为是{voice_nickname}在和我说话。"
        self.logger.info(f'[身份冲突-视觉] {message}')
        
        # TODO: 调用TTS接口播放
        self._speak(message)
    
    def _handle_identity_conflict_touch_path(self, face_id: str, voice_id: str):
        """
        触觉路径的身份冲突处理
        
        策略："咦，刚刚是【人脸ID昵称】你在摸我吗？怎么我听上去像是【声纹ID昵称】的声音呢。"
        """
        self.identity_conflict = True
        
        face_nickname = self._get_user_nickname(face_id)
        voice_nickname = self._get_user_nickname(voice_id)
        
        message = f"咦，刚刚是{face_nickname}你在摸我吗？怎么我听上去像是{voice_nickname}的声音呢。"
        self.logger.info(f'[身份冲突-触觉] {message}')
        
        # TODO: 调用TTS接口播放
        self._speak(message)
    
    # ========================================================================
    # 辅助功能（需要实现的接口）
    # ========================================================================
    
    def _verify_identity(self, face_id: str, voice_id: str) -> bool:
        """
        验证人脸ID和声纹ID是否匹配
        
        TODO: 对接用户身份数据库
        
        Args:
            face_id: 人脸识别ID
            voice_id: 声纹识别ID
        
        Returns:
            bool: 是否匹配
        """
        # 简化实现：假设ID相同则匹配
        if face_id is None or voice_id is None:
            return False
        return face_id == voice_id
    
    def _check_if_stranger(self, face_id: str) -> bool:
        """
        检查是否为陌生用户
        
        TODO: 对接用户数据库
        
        Args:
            face_id: 人脸ID
        
        Returns:
            bool: 是否为陌生用户
        """
        # TODO: 查询本地用户数据库
        # return face_id not in registered_users
        return face_id == "unknown" or face_id.startswith("guest_")
    
    def _register_temporary_user(self, face_id: str, vision_data: Dict) -> str:
        """
        为陌生用户分配临时槽位
        
        TODO: 对接用户注册系统
        
        Args:
            face_id: 人脸ID
            vision_data: 视觉数据
        
        Returns:
            str: 临时用户ID
        """
        # TODO: 实现用户注册逻辑
        # - 分配临时槽位
        # - 存储人脸特征
        # - 初始化用户状态
        temp_id = f"temp_user_{int(time.time())}"
        self.logger.info(f'[用户注册] 陌生用户注册为临时用户: {temp_id}')
        return temp_id
    
    def _get_user_nickname(self, user_id: str) -> str:
        """
        获取用户昵称
        
        TODO: 对接用户数据库
        
        Args:
            user_id: 用户ID
        
        Returns:
            str: 用户昵称
        """
        # TODO: 从数据库查询用户昵称
        # return user_database.get(user_id).nickname
        return user_id  # 简化：直接返回ID
    
    def _turn_to_direction(self, angle: float):
        """
        转向指定角度（使用头身协同控制器）
        
        Args:
            angle: 目标角度（度）
        """
        self.logger.info(f'[控制] 转向角度: {angle:.1f}°')
        
        # 获取当前角度
        current_head_angle = self._get_current_head_angle()
        current_body_angle = self._get_current_body_angle()
        
        # 调用头身协同控制器
        self.head_body_coordinator.update(
            desired_head_direction=angle,
            current_head_angle=current_head_angle,
            current_body_angle=current_body_angle
        )
    
    def _get_current_head_angle(self) -> float:
        """
        获取当前头部角度
        
        Returns:
            float: 头部角度（度），相对于身体中线
        """
        # TODO: 从实际传感器读取
        # 选项1: 从编码器读取
        # return self.parent_node.head_encoder.get_angle()
        
        # 选项2: 从ROS话题获取
        # return self.parent_node.current_head_angle
        
        # 选项3: 从头身协同控制器获取
        return self.head_body_coordinator.current_head_angle

    def _get_current_body_angle(self) -> float:
        """
        获取当前身体角度
        
        Returns:
            float: 身体角度（度），绝对角度
        """
        # TODO: 从实际传感器读取
        # 选项1: 从IMU读取
        # return self.parent_node.imu.get_yaw()
        
        # 选项2: 从里程计读取
        # return self.parent_node.odometry.get_yaw()
        
        # 选项3: 从头身协同控制器获取
        return self.head_body_coordinator.current_body_angle
    
    def _get_direction_from_sensor(self, sensor_position: str) -> float:
        """
        根据触摸传感器位置计算转向角度
        
        Args:
            sensor_position: 传感器位置（如"left", "right", "front", "back"）
        
        Returns:
            float: 转向角度
        """
        sensor_angle_map = {
            "left": -90.0,
            "right": 90.0,
            "front": 0.0,
            "back": 180.0,
            "left_front": -45.0,
            "right_front": 45.0,
            "left_back": -135.0,
            "right_back": 135.0,
        }
        return sensor_angle_map.get(sensor_position, 0.0)
    
    def _speak(self, message: str):
        """
        播放语音
        
        TODO: 对接TTS系统
        
        Args:
            message: 要播放的文本
        """
        # TODO: 调用TTS接口
        # self.tts_client.speak(message)
        self.logger.info(f'[TTS] "{message}"')
    
    def _reset_pose(self):
        """
        执行复位动作（使用头身协同控制器）
        """
        self.logger.info('[运动控制] 执行复位动作')
        
        # 重置头身协同控制器
        self.head_body_coordinator.reset()
        
        # 回到中心位置（头部0°，身体回到初始朝向）
        self._turn_to_direction(0.0)
    
    # ========================================================================
    # 数据解析
    # ========================================================================
    
    def _parse_vision_info(self, vision_info) -> Dict:
        """解析视觉信息"""
        if vision_info is None:
            return {
                "face_detected": False,
                "face_id": None,
                "position": None,
                "confidence": 0.0
            }
        
        try:
            data = json.loads(vision_info) if isinstance(vision_info, str) else vision_info
            return {
                "face_detected": data.get("face_detected", False),
                "face_id": data.get("face_id"),
                "position": data.get("position"),
                "confidence": data.get("confidence", 0.0)
            }
        except:
            return {
                "face_detected": False,
                "face_id": None,
                "position": None,
                "confidence": 0.0
            }
    
    def _parse_audio_info(self, audio_info) -> Dict:
        """解析声觉信息"""
        if audio_info is None:
            return {
                "sound_detected": False,
                "voice_id": None,
                "doa_direction": None,
                "confidence": 0.0
            }
        
        try:
            data = json.loads(audio_info) if isinstance(audio_info, str) else audio_info
            return {
                "sound_detected": data.get("sound_detected", False),
                "voice_id": data.get("voice_id"),
                "doa_direction": data.get("doa_direction"),
                "confidence": data.get("confidence", 0.0)
            }
        except:
            return {
                "sound_detected": False,
                "voice_id": None,
                "doa_direction": None,
                "confidence": 0.0
            }
    
    def _parse_touch_info(self, touch_info) -> Dict:
        """解析触觉传感器信息"""
        if touch_info is None:
            return {
                "touched": False,
                "sensor_position": None
            }
        
        try:
            data = json.loads(touch_info) if isinstance(touch_info, str) else touch_info
            return {
                "touched": data.get("touched", False),
                "sensor_position": data.get("sensor_position")
            }
        except:
            return {
                "touched": False,
                "sensor_position": None
            }
    
    def _parse_imu_info(self, imu_info) -> Dict:
        """解析IMU信息（检测移动）"""
        if imu_info is None:
            return {
                "is_moving": False,
                "acceleration": None
            }
        
        try:
            data = json.loads(imu_info) if isinstance(imu_info, str) else imu_info
            return {
                "is_moving": data.get("is_moving", False),
                "acceleration": data.get("acceleration")
            }
        except:
            return {
                "is_moving": False,
                "acceleration": None
            }