# 导纳控制计算
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
import math  
from rclpy.node import Node


# ========== 关节参数配置表（在这里定义所有关节的参数） ==========
JOINT_CONFIGS = {
    '''
    'joint': {
        'current_threshold': 0.03,              # 电流突变阈值 (A)
        'current_recovery_threshold': 0.015,    # 电流恢复阈值 (A)
        'current_to_torque_coeff': 1.2,        # 电流到力矩转换系数
        'expected_torque': 0.1,                 # 期望力矩 (N·m)
        'damping_coeff': 15.0,                  # 阻尼系数 (B)
        'stiffness_coeff': 120.0,               # 刚度系数 (K)
    },
    '''
    'right_shoulder_roll': {
        'current_threshold': 0.04,              # 电流突变阈值 (A)
        'current_recovery_threshold': 0.02,    # 电流恢复阈值 (A)
        'current_to_torque_coeff': 0.8,        # 电流到力矩转换系数
        'expected_torque': 0.0004,                 # 期望力矩 (N·m)
        'damping_coeff': 0.0001,                  # 阻尼系数 (B)
        'stiffness_coeff': 0.07,               # 刚度系数 (K)
    },#
    'right_shoulder_yaw': {
        'current_threshold': 0.02,
        'current_recovery_threshold': 0.01,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'right_elbow_pitch': {
        'current_threshold': 0.02,
        'current_recovery_threshold': 0.01,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.06,
    },#
    'right_wrist_yaw': {
        'current_threshold': 0.035,
        'current_recovery_threshold': 0.0175,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'left_shoulder_roll': {
        'current_threshold': 0.04,
        'current_recovery_threshold': 0.02,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'left_shoulder_yaw': {
        'current_threshold': 0.02,
        'current_recovery_threshold': 0.01,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'left_elbow_pitch': {
        'current_threshold': 0.02,
        'current_recovery_threshold': 0.01,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 20.0,
        'stiffness_coeff': 200.0,
    },#
    'left_wrist_yaw': {
        'current_threshold': 0.035,
        'current_recovery_threshold': 0.0175,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'right_shoulder_pitch': {
        'current_threshold': 0.02,
        'current_recovery_threshold': 0.01,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'left_shoulder_pitch': {
        'current_threshold': 0.02,
        'current_recovery_threshold': 0.01,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'neck_roll': {
        'current_threshold': 0.025,
        'current_recovery_threshold': 0.012,
        'current_to_torque_coeff': 1.0,
        'expected_torque': 0.08,
        'damping_coeff': 12.0,
        'stiffness_coeff': 100.0,
    },
    'neck_yaw': {
        'current_threshold': 0.04,
        'current_recovery_threshold': 0.02,
        'current_to_torque_coeff': 1.5,
        'expected_torque': 0.15,
        'damping_coeff': 20.0,
        'stiffness_coeff': 150.0,
    },
    'waist_pitch': {
        'current_threshold': 0.022,
        'current_recovery_threshold': 0.011,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.05,
        'damping_coeff': 10.0,
        'stiffness_coeff': 90.0,
    },
    'waist_roll': {
        'current_threshold': 0.025,
        'current_recovery_threshold': 0.012,
        'current_to_torque_coeff': 1.0,
        'expected_torque': 0.08,
        'damping_coeff': 12.0,
        'stiffness_coeff': 100.0,
    },
    'right_hip_pitch': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.005,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },
    'left_hip_pitch': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.005,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },
    'waist_yaw': {
        'current_threshold': 0.025,
        'current_recovery_threshold': 0.012,
        'current_to_torque_coeff': 1.0,
        'expected_torque': 0.08,
        'damping_coeff': 12.0,
        'stiffness_coeff': 100.0,
    },
    'right_hip_roll': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.04,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'right_hip_yaw': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.03,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'right_knee_pitch': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.04,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'right_ankle_yaw': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.02,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'right_ankle_pitch': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.025,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'left_hip_roll': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.04,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'left_hip_yaw': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.03,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'left_knee_pitch': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.04,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'left_ankle_yaw': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.02,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
    'left_ankle_pitch': {
        'current_threshold': 2,
        'current_recovery_threshold': 0.025,
        'current_to_torque_coeff': 0.8,
        'expected_torque': 0.0004,
        'damping_coeff': 0.0001,
        'stiffness_coeff': 0.07,
    },#
}

# 默认配置（如果某个关节没有在上面定义）
DEFAULT_CONFIG = {
    'current_threshold': 0.02,
    'current_recovery_threshold': 0.01,
    'current_to_torque_coeff': 1.0,
    'expected_torque': 0.0,
    'damping_coeff': 10.0,
    'stiffness_coeff': 100.0,
}

# 通用参数（所有关节共用）
COMMON_PARAMS = {
    'collision_confirm_threshold': 2,      # 碰撞确认阈值
    'recovery_confirm_threshold': 2,       # 恢复确认阈值
    'baseline_update_interval': 100,       # 基准更新间隔
    'filter_window_size': 20,              # 滤波窗口大小
    'max_position_adjustment': 30.0,       # 最大位置调整量 (度)
}
# ================================================================


@dataclass
class CurrentFilter:
    """电流滤波器 - 滑动窗口平均"""
    window_size: int = 20
    buffer: deque = field(default_factory=deque)
    sum_value: float = 0.0
    
    def add_sample(self, value: float):
        self.buffer.append(value)
        self.sum_value += value
        if len(self.buffer) > self.window_size:
            self.sum_value -= self.buffer.popleft()
    
    def get_average(self) -> float:
        if not self.buffer:
            return 0.0
        return self.sum_value / len(self.buffer)


@dataclass
class MotorAdmittanceState:
    """单个电机的导纳控制状态"""
    joint_id: str = ""
    current_current: float = 0.0
    current_position: float = 0.0
    last_current: float = 0.0
    last_position: float = 0.0
    target_position: float = 0.0
    planned_position: float = 0.0
    
    current_filter: CurrentFilter = field(default_factory=lambda: CurrentFilter(20))
    baseline_current: float = 0.0
    sample_counter: int = 0
    
    collision_detected: bool = False
    collision_counter: int = 0
    recovery_counter: int = 0
    
    last_velocity: float = 0.0
    last_update_time: float = field(default_factory=time.time)


class JointAdmittanceController(Node):
    """关节导纳控制器"""
    
    def __init__(self):
        super().__init__('joint_admittance_controller')
        self.motor_states: Dict[str, MotorAdmittanceState] = {}
    
    def _get_config(self, joint_id: str) -> dict:
        """获取关节配置（内部方法）"""
        if joint_id in JOINT_CONFIGS:
            return JOINT_CONFIGS[joint_id]
        else:
            print(f"⚠️  关节 {joint_id} 未在配置表中定义，使用默认配置")
            return DEFAULT_CONFIG
    
    def _init_joint(self, joint_id: str):
        """初始化关节（内部方法）"""
        if joint_id not in self.motor_states:
            state = MotorAdmittanceState(joint_id=joint_id)
            state.current_filter = CurrentFilter(COMMON_PARAMS['filter_window_size'])
            self.motor_states[joint_id] = state
    
    def execute_admittance_control(self, joint_id: str, current: float, position: float) -> Tuple[bool, float]:
        """
        执行导纳控制（主函数 - 唯一需要调用的接口）
        
        Args:
            joint_id: 关节标识符
            current: 当前电流 (A)
            position: 当前关节位置 (度)
        
        Returns:
            Tuple[bool, float]: (是否检测到碰撞, 更新后的目标位置)
        """
        # 自动初始化
        self._init_joint(joint_id)
        
        state = self.motor_states[joint_id]
        config = self._get_config(joint_id)
        
        # 更新传感器数据
        state.current_current = current
        state.current_position = position
        
        # 电流滤波
        state.current_filter.add_sample(state.current_current)
        state.sample_counter += 1
        if state.sample_counter >= COMMON_PARAMS['baseline_update_interval']:
            state.baseline_current = state.current_filter.get_average()
            state.sample_counter = 0
        
        # 碰撞检测
        collision_detected = self._detect_collision(state, config)
        
        # 计算力矩差
        measured_torque = state.current_current * config['current_to_torque_coeff']
        torque_difference = measured_torque - config['expected_torque']
        
        # 计算速度差
        current_time = time.time()
        dt = current_time - state.last_update_time
        velocity = 0.0
        if dt > 0:
            velocity = (state.current_position - state.last_position) / dt
        velocity_difference = velocity - state.last_velocity
        
        # 导纳方程求解位置调整量
        position_diff = (torque_difference - config['damping_coeff'] * velocity_difference) / config['stiffness_coeff']
        
        # 限幅
        max_adj = COMMON_PARAMS['max_position_adjustment']
        position_diff = max(min(position_diff, max_adj), -max_adj)
        self.get_logger().info(f'collision_detected:  {collision_detected}  position_diff:  {position_diff}')
        
        # 更新目标位置
        state.target_position = state.planned_position + position_diff
        self.get_logger().info(f'target_position:  {state.target_position}')
        
        # 更新历史数据
        state.last_current = state.current_current
        state.last_position = state.current_position
        state.last_velocity = velocity
        state.last_update_time = current_time
        
        return collision_detected, state.target_position
    
    def _detect_collision(self, state: MotorAdmittanceState, config: dict) -> bool:
        """碰撞检测（内部方法）"""
        current_deviation = abs(state.current_current - state.baseline_current)
        
        if state.collision_detected:
            # 检测恢复
            if current_deviation < config['current_recovery_threshold']:
                state.recovery_counter += 1
                if state.recovery_counter >= COMMON_PARAMS['recovery_confirm_threshold']:
                    state.collision_detected = False
                    state.collision_counter = 0
                    state.recovery_counter = 0
                    print(f"✓ 关节 {state.joint_id}: 碰撞恢复")
                    return False
            else:
                state.recovery_counter = 0
        else:
            # 检测碰撞
            if current_deviation > config['current_threshold']:
                state.collision_counter += 1
                if state.collision_counter >= COMMON_PARAMS['collision_confirm_threshold']:
                    state.collision_detected = True
                    state.recovery_counter = 0
                    self.get_logger().info(f"⚠️  关节 {state.joint_id}: 检测到碰撞 (电流偏差: {current_deviation:.4f}A)")
                    return True
            else:
                state.collision_counter = 0
        
        return state.collision_detected
    
    def set_planned_position(self, joint_id: str, planned_pos: float):
        """设置规划位置"""
        self._init_joint(joint_id)
        self.motor_states[joint_id].planned_position = planned_pos
    
    def get_position_adjustment(self, joint_id: str) -> float:
        """获取位置调整量"""
        if joint_id not in self.motor_states:
            return 0.0
        state = self.motor_states[joint_id]
        return state.target_position - state.planned_position
    
    def get_diagnostic_info(self, joint_id: str) -> str:
        """获取诊断信息"""
        if joint_id not in self.motor_states:
            return f"关节 {joint_id} 未初始化"
        
        state = self.motor_states[joint_id]
        config = self._get_config(joint_id)
        
        return f"""
========== 关节 {joint_id} 诊断信息 ==========
当前电流: {state.current_current:.4f} A
当前位置: {state.current_position:.2f}°
基准电流: {state.baseline_current:.4f} A
电流偏差: {abs(state.current_current - state.baseline_current):.4f} A

目标位置: {state.target_position:.2f}°
规划位置: {state.planned_position:.2f}°
位置调整: {state.target_position - state.planned_position:.2f}°

碰撞状态: {'是' if state.collision_detected else '否'}

控制参数:
  - 阻尼系数: {config['damping_coeff']}
  - 刚度系数: {config['stiffness_coeff']}
  - 电流阈值: {config['current_threshold']}A
===============================================
"""


# # ========== 使用示例 ==========
# if __name__ == "__main__":
#     # 创建控制器
#     controller = JointAdmittanceController()
    
#     # 设置规划位置
#     controller.set_planned_position('right_hip_pitch', 90.0)
#     controller.set_planned_position('right_hip_yaw', 45.0)
    
#     # 模拟控制循环 - right_hip_pitch 
#     print("开始模拟 right_hip_pitch ...")
#     for i in range(150):
#         current = 0.05 + 0.001 * math.sin(i * 0.1)
#         position = 90.0 + 0.5 * math.sin(i * 0.05)
        
#         if 70 <= i <= 80:
#             current += 0.05  # 模拟碰撞
        
#         # 只需要调用这一个函数！
#         collision, target_pos = controller.execute_admittance_control('right_hip_pitch', current, position)
        
#         if i % 20 == 0:
#             print(f"[right_hip_pitch] 步数 {i:3d}: 电流={current:.4f}A, 目标={target_pos:.2f}°, 碰撞={'是' if collision else '否'}")
        
#         time.sleep(0.02)
    
#     # 模拟控制循环 - right_hip_yaw (会使用不同的参数)
#     print("\n开始模拟 right_hip_yaw...")
#     for i in range(100):
#         current = 0.04 + 0.001 * math.sin(i * 0.15)
#         position = 45.0 + 0.3 * math.sin(i * 0.08)
        
#         if 50 <= i <= 60:
#             current += 0.04
        
#         collision, target_pos = controller.execute_admittance_control('right_hip_yaw', current, position)
        
#         if i % 20 == 0:
#             print(f"[right_hip_yaw] 步数 {i:3d}: 电流={current:.4f}A, 目标={target_pos:.2f}°, 碰撞={'是' if collision else '否'}")
        
#         time.sleep(0.02)
    
#     # 打印诊断信息
#     print(controller.get_diagnostic_info('right_hip_pitch'))


# ========== ROS2导纳控制节点 ==========
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import numpy as np
import sys
import os
from robot_state_machine.utils.robot_protocol import (
    RobotController, SerialConfig, MotorAngle
)


class AdmittanceControlNode(Node):
    """导纳控制节点 - 接收关节命令，执行导纳控制，发送给机器人"""
    
    def __init__(self):
        super().__init__('admittance_control_node')
        
        # ========== 配置参数 ==========
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('enable_admittance', True)
        self.declare_parameter('enable_robot_comm', True)
        
        self.SERIAL_PORT = self.get_parameter('serial_port').value
        self.BAUDRATE = self.get_parameter('baudrate').value
        self.ENABLE_ADMITTANCE = self.get_parameter('enable_admittance').value
        self.ENABLE_ROBOT_COMM = self.get_parameter('enable_robot_comm').value
        
        # ========== 导纳控制器 ==========
        if self.ENABLE_ADMITTANCE:
            self.admittance_controller = JointAdmittanceController()
            self.get_logger().info('✅ 导纳控制器已启用')
        else:
            self.admittance_controller = None
            self.get_logger().info('⚠️  导纳控制器已禁用')
        
        # ========== 机器人控制器 ==========
        if self.ENABLE_ROBOT_COMM and RobotController is not None:
            try:
                config = SerialConfig(
                    port=self.SERIAL_PORT,
                    baudrate=self.BAUDRATE,
                    timeout=1.0,
                    write_timeout=1.0
                )
                
                self.robot_controller = RobotController(config)
                self.robot_controller.response_timeout = 1.0
                self.robot_controller.command_interval = 0.01
                self.robot_controller.retry_count = 1
                
                if self.robot_controller.open_serial():
                    self.get_logger().info(
                        f'✅ 机器人通信已启动\n'
                        f'  串口: {self.SERIAL_PORT}\n'
                        f'  波特率: {self.BAUDRATE}'
                    )
                else:
                    self.robot_controller = None
                    self.get_logger().error('❌ 机器人串口打开失败')
            except Exception as e:
                self.get_logger().error(f'❌ 机器人控制器初始化失败: {e}')
                self.robot_controller = None
        else:
            self.robot_controller = None
            self.get_logger().info('⚠️  机器人通信已禁用')
        
        # ========== 关节名称映射 ==========
        self.joint_names = [
            'left_hip_pitch', 'left_hip_roll', 'left_hip_yaw',
            'left_knee_pitch', 'left_ankle_yaw', 'left_ankle_pitch',
            'right_hip_pitch', 'right_hip_roll', 'right_hip_yaw',
            'right_knee_pitch', 'right_ankle_yaw', 'right_ankle_pitch',
            'waist_yaw', 'waist_pitch', 'waist_roll',
            'left_shoulder_pitch', 'left_shoulder_roll', 'left_shoulder_yaw',
            'left_elbow_pitch', 'left_wrist_yaw',
            'right_shoulder_pitch', 'right_shoulder_roll', 'right_shoulder_yaw',
            'right_elbow_pitch', 'right_wrist_yaw',
            'neck_yaw', 'neck_roll', 'neck_pitch'
        ]
        
        # ========== ROS2订阅和发布 ==========
        self.joint_command_sub = self.create_subscription(
            String,
            '/joint_command',
            self.joint_command_callback,
            10
        )
        
        self.robot_feedback_pub = self.create_publisher(
            String,
            '/robot_feedback',
            10
        )
        
        # ========== 统计信息 ==========
        self.stats = {
            'total_commands_received': 0,
            'total_commands_sent': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'timeout_responses': 0,
            'admittance_adjustments': 0,
            'start_time': time.time()
        }
        
        # ========== 缓存最近的反馈数据 ==========
        self.last_feedback = {}
        
        # 定期打印统计信息
        self.create_timer(5.0, self.print_statistics)
        
        self.get_logger().info('='*70)
        self.get_logger().info('🎯 导纳控制节点已启动')
        self.get_logger().info(f'  导纳控制: {"✅ 启用" if self.ENABLE_ADMITTANCE else "❌ 禁用"}')
        self.get_logger().info(f'  机器人通信: {"✅ 启用" if self.robot_controller else "❌ 禁用"}')
        self.get_logger().info('='*70)
    
    def joint_command_callback(self, msg):
        """接收关节命令，执行导纳控制，发送给机器人"""
        try:
            # 解析命令
            command_data = json.loads(msg.data)
            joint_angles = np.array(command_data['joint_angles'])
            only_legs = command_data.get('only_legs', False)
            
            self.stats['total_commands_received'] += 1
            
            # 执行导纳控制（如果启用）
            if self.ENABLE_ADMITTANCE and self.admittance_controller:
                adjusted_angles = self.apply_admittance_control(joint_angles)
            else:
                adjusted_angles = joint_angles
            
            # 发送给机器人（如果启用）
            if self.robot_controller:
                self.send_to_robot(adjusted_angles, only_legs)
            
        except Exception as e:
            self.get_logger().error(f'处理关节命令失败: {e}')
            import traceback
            self.get_logger().error(traceback.format_exc())
    
    def apply_admittance_control(self, joint_angles):
        """
        应用导纳控制
        
        Args:
            joint_angles: 28个关节角度
            
        Returns:
            调整后的关节角度
        """
        adjusted_angles = joint_angles.copy()
        
        # 遍历所有关节，应用导纳控制
        for i, joint_name in enumerate(self.joint_names):
            if joint_name not in self.last_feedback:
                # 没有反馈数据，直接使用原始角度
                continue
            
            # 获取该关节的电流和实际位置
            feedback = self.last_feedback[joint_name]
            current = feedback.get('current', 0.0)
            actual_position = feedback.get('actual_angle', joint_angles[i])
            
            # 设置规划位置（命令角度）
            self.admittance_controller.set_planned_position(joint_name, joint_angles[i])
            
            # 执行导纳控制
            collision_detected, target_position = self.admittance_controller.execute_admittance_control(
                joint_name,
                current,
                actual_position
            )
            if(collision_detected):
                # 更新调整后的角度
                adjustment = target_position - joint_angles[i]
                if abs(adjustment) > 0.01:  # 只有调整量大于阈值时才应用
                    adjusted_angles[i] = target_position
                    self.stats['admittance_adjustments'] += 1
                    
                    if abs(adjustment) > 1.0:  # 较大调整时打印
                        self.get_logger().debug(
                            f'关节 {joint_name}: 导纳调整 {adjustment:.2f}° '
                            f'(碰撞: {"是" if collision_detected else "否"})'
                        )
        
        return adjusted_angles
    
    def send_to_robot(self, joint_angles, only_legs=False):
        """发送命令给机器人"""
        try:
            # 将关节角度映射到板和电机
            board_mapping = self.joint_angles_to_board_mapping(joint_angles, only_legs)
            
            # 发送命令并收集反馈
            feedback_data = {}
            successful_boards = 0
            failed_boards = 0
            
            for board_id, (angle_a01, angle_b01) in board_mapping.items():
                self.stats['total_commands_sent'] += 1
                
                # 发送命令
                result = self.robot_controller.send_single_motor_angles(
                    board_id,
                    angle_a01,
                    angle_b01,
                    retry=False
                )
                
                if result is not None:
                    # 成功
                    feedback_data[board_id] = {
                        'success': True,
                        'target_angles': [angle_a01, angle_b01],
                        'actual_angles': [result['angle_a01'], result['angle_b01']],
                        'currents': [result['current_a01'], result['current_b01']]
                    }
                    successful_boards += 1
                    self.stats['successful_responses'] += 1
                    
                    # 更新反馈缓存（用于下次导纳控制）
                    self.update_feedback_cache(board_id, result)
                else:
                    # 失败
                    feedback_data[board_id] = {
                        'success': False,
                        'target_angles': [angle_a01, angle_b01],
                        'error': 'Communication failed'
                    }
                    failed_boards += 1
                    self.stats['failed_responses'] += 1
            
            # 发布反馈数据
            self.publish_robot_feedback(feedback_data)
            
        except Exception as e:
            self.get_logger().error(f'发送给机器人失败: {e}')
    
    def update_feedback_cache(self, board_id, result):
        """更新反馈缓存，将板级反馈映射回关节"""
        # 板号到关节的映射（根据joint_angles_to_board_mapping的逆映射）
        board_to_joints = {
            0x09: [('left_hip_pitch', 'angle_a01'), ('right_hip_pitch', 'angle_b01')],
            0x0A: [('right_hip_roll', 'angle_a01'), ('right_hip_yaw', 'angle_b01')],
            0x0B: [('right_knee_pitch', 'angle_a01'), ('right_ankle_yaw', 'angle_b01')],
            0x0C: [('right_ankle_pitch', 'angle_a01'), (None, 'angle_b01')],
            0x0D: [('left_hip_roll', 'angle_a01'), ('left_hip_yaw', 'angle_b01')],
            0x0E: [('left_knee_pitch', 'angle_a01'), ('left_ankle_yaw', 'angle_b01')],
            0x0F: [('left_ankle_pitch', 'angle_a01'), (None, 'angle_b01')],
            0x00: [('right_shoulder_roll', 'angle_a01'), ('right_shoulder_yaw', 'angle_b01')],
            0x01: [('right_elbow_pitch', 'angle_a01'), ('right_wrist_yaw', 'angle_b01')],
            0x02: [('left_shoulder_roll', 'angle_a01'), ('left_shoulder_yaw', 'angle_b01')],
            0x03: [('left_elbow_pitch', 'angle_a01'), ('left_wrist_yaw', 'angle_b01')],
            0x04: [('right_shoulder_pitch', 'angle_a01'), ('left_shoulder_pitch', 'angle_b01')],
            0x05: [('waist_yaw', 'angle_a01'), ('waist_pitch', 'angle_b01')],
            0x06: [('waist_roll', 'angle_a01'), ('neck_yaw', 'angle_b01')],
            0x07: [('neck_roll', 'angle_a01'), ('neck_pitch', 'angle_b01')],
        }
        
        if board_id in board_to_joints:
            joints = board_to_joints[board_id]
            
            # 更新第一个电机
            if joints[0][0] is not None:
                self.last_feedback[joints[0][0]] = {
                    'actual_angle': result['angle_a01'],
                    'current': result['current_a01']
                }
            
            # 更新第二个电机
            if joints[1][0] is not None:
                self.last_feedback[joints[1][0]] = {
                    'actual_angle': result['angle_b01'],
                    'current': result['current_b01']
                }
    
    def joint_angles_to_board_mapping(self, joint_angles, only_legs=False):
        """
        将28个关节角度映射到板和电机
        （与main_node_offline.py中的方法相同）
        """
        # if len(joint_angles) != 28:
        #     raise ValueError(f"期望28个关节角度，实际收到{len(joint_angles)}个")
        
        # def normalize_angle(angle):
        #     angle = float(angle) % 360.0
        #     if angle < 0:
        #         angle += 360.0
        #     return angle + 70
        whole_offset = 160                          # + whole_offset
        right_shoulder_roll_offset = 160 - (-90)
        left_shoulder_roll_offset = 160 - 90
        board_mapping = {}

        # ========== 腿部关节 ==========
        # board_mapping[0x09] = (
        #     joint_angles[0],    # left_hip_pitch
        #     joint_angles[6]   # right_hip_pitch
        # )
        
        # board_mapping[0x0A] = (
        #     joint_angles[7],   # right_hip_roll
        #     joint_angles[8]    # right_hip_yaw
        # )
        
        # board_mapping[0x0B] = (
        #     joint_angles[9],   # right_knee_pitch
        #     joint_angles[10]   # right_ankle_yaw
        # )
        
        # board_mapping[0x0C] = (
        #     joint_angles[11],  # right_ankle_pitch
        #     0.0
        # )
        
        # board_mapping[0x0D] = (
        #     joint_angles[1],   # left_hip_roll
        #     joint_angles[2]    # left_hip_yaw
        # )
        
        board_mapping[0x0E] = (
            -joint_angles[3] + whole_offset,   # left_knee_pitch
            joint_angles[4] + whole_offset    # left_ankle_yaw
        )
        
        board_mapping[0x0F] = (
            joint_angles[5] + whole_offset,   # left_ankle_pitch
            0.0
        )
        
        
        if only_legs:
            return board_mapping
        
        # ========== 手臂关节 ==========
        board_mapping[0x00] = (
            -joint_angles[21] + right_shoulder_roll_offset,  # right_shoulder_roll
            joint_angles[22] + whole_offset   # right_shoulder_yaw
        )
        
        board_mapping[0x01] = (
            -joint_angles[23] + whole_offset,  # right_elbow_pitch
            joint_angles[24] + whole_offset   # right_wrist_yaw
        )
        
        board_mapping[0x02] = (
            -joint_angles[16] + left_shoulder_roll_offset,  # left_shoulder_roll
            -joint_angles[17] + whole_offset   # left_shoulder_yaw
        )
        
        board_mapping[0x03] = (
            -joint_angles[18] + whole_offset,  # left_elbow_pitch
            joint_angles[19] + whole_offset   # left_wrist_yaw
        )
        
        board_mapping[0x04] = (
            joint_angles[15] + whole_offset,   # left_shoulder_pitch
            -joint_angles[20] + whole_offset  # right_shoulder_pitch
        )


        # ========== 腰部和颈部 ==========
        board_mapping[0x05] = (
            joint_angles[12],  # waist_yaw
            joint_angles[13]   # waist_pitch
        )
        
        board_mapping[0x06] = (
            joint_angles[14],  # waist_roll
            joint_angles[25]   # neck_yaw
        )
        
        board_mapping[0x07] = (
            joint_angles[26],  # neck_roll
            joint_angles[27]   # neck_pitch
        )
        
        return board_mapping
    
    def publish_robot_feedback(self, feedback_data):
        """发布机器人反馈数据"""
        try:
            msg = String()
            msg.data = json.dumps({
                'timestamp': time.time(),
                'feedback_data': feedback_data,
                'stats': self.stats
            })
            self.robot_feedback_pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f'发布反馈数据失败: {e}')
    
    def print_statistics(self):
        """打印统计信息"""
        elapsed = time.time() - self.stats['start_time']
        
        success_rate = 0.0
        if self.stats['total_commands_sent'] > 0:
            success_rate = (self.stats['successful_responses'] / self.stats['total_commands_sent']) * 100
        
        self.get_logger().info(
            f'\n'
            f'📊 导纳控制节点统计:\n'
            f'  ⏱️  运行时间: {elapsed:.1f}秒\n'
            f'  📥 接收命令: {self.stats["total_commands_received"]}帧\n'
            f'  📤 发送命令: {self.stats["total_commands_sent"]}次\n'
            f'  ✅ 成功响应: {self.stats["successful_responses"]} ({success_rate:.1f}%)\n'
            f'  ❌ 失败响应: {self.stats["failed_responses"]}\n'
            f'  ⏰ 超时响应: {self.stats["timeout_responses"]}\n'
            f'  🔧 导纳调整: {self.stats["admittance_adjustments"]}次\n'
        )
    
    def shutdown(self):
        """关闭节点"""
        self.get_logger().info('关闭导纳控制节点...')
        
        if self.robot_controller:
            try:
                self.robot_controller.close_serial()
                self.get_logger().info('串口已关闭')
            except Exception as e:
                self.get_logger().error(f'关闭串口失败: {e}')


def main_admittance_node(args=None):
    """导纳控制节点主函数"""
    rclpy.init(args=args)
    node = AdmittanceControlNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main_admittance_node()