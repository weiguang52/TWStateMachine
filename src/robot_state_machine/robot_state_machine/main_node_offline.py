#!/usr/bin/env python3
"""
主状态机节点 - 离线测试版 + 优化打断策略 + 机器人通信
线程A: 持续处理数据放入共享队列，队列快满时暂停，支持打断处理
线程B: 自己队列少于1帧时从线程A队列取数据，以100Hz发送，支持打断复制
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import threading
import time
import json
import numpy as np
from queue import Queue, Empty
from collections import deque
import os

# 导入各个模块
from robot_state_machine.search_module import SearchModule
from robot_state_machine.follow_module import FollowModule
from robot_state_machine.scan_module import ScanModule
from robot_state_machine.obstacle_avoidance_module import ObstacleAvoidanceModule

from robot_state_machine.utils.Interpolation.easy_MotionInterpolator import HumanoidMotionInterpolator
from robot_state_machine.utils.IK_Redirection.ik_redirection import H1PinkSolver
from robot_state_machine.utils.cubic_spline import JointTrajectoryInterpolator


class OfflineNPZLoader:
    """离线NPZ文件加载器"""
    
    def __init__(self, npz_file, urdf_path, logger, total_batches=10):
        self.npz_file = npz_file
        self.urdf_path = urdf_path
        self.logger = logger
        self.total_batches = total_batches
        self.current_batch = 0
        self._load_npz_data()
    
    def _load_npz_data(self):
        """加载并缓存NPZ数据"""
        if not os.path.exists(self.npz_file):
            self.logger.error(f'[离线加载器] 文件不存在: {self.npz_file}')
            self.npz_data = None
            self.total_frames = 0
            return
        
        try:
            data = np.load(self.npz_file, allow_pickle=True)
            
            self.npz_data = {
                'trans': data['trans'],
                'poses': data['poses'],
                'betas': data['betas'],
                'gender': str(data['gender']),
                'mocap_framerate': int(data['mocap_framerate'])
            }
            
            self.total_frames = len(self.npz_data['trans'])
            
            self.logger.info(
                f'[离线加载器] 成功加载: {os.path.basename(self.npz_file)}\n'
                f'  总帧数: {self.total_frames}\n'
                f'  帧率: {self.npz_data["mocap_framerate"]}fps\n'
                f'  将重复使用此文件进行{self.total_batches}批次测试'
            )
            
        except Exception as e:
            self.logger.error(f'[离线加载器] 加载失败: {e}')
            import traceback
            self.logger.error(traceback.format_exc())
            self.npz_data = None
            self.total_frames = 0
    
    def load_next_batch(self, frames_per_batch):
        """加载下一批数据"""
        if self.npz_data is None:
            self.logger.error('[离线加载器] NPZ数据未加载')
            return None
        
        if self.current_batch >= self.total_batches:
            self.logger.info('[离线加载器] 所有批次已完成')
            return None
        
        start_frame = (self.current_batch * frames_per_batch) % self.total_frames
        end_frame = start_frame + frames_per_batch
        
        if end_frame > self.total_frames:
            part1_frames = self.total_frames - start_frame
            part1 = {
                'trans': self.npz_data['trans'][start_frame:],
                'poses': self.npz_data['poses'][start_frame:],
            }
            
            part2_frames = frames_per_batch - part1_frames
            part2 = {
                'trans': self.npz_data['trans'][:part2_frames],
                'poses': self.npz_data['poses'][:part2_frames],
            }
            
            amass_data = {
                'trans': np.concatenate([part1['trans'], part2['trans']], axis=0),
                'poses': np.concatenate([part1['poses'], part2['poses']], axis=0),
                'pose_aa': np.concatenate([part1['poses'], part2['poses']], axis=0),
                'betas': self.npz_data['betas'],
                'gender': self.npz_data['gender'],
                'mocap_framerate': self.npz_data['mocap_framerate'],
                'fps': self.npz_data['mocap_framerate']
            }
        else:
            amass_data = {
                'trans': self.npz_data['trans'][start_frame:end_frame],
                'poses': self.npz_data['poses'][start_frame:end_frame],
                'pose_aa': self.npz_data['poses'][start_frame:end_frame],
                'betas': self.npz_data['betas'],
                'gender': self.npz_data['gender'],
                'mocap_framerate': self.npz_data['mocap_framerate'],
                'fps': self.npz_data['mocap_framerate']
            }
        
        self.current_batch += 1
        
        self.logger.info(
            f'[离线加载器] 加载批次 {self.current_batch}/{self.total_batches}, '
            f'帧范围: {start_frame}~{end_frame-1} (共{frames_per_batch}帧)'
        )
        
        return {
            'amass_data': amass_data,
            'batch_index': self.current_batch - 1,
            'need_ik': True
        }
    
    def get_progress(self):
        """获取加载进度"""
        if self.total_batches == 0:
            return 100.0
        return (self.current_batch / self.total_batches) * 100


class MainNode(Node):
    def __init__(self):
        super().__init__('main_node_offline_npz')
        
        # ========== 配置参数 ==========
        self.TIMEOUT = 30.0
        self.CUT_FRAME_NUM = 20  # 每批处理的帧数
        
        # 离线测试参数
        self.OFFLINE_MODE = True
        self.NPZ_FILE = "/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/input/3.npz"
        self.TOTAL_BATCHES = 10
        
        # ========== 机器人通信配置（已移至导纳控制节点） ==========
        # 机器人通信现在由独立的导纳控制节点处理
        self.ONLY_SEND_LEG_JOINTS = True  # 是否只发送腿部关节（保留配置供参考）
        
        # ========== 机器人反馈数据（从导纳节点接收） ==========
        self.robot_feedback_data = {}  # 存储各板的反馈数据
        
        # ========== 队列配置 ==========
        self.THREAD_A_QUEUE_SIZE = 500  # 线程A队列大小
        self.THREAD_B_QUEUE_SIZE = 100  # 线程B队列大小
        self.QUEUE_HIGH_WATERMARK = 0.8  # 队列高水位线（80%时暂停加载）
        self.QUEUE_LOW_WATERMARK = 0.5   # 队列低水位线（50%时恢复加载）
        
        # ========== 共享数据 ==========
        self.data_lock = threading.Lock()
        
        # 线程A生成的命令帧队列（共享队列）
        self.thread_a_command_queue = Queue(maxsize=self.THREAD_A_QUEUE_SIZE)
        
        # 线程B自己的命令帧队列（线程B内部队列）
        self.thread_b_command_queue = Queue(maxsize=self.THREAD_B_QUEUE_SIZE)
        
        self.cloud_action_queue = deque(maxlen=10)
        self.point_cloud_data = None
        self.vision_info = None
        self.audio_info = None
        
        # ========== 状态标志 ==========
        self.FOLLOW_STATE = False
        self.search_command_received = False
        
        # ========== 打断状态标志（优化版） ==========
        self.interrupt_signal_received = False
        self.copied_frames = []  # 存储从队列B复制的帧
        self.interrupt_processing_a = False  # 线程A是否正在处理打断
        self.interrupt_processing_b = False  # 线程B是否正在处理打断
        self.interrupt_processed_a = False   # 线程A是否已处理过打断
        self.interrupt_processed_b = False   # 线程B是否已处理过打断
        
        # ========== 模块初始化 ==========
        self.search_module = SearchModule(self)
        self.follow_module = FollowModule(self)
        self.scan_module = ScanModule(self)
        self.obstacle_avoidance_module = ObstacleAvoidanceModule(self)
        
        # ========== 离线NPZ加载器 ==========
        self.urdf_path = "/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data/Assembly/Assembly.SLDASM.urdf"
        
        if self.OFFLINE_MODE:
            self.offline_loader = OfflineNPZLoader(
                self.NPZ_FILE, 
                self.urdf_path,
                self.get_logger(),
                self.TOTAL_BATCHES
            )
        
        # ========== 插值器初始化 ==========
        self.motion_interpolator = HumanoidMotionInterpolator(transition_times=1.0)
        
        self.joint_names = [f"joint_{i}" for i in range(28)]
        self.planning_freq = 20.0
        self.admittance_freq = 100.0
        
        self.trajectory_interpolator = JointTrajectoryInterpolator(
            joint_names=self.joint_names,
            planning_freq=self.planning_freq,
            admittance_freq=self.admittance_freq
        )
        
        self.IK_interpolator = H1PinkSolver(self.urdf_path)

        # ========== 话题订阅 ==========
        self.search_cmd_sub = self.create_subscription(
            Bool, '/search_command', self.search_command_callback, 10)
        self.vision_sub = self.create_subscription(
            String, '/vision_info', self.vision_callback, 10)
        self.audio_sub = self.create_subscription(
            String, '/audio_info', self.audio_callback, 10)
        self.point_cloud_sub = self.create_subscription(
            String, '/point_cloud', self.point_cloud_callback, 10)
        
        # ========== 打断信号订阅 ==========
        self.interrupt_sub = self.create_subscription(
            Bool, '/interrupt_signal', self.interrupt_callback, 10)
        
        # ========== 话题发布 ==========
        self.state_pub = self.create_publisher(String, '/current_state', 10)
        
        # ========== 关节命令发布（发送给导纳控制节点） ==========
        self.joint_command_pub = self.create_publisher(String, '/joint_command', 10)
        
        # ========== 机器人反馈数据发布 ==========
        self.robot_feedback_pub = self.create_publisher(String, '/robot_feedback', 10)
        
        # ========== 统计信息 ==========
        self.stats = {
            'total_frames_loaded': 0,
            'total_frames_sent': 0,
            'start_time': time.time(),
            'batches_processed': 0,
            'interrupts_processed': 0
        }
        
        # ========== 线程启动 ==========
        self.running = True
        
        self.thread_a = threading.Thread(target=self.thread_a_loop, daemon=True)
        self.thread_a.start()
        
        self.thread_b = threading.Thread(target=self.thread_b_loop, daemon=True)
        self.thread_b.start()
        
        # 状态监控
        self.monitor_timer = self.create_timer(5.0, self.print_status)
        
        self.get_logger().info('='*70)
        self.get_logger().info('主状态机节点已初始化（双队列模式 + 优化打断策略 + 机器人通信）')
        self.get_logger().info(f'  NPZ文件: {self.NPZ_FILE}')
        self.get_logger().info(f'  每批帧数: {self.CUT_FRAME_NUM}帧')
        self.get_logger().info(f'  总批次: {self.TOTAL_BATCHES}批')
        self.get_logger().info(f'  线程A队列: {self.THREAD_A_QUEUE_SIZE}帧 (高水位: {self.QUEUE_HIGH_WATERMARK*100:.0f}%, 低水位: {self.QUEUE_LOW_WATERMARK*100:.0f}%)')
        self.get_logger().info(f'  线程B队列: {self.THREAD_B_QUEUE_SIZE}帧')
        self.get_logger().info(f'  打断策略: 复制帧 + 平滑过渡')
        self.get_logger().info(f'  线程B发送频率: 100Hz')
        # self.get_logger().info(f'  机器人通信: {"启用" if self.ENABLE_ROBOT_COMMUNICATION else "禁用"}')
        # if self.ENABLE_ROBOT_COMMUNICATION:
        #     self.get_logger().info(f'  串口配置: {self.ROBOT_SERIAL_PORT} @ {self.ROBOT_BAUDRATE}bps')
        self.get_logger().info('='*70)
    
    # ========================================================================
    # 关节角度到板/电机映射
    # ========================================================================
    
    # def joint_angles_to_board_mapping(self, joint_angles):
    #     """
    #     将28个关节角度映射到板和电机
        
    #     关节名称顺序（28个）：
    #     [0-5]   Left Leg: left_hip_pitch, left_hip_roll, left_hip_yaw, left_knee_pitch, left_ankle_yaw, left_ankle_pitch
    #     [6-11]  Right Leg: right_hip_pitch, right_hip_roll, right_hip_yaw, right_knee_pitch, right_ankle_yaw, right_ankle_pitch
    #     [12-14] Waist: waist_yaw, waist_pitch, waist_roll
    #     [15-19] Left Arm: left_shoulder_pitch, left_shoulder_roll, left_shoulder_yaw, left_elbow_pitch, left_wrist_yaw
    #     [20-24] Right Arm: right_shoulder_pitch, right_shoulder_roll, right_shoulder_yaw, right_elbow_pitch, right_wrist_yaw
    #     [25-27] Neck: neck_yaw, neck_roll, neck_pitch
        
    #     Args:
    #         joint_angles: 28个关节角度的numpy数组或列表
            
    #     Returns:
    #         字典，格式为 {board_id: (angle_a01, angle_b01)}
    #     """
    #     if len(joint_angles) != 28:
    #         raise ValueError(f"期望28个关节角度，实际收到{len(joint_angles)}个")
        
    #     # 确保角度在0-360范围内的辅助函数
    #     def normalize_angle(angle):
    #         angle = float(angle) % 360.0
    #         if angle < 0:
    #             angle += 360.0
    #         return angle
        
    #     board_mapping = {}
        
    #     # ========== 手臂关节 ==========
    #     # 0x00: right_shoulder_roll (21) - right_shoulder_yaw (22)
    #     board_mapping[0x00] = (
    #         normalize_angle(joint_angles[21]),  # right_shoulder_roll
    #         normalize_angle(joint_angles[22])   # right_shoulder_yaw
    #     )
        
    #     # 0x01: right_elbow_pitch (23) - right_wrist_yaw (24)
    #     board_mapping[0x01] = (
    #         normalize_angle(joint_angles[23]),  # right_elbow_pitch
    #         normalize_angle(joint_angles[24])   # right_wrist_yaw
    #     )
        
    #     # 0x02: left_shoulder_roll (16) - left_shoulder_yaw (17)
    #     board_mapping[0x02] = (
    #         normalize_angle(joint_angles[16]),  # left_shoulder_roll
    #         normalize_angle(joint_angles[17])   # left_shoulder_yaw
    #     )
        
    #     # 0x03: left_elbow_pitch (18) - left_wrist_yaw (19)
    #     board_mapping[0x03] = (
    #         normalize_angle(joint_angles[18]),  # left_elbow_pitch
    #         normalize_angle(joint_angles[19])   # left_wrist_yaw
    #     )
        
    #     # 0x04: right_shoulder_pitch (20) - left_shoulder_pitch (15)
    #     board_mapping[0x04] = (
    #         normalize_angle(joint_angles[20]),  # right_shoulder_pitch
    #         normalize_angle(joint_angles[15])   # left_shoulder_pitch
    #     )
        
    #     # ========== 腿部关节 ==========
    #     # 0x09: right_hip_pitch (6) - left_hip_pitch (0)
    #     board_mapping[0x09] = (
    #         normalize_angle(joint_angles[6]),   # right_hip_pitch
    #         normalize_angle(joint_angles[0])    # left_hip_pitch
    #     )
        
    #     # 0x0A: right_hip_roll (7) - right_hip_yaw (8)
    #     board_mapping[0x0A] = (
    #         normalize_angle(joint_angles[7]),   # right_hip_roll
    #         normalize_angle(joint_angles[8])    # right_hip_yaw
    #     )
        
    #     # 0x0B: right_knee_pitch (9) - right_ankle_yaw (10)
    #     board_mapping[0x0B] = (
    #         normalize_angle(joint_angles[9]),   # right_knee_pitch
    #         normalize_angle(joint_angles[10])   # right_ankle_yaw
    #     )
        
    #     # 0x0C: right_ankle_pitch (11) - 暂时用0度或重复第一个电机
    #     board_mapping[0x0C] = (
    #         normalize_angle(joint_angles[11]),  # right_ankle_pitch
    #         0.0  # 第二个电机暂时设为0度（待后续修改）
    #     )
        
    #     # 0x0D: left_hip_roll (1) - left_hip_yaw (2)
    #     board_mapping[0x0D] = (
    #         normalize_angle(joint_angles[1]),   # left_hip_roll
    #         normalize_angle(joint_angles[2])    # left_hip_yaw
    #     )
        
    #     # 0x0E: left_knee_pitch (3) - left_ankle_yaw (4)
    #     board_mapping[0x0E] = (
    #         normalize_angle(joint_angles[3]),   # left_knee_pitch
    #         normalize_angle(joint_angles[4])    # left_ankle_yaw
    #     )
        
    #     # 0x0F: left_ankle_pitch (5) - 暂时用0度或重复第一个电机
    #     board_mapping[0x0F] = (
    #         normalize_angle(joint_angles[5]),   # left_ankle_pitch
    #         0.0  # 第二个电机暂时设为0度（待后续修改）
    #     )
        
    #     # ========== 未映射的关节（腰部和颈部）- 暂时分配到其他板号 ==========
    #     # 你可以后续修改这些映射
        
    #     # 0x05: waist_yaw (12) - waist_pitch (13)
    #     board_mapping[0x05] = (
    #         normalize_angle(joint_angles[12]),  # waist_yaw
    #         normalize_angle(joint_angles[13])   # waist_pitch
    #     )
        
    #     # 0x06: waist_roll (14) - neck_yaw (25)
    #     board_mapping[0x06] = (
    #         normalize_angle(joint_angles[14]),  # waist_roll
    #         normalize_angle(joint_angles[25])   # neck_yaw
    #     )
        
    #     # 0x07: neck_roll (26) - neck_pitch (27)
    #     board_mapping[0x07] = (
    #         normalize_angle(joint_angles[26]),  # neck_roll
    #         normalize_angle(joint_angles[27])   # neck_pitch
    #     )
        
    #     return board_mapping
    def joint_angles_to_board_mapping(self, joint_angles, only_legs=False):
        """
        将28个关节角度映射到板和电机
        
        Args:
            joint_angles: 28个关节角度的numpy数组或列表
            only_legs: 是否只返回腿部关节的映射（默认False返回所有）
            
        Returns:
            字典，格式为 {board_id: (angle_a01, angle_b01)}
        """
        if len(joint_angles) != 28:
            raise ValueError(f"期望28个关节角度，实际收到{len(joint_angles)}个")
        
        def normalize_angle(angle):
            angle = float(angle) % 360.0
            if angle < 0:
                angle += 360.0
            return angle
        
        board_mapping = {}
        
        # ========== 腿部关节（始终包含） ==========
        # 0x09: right_hip_pitch (6) - left_hip_pitch (0)
        board_mapping[0x09] = (
            normalize_angle(joint_angles[6]),
            normalize_angle(joint_angles[0])
        )
        
        # 0x0A: right_hip_roll (7) - right_hip_yaw (8)
        board_mapping[0x0A] = (
            normalize_angle(joint_angles[7]),
            normalize_angle(joint_angles[8])
        )
        
        # 0x0B: right_knee_pitch (9) - right_ankle_yaw (10)
        board_mapping[0x0B] = (
            normalize_angle(joint_angles[9]),
            normalize_angle(joint_angles[10])
        )
        
        # 0x0C: right_ankle_pitch (11) - 第二个电机暂时设为0度
        board_mapping[0x0C] = (
            normalize_angle(joint_angles[11]),
            0.0
        )
        
        # 0x0D: left_hip_roll (1) - left_hip_yaw (2)
        board_mapping[0x0D] = (
            normalize_angle(joint_angles[1]),
            normalize_angle(joint_angles[2])
        )
        
        # 0x0E: left_knee_pitch (3) - left_ankle_yaw (4)
        board_mapping[0x0E] = (
            normalize_angle(joint_angles[3]),
            normalize_angle(joint_angles[4])
        )
        
        # 0x0F: left_ankle_pitch (5) - 第二个电机暂时设为0度
        board_mapping[0x0F] = (
            normalize_angle(joint_angles[5]),
            0.0
        )
        
        # 如果只需要腿部关节，直接返回
        if only_legs:
            return board_mapping
        
        # ========== 手臂关节（only_legs=False时才包含） ==========
        board_mapping[0x00] = (
            normalize_angle(joint_angles[21]),  # right_shoulder_roll
            normalize_angle(joint_angles[22])   # right_shoulder_yaw
        )
        
        board_mapping[0x01] = (
            normalize_angle(joint_angles[23]),  # right_elbow_pitch
            normalize_angle(joint_angles[24])   # right_wrist_yaw
        )
        
        board_mapping[0x02] = (
            normalize_angle(joint_angles[16]),  # left_shoulder_roll
            normalize_angle(joint_angles[17])   # left_shoulder_yaw
        )
        
        board_mapping[0x03] = (
            normalize_angle(joint_angles[18]),  # left_elbow_pitch
            normalize_angle(joint_angles[19])   # left_wrist_yaw
        )
        
        board_mapping[0x04] = (
            normalize_angle(joint_angles[20]),  # right_shoulder_pitch
            normalize_angle(joint_angles[15])   # left_shoulder_pitch
        )
        
        # ========== 腰部和颈部关节 ==========
        board_mapping[0x05] = (
            normalize_angle(joint_angles[12]),  # waist_yaw
            normalize_angle(joint_angles[13])   # waist_pitch
        )
        
        board_mapping[0x06] = (
            normalize_angle(joint_angles[14]),  # waist_roll
            normalize_angle(joint_angles[25])   # neck_yaw
        )
        
        board_mapping[0x07] = (
            normalize_angle(joint_angles[26]),  # neck_roll
            normalize_angle(joint_angles[27])   # neck_pitch
        )
        
        return board_mapping

    
    def publish_robot_feedback(self, feedback_data):
        """发布机器人反馈数据"""
        try:
            feedback_msg = String()
            feedback_msg.data = json.dumps({
                'timestamp': time.time(),
                'feedback_data': feedback_data,
                'stats': self.robot_communication_stats
            })
            self.robot_feedback_pub.publish(feedback_msg)
        except Exception as e:
            self.get_logger().error(f'[机器人通信] 发布反馈数据失败: {e}')
    
    # ========================================================================
    # 回调函数
    # ========================================================================
    
    def search_command_callback(self, msg):
        if msg.data:
            with self.data_lock:
                self.search_command_received = True
    
    def vision_callback(self, msg):
        with self.data_lock:
            self.vision_info = msg.data
    
    def audio_callback(self, msg):
        with self.data_lock:
            self.audio_info = msg.data
    
    def point_cloud_callback(self, msg):
        with self.data_lock:
            self.point_cloud_data = msg.data
    
    def interrupt_callback(self, msg):
        """打断信号回调"""
        if msg.data:
            with self.data_lock:
                # 只有在没有处理过打断时才设置信号
                if not self.interrupt_processed_a and not self.interrupt_processed_b:
                    self.interrupt_signal_received = True
                    self.get_logger().info('🚨 [打断] 收到打断信号！')
                else:
                    self.get_logger().info('🚨 [打断] 收到打断信号，但已处理过，忽略')
    
    def print_status(self):
        """状态监控"""
        elapsed = time.time() - self.stats['start_time']
        progress = self.offline_loader.get_progress()
        
        thread_a_usage = (self.thread_a_command_queue.qsize() / self.THREAD_A_QUEUE_SIZE) * 100
        thread_b_usage = (self.thread_b_command_queue.qsize() / self.THREAD_B_QUEUE_SIZE) * 100
        
        self.get_logger().info(
            f'\n'
            f'📊 系统状态监控:\n'
            f'  ⏱️  运行时间: {elapsed:.1f}秒\n'
            f'  📈 进度: {progress:.1f}%\n'
            f'  📦 线程A队列: {self.thread_a_command_queue.qsize()}/{self.THREAD_A_QUEUE_SIZE} ({thread_a_usage:.1f}%)\n'
            f'  📦 线程B队列: {self.thread_b_command_queue.qsize()}/{self.THREAD_B_QUEUE_SIZE} ({thread_b_usage:.1f}%)\n'
            f'  📤 命令发布: {self._send_count if hasattr(self, "_send_count") else 0}帧\n'
            f'  🔄 已处理批次: {self.stats["batches_processed"]}\n'
            f'  ⚡ 打断处理次数: {self.stats["interrupts_processed"]}\n'
        )

    # ========================================================================
    # 数据格式转换辅助函数
    # ========================================================================
    
    def _command_frames_to_action(self, command_frames):
        """将命令帧列表转换为动作格式（供插值器使用）"""
        if not command_frames:
            return None
        
        num_frames = len(command_frames)
        dof_data = np.zeros((num_frames, 28))
        
        for i, frame in enumerate(command_frames):
            dof_data[i] = np.deg2rad(frame["joint_angles"])  # 转换为弧度
        
        # 构造动作格式
        action = {
            "fps": 100,  # 命令帧是100Hz
            "dof": dof_data,
            "root_trans_offset": np.zeros((num_frames, 3)),  # 假设根节点位置为0
            "root_rot": np.tile([1.0, 0.0, 0.0, 0.0], (num_frames, 1))  # 假设根节点无旋转
        }
        
        return action
    
    def _action_to_command_frames(self, action, start_timestamp=0.0):
        """将动作格式转换为命令帧列表"""
        command_frames = []
        fps = action["fps"]
        dof_data = action["dof"]
        
        for i in range(len(dof_data)):
            frame = {
                "joint_angles": np.rad2deg(dof_data[i]),  # 转换为角度
                "timestamp": start_timestamp + i / fps,
                "frame_index": i,
                "source": "interrupt_transition"
            }
            command_frames.append(frame)
        
        return command_frames
    
    # ========================================================================
    # 线程A: 持续数据加载与处理 + 打断处理
    # ========================================================================
    
    def thread_a_loop(self):
        """线程A主循环 - 持续处理数据并放入队列，队列快满时暂停，支持打断处理"""
        self.get_logger().info('[线程A] 启动 - 持续加载模式 + 打断支持')
        
        # 状态变量
        is_loading_paused = False
        last_queue_check_time = time.time()
        queue_check_interval = 0.1  # 每100ms检查一次队列状态
        
        while self.running:
            try:
                current_time = time.time()
                
                # ========== 1. 检查打断信号（只处理一次） ==========
                with self.data_lock:
                    interrupt_received = self.interrupt_signal_received
                    already_processed = self.interrupt_processed_a
                
                if interrupt_received and not already_processed:
                    self.get_logger().info('[线程A] 🚨 检测到打断信号，开始处理...')
                    self._handle_interrupt_in_thread_a()
                    continue  # 处理完打断后继续主循环
                
                # ========== 2. 定期检查队列状态，决定是否暂停/恢复加载 ==========
                if current_time - last_queue_check_time >= queue_check_interval:
                    queue_size = self.thread_a_command_queue.qsize()
                    queue_usage = queue_size / self.THREAD_A_QUEUE_SIZE
                    
                    if not is_loading_paused and queue_usage >= self.QUEUE_HIGH_WATERMARK:
                        # 队列使用率达到高水位线，暂停加载
                        is_loading_paused = True
                        self.get_logger().info(
                            f'[线程A] 🛑 队列使用率达到{queue_usage*100:.1f}%，暂停加载 '
                            f'({queue_size}/{self.THREAD_A_QUEUE_SIZE})'
                        )
                    
                    elif is_loading_paused and queue_usage <= self.QUEUE_LOW_WATERMARK:
                        # 队列使用率降到低水位线，恢复加载
                        is_loading_paused = False
                        self.get_logger().info(
                            f'[线程A] 🟢 队列使用率降到{queue_usage*100:.1f}%，恢复加载 '
                            f'({queue_size}/{self.THREAD_A_QUEUE_SIZE})'
                        )
                    
                    last_queue_check_time = current_time
                
                # ========== 3. 如果没有暂停，继续加载新批次 ==========
                if not is_loading_paused:
                    # 检查是否需要加载新批次
                    should_load_new_batch = False
                    
                    with self.data_lock:
                        if len(self.cloud_action_queue) == 0:
                            # 动作队列为空，需要加载新批次
                            should_load_new_batch = True
                    
                    if should_load_new_batch:
                        action_data = self.offline_loader.load_next_batch(self.CUT_FRAME_NUM)
                        
                        if action_data is not None:
                            with self.data_lock:
                                self.cloud_action_queue.append(action_data)
                            
                            self.stats['total_frames_loaded'] += self.CUT_FRAME_NUM
                            
                            self.get_logger().info(
                                f'[线程A] ✓ 新批次已加载, 进度: {self.offline_loader.get_progress():.1f}%'
                            )
                        else:
                            # 所有批次加载完毕
                            self.get_logger().info('[线程A] ✓ 所有批次加载完毕')
                
                # ========== 4. 处理队列中的动作（如果有的话） ==========
                with self.data_lock:
                    has_action_to_process = len(self.cloud_action_queue) > 0
                
                if has_action_to_process and not is_loading_paused:
                    # 只有在没有暂停加载时才处理动作，避免队列进一步增长
                    self._process_cloud_action()
                
                # ========== 5. 短暂休眠 ==========
                time.sleep(0.01)  # 10ms
                
            except Exception as e:
                self.get_logger().error(f'[线程A] 错误: {e}')
                import traceback
                self.get_logger().error(traceback.format_exc())
                time.sleep(0.1)
    
    def _handle_interrupt_in_thread_a(self):
        """线程A处理打断信号（只处理一次）"""
        with self.data_lock:
            self.interrupt_processing_a = True
        
        try:
            # 1. 清除线程A队列，只保留尾帧（1帧）
            frames_cleared = 0
            tail_frame = None
            
            # 先取出所有帧
            all_frames = []
            while True:
                try:
                    frame = self.thread_a_command_queue.get(block=False)
                    all_frames.append(frame)
                except Empty:
                    break
            
            frames_cleared = len(all_frames)
            
            # 只保留最后一帧作为尾帧
            if all_frames:
                tail_frame = all_frames[-1]
                try:
                    self.thread_a_command_queue.put(tail_frame, block=False)
                except:
                    pass  # 队列满了就算了
            
            self.get_logger().info(
                f'[线程A-打断] 清除线程A队列 {frames_cleared} 帧，保留尾帧 1 帧'
            )
            
            # 2. 正常执行流程：处理云端动作
            with self.data_lock:
                has_action_to_process = len(self.cloud_action_queue) > 0
            
            if has_action_to_process:
                self.get_logger().info('[线程A-打断] 开始处理云端动作...')
                self._process_cloud_action()
            
            # 3. 三次插值完成后，创建队列C并生成过渡帧
            self._create_interrupt_transition_with_copied_frames()
            
            self.stats['interrupts_processed'] += 1
            
            # 4. 标记已处理
            with self.data_lock:
                self.interrupt_processed_a = True
                self.get_logger().info('[线程A-打断] 打断处理完成，标记为已处理')
            
        except Exception as e:
            self.get_logger().error(f'[线程A-打断] 处理失败: {e}')
            import traceback
            self.get_logger().error(traceback.format_exc())
        finally:
            with self.data_lock:
                self.interrupt_processing_a = False
    
    def _create_interrupt_transition_with_copied_frames(self):
        """创建打断过渡：复制帧 + 过渡帧 + 新数据，然后去除复制帧"""
        
        # 1. 检查是否有复制的帧
        with self.data_lock:
            copied_frames = self.copied_frames.copy()
            self.copied_frames.clear()  # 清空复制帧缓存
        
        if not copied_frames:
            self.get_logger().warning('[线程A-打断] 没有复制帧，跳过过渡生成')
            return
        
        # 2. 获取新生成的数据（从线程A队列取一些帧作为新数据的开始）
        new_frames = []
        NEW_FRAMES_COUNT = 20  # 取20帧作为新数据的代表
        
        for _ in range(NEW_FRAMES_COUNT):
            try:
                frame = self.thread_a_command_queue.get(block=False)
                new_frames.append(frame)
            except Empty:
                break
        
        if not new_frames:
            self.get_logger().warning('[线程A-打断] 没有新数据帧，跳过过渡生成')
            # 把复制的帧直接放回线程B队列
            self._send_frames_to_thread_b(copied_frames)
            return
        
        self.get_logger().info(
            f'[线程A-打断] 开始生成过渡：复制帧{len(copied_frames)}帧 -> 新数据{len(new_frames)}帧'
        )
        
        try:
            # 3. 转换为动作格式
            action_copied = self._command_frames_to_action(copied_frames)
            action_new = self._command_frames_to_action(new_frames)
            
            if action_copied is None or action_new is None:
                self.get_logger().error('[线程A-打断] 动作格式转换失败')
                return
            
            # 4. 使用插值器生成过渡
            self.get_logger().info('[线程A-打断] 使用插值器生成平滑过渡...')
            
            # 使用复制帧的最后一帧和新数据的第一帧进行过渡
            index_A = len(action_copied["dof"]) - 1  # 复制帧的最后一帧
            index_B = 0  # 新数据的第一帧
            
            transition_action = self.motion_interpolator.run(
                action_copied, 
                action_new,
                is_smooth=True,
                target_fps=100,  # 保持100Hz
                index_A=index_A,
                index_B=index_B
            )
            
            # 5. 转换回命令帧格式
            transition_frames = self._action_to_command_frames(transition_action)
            
            self.get_logger().info(
                f'[线程A-打断] 过渡生成完成：总共{len(transition_frames)}帧'
            )
            
            # 6. 从过渡帧中去除复制帧部分，只保留过渡+新数据部分
            # 复制帧的长度就是需要跳过的帧数
            copied_frames_count = len(copied_frames)
            
            # 保留从复制帧结束后开始的所有帧（过渡帧 + 新数据帧）
            final_frames = transition_frames[copied_frames_count:]
            
            self.get_logger().info(
                f'[线程A-打断] 去除复制帧{copied_frames_count}帧，剩余{len(final_frames)}帧发送到线程B'
            )
            
            # 7. 发送到线程B队列
            self._send_frames_to_thread_b(final_frames)
            
            # 8. 把剩余的新数据帧放回线程A队列
            for frame in new_frames[1:]:  # 跳过第一帧（已经在过渡中了）
                try:
                    self.thread_a_command_queue.put(frame, block=False)
                except:
                    break  # 队列满了就停止
            
        except Exception as e:
            self.get_logger().error(f'[线程A-打断] 过渡生成失败: {e}')
            import traceback
            self.get_logger().error(traceback.format_exc())
            
            # 失败时直接发送复制帧
            self._send_frames_to_thread_b(copied_frames)
    
    def _send_frames_to_thread_b(self, frames):
        """将帧列表发送到线程B队列"""
        if not frames:
            return
        
        frames_sent = 0
        for frame in frames:
            try:
                self.thread_b_command_queue.put(frame, block=False)
                frames_sent += 1
            except:
                break  # 队列满了就停止
        
        self.get_logger().info(
            f'[线程A-打断] 发送{frames_sent}/{len(frames)}帧到线程B队列'
        )
    
    def _process_cloud_action(self):
        """处理动作：IK + 插值 + 生成命令帧放入线程A队列"""
        
        with self.data_lock:
            if not self.cloud_action_queue:
                return
            action_data = self.cloud_action_queue[0]
        
        if not action_data.get('need_ik', False):
            self.get_logger().warning('[线程A] 动作不需要IK处理')
            with self.data_lock:
                if self.cloud_action_queue:
                    self.cloud_action_queue.popleft()
            return
        
        amass_data = action_data['amass_data']
        batch_index = action_data.get('batch_index', 0)
        
        self.get_logger().info(f'[线程A] 🔄 处理批次 {batch_index}, 帧数: {len(amass_data["trans"])}')
        
        # ========== 1. IK处理 ==========
        self.get_logger().info('[线程A] 开始IK重定向...')
        start_time = time.time()
        
        try:
            ik_result = self.IK_interpolator.process_cloud_action_to_joint_angles(
                amass_data,
                urdf_path=self.urdf_path
            )
            
            ik_time = time.time() - start_time
            self.get_logger().info(f'[线程A] IK完成，耗时: {ik_time*1000:.2f}ms')
            
            dof_real = ik_result['dof_real']
            num_frames = ik_result['num_frames']
            
        except Exception as e:
            self.get_logger().error(f'[线程A] IK处理失败: {e}')
            with self.data_lock:
                if self.cloud_action_queue:
                    self.cloud_action_queue.popleft()
            return
        
        # ========== 2. 三次样条插值 ==========
        self.get_logger().info('[线程A] 三次样条插值...')
        interp_start = time.time()
        
        joint_trajectory = {}
        for i, joint_name in enumerate(self.joint_names):
            joint_trajectory[joint_name] = (dof_real[:, i] * np.pi / 180.0).tolist()
        
        self.trajectory_interpolator.load_planning_trajectory(joint_trajectory)
        interpolated_time_stamps, interpolated_trajectory = \
            self.trajectory_interpolator.get_full_interpolated_trajectory()
        
        interp_time = time.time() - interp_start
        num_interpolated_frames = len(interpolated_time_stamps)
        
        self.get_logger().info(
            f'[线程A] 插值完成耗时: {interp_time*1000:.2f}ms'
            f'[线程A] {num_frames}帧 -> {num_interpolated_frames}帧 (100Hz)'
        )
        
        # ========== 3. 生成命令帧并放入线程A队列 ==========
        frames_added = 0
        frames_dropped = 0
        gen_start = time.time()
        
        for frame_idx in range(num_interpolated_frames):
            frame_angles_rad = np.array([
                interpolated_trajectory[joint_name][frame_idx]
                for joint_name in self.joint_names
            ])
            
            frame_angles_deg = frame_angles_rad * 180.0 / np.pi
            
            command_frame = {
                "joint_angles": frame_angles_deg,
                "timestamp": interpolated_time_stamps[frame_idx],
                "frame_index": frame_idx,
                "source": "cloud_action",
                "batch_index": batch_index
            }
            
            try:
                # 非阻塞放入线程A队列
                self.thread_a_command_queue.put(command_frame, block=False)
                frames_added += 1
            except:
                frames_dropped += 1
                # 队列满了，停止添加
                break

        gen_time = time.time() - gen_start
        self.get_logger().info(f'[线程A] 生成命令帧完成，耗时: {gen_time*1000:.2f}ms')
        
        if frames_dropped > 0:
            self.get_logger().warning(
                f'[线程A] ⚠️ 队列满，成功添加{frames_added}帧，丢弃{frames_dropped}帧'
            )
        else:
            self.get_logger().info(
                f'[线程A] ✓ 成功添加{frames_added}帧到队列 '
                f'(队列: {self.thread_a_command_queue.qsize()}/{self.THREAD_A_QUEUE_SIZE})'
            )
        
        # ========== 4. 移除已处理的批次 ==========
        with self.data_lock:
            if self.cloud_action_queue:
                self.cloud_action_queue.popleft()
        
        self.stats['batches_processed'] += 1
    
    # ========================================================================
    # 线程B: 命令帧发送（100Hz）+ 打断复制 + 机器人通信
    # ========================================================================
    
    def thread_b_loop(self):
        """线程B主循环 - 从自己的队列以100Hz发送，队列少时从线程A队列补充，支持打断复制"""
        self.get_logger().info('[线程B] 启动（100Hz发送模式 + 打断支持 + 机器人通信）')
        
        # 日志控制变量
        frame_count = 0
        last_log_time = time.time()
        log_interval = 2.0
        
        # 每次从线程A队列取多少帧
        BATCH_SIZE = 96
        
        while self.running:
            try:
                loop_start_time = time.time()
                
                # ========== 1. 检查打断信号（优先级最高，只处理一次） ==========
                with self.data_lock:
                    interrupt_received = self.interrupt_signal_received
                    already_processed = self.interrupt_processed_b
                
                if interrupt_received and not already_processed:
                    self.get_logger().info('[线程B] 🚨 检测到打断信号，开始复制队列...')
                    self._handle_interrupt_in_thread_b()
                    # 注意：不要continue，继续正常发送命令帧
                
                # ========== 2. 检查线程B队列，少于2帧时从线程A队列补充 ==========
                thread_b_queue_size = self.thread_b_command_queue.qsize()
                
                if thread_b_queue_size < 2:
                    # 从线程A队列批量取帧
                    thread_a_queue_size = self.thread_a_command_queue.qsize()
                    
                    if thread_a_queue_size > 0:
                        self.get_logger().info(
                            f'[线程B] 📥 自己队列仅剩{thread_b_queue_size}帧，'
                            f'从线程A队列(有{thread_a_queue_size}帧)取{BATCH_SIZE}帧'
                        )
                        
                        frames_transferred = 0
                        for _ in range(BATCH_SIZE):
                            try:
                                # 从线程A队列取一帧
                                frame = self.thread_a_command_queue.get(block=False)
                                # 放入线程B队列
                                self.thread_b_command_queue.put(frame, block=False)
                                frames_transferred += 1
                            except Empty:
                                # 线程A队列空了
                                break
                            except:
                                # 线程B队列满了
                                break
                        
                        if frames_transferred > 0:
                            self.get_logger().info(
                                f'[线程B] ✓ 成功转移{frames_transferred}帧 '
                                f'(线程B队列: {self.thread_b_command_queue.qsize()}/{self.THREAD_B_QUEUE_SIZE})'
                            )
                    else:
                        # 线程A队列也空了
                        if frame_count % 100 == 0:  # 减少日志频率
                            self.get_logger().debug('[线程B] ⏳ 等待线程A生成数据...')
                
                # ========== 3. 从线程B队列获取命令帧 ==========
                try:
                    command_frame = self.thread_b_command_queue.get(timeout=0.01)
                except Empty:
                    # 线程B队列为空，等待
                    time.sleep(0.001)
                    continue
                
                frame_count += 1
                self.stats['total_frames_sent'] += 1
                
                # ========== 4. 检查搜寻命令 ==========
                with self.data_lock:
                    search_cmd = self.search_command_received
                
                if search_cmd:
                    self.get_logger().info('[线程B] 收到搜寻命令，进入搜寻子状态')
                    self._enter_search_state()
                    continue
                
                # ========== 5. 检查跟随状态 ==========
                with self.data_lock:
                    follow_state = self.FOLLOW_STATE
                
                if follow_state:
                    final_command = self._merge_follow_command(command_frame)
                    
                    if frame_count % 100 == 0:
                        self.get_logger().info(
                            f'[线程B] 跟随模式激活，已发送{frame_count}帧'
                        )
                else:
                    final_command = command_frame["joint_angles"]
                
                # ========== 6. 发送命令给机器人 ==========
                self.send_joint_command(final_command)
                
                # ========== 7. 更新跟随状态 ==========
                self._update_follow_state()
                
                # ========== 8. 周期性打印详细信息 ==========
                current_time = time.time()
                if current_time - last_log_time >= log_interval:
                    actual_freq = frame_count / (current_time - self.stats["start_time"])
                    self.get_logger().info(
                        f'[线程B] 状态报告:\n'
                        f'  已发送帧数: {frame_count}\n'
                        f'  线程A队列: {self.thread_a_command_queue.qsize()}/{self.THREAD_A_QUEUE_SIZE}\n'
                        f'  线程B队列: {self.thread_b_command_queue.qsize()}/{self.THREAD_B_QUEUE_SIZE}\n'
                        f'  跟随状态: {"激活" if follow_state else "未激活"}\n'
                        f'  搜寻状态: {"激活" if search_cmd else "未激活"}\n'
                        f'  实际频率: {actual_freq:.1f} Hz (目标: 100Hz)'
                    )
                    last_log_time = current_time
                
                # ========== 9. 控制发送频率为100Hz ==========
                loop_time = time.time() - loop_start_time
                target_period = 0.01  # 10ms = 100Hz
                sleep_time = target_period - loop_time
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                self.get_logger().error(f'[线程B] 错误: {e}')
                import traceback
                self.get_logger().error(traceback.format_exc())
                time.sleep(0.1)
    
    def _handle_interrupt_in_thread_b(self):
        """线程B处理打断信号：复制队列B的剩余帧（只处理一次）"""
        
        # 复制队列B中的所有剩余帧
        copied_frames = []
        
        # 创建队列的临时副本，不影响原队列
        temp_queue = Queue()
        
        # 先把所有帧取出来
        all_frames = []
        while True:
            try:
                frame = self.thread_b_command_queue.get(block=False)
                all_frames.append(frame)
            except Empty:
                break
        
        # 复制所有帧
        copied_frames = [frame.copy() for frame in all_frames]
        
        # 把原帧放回队列（保持正常发送）
        for frame in all_frames:
            try:
                self.thread_b_command_queue.put(frame, block=False)
            except:
                break  # 队列满了就停止
        
        # 存储复制的帧
        with self.data_lock:
            self.copied_frames = copied_frames
            self.interrupt_processed_b = True  # 标记已处理
        
        self.get_logger().info(
            f'[线程B-打断] 复制了{len(copied_frames)}帧 '
            f'(队列B剩余: {self.thread_b_command_queue.qsize()}帧)，标记为已处理'
        )
    
    def _merge_follow_command(self, command_frame):
        """合并跟随命令"""
        thread_a_angles = command_frame["joint_angles"]
        
        with self.data_lock:
            vision_info = self.vision_info
            audio_info = self.audio_info
        
        try:
            vision_data = json.loads(vision_info) if vision_info else {}
            target_angle = vision_data.get("position", {}).get("angle", 0)
            target_distance = vision_data.get("position", {}).get("distance", 0)
            
            self.get_logger().debug(
                f'[线程B-跟随] 目标: 角度={target_angle:.1f}°, 距离={target_distance:.2f}m'
            )
        except:
            pass
        
        follow_delta = np.zeros(28)  # TODO: 实现跟随
        merged_angles = thread_a_angles + follow_delta
        
        return merged_angles
    
    def _update_follow_state(self):
        """更新跟随状态"""
        with self.data_lock:
            vision_info = self.vision_info
        
        try:
            vision_data = json.loads(vision_info) if vision_info else {}
            target_detected = vision_data.get("face_detected", False)
            
            with self.data_lock:
                old_state = self.FOLLOW_STATE
                self.FOLLOW_STATE = target_detected
                
                if old_state != target_detected:
                    if target_detected:
                        self.get_logger().info('[线程B] 目标检测到，进入跟随状态')
                    else:
                        self.get_logger().info('[线程B] 目标丢失，退出跟随状态')
        except:
            pass
    
    def _enter_search_state(self):
        """进入搜寻子状态"""
        self.get_logger().info('[线程B-搜寻] 搜寻状态激活')
        
        with self.data_lock:
            vision_info = self.vision_info
            audio_info = self.audio_info
        
        try:
            audio_data = json.loads(audio_info) if audio_info else {}
            sound_detected = audio_data.get("sound_detected", False)
            doa_direction = audio_data.get("doa_direction", 0)
            
            if sound_detected:
                self.get_logger().info(
                    f'[线程B-搜寻] 检测到声音，DOA方向: {doa_direction:.1f}°'
                )
        except:
            pass
        
        target_found = self.search_module.execute(vision_info, audio_info)
        
        if target_found:
            self.get_logger().info('[线程B-搜寻] 找到目标，退出搜寻状态')
            with self.data_lock:
                self.search_command_received = False
                self.FOLLOW_STATE = True
        else:
            self.get_logger().debug('[线程B-搜寻] 继续搜寻...')
    
    # ========================================================================
    # 机器人通信功能
    # ========================================================================
    
    def send_joint_command(self, joint_angles):
        """
        发布关节命令到话题（供导纳控制节点处理）
        
        Args:
            joint_angles: 28个关节角度的numpy数组或列表
        """
        try:
            if self.ONLY_SEND_LEG_JOINTS:
                leg_indices = list(range(12))
                joint_angles_to_send = [joint_angles[i] for i in leg_indices]
                # self.get_logger().info('send only leg command')
            else:
                joint_angles_to_send = joint_angles.tolist() if hasattr(joint_angles, 'tolist') else list(joint_angles)

            # 构建消息数据
            command_data = {
                'timestamp': time.time(),
                'joint_angles': joint_angles_to_send,
                'only_legs': self.ONLY_SEND_LEG_JOINTS
            }
            
            # 发布到话题
            msg = String()
            msg.data = json.dumps(command_data)
            self.joint_command_pub.publish(msg)
            
            # 统计
            if not hasattr(self, '_send_count'):
                self._send_count = 0
            
            self._send_count += 1
            
            # if self._send_count % 10 == 0:
            #     self.get_logger().debug(
            #         f'[线程B-发布] 已发布{self._send_count}帧命令到话题 /joint_command'
            #     )
        
        except Exception as e:
            self.get_logger().error(f'[关节命令发布] 发布失败: {e}')
            import traceback
            self.get_logger().error(traceback.format_exc())
    
    def shutdown(self):
        """关闭节点"""
        self.get_logger().info('关闭节点...')
        self.running = False
        
        # 等待线程结束
        self.thread_a.join(timeout=2.0)
        self.thread_b.join(timeout=2.0)


def main(args=None):
    rclpy.init(args=args)
    node = MainNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
