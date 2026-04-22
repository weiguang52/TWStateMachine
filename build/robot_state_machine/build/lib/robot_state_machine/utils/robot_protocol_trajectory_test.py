#!/usr/bin/env python3
"""
机器人通信协议模块 - 异步双线程版本 + 轨迹测试
添加轨迹规划和测试功能
"""

from typing import List, Tuple, Dict, Optional, Union
import struct
import serial
import time
import threading
from dataclasses import dataclass
import logging
from queue import Queue, Empty
from collections import deque
import numpy as np

# 常量定义
MAX_ANGLE = 360.0
ANGLE_ACTUAL = 3600000
ANGLE_COMMUNICATION = 10190000
ACCURACY_ACTUAL = 100000
ACCURACY_COMMUNICATION = 101900

# CRC-8配置参数
CRC8_POLYNOMIAL = 0x31
CRC8_INIT_VALUE = 0xFFFFFFFF

# 功能码定义
FUNC_SET_DUAL_MOTOR = 0x5
FUNC_GET_DUAL_MOTOR = 0x5


# ============================================================================
# 基础协议函数（保持不变）
# ============================================================================

def crc8_accumulate(prev_crc: int, data: bytes) -> int:
    """计算CRC-8校验码"""
    crc = prev_crc & 0xFF
    data_len = len(data)
    
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ CRC8_POLYNOMIAL
            else:
                crc <<= 1
            crc &= 0xFF
    
    if data_len % 2 == 1:
        crc ^= 0x00
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ CRC8_POLYNOMIAL
            else:
                crc <<= 1
            crc &= 0xFF
    
    return crc


def current_to_raw(current: float) -> Tuple[int, bool]:
    """将电流值转换为原始数据"""
    is_negative = current < 0
    abs_current = abs(current)
    raw_value = int(abs_current * ACCURACY_COMMUNICATION / ACCURACY_ACTUAL + 0.5)
    return raw_value & 0x3FF, is_negative


def raw_to_current(raw_value: int, is_negative: bool) -> float:
    """将原始数据转换为电流值"""
    current = raw_value * ACCURACY_ACTUAL / ACCURACY_COMMUNICATION
    return -current if is_negative else current


def angle_to_raw(angle: float) -> int:
    """将角度值转换为原始数据"""
    if not (0.0 <= angle < MAX_ANGLE):
        raise ValueError(f"角度必须在0-360范围内,当前值: {angle}")
    
    raw_value = int(angle * ANGLE_COMMUNICATION / ANGLE_ACTUAL + 0.5)
    return raw_value & 0x3FF


def raw_to_angle(raw_value: int) -> float:
    """将原始数据转换为角度值"""
    return (raw_value * ANGLE_ACTUAL / ANGLE_COMMUNICATION)


def generate_dual_motor_command(board_id: int, angle_a01: float, angle_b01: float) -> bytes:
    """生成双电机控制指令"""
    if not (0 <= board_id <= 15):
        raise ValueError(f"板号必须在0-15范围内,当前值: {board_id}")
    
    x1 = angle_to_raw(angle_a01)
    x2 = angle_to_raw(angle_b01)
    
    data = bytearray()
    data.append((FUNC_SET_DUAL_MOTOR << 4) | board_id)
    
    length = 2
    data.append((length << 5) | ((x1 & 0x03) << 3) | ((x2 & 0x03) << 1))
    data.append(x1 >> 2)
    data.append(x2 >> 2)
    data.append(0x00)
    
    crc = crc8_accumulate(CRC8_INIT_VALUE, bytes(data[:length + 2]))
    data[1] |= (crc & 0x01)
    data[4] = crc >> 1
    data.append(0xFF)
    
    return bytes(data)


def parse_dual_motor_response(data: bytes) -> Dict[str, Union[int, float, str]]:
    """解析双电机返回数据"""
    result = {
        'success': False,
        'error': None,
        'board_id': None,
        'angle_a01': None,
        'angle_b01': None,
        'current_a01': None,
        'current_b01': None
    }
    
    if len(data) != 9 or data[-1] != 0xFF:
        result['error'] = f"数据格式错误:长度应为9字节且以0xFF结尾,实际{len(data)}字节"
        return result
    
    length = (data[1] >> 5)
    if 9 - length != 4:
        result['error'] = f"长度不符,期望4,实际{9 - length}"
        return result
    
    func = data[0] >> 4
    board_id = data[0] & 0x0F
    result['board_id'] = board_id
    
    if func == 0:
        result['error'] = "帧长度不匹配"
        return result
    elif func == 1:
        result['error'] = "无相应功能"
        return result
    elif func == 2:
        result['error'] = "角度超范围"
        return result
    elif func == 0xF:
        result['error'] = "功能位禁用,帧有错误"
        return result
    elif func != FUNC_GET_DUAL_MOTOR:
        result['error'] = f"功能码不匹配,期望0x{FUNC_GET_DUAL_MOTOR:X},实际0x{func:X}"
        return result
    
    raw_angle_a01 = (data[2] << 2) | ((data[1] & 0x18) >> 3)
    result['angle_a01'] = raw_to_angle(raw_angle_a01)
    
    raw_angle_b01 = (data[3] << 2) | ((data[1] & 0x06) >> 1)
    result['angle_b01'] = raw_to_angle(raw_angle_b01)
    
    raw_current_a01 = (data[4] << 2) | ((data[6] & 0x30) >> 4)
    is_negative_a01 = bool(data[6] & 0x08)
    result['current_a01'] = raw_to_current(raw_current_a01, is_negative_a01)
    
    raw_current_b01 = (data[5] << 2) | ((data[6] & 0x06) >> 1)
    is_negative_b01 = bool(data[6] & 0x01)
    result['current_b01'] = raw_to_current(raw_current_b01, is_negative_b01)
    
    result['success'] = True
    return result


def format_command_hex(data: bytes) -> str:
    """格式化命令为十六进制字符串"""
    return ' '.join(f'0x{b:02X}' for b in data)


# ============================================================================
# 🆕 三次插值轨迹生成器
# ============================================================================

class CubicTrajectoryPlanner:
    """
    三次多项式轨迹规划器
    用于生成平滑的关节轨迹
    """
    
    def __init__(self, duration: float = 2.0, frequency: float = 100.0):
        """
        初始化轨迹规划器
        
        Args:
            duration: 运动持续时间（秒）
            frequency: 采样频率（Hz）
        """
        self.duration = duration
        self.frequency = frequency
        self.num_points = int(duration * frequency)
    
    def plan_cubic_trajectory(self, 
                             start_angle: float, 
                             end_angle: float) -> np.ndarray:
        """
        使用三次多项式规划单个关节的轨迹
        
        三次多项式: θ(t) = a0 + a1*t + a2*t² + a3*t³
        
        边界条件:
        - θ(0) = start_angle, θ'(0) = 0
        - θ(T) = end_angle, θ'(T) = 0
        
        Args:
            start_angle: 起始角度
            end_angle: 目标角度
            
        Returns:
            轨迹点数组 [num_points]
        """
        # 归一化时间 t: 0 -> 1
        t = np.linspace(0, 1, self.num_points)
        
        # 三次多项式系数（根据边界条件求解）
        # θ(t) = start + (3*(end-start)*t² - 2*(end-start)*t³)
        theta = start_angle + (end_angle - start_angle) * (3 * t**2 - 2 * t**3)
        
        return theta
    
    def plan_multi_joint_trajectory(self, 
                                   start_angles: Dict[int, Tuple[float, float]], 
                                   end_angles: Dict[int, Tuple[float, float]]) -> Dict[int, np.ndarray]:
        """
        规划多关节轨迹
        
        Args:
            start_angles: 起始角度 {board_id: (angle_a01, angle_b01)}
            end_angles: 目标角度 {board_id: (angle_a01, angle_b01)}
            
        Returns:
            轨迹字典 {board_id: trajectory_array[num_points, 2]}
        """
        trajectories = {}
        
        for board_id in start_angles.keys():
            if board_id not in end_angles:
                raise ValueError(f"板{board_id}缺少目标角度")
            
            start_a, start_b = start_angles[board_id]
            end_a, end_b = end_angles[board_id]
            
            # 规划两个电机的轨迹
            traj_a = self.plan_cubic_trajectory(start_a, end_a)
            traj_b = self.plan_cubic_trajectory(start_b, end_b)
            
            # 组合成 [num_points, 2] 数组
            trajectories[board_id] = np.column_stack([traj_a, traj_b])
        
        return trajectories
    
    def get_time_stamps(self) -> np.ndarray:
        """获取时间戳"""
        return np.linspace(0, self.duration, self.num_points)


# ============================================================================
# 异步控制器相关类（保持不变）
# ============================================================================

@dataclass
class MotorAngle:
    """电机角度数据类"""
    board_id: int
    angle_a01: float
    angle_b01: float


@dataclass
class SerialConfig:
    """串口配置数据类"""
    port: str = 'COM1'
    baudrate: int = 115200
    timeout: float = 1.0
    write_timeout: float = 1.0


class ReceiveBuffer:
    """接收缓冲区"""
    
    def __init__(self, max_size: int = 1024):
        self.buffer = bytearray()
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def append(self, data: bytes):
        """向缓冲区追加数据"""
        with self.lock:
            self.buffer.extend(data)
            if len(self.buffer) > self.max_size:
                self.buffer = self.buffer[-self.max_size:]
    
    def find_complete_frame(self, frame_length: int = 9) -> Optional[bytes]:
        """从缓冲区中查找并提取完整的数据帧"""
        with self.lock:
            for i in range(len(self.buffer)):
                if self.buffer[i] == 0xFF:
                    start_index = i - frame_length + 1
                    if start_index >= 0:
                        frame = bytes(self.buffer[start_index:i + 1])
                        self.buffer = self.buffer[i + 1:]
                        return frame
            return None
    
    def clear(self):
        """清空缓冲区"""
        with self.lock:
            self.buffer.clear()
    
    def __len__(self):
        with self.lock:
            return len(self.buffer)


class ResponseWaiter:
    """响应等待器"""
    
    def __init__(self):
        self.event = threading.Event()
        self.response_data = None
        self.lock = threading.Lock()
    
    def wait_for_response(self, timeout: float) -> Optional[Dict]:
        """等待响应数据"""
        if self.event.wait(timeout):
            with self.lock:
                return self.response_data
        return None
    
    def set_response(self, response: Dict):
        """设置响应数据并通知等待线程"""
        with self.lock:
            self.response_data = response
        self.event.set()
    
    def reset(self):
        """重置等待器"""
        with self.lock:
            self.response_data = None
        self.event.clear()


# ============================================================================
# 机器人控制器（添加轨迹测试功能）
# ============================================================================

class RobotController:
    """
    机器人控制器 - 异步双线程版本 + 轨迹测试
    """
    
    def __init__(self, 
                 config: SerialConfig,
                 response_timeout: float = 1.0,
                 command_interval: float = 0.01,
                 retry_count: int = 1,
                 log_level: int = logging.INFO):
        """初始化机器人控制器"""
        self.config = config
        self.response_timeout = response_timeout
        self.command_interval = command_interval
        self.retry_count = retry_count
        
        self.serial_port: Optional[serial.Serial] = None
        self.receive_buffer = ReceiveBuffer()
        
        self.receive_thread: Optional[threading.Thread] = None
        self.running = False
        
        self.response_waiter = ResponseWaiter()
        
        self.expected_board_id: Optional[int] = None
        self.expected_board_lock = threading.Lock()
        
        # 🆕 轨迹规划器
        self.trajectory_planner = CubicTrajectoryPlanner()
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def open_serial(self) -> bool:
        """打开串口并启动接收线程"""
        try:
            self.serial_port = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                timeout=self.config.timeout,
                write_timeout=self.config.write_timeout
            )
            
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            
            self.running = True
            self.receive_thread = threading.Thread(
                target=self._receive_loop,
                daemon=True,
                name="ReceiveThread"
            )
            self.receive_thread.start()
            
            self.logger.info(f"串口已打开: {self.config.port}, 波特率: {self.config.baudrate}")
            print(f"✅ 串口已打开: {self.config.port}")
            print(f"✅ 接收线程已启动")
            return True
            
        except serial.SerialException as e:
            self.logger.error(f"打开串口失败: {e}")
            print(f"❌ 打开串口失败: {e}")
            return False
    
    def close_serial(self):
        """关闭串口并停止接收线程"""
        self.running = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2.0)
            print(f"✅ 接收线程已停止")
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.logger.info("串口已关闭")
            print(f"✅ 串口已关闭")
    
    def _receive_loop(self):
        """接收线程主循环"""
        print(f"🔄 接收线程开始运行...")
        
        while self.running:
            try:
                if self.serial_port and self.serial_port.is_open:
                    available = self.serial_port.in_waiting
                    if available > 0:
                        chunk = self.serial_port.read(available)
                        self.receive_buffer.append(chunk)
                        
                        frame = self.receive_buffer.find_complete_frame(frame_length=9)
                        
                        if frame is not None:
                            result = parse_dual_motor_response(frame)
                            
                            with self.expected_board_lock:
                                expected_id = self.expected_board_id
                            
                            if expected_id is not None:
                                if result.get('board_id') == expected_id:
                                    self.response_waiter.set_response(result)
                            else:
                                self.response_waiter.set_response(result)
                    else:
                        time.sleep(0.001)
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"接收线程异常: {e}")
                time.sleep(0.1)
        
        print(f"🔄 接收线程已退出")
    
    def send_command_and_wait_response(self, 
                                      command: bytes, 
                                      expected_board_id: Optional[int] = None) -> Optional[Dict]:
        """发送命令并等待响应"""
        try:
            if not self.serial_port or not self.serial_port.is_open:
                self.logger.error("串口未打开")
                return None
            
            with self.expected_board_lock:
                self.expected_board_id = expected_board_id
            
            self.response_waiter.reset()
            
            self.serial_port.reset_output_buffer()
            self.serial_port.write(command)
            self.serial_port.flush()
            
            result = self.response_waiter.wait_for_response(self.response_timeout)
            
            if result is None:
                return None
            
            if (expected_board_id is not None and 
                result.get('board_id') is not None and 
                result['board_id'] != expected_board_id):
                return None
            
            if not result['success']:
                return None
            
            return result
            
        except Exception as e:
            self.logger.error(f"发送命令时发生错误: {e}")
            return None
        finally:
            with self.expected_board_lock:
                self.expected_board_id = None
    
    def send_single_motor_angles(self, 
                                board_id: int, 
                                angle_a01: float, 
                                angle_b01: float, 
                                retry: bool = False) -> Optional[Dict]:
        """发送单个电机板的角度控制命令"""
        try:
            # command_start = time.time()
            command = generate_dual_motor_command(board_id, angle_a01, angle_b01)
            
            for attempt in range(self.retry_count if retry else 1):
                result = self.send_command_and_wait_response(command, board_id)
                # command_time = time.time() - command_start
                # print(command_time)
                
                if result is not None:
                    # time.sleep(0.01)
                    return result
                
                # if attempt < self.retry_count - 1:
                    # time.sleep(0.1)

        
            # result = self.send_command_and_wait_response(command, board_id)
            # command_time = time.time() - command_start
            # print(command_time)

            return None
            
        except ValueError as e:
            self.logger.error(f"板{board_id}参数错误: {e}")
            return None
    
    # ========================================================================
    # 🆕 轨迹测试功能
    # ========================================================================
    
    def test_trajectory(self,
                       start_angles: Dict[int, Tuple[float, float]],
                       end_angles: Dict[int, Tuple[float, float]],
                       duration: float = 2.0,
                       frequency: float = 100.0,
                       verbose: bool = True) -> Dict[int, List[Dict]]:
        """
        轨迹测试：生成三次插值轨迹并依次发送命令
        
        Args:
            start_angles: 起始角度 {board_id: (angle_a01, angle_b01)}
            end_angles: 目标角度 {board_id: (angle_a01, angle_b01)}
            duration: 运动持续时间（秒）
            frequency: 采样频率（Hz）
            verbose: 是否详细输出
            
        Returns:
            反馈数据 {board_id: [response_list]}
        """
        for board_id, (angle_a, angle_b) in start_angles.items():
            result = self.send_single_motor_angles(
                board_id, angle_a, angle_b, retry=False
            )

        print(f"\n{'='*70}")
        print(f"🎯 轨迹测试开始")
        print(f"{'='*70}")
        print(f"参数:")
        print(f"  持续时间: {duration}秒")
        print(f"  采样频率: {frequency}Hz")
        print(f"  总点数: {int(duration * frequency)}点")
        print(f"  板数量: {len(start_angles)}个")
        print(f"{'='*70}\n")
        
        # 1. 初始化轨迹规划器
        self.trajectory_planner = CubicTrajectoryPlanner(duration, frequency)
        
        # 2. 规划轨迹
        print("📊 生成三次插值轨迹...")
        trajectories = self.trajectory_planner.plan_multi_joint_trajectory(
            start_angles, end_angles
        )
        time_stamps = self.trajectory_planner.get_time_stamps()
        
        num_points = len(time_stamps)
        print(f"✅ 轨迹生成完成: {num_points}个点\n")
        
        # 3. 显示轨迹信息
        for board_id, traj in trajectories.items():
            start_a, start_b = start_angles[board_id]
            end_a, end_b = end_angles[board_id]
            print(f"板{board_id}轨迹:")
            print(f"  A01: {start_a:.2f}° → {end_a:.2f}°")
            print(f"  B01: {start_b:.2f}° → {end_b:.2f}°")
        print()
        
        # 4. 依次发送命令并接收反馈
        all_feedback = {board_id: [] for board_id in trajectories.keys()}
        
        print(f"🚀 开始发送轨迹命令...\n")
        start_time = time.time()
        
        for point_idx in range(num_points):
            point_start_time = time.time()
            
            if verbose and point_idx % 10 == 0:
                print(f">>> 点 {point_idx+1}/{num_points} (时间: {time_stamps[point_idx]:.3f}s)")
            
            # 按板顺序发送
            for board_id in sorted(trajectories.keys()):
                traj = trajectories[board_id]
                angle_a = traj[point_idx, 0]
                angle_b = traj[point_idx, 1]
                
                # 发送命令
                command_start = time.time()
                result = self.send_single_motor_angles(
                    board_id, angle_a, angle_b, retry=False
                )
                command_time = time.time() - command_start
                
                # 记录反馈
                if result is not None:
                    print(command_time)
                    feedback = {
                        'point_idx': point_idx,
                        'time': time_stamps[point_idx],
                        'target_a': angle_a,
                        'target_b': angle_b,
                        'actual_a': result['angle_a01'],
                        'actual_b': result['angle_b01'],
                        'current_a': result['current_a01'],
                        'current_b': result['current_b01'],
                        'error_a': abs(result['angle_a01'] - angle_a),
                        'error_b': abs(result['angle_b01'] - angle_b)
                    }
                    all_feedback[board_id].append(feedback)
                    
                    if verbose and point_idx % 10 == 0:
                        print(f"  板{board_id}: "
                              f"目标=[{angle_a:.1f}°, {angle_b:.1f}°], "
                              f"实际=[{result['angle_a01']:.1f}°, {result['angle_b01']:.1f}°], "
                              f"误差=[{feedback['error_a']:.2f}°, {feedback['error_b']:.2f}°]")
                else:
                    if verbose:
                        print(f"  板{board_id}: ❌ 无响应")
            
            # 控制发送频率
            point_elapsed = time.time() - point_start_time
            expected_interval = 1.0 / frequency
            if point_elapsed < expected_interval:
                time.sleep(expected_interval - point_elapsed)
        
        total_time = time.time() - start_time
        
        # 5. 统计结果
        print(f"\n{'='*70}")
        print(f"✅ 轨迹测试完成")
        print(f"{'='*70}")
        print(f"总耗时: {total_time:.3f}秒 (预期: {duration:.3f}秒)")
        print(f"实际频率: {num_points/total_time:.2f}Hz (预期: {frequency:.2f}Hz)")
        print()
        
        for board_id in sorted(all_feedback.keys()):
            feedback_list = all_feedback[board_id]
            success_rate = (len(feedback_list) / num_points) * 100
            
            if len(feedback_list) > 0:
                avg_error_a = np.mean([f['error_a'] for f in feedback_list])
                avg_error_b = np.mean([f['error_b'] for f in feedback_list])
                max_error_a = np.max([f['error_a'] for f in feedback_list])
                max_error_b = np.max([f['error_b'] for f in feedback_list])
                
                print(f"板{board_id}统计:")
                print(f"  成功率: {success_rate:.1f}% ({len(feedback_list)}/{num_points})")
                print(f"  平均误差: A01={avg_error_a:.3f}°, B01={avg_error_b:.3f}°")
                print(f"  最大误差: A01={max_error_a:.3f}°, B01={max_error_b:.3f}°")
            else:
                print(f"板{board_id}统计: ❌ 无有效数据")
        
        print(f"{'='*70}\n")
        
        return all_feedback
    
    def test_simple_trajectory(self, 
                              board_id: int,
                              start_a: float, start_b: float,
                              end_a: float, end_b: float,
                              duration: float = 2.0,
                              frequency: float = 100.0) -> List[Dict]:
        """
        简化的单板轨迹测试
        
        Args:
            board_id: 板号
            start_a, start_b: 起始角度
            end_a, end_b: 目标角度
            duration: 持续时间
            frequency: 频率
            
        Returns:
            反馈数据列表
        """
        start_angles = {board_id: (start_a, start_b)}
        end_angles = {board_id: (end_a, end_b)}
        
        results = self.test_trajectory(
            start_angles, end_angles, duration, frequency, verbose=True
        )
        
        return results[board_id]
    
    def __enter__(self):
        """上下文管理器入口"""
        self.open_serial()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close_serial()


# ============================================================================
# 便捷函数
# ============================================================================

def create_robot_controller(port: str = 'COM1', 
                           baudrate: int = 115200,
                           response_timeout: float = 1.0) -> RobotController:
    """创建机器人控制器的便捷函数"""
    config = SerialConfig(port=port, baudrate=baudrate)
    return RobotController(config, response_timeout=response_timeout)


# ============================================================================
# 🆕 轨迹测试示例
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("机器人轨迹测试程序")
    print("="*70)
    
    # 创建控制器
    controller = create_robot_controller(
        port='/dev/ttyUSB0',
        baudrate=115200,
        response_timeout=1.0
    )
    
    try:
        # 打开串口
        if controller.open_serial():
            time.sleep(0.5)  # 等待接收线程启动
            
            print("\n请选择测试模式:")
            print("1. 单板轨迹测试")
            print("2. 多板轨迹测试")
            print("3. 自定义测试")
            
            choice = input("\n请输入选项 (1-3): ").strip()
            
            if choice == "1":
                # 示例1: 单板轨迹测试
                print("\n=== 单板轨迹测试 ===")
                feedback = controller.test_simple_trajectory(
                    board_id=9,
                    start_a=160.0, start_b=160.0,
                    end_a=140.0, end_b=240.0,
                    duration=6.0,
                    frequency=50.0  # 50Hz
                )
                
            elif choice == "2":
                # 示例2: 多板轨迹测试
                print("\n=== 多板轨迹测试 ===")
                start_angles = {
                    9: (160.0, 160.0),
                    10: (160.0, 160.0),
                    11: (160.0, 160.0),
                }
                
                end_angles = {
                    9: (100.0, 220.0),
                    10: (220.0, 80.0),
                    11: (80.0, 220.0),
                }
                
                all_feedback = controller.test_trajectory(
                    start_angles, end_angles,
                    duration=10.0,
                    frequency=50.0,
                    verbose=True
                )
                
            elif choice == "3":
                # 示例3: 自定义测试
                print("\n=== 自定义测试 ===")
                board_id = int(input("板号 (0-15): "))
                start_a = float(input("A01起始角度 (0-360): "))
                start_b = float(input("B01起始角度 (0-360): "))
                end_a = float(input("A01目标角度 (0-360): "))
                end_b = float(input("B01目标角度 (0-360): "))
                duration = float(input("持续时间 (秒): "))
                frequency = float(input("频率 (Hz): "))
                
                feedback = controller.test_simple_trajectory(
                    board_id, start_a, start_b, end_a, end_b,
                    duration, frequency
                )
            
            else:
                print("无效选项")
        
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    finally:
        print("\n=== 关闭连接 ===")
        controller.close_serial()
        print("\n程序结束")