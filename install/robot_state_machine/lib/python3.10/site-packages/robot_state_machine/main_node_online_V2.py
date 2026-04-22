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
# from robot_state_machine.search_module import SearchModule
# from robot_state_machine.follow_module import FollowModule
from robot_state_machine.scan_module import ScanModule
from robot_state_machine.obstacle_avoidance_module import ObstacleAvoidanceModule

from robot_state_machine.utils.Interpolation.easy_MotionInterpolator import HumanoidMotionInterpolator
from robot_state_machine.utils.IK_V2.ik_redirection_npy import H1PinkSolver


class OfflineNPYLoader:
    """NPY文件加载器 - 持续监听 /tmp/robot_action.npy 文件变化

    文件格式约定（与 OnlineNPYLoader / cloud_service 一致）：
      np.load 结果可能是：
        A) 0维 object array，内含 dict，dict['motion'] shape=(B,J,C,T)
        B) 直接是 (T,J,C) 的 ndarray（旧格式/离线测试用）
      本类均兼容，统一解包为 (T,J,C) 后按批次切分。
    """

    def __init__(self, npy_file, urdf_path, logger, total_batches=10):
        self.npy_file = npy_file
        self.urdf_path = urdf_path
        self.logger = logger
        self.total_batches = total_batches  # 保留参数兼容性
        self.current_batch = 0

        # 解包后的 (T,J,C) ndarray，None 表示尚未加载
        self.npy_data = None
        self.total_frames = 0
        # 用 (mtime, size) 作为文件签名，与 OnlineNPYLoader 一致
        self._last_sig = None

    # ------------------------------------------------------------------
    # 内部：文件签名
    # ------------------------------------------------------------------
    def _file_sig(self):
        try:
            st = os.stat(self.npy_file)
            return (st.st_mtime, st.st_size)
        except OSError:
            return None

    # ------------------------------------------------------------------
    # 内部：等待文件写稳定（mtime+size 连续两次相同）
    # ------------------------------------------------------------------
    def _wait_stable(self, stable_wait=0.05):
        sig1 = self._file_sig()
        time.sleep(stable_wait)
        sig2 = self._file_sig()
        return sig1 == sig2 and sig1 is not None

    # ------------------------------------------------------------------
    # 内部：解包 np.load 结果 -> (T,J,C) ndarray
    # 兼容：
    #   - 0维 object array 内含 dict，dict['motion'] shape=(B,J,C,T)
    #   - 直接是 (T,J,C) 或 (T,...) ndarray
    # ------------------------------------------------------------------
    def _unwrap_to_motion(self, loaded):
        # Step1：如果是 0维 object array，取出内部对象
        obj = loaded
        if isinstance(loaded, np.ndarray) and loaded.ndim == 0:
            try:
                obj = loaded.item()
            except Exception:
                pass

        # Step2：如果是 dict，取 'motion' key
        if isinstance(obj, dict):
            if 'motion' in obj:
                motion = obj['motion']
            else:
                # fallback：找第一个 ndarray value
                motion = None
                for v in obj.values():
                    if isinstance(v, np.ndarray):
                        motion = v
                        break
                if motion is None:
                    raise ValueError(f'[离线加载器] dict 中找不到 ndarray，keys={list(obj.keys())}')
        elif isinstance(obj, np.ndarray):
            motion = obj
        else:
            raise TypeError(f'[离线加载器] 不支持的数据类型: {type(obj)}')

        # Step3：根据维度转换为 (T,J,C)
        if motion.ndim == 4:
            # (B,J,C,T) -> 取 batch=0 -> (J,C,T) -> transpose -> (T,J,C)
            B, J, C, T = motion.shape
            m = motion[0]          # (J,C,T)
            motion = m.transpose(2, 0, 1)  # (T,J,C)
            self.logger.info(
                f'[离线加载器] 格式 (B,J,C,T)=({B},{J},{C},{T}) -> 解包为 (T,J,C)=({T},{J},{C})'
            )
        elif motion.ndim == 3:
            # 已经是 (T,J,C)，直接用
            T, J, C = motion.shape
            self.logger.info(
                f'[离线加载器] 格式 (T,J,C)=({T},{J},{C})'
            )
        else:
            raise ValueError(f'[离线加载器] 不支持的 motion 维度: {motion.shape}')

        return motion

    # ------------------------------------------------------------------
    # 内部：检测文件变化并重新加载，返回 True 表示加载了新数据
    # ------------------------------------------------------------------
    def _try_load_file(self):
        sig = self._file_sig()
        if sig is None:
            return False  # 文件不存在
        if sig == self._last_sig:
            return False  # 文件未变化

        # 等文件写稳定
        if not self._wait_stable():
            return False

        try:
            loaded = np.load(self.npy_file, allow_pickle=True)
            motion = self._unwrap_to_motion(loaded)

            self.npy_data = motion
            self.total_frames = motion.shape[0]
            self._last_sig = sig
            self.current_batch = 0  # 有新数据，重置批次

            self.logger.info(
                f'[离线加载器] ✅ 检测到新文件: {os.path.basename(self.npy_file)}, '
                f'总帧数={self.total_frames}'
            )
            return True

        except Exception as e:
            self.logger.error(f'[离线加载器] 加载失败: {e}')
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    # ------------------------------------------------------------------
    # 公开接口：检查新数据并返回下一批次
    # ------------------------------------------------------------------
    def load_next_batch(self, frames_per_batch):
        """
        监听文件变化，有新数据时重置并从头切批次。
        无数据时返回 None（调用方应等待后重试）。
        有数据时按 frames_per_batch 循环切分，返回 dict 供 _process_cloud_action 使用。
        """
        # 每次调用都检查文件是否更新
        self._try_load_file()

        if self.npy_data is None or self.total_frames == 0:
            return None  # 文件尚未出现或解析失败

        start_frame = (self.current_batch * frames_per_batch) % self.total_frames
        end_frame = start_frame + frames_per_batch

        if end_frame > self.total_frames:
            part1 = self.npy_data[start_frame:]
            part2 = self.npy_data[:end_frame - self.total_frames]
            motion_batch = np.concatenate([part1, part2], axis=0)
        else:
            motion_batch = self.npy_data[start_frame:end_frame]

        self.current_batch += 1

        self.logger.info(
            f'[离线加载器] 批次 {self.current_batch}, '
            f'帧范围 {start_frame}~{min(end_frame, self.total_frames)-1} '
            f'(共{len(motion_batch)}帧)'
        )

        return {
            'motion': motion_batch,
            'batch_index': self.current_batch - 1,
            'need_ik': True
        }

    def get_progress(self):
        """监听模式下进度无实际意义，返回当前批次号（供日志显示用）"""
        return float(self.current_batch)


class MainNode(Node):
    def __init__(self):
        super().__init__('main_node_offline_npz')
        
        # ========== 配置参数 ==========
        self.TIMEOUT = 30.0
        self.CUT_FRAME_NUM = 20  # 每批处理的帧数
        
        # 离线测试参数
        self.OFFLINE_MODE = True
        self.NPZ_FILE = "/tmp/robot_action.npy"
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
            self.offline_loader = OfflineNPYLoader(
                self.NPZ_FILE, 
                self.urdf_path,
                self.get_logger(),
                self.TOTAL_BATCHES
            )
        
        # ========== 插值器初始化 ==========
        self.motion_interpolator = HumanoidMotionInterpolator(self.urdf_path)
        
        self.joint_names = [f"joint_{i}" for i in range(28)]
        self.planning_freq = 20.0
        self.admittance_freq = 100.0
        
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
        self.get_logger().info(f'  NPZ文件: {self.NPZ_FILE} (持续监听模式)')
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
        
        # 推断 fps：若帧里有 timestamp 信息则由帧间隔估算，否则默认 90fps
        fps = 90
        if num_frames >= 2:
            ts0 = command_frames[0].get("timestamp", None)
            ts1 = command_frames[1].get("timestamp", None)
            if ts0 is not None and ts1 is not None and (ts1 - ts0) > 0:
                fps = int(round(1.0 / (ts1 - ts0)))
        
        # 构造动作格式
        action = {
            "fps": fps,
            "dof": dof_data,
            "root_trans_offset": np.zeros((num_frames, 3)),
            "root_rot": np.tile([0, 0, 0, 1], (num_frames, 1)).astype(np.float32)
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
                            # 文件尚未出现，等待
                            self.get_logger().debug('[线程A] ⏳ 等待 /tmp/robot_action.npy 出现...')
                            time.sleep(0.5)  # 文件不存在时适当延长等待
                
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
            
            transition_action = self.motion_interpolator.run(
                action_copied, 
                action_new,
                is_smooth=True,
                target_fps=action_copied["fps"],  # 与源数据保持相同fps
                min_time=0.5,
                max_time=1.0,
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
        
        motion = action_data['motion']
        batch_index = action_data.get('batch_index', 0)

        self.get_logger().info(f'[线程A] 🔄 处理批次 {batch_index}, 帧数: {len(motion)}')

        # ========== 1. IK处理 ==========
        self.get_logger().info('[线程A] 开始IK重定向.')
        start_time = time.time()

        try:
            ik_result = self.IK_interpolator.process_motion(motion)

            ik_time = time.time() - start_time
            self.get_logger().info(f'[线程A] IK完成，耗时: {ik_time*1000:.2f}ms')

            # 新版 ik_redirection_npy.py 直接输出弧度，且已内置三次样条升采样至90fps
            dof_rad = ik_result['dof']        # shape: [N_out, 28]，单位: 弧度
            output_fps = ik_result['fps']     # 90
            num_frames = len(dof_rad)
            self.get_logger().info(
                f'[线程A] IK输出: {num_frames}帧 @ {output_fps}fps'
            )

        except Exception as e:
            self.get_logger().error(f'[线程A] IK处理失败: {e}')
            with self.data_lock:
                if self.cloud_action_queue:
                    self.cloud_action_queue.popleft()
            return
        
        # ========== 2. 生成命令帧并放入线程A队列 ==========
        # 新版IK已内置三次样条插值至90fps，无需再调用JointTrajectoryInterpolator
        frames_added = 0
        frames_dropped = 0
        gen_start = time.time()
        
        for frame_idx in range(num_frames):
            frame_angles_rad = dof_rad[frame_idx]   # 弧度，直接使用
            frame_angles_deg = np.rad2deg(frame_angles_rad)
            
            command_frame = {
                "joint_angles": frame_angles_deg,
                "timestamp": frame_idx / output_fps,
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
        
        # ========== 3. 移除已处理的批次 ==========
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
            # if self.ONLY_SEND_LEG_JOINTS:
            #     # leg_indices = list(range(12))
            #     # joint_angles_to_send = [joint_angles[i] for i in leg_indices]
            #     joint_angles_to_send = joint_angles[15:25].tolist() if hasattr(joint_angles, 'tolist') else list(joint_angles[15:25])
            #     joint_angles_to_send = [float(x) for x in joint_angles_to_send]
            #     # self.get_logger().info('send only leg command')
            # else:
            #     joint_angles_to_send = joint_angles.tolist() if hasattr(joint_angles, 'tolist') else list(joint_angles)
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