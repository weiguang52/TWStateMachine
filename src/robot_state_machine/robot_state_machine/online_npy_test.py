import os
import time
import threading
from collections import deque
from queue import Queue, Empty

import numpy as np
import rclpy
from rclpy.node import Node


class OnlineNPYLoader:
    """
    监控 npy 文件变化 -> np.load -> 解析 dict['motion'] -> 按时间帧追加到 motion_list
    兼容：
      - np.load 结果是 0-d object ndarray（里面装 dict）
      - dict: { motion: (B, J, C, T), text: [...], lengths: [...] }
    """
    def __init__(
        self,
        npy_path: str,
        logger,
        poll_interval: float = 0.05,
        stable_wait: float = 0.05,
        allow_pickle: bool = True,
        max_keep_frames: int = 5000,
        prefer_key: str = "motion",
    ):
        self.npy_path = npy_path
        self.log = logger
        self.poll_interval = poll_interval
        self.stable_wait = stable_wait
        self.allow_pickle = allow_pickle
        self.max_keep_frames = max_keep_frames
        self.prefer_key = prefer_key

        self._stop_evt = threading.Event()
        self._thread = None
        self._last_sig = None  # (mtime, size)

        self._lock = threading.Lock()
        self.motion_list = []  # 每个元素是一帧，比如 (22,3)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.log(f"[OnlineNPYLoader] watching: {self.npy_path}")

    def stop(self):
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _file_sig(self):
        try:
            st = os.stat(self.npy_path)
            return (st.st_mtime, st.st_size)
        except FileNotFoundError:
            return None

    def _wait_stable(self):
        sig1 = self._file_sig()
        time.sleep(self.stable_wait)
        sig2 = self._file_sig()
        return sig1 == sig2 and sig1 is not None

    def _unwrap_loaded(self, loaded):
        """把 np.load 的结果解包到真正的 python 对象（dict / ndarray）"""
        if isinstance(loaded, np.ndarray) and loaded.ndim == 0:
            # 0-d object array
            try:
                return loaded.item()
            except Exception:
                return loaded
        return loaded

    def _extract_frames_from_obj(self, obj):
        """
        返回 frames(list[np.ndarray])，以及一些info dict用于日志
        期望 obj 是 dict，且 obj['motion'] shape=(B,J,C,T)
        """
        info = {}
        # 如果是 dict
        if isinstance(obj, dict):
            info["keys"] = list(obj.keys())

            if self.prefer_key in obj:
                motion = obj[self.prefer_key]
            else:
                # fallback：如果没有 motion key，就找第一个 ndarray
                motion = None
                for k, v in obj.items():
                    if isinstance(v, np.ndarray):
                        motion = v
                        info["fallback_key"] = k
                        break

            info["text"] = None
            if "text" in obj:
                try:
                    info["text"] = obj["text"][0] if isinstance(obj["text"], (list, tuple)) and obj["text"] else obj["text"]
                except Exception:
                    info["text"] = "<unreadable>"

            if "lengths" in obj:
                try:
                    info["lengths"] = obj["lengths"].tolist() if isinstance(obj["lengths"], np.ndarray) else obj["lengths"]
                except Exception:
                    info["lengths"] = "<unreadable>"
        else:
            motion = obj

        if not isinstance(motion, np.ndarray):
            raise TypeError(f"expected motion ndarray, got {type(motion)}")

        info["motion_shape"] = list(motion.shape)
        info["motion_dtype"] = str(motion.dtype)

        # 你现在的数据： (1, 22, 3, 196)
        # 我们按最后一维 T 切帧：每帧 (22, 3)
        if motion.ndim == 4:
            B, J, C, T = motion.shape
            # 只取 batch=0
            m = motion[0]  # (J,C,T)
            frames = [m[:, :, t].copy() for t in range(T)]  # list of (J,C)
            info["frame_shape"] = [J, C]
            info["num_frames"] = T
            return frames, info

        # 其他情况：如果 motion 是 (T,...) 也支持
        if motion.ndim >= 1:
            T = motion.shape[0]
            frames = [motion[t].copy() for t in range(T)]
            info["num_frames"] = T
            info["frame_shape"] = list(frames[0].shape) if frames else None
            return frames, info

        # 标量就当一帧
        return [motion.copy()], info

    def _loop(self):
        while not self._stop_evt.is_set():
            sig = self._file_sig()
            if sig is None:
                time.sleep(self.poll_interval)
                continue

            if self._last_sig is None:
                self._last_sig = sig

            if sig != self._last_sig:
                if self._wait_stable():
                    self._last_sig = sig
                    try:
                        loaded = np.load(self.npy_path, allow_pickle=self.allow_pickle)
                        obj = self._unwrap_loaded(loaded)

                        frames, info = self._extract_frames_from_obj(obj)

                        appended = 0
                        with self._lock:
                            self.motion_list.extend(frames)
                            appended = len(frames)

                            if len(self.motion_list) > self.max_keep_frames:
                                drop = len(self.motion_list) - self.max_keep_frames
                                del self.motion_list[:drop]

                            total = len(self.motion_list)

                        # ✅ 只打一条关键日志
                        extra = []
                        if info.get("motion_shape") is not None:
                            extra.append(f"motion_shape={info['motion_shape']}")
                        if info.get("num_frames") is not None:
                            extra.append(f"T={info['num_frames']}")
                        if info.get("text") is not None:
                            t = info["text"]
                            if isinstance(t, str) and len(t) > 60:
                                t = t[:60] + "..."
                            extra.append(f"text={t!r}")
                        if info.get("lengths") is not None:
                            extra.append(f"lengths={info['lengths']}")

                        self.log(f"[OnlineNPYLoader] loaded ok, appended={appended}, total={total} | " + ", ".join(extra))

                    except Exception as e:
                        self.log(f"[OnlineNPYLoader] load failed: {e}")

            time.sleep(self.poll_interval)

    def pop_frames(self, n: int):
        """从缓存取前 n 帧，返回 np.ndarray shape=(k, J, C)；没数据返回 None"""
        with self._lock:
            if not self.motion_list:
                return None
            k = min(n, len(self.motion_list))
            frames = self.motion_list[:k]
            del self.motion_list[:k]

        try:
            return np.stack(frames, axis=0)
        except Exception:
            return np.array(frames, dtype=object)


class OnlineNPYMinTestNode(Node):
    """
    最小化在线测试节点：
      - OnlineNPYLoader 监控 /tmp/robot_action.npy
      - 线程A：pop_frames -> 放入队列
      - 线程B：从队列取出 -> 模拟下发（只计数+轻量日志）
    """
    def __init__(self):
        super().__init__("online_npy_min_test_node")

        # ====== 参数 ======
        self.NPY_PATH = "/tmp/robot_action.npy"
        self.CUT_FRAME_NUM = 20
        self.running = True

        # 队列：A -> B
        self.q = Queue(maxsize=200)

        # 计数
        self.total_popped = 0
        self.total_consumed = 0

        # 在线 loader
        self.loader = OnlineNPYLoader(
            npy_path=self.NPY_PATH,
            logger=self.get_logger().info,
            poll_interval=0.05,
            stable_wait=0.05,
            allow_pickle=True,
            max_keep_frames=5000,
        )
        self.loader.start()

        # 线程
        self.th_a = threading.Thread(target=self.thread_a_loop, daemon=True)
        self.th_b = threading.Thread(target=self.thread_b_loop, daemon=True)
        self.th_a.start()
        self.th_b.start()

        # 每 2 秒打印一次轻量状态（你嫌吵就把这行注释掉）
        self.timer = self.create_timer(2.0, self.print_status)

        self.get_logger().info("[MinTest] started. Only tests: load->pop->queue->consume")

    def thread_a_loop(self):
        while self.running:
            try:
                # 从在线缓存拿一批帧
                frames = self.loader.pop_frames(self.CUT_FRAME_NUM)
                if frames is None:
                    time.sleep(0.02)
                    continue

                # 放入队列（避免阻塞：满了就稍等）
                try:
                    self.q.put(frames, timeout=0.1)
                    self.total_popped += len(frames)
                    # ✅关键日志：每次入队一条（你嫌吵可改成每 N 次打印）
                    self.get_logger().info(f"[ThreadA] queued frames={len(frames)}, qsize={self.q.qsize()}")
                except Exception:
                    time.sleep(0.02)

            except Exception as e:
                self.get_logger().error(f"[ThreadA] error: {e}")
                time.sleep(0.1)

    def thread_b_loop(self):
        while self.running:
            try:
                # 队列为空时，不永久阻塞（便于观察线程活着）
                try:
                    frames = self.q.get(timeout=0.2)
                except Empty:
                    continue

                # 模拟“下发”：这里只做计数，不接实机、不做 IK
                n = len(frames) if hasattr(frames, "__len__") else 1
                self.total_consumed += n

                # ✅关键日志：每次消费一条（嫌吵可降低频率）
                self.get_logger().info(f"[ThreadB] consumed frames={n}, total={self.total_consumed}")

            except Exception as e:
                self.get_logger().error(f"[ThreadB] error: {e}")
                time.sleep(0.1)

    def print_status(self):
        # 轻量状态（你嫌吵可注释掉 timer）
        self.get_logger().info(
            f"[Status] popped={self.total_popped}, consumed={self.total_consumed}, "
            f"cache_len={len(self.loader.motion_list)}, qsize={self.q.qsize()}"
        )

    def destroy_node(self):
        self.running = False
        try:
            self.loader.stop()
        except Exception:
            pass
        super().destroy_node()


def main():
    rclpy.init()
    node = OnlineNPYMinTestNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
