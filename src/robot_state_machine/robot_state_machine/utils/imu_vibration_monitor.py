#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import math
import time
from collections import deque
from typing import Tuple

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32


class ImuVibrationEstimator:
    """
    可复用的 IMU 振动强度估计器

    输入：
        一帧陀螺仪角速度 wx, wy, wz
    输出：
        mag_high: 当前帧带通后的三轴合成幅值
        p_high  : 滑窗 RMS 后的高频能量

    说明：
    - 这里使用角速度而不是线加速度
    - 用带通后的高频分量表示“振动/敲击/抖动”强度
    """

    def __init__(
        self,
        fs: float = 100.0,
        bpf_low: float = 8.0,
        bpf_high: float = 30.0,
        filter_order: int = 4,
        rms_window_sec: float = 0.5,
    ):
        if fs <= 0:
            raise ValueError("fs must be > 0")
        if not (0 < bpf_low < bpf_high < fs / 2.0):
            raise ValueError(
                f"bandpass must satisfy 0 < low < high < fs/2, got low={bpf_low}, high={bpf_high}, fs={fs}"
            )

        self.fs = fs
        self.bpf_low = bpf_low
        self.bpf_high = bpf_high
        self.filter_order = filter_order
        self.rms_window_sec = rms_window_sec

        nyq = 0.5 * self.fs
        low = self.bpf_low / nyq
        high = self.bpf_high / nyq

        self.sos = butter(
            self.filter_order,
            [low, high],
            btype="bandpass",
            output="sos",
        )

        # 每个轴各自一套滤波器状态
        self.zi_x = sosfilt_zi(self.sos) * 0.0
        self.zi_y = sosfilt_zi(self.sos) * 0.0
        self.zi_z = sosfilt_zi(self.sos) * 0.0

        self.rms_window_size = max(2, int(self.fs * self.rms_window_sec))
        self.mag_window = deque(maxlen=self.rms_window_size)

    def reset(self):
        self.zi_x = sosfilt_zi(self.sos) * 0.0
        self.zi_y = sosfilt_zi(self.sos) * 0.0
        self.zi_z = sosfilt_zi(self.sos) * 0.0
        self.mag_window.clear()

    def update(self, wx: float, wy: float, wz: float) -> Tuple[float, float]:
        """
        输入一帧角速度，输出：
            mag_high: 当前高频带通幅值
            p_high  : 滑窗RMS高频能量
        """
        fx_arr, self.zi_x = sosfilt(self.sos, [wx], zi=self.zi_x)
        fy_arr, self.zi_y = sosfilt(self.sos, [wy], zi=self.zi_y)
        fz_arr, self.zi_z = sosfilt(self.sos, [wz], zi=self.zi_z)

        fx = float(fx_arr[0])
        fy = float(fy_arr[0])
        fz = float(fz_arr[0])

        mag_high = math.sqrt(fx * fx + fy * fy + fz * fz)

        self.mag_window.append(mag_high)
        arr = np.array(self.mag_window, dtype=np.float64)
        p_high = float(np.sqrt(np.mean(arr ** 2))) if len(arr) > 0 else 0.0

        return mag_high, p_high

    def update_from_imu_msg(self, msg: Imu) -> Tuple[float, float]:
        wx = float(msg.angular_velocity.x)
        wy = float(msg.angular_velocity.y)
        wz = float(msg.angular_velocity.z)
        return self.update(wx, wy, wz)


class ImuVibrationMonitor(Node):
    """
    独立调试节点：
    订阅 /imu/raw
    发布：
        /imu/vibration/p_high
        /imu/vibration/mag_high
    """

    def __init__(self):
        super().__init__("vibration_monitor_node")

        self.topic_name = "/imu/raw"
        self.fs = 100.0
        self.bpf_low = 8.0
        self.bpf_high = 30.0
        self.filter_order = 4
        self.rms_window_sec = 0.5

        self.log_every_n = 20
        self.counter = 0

        self.estimator = ImuVibrationEstimator(
            fs=self.fs,
            bpf_low=self.bpf_low,
            bpf_high=self.bpf_high,
            filter_order=self.filter_order,
            rms_window_sec=self.rms_window_sec,
        )

        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        self.save_dir = os.path.join(current_dir, "imu_vibration_output")
        os.makedirs(self.save_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        self.csv_path = os.path.join(self.save_dir, f"imu_vibration_{ts}.csv")

        self.start_time = time.time()

        self.sub = self.create_subscription(
            Imu, self.topic_name, self.imu_callback, 10
        )

        self.pub_p_high = self.create_publisher(Float32, "/imu/vibration/p_high", 10)
        self.pub_mag_high = self.create_publisher(Float32, "/imu/vibration/mag_high", 10)

        self.csv_file = open(self.csv_path, "w", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            "t",
            "wx", "wy", "wz",
            "mag_high",
            "p_high"
        ])
        self.csv_file.flush()

        self.get_logger().info(
            f"IMU振动检测节点已启动: topic={self.topic_name}, "
            f"fs={self.fs}Hz, BPF=[{self.bpf_low}, {self.bpf_high}]Hz, "
            f"RMS窗口={self.rms_window_sec}s"
        )
        self.get_logger().info(f"CSV保存路径: {self.csv_path}")

    def imu_callback(self, msg: Imu):
        wx = float(msg.angular_velocity.x)
        wy = float(msg.angular_velocity.y)
        wz = float(msg.angular_velocity.z)

        mag_high, p_high = self.estimator.update(wx, wy, wz)

        t = time.time() - self.start_time

        msg_p = Float32()
        msg_p.data = p_high
        self.pub_p_high.publish(msg_p)

        msg_m = Float32()
        msg_m.data = mag_high
        self.pub_mag_high.publish(msg_m)

        self.csv_writer.writerow([t, wx, wy, wz, mag_high, p_high])

        self.counter += 1
        if self.counter % self.log_every_n == 0:
            self.csv_file.flush()
            self.get_logger().info(
                f"P_high={p_high:.4f}, mag_high={mag_high:.4f}, "
                f"raw=[{wx:+.3f}, {wy:+.3f}, {wz:+.3f}]"
            )

    def destroy_node(self):
        try:
            if hasattr(self, "csv_file") and self.csv_file:
                self.csv_file.flush()
                self.csv_file.close()
        except Exception as e:
            self.get_logger().warn(f"关闭CSV文件失败: {e}")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ImuVibrationMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("收到 Ctrl-C，准备退出...")
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass

        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()


# -------------------------------------------------------------------------------

# '''
# 订阅 /imu/raw

# 不做任何高频带通滤波

# 直接保存原始 wx wy wz

# 额外保存原始三轴合成幅值 mag_raw

# 再对 mag_raw 做一个滑窗 RMS，记为 p_raw

# '''
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# import os
# import csv
# import math
# import time
# from collections import deque

# import numpy as np

# import rclpy
# from rclpy.node import Node
# from sensor_msgs.msg import Imu
# from std_msgs.msg import Float32


# class ImuVibrationMonitor(Node):
#     def __init__(self):
#         super().__init__("vibration_monitor_node")

#         # ===== 参数 =====
#         self.topic_name = "/imu/raw"
#         self.fs = 100.0
#         self.rms_window_sec = 0.5

#         # 打印频率：不要每帧都打，不然终端刷爆
#         self.log_every_n = 20   # 100Hz 下约每 0.2 秒打印一次
#         self.counter = 0

#         # 输出目录
#         current_file_path = os.path.abspath(__file__)
#         current_dir = os.path.dirname(current_file_path)
#         self.save_dir = os.path.join(current_dir, "imu_vibration_output")
#         os.makedirs(self.save_dir, exist_ok=True)

#         ts = time.strftime("%Y%m%d_%H%M%S")
#         self.csv_path = os.path.join(self.save_dir, f"imu_raw_{ts}.csv")

#         # ===== RMS 滑动窗口 =====
#         self.rms_window_size = max(2, int(self.fs * self.rms_window_sec))
#         self.mag_window = deque(maxlen=self.rms_window_size)

#         self.start_time = time.time()

#         # ===== ROS =====
#         self.sub = self.create_subscription(
#             Imu, self.topic_name, self.imu_callback, 10
#         )

#         self.pub_p_raw = self.create_publisher(Float32, "/imu/vibration/p_raw", 10)
#         self.pub_mag_raw = self.create_publisher(Float32, "/imu/vibration/mag_raw", 10)

#         # ===== CSV =====
#         self.csv_file = open(self.csv_path, "w", newline="", encoding="utf-8")
#         self.csv_writer = csv.writer(self.csv_file)
#         self.csv_writer.writerow([
#             "t",
#             "wx", "wy", "wz",
#             "mag_raw",
#             "p_raw"
#         ])
#         self.csv_file.flush()

#         self.get_logger().info(
#             f"IMU原始数据采集节点已启动: topic={self.topic_name}, "
#             f"fs={self.fs}Hz, RMS窗口={self.rms_window_sec}s"
#         )
#         self.get_logger().info(f"CSV保存路径: {self.csv_path}")

#     def imu_callback(self, msg: Imu):
#         # 原始陀螺仪角速度
#         wx = msg.angular_velocity.x
#         wy = msg.angular_velocity.y
#         wz = msg.angular_velocity.z

#         # 原始三轴合成幅值
#         mag_raw = math.sqrt(wx * wx + wy * wy + wz * wz)

#         # 滑窗 RMS（对原始幅值做）
#         self.mag_window.append(mag_raw)
#         arr = np.array(self.mag_window, dtype=np.float64)
#         p_raw = float(np.sqrt(np.mean(arr ** 2))) if len(arr) > 0 else 0.0

#         t = time.time() - self.start_time

#         # 发布
#         msg_p = Float32()
#         msg_p.data = p_raw
#         self.pub_p_raw.publish(msg_p)

#         msg_m = Float32()
#         msg_m.data = mag_raw
#         self.pub_mag_raw.publish(msg_m)

#         # 保存 CSV
#         self.csv_writer.writerow([t, wx, wy, wz, mag_raw, p_raw])

#         # 降低 flush 频率
#         self.counter += 1
#         if self.counter % self.log_every_n == 0:
#             self.csv_file.flush()
#             self.get_logger().info(
#                 f"p_raw={p_raw:.4f}, mag_raw={mag_raw:.4f}, "
#                 f"raw=[{wx:+.3f}, {wy:+.3f}, {wz:+.3f}]"
#             )

#     def destroy_node(self):
#         try:
#             if hasattr(self, "csv_file") and self.csv_file:
#                 self.csv_file.flush()
#                 self.csv_file.close()
#         except Exception as e:
#             self.get_logger().warn(f"关闭CSV文件失败: {e}")
#         super().destroy_node()


# def main(args=None):
#     rclpy.init(args=args)
#     node = ImuVibrationMonitor()

#     try:
#         rclpy.spin(node)
#     except KeyboardInterrupt:
#         node.get_logger().info("收到 Ctrl-C，准备退出...")
#     finally:
#         try:
#             node.destroy_node()
#         except Exception:
#             pass

#         # 避免重复 shutdown
#         try:
#             if rclpy.ok():
#                 rclpy.shutdown()
#         except Exception:
#             pass


# if __name__ == "__main__":
#     main()