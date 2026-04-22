"""
机器人通信协议模块
用于生成下行指令和解析上行返回数据(双电机模式)
"""

from typing import List, Tuple, Dict, Optional, Union
import struct
import serial
import time
import threading
from dataclasses import dataclass
import logging
import termios

# 常量定义
MAX_ANGLE = 360.0  # 角度范围 0-360度
ANGLE_ACTUAL = 3600000  # 实际角度范围
ANGLE_COMMUNICATION = 10190000  # 可用数据位
ACCURACY_ACTUAL = 100000  # 实际电流范围
ACCURACY_COMMUNICATION = 101900  # 电流可用数据位

# CRC-8配置参数
CRC8_POLYNOMIAL = 0x31
CRC8_INIT_VALUE = 0xFFFFFFFF

# 功能码定义
FUNC_SET_DUAL_MOTOR = 0x5  # 改二电机角度
FUNC_GET_DUAL_MOTOR = 0x5  # 发二电机值


def crc8_accumulate(prev_crc: int, data: bytes) -> int:
    """
    计算CRC-8校验码（新版协议：奇数长度补0x00）
    
    Args:
        prev_crc: 前一个CRC值(初始值为CRC8_INIT_VALUE)
        data: 待校验的数据
        
    Returns:
        计算得到的CRC-8校验码
    """
    crc = prev_crc & 0xFF  # 取低8位作为初始值
    data_len = len(data)
    
    # 处理原始数据
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ CRC8_POLYNOMIAL
            else:
                crc <<= 1
            crc &= 0xFF
    
    # 奇数长度需要额外处理一个0x00字节
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
    """
    将电流值转换为通信协议使用的原始数据
    
    Args:
        current: 电流值
        
    Returns:
        (10位原始数据值, 是否为负)
    """
    is_negative = current < 0
    abs_current = abs(current)
    raw_value = int(abs_current * ACCURACY_COMMUNICATION / ACCURACY_ACTUAL + 0.5)
    return raw_value & 0x3FF, is_negative


def raw_to_current(raw_value: int, is_negative: bool) -> float:
    """
    将原始数据转换为电流值
    
    Args:
        raw_value: 10位原始电流数据
        is_negative: 是否为负
        
    Returns:
        电流值
    """
    current = raw_value * ACCURACY_ACTUAL / ACCURACY_COMMUNICATION
    return -current if is_negative else current

def angle_to_raw(angle: float) -> int:
    """
    将角度值转换为通信协议使用的原始数据
    
    Args:
        angle: 角度值(0-360度)
        
    Returns:
        10位原始数据值
        
    Raises:
        ValueError: 角度超出范围
    """
    if not (0.0 <= angle < MAX_ANGLE):
        raise ValueError(f"角度必须在0-360范围内,当前值: {angle}")
    
    # 四舍五入转换
    raw_value = int(angle * ANGLE_COMMUNICATION / ANGLE_ACTUAL + 0.5)
    return raw_value & 0x3FF  # 限制为10位


def raw_to_angle(raw_value: int) -> float:
    """
    将原始数据转换为角度值
    
    Args:
        raw_value: 10位原始数据值
        
    Returns:
        角度值(0-360度)
    """
    return (raw_value * ANGLE_ACTUAL / ANGLE_COMMUNICATION)


def generate_dual_motor_command(board_id: int, angle_a01: float, angle_b01: float) -> bytes:
    """
    生成双电机控制指令(下行)
    
    Args:
        board_id: 板号(0-15, 0x0-0xF)
        angle_a01: A01电机角度(0-360度)
        angle_b01: B01电机角度(0-360度)
        
    Returns:
        完整的指令字节串,以0xFF结尾
        
    Raises:
        ValueError: 参数超出范围
    """
    if not (0 <= board_id <= 15):
        raise ValueError(f"板号必须在0-15范围内,当前值: {board_id}")
    
    # 转换角度为原始值
    x1 = angle_to_raw(angle_a01)
    x2 = angle_to_raw(angle_b01)
    
    # 构建数据帧
    data = bytearray()
    
    # Byte 0: 功能位(高4位) | 板号(低4位)
    data.append((FUNC_SET_DUAL_MOTOR << 4) | board_id)
    
    # Byte 1: 长度位(高3位) | x1低2位(bit4-3) | x2低2位(bit2-1) | CRC最低位(bit0,暂时为0)
    length = 2  # 数据长度
    data.append((length << 5) | ((x1 & 0x03) << 3) | ((x2 & 0x03) << 1))
    
    # Byte 2: x1高8位
    data.append(x1 >> 2)
    
    # Byte 3: x2高8位
    data.append(x2 >> 2)
    
    # Byte 4: CRC高7位(暂时为0)
    data.append(0x00)
    
    # 计算CRC
    crc = crc8_accumulate(CRC8_INIT_VALUE, bytes(data[:length + 2]))
    
    # 将CRC嵌入到数据中
    data[1] |= (crc & 0x01)  # CRC最低位放在Byte1的bit0
    data[4] = crc >> 1  # CRC高7位放在Byte4
    
    # Byte 5: 结束标志
    data.append(0xFF)
    
    return bytes(data)


def parse_dual_motor_response(data: bytes) -> Dict[str, Union[int, float, str]]:
    """
    解析双电机返回数据(上行) - 新版协议
    
    数据格式（8字节）:
    - data[0]: func(高4位) | board(低4位)
    - data[1]: len(高3位) | angle1_bit1-0(bit4-3) | angle2_bit1-0(bit2-1) | crc_bit0
    - data[2]: angle1_bit9-2
    - data[3]: angle2_bit9-2
    - data[4]: current1_bit9-2
    - data[5]: current2_bit9-2
    - data[6]: current1_bit1-0(bit5-4) | current1_sign(bit3) | current2_bit1-0(bit2-1) | current2_sign(bit0)
    - data[7]: crc_bit7-1
    - data[8]: 0xFF
    """
    result = {
        'success': False,
        'error': None,
        'board_id': None,
        'angle_a01': None,
        'angle_b01': None,
        'current_a01': None,
        'current_b01': None
    }
    
    # 检查数据完整性（新版固定9字节）
    if len(data) != 9 or data[-1] != 0xFF:
        result['error'] = f"数据格式错误:长度应为9字节且以0xFF结尾,实际{len(data)}字节"
        return result
    
    # 提取长度
    length = (data[1] >> 5)
    if 9 - length != 4:  # 新版返回数据长度固定为4
        result['error'] = f"长度不符,期望4,实际{9 - length}"
        return result
    
    # CRC校验
    crc_received = (data[7] << 1) | (data[1] & 0x01)
    
    # 创建数据副本用于CRC计算（前6字节，清除data[1]的最低位）
    data_for_crc = bytearray(data[:6])
    data_for_crc[1] &= 0xFE  # 清除最低位
    
    crc_calculated = crc8_accumulate(CRC8_INIT_VALUE, bytes(data_for_crc))
    
    # if crc_calculated != crc_received:
    #     result['error'] = f"CRC校验失败,期望0x{crc_calculated:02X},实际0x{crc_received:02X}"
    #     return result
    
    # 解析功能码和板号
    func = data[0] >> 4
    board_id = data[0] & 0x0F
    result['board_id'] = board_id
    
    # 检查功能码
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
    
    # 解析双电机数据（新版协议）
    # A01角度: data[2]高8位 + data[1]的bit4-3
    raw_angle_a01 = (data[2] << 2) | ((data[1] & 0x18) >> 3)
    result['angle_a01'] = raw_to_angle(raw_angle_a01)
    
    # B01角度: data[3]高8位 + data[1]的bit2-1
    raw_angle_b01 = (data[3] << 2) | ((data[1] & 0x06) >> 1)
    result['angle_b01'] = raw_to_angle(raw_angle_b01)
    
    # A01电流: data[4]高8位 + data[6]的bit5-4，符号位在data[6]的bit3
    raw_current_a01 = (data[4] << 2) | ((data[6] & 0x30) >> 4)
    is_negative_a01 = bool(data[6] & 0x08)
    result['current_a01'] = raw_to_current(raw_current_a01, is_negative_a01)
    
    # B01电流: data[5]高8位 + data[6]的bit2-1，符号位在data[6]的bit0
    raw_current_b01 = (data[5] << 2) | ((data[6] & 0x06) >> 1)
    is_negative_b01 = bool(data[6] & 0x01)
    result['current_b01'] = raw_to_current(raw_current_b01, is_negative_b01)
    
    result['success'] = True
    return result



def generate_multi_board_commands(board_angles: Dict[int, Tuple[float, float]]) -> Dict[int, bytes]:
    """
    为多个板生成控制指令
    
    Args:
        board_angles: 字典,键为板号,值为(angle_a01, angle_b01)元组
        例如: {0: (90.0, 180.0), 1: (45.0, 270.0)}
        
    Returns:
        字典,键为板号,值为对应的指令字节串
    """
    commands = {}
    for board_id, (angle_a01, angle_b01) in board_angles.items():
        try:
            commands[board_id] = generate_dual_motor_command(board_id, angle_a01, angle_b01)
        except ValueError as e:
            print(f"警告: 板{board_id}生成指令失败: {e}")
    
    return commands


def parse_multi_board_responses(responses: Dict[int, bytes]) -> Dict[int, Dict]:
    """
    解析多个板的返回数据
    
    Args:
        responses: 字典,键为板号,值为接收到的数据字节串
        
    Returns:
        字典,键为板号,值为解析结果字典
    """
    results = {}
    for board_id, data in responses.items():
        try:
            result = parse_dual_motor_response(data)
            # 验证板号是否匹配
            if result['board_id'] is not None and result['board_id'] != board_id:
                result['error'] = f"板号不匹配,期望{board_id},实际{result['board_id']}"
                result['success'] = False
            results[board_id] = result
        except Exception as e:
            results[board_id] = {
                'success': False,
                'error': f"解析异常: {str(e)}",
                'board_id': board_id
            }
    
    return results


def format_command_hex(command: bytes) -> str:
    """
    将指令格式化为十六进制字符串(用于调试)
    
    Args:
        command: 指令字节串
        
    Returns:
        格式化的十六进制字符串
    """
    return ' '.join(f'{b:02X}' for b in command)


def bytes_from_hex_string(hex_str: str) -> bytes:
    """
    从十六进制字符串创建字节串(用于测试)
    
    Args:
        hex_str: 十六进制字符串,如"60 00 00 FF"或"60000FF"
        
    Returns:
        字节串
    """
    # 移除空格和其他分隔符
    hex_str = hex_str.replace(' ', '').replace('\t', '').replace(',', '')
    # 转换为字节
    return bytes.fromhex(hex_str)


# ============= 便捷函数 =============

def send_angles_to_board(board_id: int, angle_a01: float, angle_b01: float) -> bytes:
    """
    便捷函数:为单个板生成角度控制指令
    
    Args:
        board_id: 板号(0-15)
        angle_a01: A01电机角度(0-360度)
        angle_b01: B01电机角度(0-360度)
        
    Returns:
        指令字节串
    """
    return generate_dual_motor_command(board_id, angle_a01, angle_b01)


def read_board_response(response_data: bytes) -> Optional[Dict]:
    """
    便捷函数:读取并解析单个板的返回数据
    
    Args:
        response_data: 接收到的数据字节串
        
    Returns:
        解析结果字典,如果失败返回None
    """
    result = parse_dual_motor_response(response_data)
    if result['success']:
        return result
    else:
        print(f"解析失败: {result['error']}")
        return None
# ============= 新增的串口通信和控制功能 =============
@dataclass
class SerialConfig:
    """串口配置参数"""
    port: str = 'COM1'  # 串口号
    baudrate: int = 115200  # 波特率
    bytesize: int = serial.EIGHTBITS  # 数据位
    parity: str = serial.PARITY_NONE  # 校验位
    stopbits: int = serial.STOPBITS_ONE  # 停止位
    timeout: float = 1.0  # 读取超时时间(秒)
    write_timeout: float = 1.0  # 写入超时时间(秒)
@dataclass
class MotorAngle:
    """电机角度数据"""
    board_id: int  # 板号
    angle_a01: float  # A01电机角度
    angle_b01: float  # B01电机角度
class RobotController:
    """机器人控制器类"""
    
    def __init__(self, config: SerialConfig = None, logger: logging.Logger = None):
        """
        初始化机器人控制器
        
        Args:
            config: 串口配置，如果为None则使用默认配置
            logger: 日志记录器，如果为None则创建默认记录器
        """
        self.config = config or SerialConfig()
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self._lock = threading.Lock()  # 线程锁，确保串口操作的线程安全
        
        # 设置日志
        self.logger = logger or self._create_default_logger()
        
        # 通信参数
        self.response_timeout = 1.0  # 等待响应超时时间(秒)
        self.retry_count = 3  # 重试次数
        self.command_interval = 0.01  # 命令间隔时间(秒)
    
    def _create_default_logger(self) -> logging.Logger:
        """创建默认日志记录器"""
        logger = logging.getLogger('RobotController')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def open_serial(self) -> bool:
        """
        打开串口连接
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            with self._lock:
                if self.is_connected:
                    self.logger.warning("串口已经打开")
                    return True
                
                self.serial_port = serial.Serial(
                    port=self.config.port,
                    baudrate=self.config.baudrate,
                    bytesize=self.config.bytesize,
                    parity=self.config.parity,
                    stopbits=self.config.stopbits,
                    timeout=self.config.timeout,
                    write_timeout=self.config.write_timeout
                )
                
                # 清空缓冲区
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()
                
                self.is_connected = True
                self.logger.info(f"串口 {self.config.port} 打开成功")
                return True
                
        except serial.SerialException as e:
            self.logger.error(f"打开串口失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"打开串口时发生未知错误: {e}")
            return False
    
    def close_serial(self) -> bool:
        """
        关闭串口连接
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            with self._lock:
                if not self.is_connected or self.serial_port is None:
                    self.logger.warning("串口未打开")
                    return True
                
                self.serial_port.close()
                self.serial_port = None
                self.is_connected = False
                self.logger.info("串口关闭成功")
                return True
                
        except Exception as e:
            self.logger.error(f"关闭串口时发生错误: {e}")
            return False
    
    def send_command_and_wait_response(self, command: bytes, expected_board_id: int = None) -> Optional[Dict]:
        """
        发送命令并等待响应 - 增强版，显示原始数据
        
        Args:
            command: 要发送的命令字节串
            expected_board_id: 期望的板号，用于验证响应
            
        Returns:
            解析后的响应数据字典，失败返回None
        """
        if not self.is_connected or self.serial_port is None:
            self.logger.error("串口未连接")
            return None
        
        available_num = 0
        try:
            with self._lock:
                # 发送命令
                write_start = time.time()
                self.serial_port.write(command)
                self.serial_port.flush()
                write_time = time.time() - write_start
                print(f'write_time:  {write_time}')
                
                print(f"📤 发送原始数据: {format_command_hex(command)}")
                # self.logger.debug(f"发送命令: {format_command_hex(command)}")
                
                # 等待响应 (期望9字节响应)
                start_time = time.time()
                response_data = b''

                while len(response_data) < 9:
                    loop_start = time.time()
                    if time.time() - start_time > self.response_timeout:
                        self.logger.error("等待响应超时")
                        print("❌ 响应超时")
                        return None
                    
                    # 读取可用数据
                    available_start = time.time()
                    available = self.serial_port.in_waiting
                    available_time = time.time() - available_start
                    print(f'available:  {available}  available_time:  {available_time}')
                    available_num = available_num + 1
                    if available > 0:
                        read_start = time.time()
                        chunk = self.serial_port.read(available)
                        read_time = time.time() - read_start
                        print(f'read_time:  {read_time}')
                        response_data += chunk
                        # print(f"📥 接收数据块: {format_command_hex(chunk)} (总计: {len(response_data)}/9)")
                    # else:
                    #     time.sleep(0.001)  # 短暂等待
                    loop_time = time.time() - loop_start
                    print(f'loop_time:  {loop_time}')
                
                print(f"📥available_num: {available_num} 接收完整响应: {format_command_hex(response_data)}")
                # self.logger.debug(f"接收响应: {format_command_hex(response_data)}")
                parse_start = time.time()
                # 解析响应
                result = parse_dual_motor_response(response_data)
                parse_time = time.time() - parse_start
                print(f'parse_time: {parse_time}')
                
                if not result['success']:
                    self.logger.error(f"响应解析失败: {result['error']}")
                    return None
                
                return result
                
        except serial.SerialTimeoutException:
            self.logger.error("串口通信超时")
            print("❌ 串口通信超时")
            return None
        except Exception as e:
            self.logger.error(f"发送命令时发生错误: {e}")
            print(f"❌ 通信异常: {e}")
            return None
    
    def send_single_motor_angles(self, board_id: int, angle_a01: float, angle_b01: float, 
                                retry: bool = False) -> Optional[Dict]:
        """
        发送单个电机板的角度控制命令
        
        Args:
            board_id: 板号
            angle_a01: A01电机角度
            angle_b01: B01电机角度
            retry: 是否启用重试
            
        Returns:
            响应数据字典，失败返回None
        """
        try:
            send_start = time.time()
            generate_start = time.time()
            # 生成命令
            command = generate_dual_motor_command(board_id, angle_a01, angle_b01)
            print(f"\n发送命令到板{board_id}: {format_command_hex(command)}")
            generate_time = time.time() - generate_start
            print(f'generate_time:  {generate_time}')

            # 发送命令并等待响应
            for attempt in range(self.retry_count if retry else 1):
                result = self.send_command_and_wait_response(command, board_id)
                send_time = time.time() - send_start
                print(f'send_time:  {send_time}')
                
                if result is not None:
                    # 详细的成功信息，包含电流
                    success_msg = (
                        f"板{board_id}控制成功:\n"
                        f"  目标角度: A01={angle_a01:.2f}°, B01={angle_b01:.2f}°\n"
                        f"  实际角度: A01={result['angle_a01']:.2f}°, B01={result['angle_b01']:.2f}°\n"
                        f"  电流值: A01={result['current_a01']:.4f}, B01={result['current_b01']:.4f}\n"
                    )
                    
                    # self.logger.info(success_msg)
                    print(success_msg)  # 同时打印到控制台
                    
                    return result
                
                if attempt < self.retry_count - 1:
                    self.logger.warning(f"板{board_id}第{attempt + 1}次尝试失败，重试中...")
                    # time.sleep(0.1)  # 重试前短暂等待
            
            # self.logger.error(f"板{board_id}控制失败，已重试{self.retry_count}次")
            return None
            
        except ValueError as e:
            self.logger.error(f"板{board_id}参数错误: {e}")
            return None
    
    def send_multiple_motor_angles(self, motor_angles: List[MotorAngle], 
                                  stop_on_error: bool = False) -> Dict[int, Optional[Dict]]:
        """
        批量发送多个电机板的角度控制命令
        
        Args:
            motor_angles: 电机角度数据列表
            stop_on_error: 遇到错误时是否停止后续发送
            
        Returns:
            字典，键为板号，值为响应数据字典（失败为None）
        """
        results = {}
        
        # self.logger.info(f"开始批量发送{len(motor_angles)}个电机板的控制命令")
        
        for i, motor_angle in enumerate(motor_angles):
            # self.logger.info(f"发送第{i + 1}/{len(motor_angles)}个命令 - 板{motor_angle.board_id}")
            
            result = self.send_single_motor_angles(
                motor_angle.board_id,
                motor_angle.angle_a01,
                motor_angle.angle_b01,
                retry=False
            )
            
            results[motor_angle.board_id] = result
            
            # 检查是否需要在错误时停止
            if result is None and stop_on_error:
                self.logger.error(f"板{motor_angle.board_id}控制失败，停止后续发送")
                break
            
            # # 命令间隔
            # if i < len(motor_angles) - 1:  # 不是最后一个命令
            #     time.sleep(self.command_interval)
        
        return results
    
    def send_angles_dict(self, angles_dict: Dict[int, Tuple[float, float]], 
                        stop_on_error: bool = False) -> Dict[int, Optional[Dict]]:
        """
        使用字典格式发送角度数据（便捷方法）
        
        Args:
            angles_dict: 角度字典，格式为 {board_id: (angle_a01, angle_b01)}
            stop_on_error: 遇到错误时是否停止后续发送
            
        Returns:
            字典，键为板号，值为响应数据字典（失败为None）
        """
        motor_angles = [
            MotorAngle(board_id, angle_a01, angle_b01)
            for board_id, (angle_a01, angle_b01) in angles_dict.items()
        ]
        
        return self.send_multiple_motor_angles(motor_angles, stop_on_error)
    
    def __enter__(self):
        """上下文管理器入口"""
        self.open_serial()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close_serial()
# ============= 便捷函数 =============
def create_robot_controller(port: str = 'COM1', baudrate: int = 115200) -> RobotController:
    """
    创建机器人控制器的便捷函数
    
    Args:
        port: 串口号
        baudrate: 波特率
        
    Returns:
        RobotController实例
    """
    config = SerialConfig(port=port, baudrate=baudrate)
    return RobotController(config)

# ============= 使用示例 =============
if __name__ == "__main__":
    # 示例1: 基本使用
    print("=== 示例1: 基本使用 ===")
    
    # 创建控制器
    controller = create_robot_controller('/dev/ttyUSB0', 115200)
    
    try:
        # 打开串口
        if controller.open_serial():
            time.sleep(0.5)
            # 发送单个电机板控制命令
            result = controller.send_single_motor_angles(9, 160.0, 160.0)
            if result:
                print(f"控制成功: {result}")
            
            # # 批量发送多个电机板
            # motor_data = [
            #     MotorAngle(9, 160.0, 160.0),
            #     MotorAngle(10, 160.0, 160.0),
            #     MotorAngle(11, 160.0, 160.0),
            #     MotorAngle(12, 160.0, 160.0)
            # ]
            
            # results = controller.send_multiple_motor_angles(motor_data)
            # for board_id, result in results.items():
            #     if result:
            #         print(f"板{board_id}: 成功")
            #     else:
            #         print(f"板{board_id}: 失败")
        
    finally:
        # 关闭串口
        controller.close_serial()
    
