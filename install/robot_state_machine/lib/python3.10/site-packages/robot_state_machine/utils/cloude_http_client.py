#!/usr/bin/env python3
"""
云端HTTP通信模块（改进版）
支持动态接收.npy文件并转换为NPZ格式处理
"""
import io
import os
import time
import logging
import threading
import numpy as np
import requests
from typing import Optional, Callable, Dict, Any
from queue import Queue, Empty


class CloudHTTPClient:
    """
    云端HTTP通信客户端（改进版）
    
    功能：
    1. 定期向服务器请求.npy文件
    2. 动态读取motion字段
    3. 转换为NPZ格式（兼容原有处理流程）
    4. 将动作存入队列并回调通知
    """
    
    def __init__(self, 
                 server_url: str = "http://localhost:8000/results.npy",
                 poll_interval: float = 0.2,
                 request_method: str = "GET",
                 request_data: Optional[Dict] = None,
                 logger: Optional[logging.Logger] = None,
                 # ========== 新增：NPZ保存相关参数 ==========
                 save_npz: bool = False,
                 npz_save_dir: str = "./received_actions",
                 npz_name_prefix: str = "action"):
        """
        初始化HTTP客户端
        
        Args:
            save_npz: 是否自动保存为NPZ文件
            npz_save_dir: NPZ文件保存目录
            npz_name_prefix: NPZ文件名前缀
        """
        self.server_url = server_url
        self.poll_interval = poll_interval
        self.request_method = request_method.upper()
        self.request_data = request_data or {"text": "a person walks forward"}
        
        # 日志
        self.logger = logger or self._create_default_logger()
        
        # 动作序列队列
        self.action_queue = Queue(maxsize=10)
        
        # 回调函数
        self.on_action_received: Optional[Callable[[Dict], None]] = None
        self.on_error_received: Optional[Callable[[str], None]] = None
        
        # 连接状态
        self.running = False
        self.poll_thread = None
        
        # 统计信息
        self.stats = {
            "requests_sent": 0,
            "actions_received": 0,
            "errors": 0,
            "last_request_time": None,
            "npz_files_saved": 0  # ← 新增
        }
        
        # 上次接收的动作ID（用于去重）
        self.last_action_id = None
        
        # 连续失败计数
        self.consecutive_failures = 0
        self.max_failures_before_warning = 5
        
        # ========== NPZ保存配置 ==========
        self.save_npz = save_npz
        self.npz_save_dir = npz_save_dir
        self.npz_name_prefix = npz_name_prefix
        
        # 创建保存目录
        if self.save_npz:
            os.makedirs(self.npz_save_dir, exist_ok=True)
            self.logger.info(f"[CloudHTTP] NPZ保存已启用: {self.npz_save_dir}")
        
        self.logger.info(f"[CloudHTTP] 初始化完成")
        self.logger.info(f"  服务器: {server_url}")
        self.logger.info(f"  请求方法: {self.request_method}")
        if self.request_method == "POST":
            self.logger.info(f"  POST数据: {self.request_data}")
        self.logger.info(f"  轮询间隔: {poll_interval}秒 ({1/poll_interval:.1f}Hz)")
    
    def _create_default_logger(self) -> logging.Logger:
        """创建默认日志记录器"""
        logger = logging.getLogger("CloudHTTPClient")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def start(self):
        """启动HTTP轮询"""
        if self.running:
            self.logger.warning("[CloudHTTP] 客户端已在运行")
            return
        
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        
        self.logger.info("[CloudHTTP] 开始轮询云端数据")
    
    def stop(self):
        """停止HTTP轮询"""
        if not self.running:
            return
        
        self.running = False
        if self.poll_thread:
            self.poll_thread.join(timeout=2.0)
        
        self.logger.info("[CloudHTTP] 停止轮询")
    
    def _poll_loop(self):
        """轮询循环（在后台线程中运行）"""
        while self.running:
            try:
                self._fetch_and_process()
                time.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.error(f"[CloudHTTP] 轮询错误: {e}")
                self.stats["errors"] += 1
                self.consecutive_failures += 1
                
                # 错误后延长间隔
                time.sleep(min(self.poll_interval * 2, 5.0))
    
    def _fetch_and_process(self):
        """获取并处理.npy文件"""
        try:
            # 根据请求方法发送HTTP请求
            if self.request_method == "POST":
                # POST请求
                response = requests.post(
                    self.server_url,
                    json=self.request_data,  # 发送JSON数据
                    headers={'Content-Type': 'application/json'},
                    timeout=5.0
                )
            else:
                # GET请求
                response = requests.get(
                    self.server_url,
                    timeout=5.0,
                    stream=False
                )
            
            self.stats["requests_sent"] += 1
            self.stats["last_request_time"] = time.time()
            
            # 检查响应状态
            if response.status_code != 200:
                if self.consecutive_failures < self.max_failures_before_warning:
                    self.consecutive_failures += 1
                elif self.consecutive_failures == self.max_failures_before_warning:
                    self.logger.warning(
                        f"[CloudHTTP] HTTP错误: {response.status_code}"
                    )
                    self.consecutive_failures += 1
                return
            
            # 重置失败计数
            if self.consecutive_failures > 0:
                self.logger.info("[CloudHTTP] 连接恢复")
                self.consecutive_failures = 0
            
            # 解析.npy文件
            npy_data = response.content
            
            # 检查数据是否为空
            if not npy_data or len(npy_data) < 128:  # NPY文件最小头部
                return
            
            # 解析动作数据
            action_data = self._parse_npy_to_action(npy_data)
            
            if action_data:
                # 去重检查（基于时间戳或内容hash）
                action_id = action_data.get("request_id")
                if action_id == self.last_action_id:
                    # 相同的动作，跳过
                    return
                
                self.last_action_id = action_id
                
                # 存入队列
                if self.action_queue.full():
                    # 队列满，移除最旧的
                    try:
                        self.action_queue.get_nowait()
                        self.logger.warning("[CloudHTTP] 队列已满，丢弃最旧动作")
                    except Empty:
                        pass
                
                self.action_queue.put(action_data)
                self.stats["actions_received"] += 1
                
                self.logger.info(
                    f"[CloudHTTP] 收到动作: {action_data.get('description', '未知')}, "
                    f"帧数: {action_data['num_frames']}, "
                    f"队列: {self.action_queue.qsize()}/10"
                )
                
                # 触发回调
                if self.on_action_received:
                    try:
                        self.on_action_received(action_data)
                    except Exception as e:
                        self.logger.error(f"[CloudHTTP] 回调错误: {e}")
        
        except requests.exceptions.Timeout:
            self.consecutive_failures += 1
            if self.consecutive_failures == self.max_failures_before_warning:
                self.logger.warning("[CloudHTTP] 请求超时（持续）")
        
        except requests.exceptions.ConnectionError:
            self.consecutive_failures += 1
            if self.consecutive_failures == self.max_failures_before_warning:
                self.logger.warning("[CloudHTTP] 连接失败（持续）")
        
        except Exception as e:
            self.logger.error(f"[CloudHTTP] 处理错误: {e}")
            if self.on_error_received:
                self.on_error_received(str(e))
    
    def _parse_npy_to_action(self, npy_bytes: bytes) -> Optional[Dict]:
        """
        解析.npy文件并转换为action_data（类似NPZ格式）
        
        Args:
            npy_bytes: .npy文件的字节流
        
        Returns:
            Dict: 兼容NPZ格式的动作数据字典
        """
        try:
            # 从字节流加载numpy数组
            data = np.load(io.BytesIO(npy_bytes), allow_pickle=True)
            
            # 根据数据类型处理
            if data.dtype == np.object_:
                # 结构化数据（字典）
                data_dict = data.item()
                
                if isinstance(data_dict, dict):
                    # 提取motion字段
                    motion = data_dict.get('motion')
                    
                    if motion is None:
                        self.logger.warning("[CloudHTTP] .npy中未找到motion字段")
                        return None
                    
                    # 构造NPZ兼容格式
                    action_data = self._build_action_data(
                        motion=motion,
                        fps=data_dict.get('fps', 20),
                        description=data_dict.get('description', 'HTTP动作'),
                        metadata=data_dict
                    )
                    
                    return action_data
                else:
                    self.logger.warning(f"[CloudHTTP] 不支持的数据类型: {type(data_dict)}")
                    return None
            
            else:
                # 直接是motion数组
                action_data = self._build_action_data(
                    motion=data,
                    fps=20,
                    description='HTTP动作'
                )
                
                return action_data
        
        except Exception as e:
            self.logger.error(f"[CloudHTTP] 解析.npy失败: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def _build_action_data(self, 
                        motion: np.ndarray, 
                        fps: int = 20,
                        description: str = "动作",
                        metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        构造标准的action_data格式（兼容NPZ处理流程）
        """
        try:
            # ========== 打印调试信息 ==========
            self.logger.info(
                f"[CloudHTTP] motion原始形状: {motion.shape}, "
                f"dtype: {motion.dtype}, ndim: {motion.ndim}"
            )
            
            # ========== 处理不同维度的motion数据 ==========
            if motion.ndim == 0:
                self.logger.error("[CloudHTTP] motion是标量，无法处理")
                return None
            
            elif motion.ndim == 1:
                self.logger.warning(
                    f"[CloudHTTP] motion是1D数组(长度{len(motion)})，reshape为单帧"
                )
                motion = motion.reshape(1, -1)
            
            elif motion.ndim == 2:
                # 2D数组 [num_frames, num_joints]，正常情况
                pass
            
            elif motion.ndim == 3:
                # 3D数组，可能是 [batch, num_frames, num_joints]
                self.logger.warning(
                    f"[CloudHTTP] motion是3D数组{motion.shape}，取第一个batch"
                )
                motion = motion[0]
            
            elif motion.ndim == 4:
                # 4D数组，通常是 [batch, num_joints, xyz, num_frames]
                # 需要转换为 [num_frames, num_joints * xyz]
                batch, num_joints, xyz, num_frames = motion.shape
                
                self.logger.warning(
                    f"[CloudHTTP] motion是4D数组{motion.shape}，"
                    f"识别为[batch={batch}, joints={num_joints}, xyz={xyz}, frames={num_frames}]"
                )
                
                # 取第一个batch: [num_joints, xyz, num_frames]
                motion = motion[0]
                
                # 转置为 [num_frames, num_joints, xyz]
                motion = np.transpose(motion, (2, 0, 1))
                
                # reshape为 [num_frames, num_joints * xyz]
                motion = motion.reshape(num_frames, -1)
                
                self.logger.info(
                    f"[CloudHTTP] 4D数据转换完成: "
                    f"{(batch, num_joints, xyz, num_frames)} → {motion.shape}"
                )
            
            else:
                # 更高维度
                self.logger.error(
                    f"[CloudHTTP] 不支持{motion.ndim}D数组: {motion.shape}"
                )
                return None
            
            # ========== 再次检查维度 ==========
            if motion.ndim != 2:
                self.logger.error(
                    f"[CloudHTTP] 处理后motion维度仍不是2D: {motion.shape}"
                )
                return None
            
            num_frames, num_joints = motion.shape
            
            # ========== 数据有效性检查 ==========
            if num_frames == 0 or num_joints == 0:
                self.logger.error(
                    f"[CloudHTTP] motion形状无效: ({num_frames}, {num_joints})"
                )
                return None
            
            self.logger.info(
                f"[CloudHTTP] ✓ 最终motion形状: ({num_frames}帧, {num_joints}维)"
            )
            
            # ========== 构造action_data ==========
            action_data = {
                "dof_real": motion,  # [num_frames, num_joints]
                "fps": fps,
                "num_frames": num_frames,
                "description": description,
                "request_id": f"http_{int(time.time() * 1000)}",
                "received_time": time.time()
            }
            
            # ========== 添加可选字段 ==========
            if metadata:
                if 'root_trans_offset' in metadata:
                    root_trans = metadata['root_trans_offset']
                    if isinstance(root_trans, np.ndarray):
                        if root_trans.ndim == 3:
                            root_trans = root_trans[0]
                        if root_trans.ndim == 2 and root_trans.shape[0] != num_frames:
                            self.logger.warning(
                                f"[CloudHTTP] root_trans_offset帧数不匹配: "
                                f"{root_trans.shape[0]} vs {num_frames}"
                            )
                        action_data['root_trans_offset'] = root_trans
                
                if 'root_rot' in metadata:
                    root_rot = metadata['root_rot']
                    if isinstance(root_rot, np.ndarray):
                        if root_rot.ndim == 3:
                            root_rot = root_rot[0]
                        if root_rot.ndim == 2 and root_rot.shape[0] != num_frames:
                            self.logger.warning(
                                f"[CloudHTTP] root_rot帧数不匹配: "
                                f"{root_rot.shape[0]} vs {num_frames}"
                            )
                        action_data['root_rot'] = root_rot
            
            return action_data
        
        except Exception as e:
            self.logger.error(f"[CloudHTTP] 构造action_data失败: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None

    def _fetch_and_process(self):
        """获取并处理.npy文件"""
        try:
            # ========== 1. 发送HTTP请求 ==========
            if self.request_method == "POST":
                # POST请求
                response = requests.post(
                    self.server_url,
                    json=self.request_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=5.0
                )
            else:
                # GET请求
                response = requests.get(
                    self.server_url,
                    timeout=5.0,
                    stream=False
                )
            
            self.stats["requests_sent"] += 1
            self.stats["last_request_time"] = time.time()
            
            # ========== 2. 检查响应状态 ==========
            if response.status_code != 200:
                if self.consecutive_failures < self.max_failures_before_warning:
                    self.consecutive_failures += 1
                elif self.consecutive_failures == self.max_failures_before_warning:
                    self.logger.warning(
                        f"[CloudHTTP] HTTP错误: {response.status_code}"
                    )
                    self.consecutive_failures += 1
                return
            
            # ========== 3. 重置失败计数 ==========
            if self.consecutive_failures > 0:
                self.logger.info("[CloudHTTP] 连接恢复")
                self.consecutive_failures = 0
            
            # ========== 4. 获取响应内容（定义npy_data）==========
            npy_data = response.content  # ← 这里定义npy_data
            
            # ========== 5. 检查数据是否为空 ==========
            if not npy_data or len(npy_data) < 128:  # NPY文件最小头部
                return
            
            # 解析动作数据
            action_data = self._parse_npy_to_action(npy_data)
            
            if action_data:
                # 去重检查
                action_id = action_data.get("request_id")
                if action_id == self.last_action_id:
                    return
                
                self.last_action_id = action_id
                
                # ========== 新增：保存为NPZ文件 ==========
                if self.save_npz:
                    npz_path = self.save_action_to_npz(action_data)
                    if npz_path:
                        action_data['npz_path'] = npz_path  # 添加路径到数据中
                
                # 存入队列
                if self.action_queue.full():
                    try:
                        self.action_queue.get_nowait()
                        self.logger.warning("[CloudHTTP] 队列已满，丢弃最旧动作")
                    except Empty:
                        pass
                
                self.action_queue.put(action_data)
                self.stats["actions_received"] += 1
                
                self.logger.info(
                    f"[CloudHTTP] 收到动作: {action_data.get('description', '未知')}, "
                    f"帧数: {action_data['num_frames']}, "
                    f"队列: {self.action_queue.qsize()}/10"
                )
                
                # 触发回调
                if self.on_action_received:
                    try:
                        self.on_action_received(action_data)
                    except Exception as e:
                        self.logger.error(f"[CloudHTTP] 回调错误: {e}")
        
        except Exception as e:
            self.logger.error(f"[CloudHTTP] 处理错误: {e}")
            if self.on_error_received:
                self.on_error_received(str(e))
    
    def save_action_to_npz(self, action_data: Dict) -> Optional[str]:
        """
        将action_data保存为NPZ文件
        
        Args:
            action_data: 动作数据字典
        
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            # 生成文件名（时间戳 + 描述）
            timestamp = int(time.time() * 1000)
            description = action_data.get('description', 'unknown')
            # 清理文件名（移除特殊字符）
            safe_description = "".join(c for c in description if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_description = safe_description.replace(' ', '_')[:50]  # 限制长度
            
            filename = f"{self.npz_name_prefix}_{timestamp}_{safe_description}.npz"
            filepath = os.path.join(self.npz_save_dir, filename)
            
            # 准备保存的数据
            save_dict = {
                'dof_real': action_data['dof_real'],  # [N, num_joints]
                'fps': action_data['fps'],
                'num_frames': action_data['num_frames'],
                'description': action_data.get('description', ''),
                'request_id': action_data.get('request_id', ''),
                'received_time': action_data.get('received_time', time.time())
            }
            
            # 添加可选字段
            if 'root_trans_offset' in action_data and action_data['root_trans_offset'] is not None:
                save_dict['root_trans_offset'] = action_data['root_trans_offset']
            
            if 'root_rot' in action_data and action_data['root_rot'] is not None:
                save_dict['root_rot'] = action_data['root_rot']
            
            # 保存为NPZ
            np.savez_compressed(filepath, **save_dict)
            
            self.stats["npz_files_saved"] += 1
            
            self.logger.info(f"[CloudHTTP] ✓ 保存NPZ: {filename}")
            
            return filepath
        
        except Exception as e:
            self.logger.error(f"[CloudHTTP] 保存NPZ失败: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def save_action_to_npz_manual(self, action_data: Dict, filepath: str) -> bool:
        """
        手动保存action_data到指定路径
        
        Args:
            action_data: 动作数据字典
            filepath: 保存路径（包含文件名）
        
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 准备保存的数据
            save_dict = {
                'dof_real': action_data['dof_real'],
                'fps': action_data['fps'],
                'num_frames': action_data['num_frames'],
                'description': action_data.get('description', ''),
                'request_id': action_data.get('request_id', ''),
                'received_time': action_data.get('received_time', time.time())
            }
            
            # 添加可选字段
            if 'root_trans_offset' in action_data and action_data['root_trans_offset'] is not None:
                save_dict['root_trans_offset'] = action_data['root_trans_offset']
            
            if 'root_rot' in action_data and action_data['root_rot'] is not None:
                save_dict['root_rot'] = action_data['root_rot']
            
            # 保存
            np.savez_compressed(filepath, **save_dict)
            
            self.logger.info(f"[CloudHTTP] ✓ 手动保存NPZ: {filepath}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"[CloudHTTP] 手动保存NPZ失败: {e}")
            return False
    
    # ========== 队列操作接口 ==========
    
    def get_action(self, timeout: Optional[float] = None) -> Optional[Dict]:
        """
        从队列获取动作（阻塞）
        
        Args:
            timeout: 超时时间（秒），None表示永久等待
        
        Returns:
            Dict: 动作数据，超时返回None
        """
        try:
            return self.action_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def try_get_action(self) -> Optional[Dict]:
        """
        尝试从队列获取动作（非阻塞）
        
        Returns:
            Dict: 动作数据，队列为空返回None
        """
        try:
            return self.action_queue.get_nowait()
        except Empty:
            return None
    
    def has_action(self) -> bool:
        """
        检查队列是否有动作
        
        Returns:
            bool: 是否有动作
        """
        return not self.action_queue.empty()
    
    def clear_actions(self):
        """清空动作队列"""
        while not self.action_queue.empty():
            try:
                self.action_queue.get_nowait()
            except Empty:
                break
        
        self.logger.info("[CloudHTTP] 清空动作队列")
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.action_queue.qsize()
    
    # ========== 统计信息 ==========
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "queue_size": self.get_queue_size(),
            "running": self.running,
            "consecutive_failures": self.consecutive_failures
        }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        
        print("=" * 50)
        print("CloudHTTP客户端统计信息")
        print("=" * 50)
        print(f"服务器URL: {self.server_url}")
        print(f"运行状态: {'运行中' if stats['running'] else '已停止'}")
        print(f"轮询频率: {1/self.poll_interval:.1f}Hz")
        print(f"请求次数: {stats['requests_sent']}")
        print(f"收到动作: {stats['actions_received']}")
        print(f"错误次数: {stats['errors']}")
        print(f"连续失败: {stats['consecutive_failures']}")
        print(f"队列大小: {stats['queue_size']}/10")
        
        if stats['last_request_time']:
            elapsed = time.time() - stats['last_request_time']
            print(f"上次请求: {elapsed:.1f}秒前")
        
        print("=" * 50)


# ========== 本地文件版本（用于离线测试）==========

class CloudLocalFileClient:
    """
    本地文件客户端（用于离线测试）
    监控本地.npy文件变化并动态加载
    """
    
    def __init__(self, 
                 file_path: str = "results.npy",
                 poll_interval: float = 0.2,
                 logger: Optional[logging.Logger] = None):
        """
        初始化本地文件客户端
        
        Args:
            file_path: .npy文件路径
            poll_interval: 轮询间隔（秒）
            logger: 日志记录器
        """
        self.file_path = file_path
        self.poll_interval = poll_interval
        
        # 日志
        self.logger = logger or self._create_default_logger()
        
        # 动作序列队列
        self.action_queue = Queue(maxsize=10)
        
        # 回调函数
        self.on_action_received: Optional[Callable[[Dict], None]] = None
        
        # 连接状态
        self.running = False
        self.poll_thread = None
        
        # 上次文件修改时间和内容hash
        self.last_mtime = None
        self.last_content_hash = None
        
        self.logger.info(f"[CloudLocal] 初始化完成")
        self.logger.info(f"  文件路径: {file_path}")
        self.logger.info(f"  轮询间隔: {poll_interval}秒")
    
    def _create_default_logger(self) -> logging.Logger:
        """创建默认日志记录器"""
        logger = logging.getLogger("CloudLocalFileClient")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def start(self):
        """启动文件监控"""
        if self.running:
            self.logger.warning("[CloudLocal] 客户端已在运行")
            return
        
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        
        self.logger.info("[CloudLocal] 开始监控文件")
    
    def stop(self):
        """停止文件监控"""
        if not self.running:
            return
        
        self.running = False
        if self.poll_thread:
            self.poll_thread.join(timeout=2.0)
        
        self.logger.info("[CloudLocal] 停止监控")
    
    def _poll_loop(self):
        """轮询循环"""
        while self.running:
            try:
                self._check_and_load()
                time.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.error(f"[CloudLocal] 轮询错误: {e}")
                time.sleep(self.poll_interval)
    
    def _check_and_load(self):
        """检查文件并加载"""
        try:
            # 检查文件是否存在
            if not os.path.exists(self.file_path):
                return
            
            # 检查文件修改时间
            mtime = os.path.getmtime(self.file_path)
            
            # 只有文件确实更新时才加载
            if self.last_mtime is not None and mtime <= self.last_mtime:
                return
            
            self.last_mtime = mtime
            
            # 加载文件
            self.logger.info(f"[CloudLocal] 检测到文件更新")
            action_data = self._load_npy_file()
            
            if action_data:
                # 内容去重（基于数据hash）
                import hashlib
                content_hash = hashlib.md5(
                    action_data['dof_real'].tobytes()
                ).hexdigest()
                
                if content_hash == self.last_content_hash:
                    self.logger.debug("[CloudLocal] 内容未变化，跳过")
                    return
                
                self.last_content_hash = content_hash
                
                # 存入队列
                if self.action_queue.full():
                    try:
                        self.action_queue.get_nowait()
                    except Empty:
                        pass
                
                self.action_queue.put(action_data)
                
                self.logger.info(
                    f"[CloudLocal] 加载动作: {action_data.get('description', '未知')}, "
                    f"帧数: {action_data['num_frames']}, "
                    f"队列: {self.action_queue.qsize()}/10"
                )
                
                # 触发回调
                if self.on_action_received:
                    self.on_action_received(action_data)
        
        except Exception as e:
            self.logger.error(f"[CloudLocal] 加载错误: {e}")
    
    def _load_npy_file(self) -> Optional[Dict]:
        """加载.npy文件并转换为action_data"""
        try:
            # 读取.npy文件
            data = np.load(self.file_path, allow_pickle=True)
            
            # 提取motion字段
            if data.dtype == np.object_:
                data_dict = data.item()
                
                if isinstance(data_dict, dict) and 'motion' in data_dict:
                    motion = data_dict['motion']
                    
                    # 构造action_data
                    action_data = {
                        "dof_real": motion,
                        "fps": data_dict.get('fps', 20),
                        "num_frames": len(motion) if motion.ndim > 0 else 1,
                        "description": data_dict.get('description', '本地文件动作'),
                        "request_id": f"local_{int(time.time() * 1000)}",
                        "received_time": time.time()
                    }
                    
                    return action_data
            else:
                # 直接是motion数组
                action_data = {
                    "dof_real": data,
                    "fps": 20,
                    "num_frames": len(data) if data.ndim > 0 else 1,
                    "description": "本地文件动作",
                    "request_id": f"local_{int(time.time() * 1000)}",
                    "received_time": time.time()
                }
                
                return action_data
        
        except Exception as e:
            self.logger.error(f"[CloudLocal] 加载失败: {e}")
            return None
    
    # 队列操作接口（与CloudHTTPClient相同）
    def get_action(self, timeout: Optional[float] = None) -> Optional[Dict]:
        try:
            return self.action_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def try_get_action(self) -> Optional[Dict]:
        try:
            return self.action_queue.get_nowait()
        except Empty:
            return None
    
    def has_action(self) -> bool:
        return not self.action_queue.empty()
    
    def clear_actions(self):
        while not self.action_queue.empty():
            try:
                self.action_queue.get_nowait()
            except Empty:
                break
    
    def get_queue_size(self) -> int:
        return self.action_queue.qsize()


# ========== 使用示例 ==========

def example_usage():
    """使用示例"""
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("云端HTTP客户端 - 使用示例")
    print("=" * 60)
    
    # 选择模式
    mode = "local"  # "http" 或 "local"
    
    if mode == "http":
        # HTTP模式
        client = CloudHTTPClient(
            server_url="http://localhost:8000/results.npy",
            poll_interval=0.2  # 5Hz轮询
        )
    else:
        # 本地文件模式
        client = CloudLocalFileClient(
            file_path="results.npy",
            poll_interval=0.2
        )
    
    # 设置回调
    def on_action(action_data):
        print(f"\n✓ 收到动作:")
        print(f"  帧数: {action_data['num_frames']}")
        print(f"  形状: {action_data['dof_real'].shape}")
        print(f"  描述: {action_data.get('description', '未知')}")
    
    client.on_action_received = on_action
    
    # 启动客户端
    client.start()
    
    print(f"\n客户端已启动（{mode}模式）")
    print("等待云端发送动作...")
    print("按Ctrl+C停止\n")
    
    try:
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n停止客户端...")
        client.stop()
        client.print_stats()


if __name__ == "__main__":
    example_usage()