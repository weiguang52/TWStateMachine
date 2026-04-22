#!/usr/bin/env python3
"""
主状态机节点 - 双线程架构
线程A: 云端数据获取 + 处理 + 生成命令帧
线程B: 命令帧发送 + 跟随/搜寻状态处理
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

# 导入各个模块
from robot_state_machine.search_module import SearchModule
from robot_state_machine.follow_module import FollowModule
from robot_state_machine.scan_module import ScanModule
from robot_state_machine.obstacle_avoidance_module import ObstacleAvoidanceModule

from robot_state_machine.utils.Interpolation.easy_MotionInterpolator import HumanoidMotionInterpolator
from robot_state_machine.utils.IK_Redirection.ik_redirection import process_cloud_action_to_joint_angles
from robot_state_machine.utils.cubic_spline import JointTrajectoryInterpolator
from robot_state_machine.utils.cloude_http_client import CloudHTTPClient


class MainNode(Node):
    def __init__(self):
        super().__init__('main_node')
        
        # ========== 配置参数 ==========
        self.TIMEOUT = 30.0  # 云端数据超时时间（秒）
        self.CUT_FRAME_NUM = 20  # 每次截取的帧数
        
        # ========== 共享数据（需要线程锁保护）==========
        self.data_lock = threading.Lock()
        
        # 云端动作队列（线程A写入，线程A读取）
        self.cloud_action_queue = deque(maxlen=10)  # 最多存储10个动作
        
        # 命令帧队列（线程A写入，线程B读取）
        self.command_frame_queue = Queue(maxsize=100)
        
        # 点云数据（外部写入，线程A读取）
        self.point_cloud_data = None
        
        # 视觉/听觉数据（外部写入，线程B读取）
        self.vision_info = None
        self.audio_info = None
        
        # ========== 状态标志 ==========
        self.FOLLOW_STATE = False  # 跟随状态标志
        self.search_command_received = False  # 搜寻命令标志
        
        # 线程A向线程B的通知标志
        self.need_new_action = threading.Event()  # 线程B通知线程A需要新动作
        
        # ========== 模块初始化 ==========
        self.search_module = SearchModule(self)
        self.follow_module = FollowModule(self)
        self.scan_module = ScanModule(self)
        self.obstacle_avoidance_module = ObstacleAvoidanceModule(self)
        
        # ========== 云端客户端初始化 ==========
        self.npz_save_dir = "/home/sunrise/TWStateMachine/received_actions"
        self.cloud_client = CloudHTTPClient(
            server_url="http://36.103.177.248:8888/generate",
            poll_interval=0.2,
            request_method="POST",
            request_data={"text": "a person walks forward"},
            logger=self.get_logger(),
            save_npz=True,
            npz_save_dir=self.npz_save_dir,
            npz_name_prefix="http_action"
        )
        self.cloud_client.on_action_received = self.on_cloud_action_received
        self.cloud_client.start()
        
        # ========== 处理器初始化 ==========
        self.motion_interpolator = HumanoidMotionInterpolator(transition_times=1.0)
        self.urdf_path = "/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data/Assembly/Assembly.SLDASM.urdf"
        
        # 三次样条插值器
        self.joint_names = [f"joint_{i}" for i in range(28)]
        self.planning_freq = 20.0  # 规划层频率
        self.admittance_freq = 100.0  # 导纳控制层频率
        
        self.trajectory_interpolator = JointTrajectoryInterpolator(
            joint_names=self.joint_names,
            planning_freq=self.planning_freq,
            admittance_freq=self.admittance_freq
        )
        
        # ========== 话题订阅 ==========
        self.search_cmd_sub = self.create_subscription(
            Bool, '/search_command', self.search_command_callback, 10)
        
        self.vision_sub = self.create_subscription(
            String, '/vision_info', self.vision_callback, 10)
        
        self.audio_sub = self.create_subscription(
            String, '/audio_info', self.audio_callback, 10)
        
        self.point_cloud_sub = self.create_subscription(
            String, '/point_cloud', self.point_cloud_callback, 10)
        
        # ========== 话题发布 ==========
        self.state_pub = self.create_publisher(String, '/current_state', 10)
        
        # ========== 线程启动 ==========
        self.running = True
        
        # 线程A: 云端数据获取与处理
        self.thread_a = threading.Thread(target=self.thread_a_loop, daemon=True)
        self.thread_a.start()
        
        # 线程B: 命令帧发送与状态处理
        self.thread_b = threading.Thread(target=self.thread_b_loop, daemon=True)
        self.thread_b.start()
        
        self.get_logger().info('='*60)
        self.get_logger().info('主状态机节点已初始化（双线程架构）')
        self.get_logger().info('  线程A: 云端数据获取 + 处理 + 生成命令帧')
        self.get_logger().info('  线程B: 命令帧发送 + 跟随/搜寻状态处理')
        self.get_logger().info('='*60)
    
    # ========================================================================
    # 回调函数
    # ========================================================================
    
    def search_command_callback(self, msg):
        """接收搜寻指令"""
        if msg.data:
            self.get_logger().info('[指令] 收到搜寻指令')
            with self.data_lock:
                self.search_command_received = True
    
    def vision_callback(self, msg):
        """接收视觉信息"""
        with self.data_lock:
            self.vision_info = msg.data
    
    def audio_callback(self, msg):
        """接收声觉信息"""
        with self.data_lock:
            self.audio_info = msg.data
    
    def point_cloud_callback(self, msg):
        """接收点云信息"""
        with self.data_lock:
            self.point_cloud_data = msg.data
    
    def on_cloud_action_received(self, action_data):
        """云端动作接收回调（云端客户端线程调用）"""
        with self.data_lock:
            self.cloud_action_queue.append(action_data)
            self.get_logger().info(
                f'[云端] 收到动作: {action_data.get("description", "未知")}, '
                f'帧数: {action_data["num_frames"]}, '
                f'队列大小: {len(self.cloud_action_queue)}'
            )
    
    # ========================================================================
    # 线程A: 云端数据获取与处理
    # ========================================================================
    
    def thread_a_loop(self):
        """
        线程A主循环
        
        功能：
        1. 不断从云端获取.npy数据
        2. 检查超时，超时则进入扫描状态
        3. 获取数据后存入队列
        4. 截取cutFrameNum帧
        5. 检查避障需求
        6. 进行IK重定向 + 三次插值
        7. 生成命令帧放入命令帧队列
        """
        last_data_time = time.time()  # 上次收到数据的时间
        scan_state_active = False
        
        self.get_logger().info('[线程A] 启动')
        
        while self.running:
            try:
                # ========== 1. 检查是否有云端数据 ==========
                with self.data_lock:
                    has_data = len(self.cloud_action_queue) > 0
                
                if has_data:
                    # 收到数据，重置超时计时器
                    last_data_time = time.time()
                    scan_state_active = False
                    
                    # ========== 2. 处理云端动作 ==========
                    self._process_cloud_action()
                
                else:
                    # 没有数据，检查超时
                    elapsed = time.time() - last_data_time
                    
                    if elapsed > self.TIMEOUT and not scan_state_active:
                        # 超时，进入扫描状态
                        self.get_logger().info(
                            f'[线程A] 云端数据超时({elapsed:.1f}s > {self.TIMEOUT}s)，进入扫描状态'
                        )
                        scan_state_active = True
                        self._enter_scan_state()
                    
                    # 扫描状态下继续扫描
                    if scan_state_active:
                        # 扫描模块会生成扫描命令
                        # TODO: 调用扫描模块
                        pass
                
                # ========== 3. 检查线程B是否需要新动作 ==========
                if self.need_new_action.is_set():
                    self.get_logger().info('[线程A] 收到线程B请求，立即处理下一个动作')
                    self.need_new_action.clear()
                    # 下一次循环会处理
                
                time.sleep(0.01)  # 100Hz
                
            except Exception as e:
                self.get_logger().error(f'[线程A] 错误: {e}')
                import traceback
                self.get_logger().error(traceback.format_exc())
                time.sleep(0.1)
    
    def _process_cloud_action(self):
        """处理云端动作：截取 + 避障检查 + IK + 插值 + 生成命令帧"""
        
        # ========== 1. 从队列获取动作 ==========
        with self.data_lock:
            if not self.cloud_action_queue:
                return
            action_data = self.cloud_action_queue[0]  # 取第一个但不删除
        
        # ========== 2. 截取cutFrameNum帧 ==========
        dof_real = action_data["dof_real"]  # [N, 28]
        total_frames = action_data["num_frames"]
        
        # 计算可以截取的帧数
        frames_to_process = min(self.CUT_FRAME_NUM, total_frames)
        
        if frames_to_process == 0:
            # 当前动作已处理完，移除
            with self.data_lock:
                self.cloud_action_queue.popleft()
            return
        
        # 截取前frames_to_process帧
        cut_dof = dof_real[:frames_to_process]  # [cut_frames, 28]
        
        self.get_logger().info(
            f'[线程A] 截取动作: {frames_to_process}/{total_frames}帧'
        )
        
        # ========== 3. 检查是否需要避障 ==========
        need_obstacle_avoidance = self._check_obstacle_avoidance()
        
        if need_obstacle_avoidance:
            # ========== 3a. 需要避障：生成避障轨迹 ==========
            self.get_logger().info('[线程A] 检测到障碍物，生成避障轨迹')
            
            # 获取点云信息
            with self.data_lock:
                point_cloud = self.point_cloud_data
            
            # 调用避障模块生成包络信息
            envelope_info = self.obstacle_avoidance_module.generate_envelope(point_cloud)
            
            # 生成避障轨迹
            # TODO: 实现避障轨迹生成接口
            obstacle_trajectory = self._generate_obstacle_avoidance_trajectory(
                cut_dof, envelope_info
            )
            
            # 使用避障轨迹替代原始轨迹
            processed_dof = obstacle_trajectory
        else:
            # ========== 3b. 不需要避障：直接使用原始轨迹 ==========
            processed_dof = cut_dof
        
        # ========== 4. IK重定向 ==========
        self.get_logger().info('[线程A] 进行IK重定向')
        
        # 构造动作字典
        action_dict = {
            "dof": processed_dof,
            "fps": action_data["fps"],
            "root_trans_offset": action_data.get("root_trans_offset", 
                np.zeros((frames_to_process, 3)))[:frames_to_process],
            "root_rot": action_data.get("root_rot", 
                np.tile([0, 0, 0, 1], (frames_to_process, 1)))[:frames_to_process],
        }
        
        # TODO: 调用IK处理
        # ik_result = process_cloud_action_to_joint_angles(action_dict, self.urdf_path)
        # 临时：直接使用原始数据
        ik_result = {
            'dof_real': processed_dof,  # [cut_frames, 28]
            'fps': action_data["fps"],
            'num_frames': frames_to_process
        }
        
        # ========== 5. 三次样条插值（满足导纳层帧率）==========
        self.get_logger().info('[线程A] 三次样条插值')
        
        # 构造关节轨迹字典
        joint_trajectory = {}
        for i, joint_name in enumerate(self.joint_names):
            # 度数转弧度
            joint_trajectory[joint_name] = (ik_result['dof_real'][:, i] * np.pi / 180.0).tolist()
        
        # 加载到插值器
        self.trajectory_interpolator.load_planning_trajectory(joint_trajectory)
        
        # 获取插值后的轨迹（100Hz）
        interpolated_time_stamps, interpolated_trajectory = \
            self.trajectory_interpolator.get_full_interpolated_trajectory()
        
        # ========== 6. 生成命令帧 ==========
        num_interpolated_frames = len(interpolated_time_stamps)
        
        self.get_logger().info(
            f'[线程A] 生成命令帧: {frames_to_process}帧 -> {num_interpolated_frames}帧 (100Hz)'
        )
        
        # 将每一帧转换为命令帧并放入队列
        for frame_idx in range(num_interpolated_frames):
            # 获取当前帧的关节角度（弧度）
            frame_angles_rad = np.array([
                interpolated_trajectory[joint_name][frame_idx]
                for joint_name in self.joint_names
            ])
            
            # 转换为度数
            frame_angles_deg = frame_angles_rad * 180.0 / np.pi
            
            # 构造命令帧
            command_frame = {
                "joint_angles": frame_angles_deg,  # [28]
                "timestamp": interpolated_time_stamps[frame_idx],
                "frame_index": frame_idx,
                "source": "cloud_action"
            }
            
            # 放入命令帧队列
            try:
                self.command_frame_queue.put(command_frame, timeout=1.0)
            except:
                self.get_logger().warning('[线程A] 命令帧队列已满，丢弃帧')
                break
        
        # ========== 7. 更新云端动作队列 ==========
        with self.data_lock:
            if self.cloud_action_queue:
                # 移除已处理的帧
                remaining_frames = total_frames - frames_to_process
                
                if remaining_frames > 0:
                    # 更新动作数据（保留剩余帧）
                    self.cloud_action_queue[0]["dof_real"] = dof_real[frames_to_process:]
                    self.cloud_action_queue[0]["num_frames"] = remaining_frames
                    
                    if "root_trans_offset" in self.cloud_action_queue[0]:
                        self.cloud_action_queue[0]["root_trans_offset"] = \
                            self.cloud_action_queue[0]["root_trans_offset"][frames_to_process:]
                    
                    if "root_rot" in self.cloud_action_queue[0]:
                        self.cloud_action_queue[0]["root_rot"] = \
                            self.cloud_action_queue[0]["root_rot"][frames_to_process:]
                else:
                    # 当前动作已处理完，移除
                    self.cloud_action_queue.popleft()
                    self.get_logger().info('[线程A] 当前动作处理完毕')
    
    def _check_obstacle_avoidance(self):
        """检查是否需要避障"""
        with self.data_lock:
            point_cloud = self.point_cloud_data
        
        if point_cloud is None:
            return False
        
        # TODO: 调用避障检测接口
        # return self.obstacle_avoidance_module.detect_obstacle(point_cloud)
        
        # 临时实现：解析点云数据
        try:
            data = json.loads(point_cloud)
            return data.get("obstacle_detected", False)
        except:
            return False
    
    def _generate_obstacle_avoidance_trajectory(self, original_dof, envelope_info):
        """
        生成避障轨迹
        
        接口函数：需要实现
        
        Args:
            original_dof: 原始关节角度 [N, 28]
            envelope_info: 包络信息（从避障模块获取）
        
        Returns:
            obstacle_dof: 避障后的关节角度 [N, 28]
        """
        # TODO: 实现避障轨迹生成
        # 可能的方案：
        # 1. 在关节空间进行轨迹修正
        # 2. 在笛卡尔空间规划避障路径后逆解
        # 3. 使用优化算法（如MPC）生成避障轨迹
        
        # 临时：直接返回原始轨迹
        self.get_logger().warning('[线程A] 避障轨迹生成未实现，使用原始轨迹')
        return original_dof
    
    def _enter_scan_state(self):
        """进入扫描状态"""
        # TODO: 调用扫描模块
        # self.scan_module.reset()
        # 扫描模块会生成扫描命令并放入命令帧队列
        self.get_logger().info('[线程A] 扫描状态激活')
    
    # ========================================================================
    # 线程B: 命令帧发送与状态处理
    # ========================================================================
    
    def thread_b_loop(self):
        """
        线程B主循环
        
        功能：
        1. 从命令帧队列获取命令帧
        2. 并行判断：
           a. 检查命令帧数量是否为1
           b. 检查FOLLOW_STATE
        3. 根据状态处理命令帧
        4. 发送给机器人
        """
        self.get_logger().info('[线程B] 启动')
        
        while self.running:
            try:
                # ========== 1. 从命令帧队列获取命令帧 ==========
                try:
                    command_frame = self.command_frame_queue.get(timeout=0.01)  # 10ms超时
                except Empty:
                    # 队列为空，继续循环
                    time.sleep(0.001)
                    continue
                
                # ========== 2. 并行判断 ==========
                
                # 判断1: 检查命令帧数量
                queue_size = self.command_frame_queue.qsize()
                
                if queue_size == 1:
                    # 队列中只剩1帧，通知线程A获取新动作
                    self.get_logger().info('[线程B] 命令帧仅剩1帧，通知线程A获取新动作')
                    self.need_new_action.set()
                
                # 判断2: 检查搜寻命令
                with self.data_lock:
                    search_cmd = self.search_command_received
                
                if search_cmd:
                    # 收到搜寻命令，进入搜寻子状态
                    self.get_logger().info('[线程B] 进入搜寻子状态')
                    self._enter_search_state()
                    # 搜寻状态下，线程A的命令帧停止发送
                    continue
                
                # 判断3: 检查FOLLOW_STATE
                with self.data_lock:
                    follow_state = self.FOLLOW_STATE
                
                if follow_state:
                    # ========== 2a. 跟随状态：合并命令 ==========
                    final_command = self._merge_follow_command(command_frame)
                else:
                    # ========== 2b. 非跟随状态：直接使用线程A的命令 ==========
                    final_command = command_frame["joint_angles"]
                
                # ========== 3. 发送命令给机器人 ==========
                self.send_joint_command(final_command)
                
                # ========== 4. 更新跟随状态（基于视觉/听觉信息）==========
                self._update_follow_state()
                
                # 控制发送频率（100Hz）
                time.sleep(0.01)
                
            except Exception as e:
                self.get_logger().error(f'[线程B] 错误: {e}')
                import traceback
                self.get_logger().error(traceback.format_exc())
                time.sleep(0.1)
    
    def _merge_follow_command(self, command_frame):
        """
        合并跟随命令和线程A的命令帧
        
        Args:
            command_frame: 线程A生成的命令帧
        
        Returns:
            merged_angles: 合并后的关节角度 [28]
        """
        # 获取线程A的命令
        thread_a_angles = command_frame["joint_angles"]  # [28]
        
        # 获取视觉/听觉信息
        with self.data_lock:
            vision_info = self.vision_info
            audio_info = self.audio_info
        
        # 调用跟随模块生成跟随命令
        # TODO: 跟随模块需要提供一个接口返回关节角度增量
        follow_delta = self._get_follow_command_delta(vision_info, audio_info)
        
        # 合并：线程A命令 + 跟随增量
        merged_angles = thread_a_angles + follow_delta
        
        return merged_angles
    
    def _get_follow_command_delta(self, vision_info, audio_info):
        """
        获取跟随命令的关节角度增量
        
        接口函数：需要实现
        
        Args:
            vision_info: 视觉信息
            audio_info: 听觉信息
        
        Returns:
            delta_angles: 关节角度增量 [28]
        """
        # TODO: 实现跟随命令生成
        # 可能的方案：
        # 1. 调用follow_module.get_follow_delta()
        # 2. 基于目标位置计算头部/身体转向角度
        # 3. 只修改相关关节（如颈部、腰部），其他关节保持0
        
        # 临时：返回零增量
        return np.zeros(28)
    
    def _update_follow_state(self):
        """更新跟随状态"""
        # 获取视觉/听觉信息
        with self.data_lock:
            vision_info = self.vision_info
            audio_info = self.audio_info
        
        # 解析视觉信息
        try:
            vision_data = json.loads(vision_info) if vision_info else {}
            target_detected = vision_data.get("face_detected", False)
            
            # 更新FOLLOW_STATE
            with self.data_lock:
                self.FOLLOW_STATE = target_detected
                
        except:
            pass
    
    def _enter_search_state(self):
        """
        进入搜寻子状态
        
        搜寻状态下：
        1. 生成搜寻命令
        2. 直接发送给机器人
        3. 线程A的命令帧停止发送
        """
        self.get_logger().info('[线程B] 搜寻状态激活')
        
        # 获取视觉/听觉信息
        with self.data_lock:
            vision_info = self.vision_info
            audio_info = self.audio_info
        
        # 调用搜索模块
        target_found = self.search_module.execute(vision_info, audio_info)
        
        if target_found:
            # 找到目标，退出搜寻状态
            self.get_logger().info('[线程B] 找到目标，退出搜寻状态')
            with self.data_lock:
                self.search_command_received = False
                self.FOLLOW_STATE = True  # 进入跟随状态
        else:
            # 继续搜寻
            # 生成搜寻命令
            search_command = self._generate_search_command()
            
            # 发送搜寻命令
            self.send_joint_command(search_command)
    
    def _generate_search_command(self):
        """
        生成搜寻命令
        
        接口函数：需要实现
        
        Returns:
            search_angles: 搜寻关节角度 [28]
        """
        # TODO: 实现搜寻命令生成
        # 可能的方案：
        # 1. 调用search_module.get_search_command()
        # 2. 生成头部/身体扫视动作
        # 3. 基于DOA方向生成转向命令
        
        # 临时：返回零角度
        return np.zeros(28)
    
    # ========================================================================
    # 机器人通信接口
    # ========================================================================
    
    def send_joint_command(self, joint_angles):
        """
        发送关节角度命令给机器人
        
        接口函数：需要实现
        
        Args:
            joint_angles: np.array([28]) 或 list，单位为度数
        """
        # TODO: 实现与机器人通信的逻辑
        # 示例：
        # 1. 将角度转换为机器人协议格式
        # 2. 通过串口/网络发送给机器人控制器
        # 3. 等待反馈（可选）
        
        # 示例实现（发布ROS消息）：
        # from sensor_msgs.msg import JointState
        # msg = JointState()
        # msg.name = self.joint_names
        # msg.position = joint_angles.tolist() if isinstance(joint_angles, np.ndarray) else joint_angles
        # msg.header.stamp = self.get_clock().now().to_msg()
        # self.joint_cmd_pub.publish(msg)
        
        pass
    
    def shutdown(self):
        """关闭节点"""
        self.get_logger().info('关闭主节点...')
        self.running = False
        self.cloud_client.stop()
        
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