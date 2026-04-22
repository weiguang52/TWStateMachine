# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# import os
# import csv
# import math
# import time
# from collections import deque

# import numpy as np
# from scipy.signal import butter, sosfilt, sosfilt_zi

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
#         self.bpf_low = 8.0
#         self.bpf_high = 30.0
#         self.filter_order = 4
#         self.rms_window_sec = 0.5

#         # 打印频率：不要每帧都打，不然终端刷爆
#         self.log_every_n = 20   # 100Hz下约每0.2秒打印一次
#         self.counter = 0

#         # 输出目录
#         current_file_path = os.path.abspath(__file__)
#         current_dir = os.path.dirname(current_file_path)
#         self.save_dir = os.path.join(current_dir, "imu_vibration_output")
#         # self.save_dir = os.path.expanduser("~/imu_vibration_logs")
#         os.makedirs(self.save_dir, exist_ok=True)
#         ts = time.strftime("%Y%m%d_%H%M%S")
#         self.csv_path = os.path.join(self.save_dir, f"imu_vibration_{ts}.csv")

#         # ===== 滤波器 =====
#         nyq = 0.5 * self.fs
#         low = self.bpf_low / nyq
#         high = self.bpf_high / nyq

#         self.sos = butter(
#             self.filter_order,
#             [low, high],
#             btype="bandpass",
#             output="sos"
#         )

#         self.zi_x = sosfilt_zi(self.sos) * 0.0
#         self.zi_y = sosfilt_zi(self.sos) * 0.0
#         self.zi_z = sosfilt_zi(self.sos) * 0.0

#         self.rms_window_size = max(2, int(self.fs * self.rms_window_sec))
#         self.mag_window = deque(maxlen=self.rms_window_size)

#         self.start_time = time.time()

#         # ===== ROS =====
#         self.sub = self.create_subscription(
#             Imu, self.topic_name, self.imu_callback, 10
#         )

#         self.pub_p_high = self.create_publisher(Float32, "/imu/vibration/p_high", 10)
#         self.pub_mag_high = self.create_publisher(Float32, "/imu/vibration/mag_high", 10)

#         # ===== CSV =====
#         self.csv_file = open(self.csv_path, "w", newline="", encoding="utf-8")
#         self.csv_writer = csv.writer(self.csv_file)
#         self.csv_writer.writerow([
#             "t",
#             "wx", "wy", "wz",
#             "fx", "fy", "fz",
#             "mag_high",
#             "p_high"
#         ])
#         self.csv_file.flush()

#         self.get_logger().info(
#             f"IMU振动检测节点已启动: topic={self.topic_name}, "
#             f"fs={self.fs}Hz, BPF=[{self.bpf_low}, {self.bpf_high}]Hz, "
#             f"RMS窗口={self.rms_window_sec}s"
#         )
#         self.get_logger().info(f"CSV保存路径: {self.csv_path}")

#     def imu_callback(self, msg: Imu):
#         wx = msg.angular_velocity.x
#         wy = msg.angular_velocity.y
#         wz = msg.angular_velocity.z

#         fx_arr, self.zi_x = sosfilt(self.sos, [wx], zi=self.zi_x)
#         fy_arr, self.zi_y = sosfilt(self.sos, [wy], zi=self.zi_y)
#         fz_arr, self.zi_z = sosfilt(self.sos, [wz], zi=self.zi_z)

#         fx = float(fx_arr[0])
#         fy = float(fy_arr[0])
#         fz = float(fz_arr[0])

#         mag_high = math.sqrt(fx * fx + fy * fy + fz * fz)

#         self.mag_window.append(mag_high)
#         arr = np.array(self.mag_window, dtype=np.float64)
#         p_high = float(np.sqrt(np.mean(arr ** 2))) if len(arr) > 0 else 0.0

#         t = time.time() - self.start_time

#         # 发布
#         msg_p = Float32()
#         msg_p.data = p_high
#         self.pub_p_high.publish(msg_p)

#         msg_m = Float32()
#         msg_m.data = mag_high
#         self.pub_mag_high.publish(msg_m)

#         # 保存 CSV
#         self.csv_writer.writerow([t, wx, wy, wz, fx, fy, fz, mag_high, p_high])

#         # 降低 flush 频率
#         self.counter += 1
#         if self.counter % self.log_every_n == 0:
#             self.csv_file.flush()
#             self.get_logger().info(
#                 f"P_high={p_high:.4f}, mag_high={mag_high:.4f}, "
#                 f"raw=[{wx:+.3f}, {wy:+.3f}, {wz:+.3f}], "
#                 f"high=[{fx:+.3f}, {fy:+.3f}, {fz:+.3f}]"
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import math
import time
from collections import deque

import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32


class ImuVibrationMonitor(Node):
    def __init__(self):
        super().__init__("vibration_monitor_node")

        # ===== 参数 =====
        self.topic_name = "/imu/raw"
        self.fs = 100.0
        self.rms_window_sec = 0.5

        # 打印频率：不要每帧都打，不然终端刷爆
        self.log_every_n = 20   # 100Hz 下约每 0.2 秒打印一次
        self.counter = 0

        # 输出目录
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        self.save_dir = os.path.join(current_dir, "imu_vibration_output")
        os.makedirs(self.save_dir, exist_ok=True)

        ts = time.strftime("%Y%m%d_%H%M%S")
        self.csv_path = os.path.join(self.save_dir, f"imu_raw_{ts}.csv")

        # ===== RMS 滑动窗口 =====
        self.rms_window_size = max(2, int(self.fs * self.rms_window_sec))
        self.mag_window = deque(maxlen=self.rms_window_size)

        self.start_time = time.time()

        # ===== ROS =====
        self.sub = self.create_subscription(
            Imu, self.topic_name, self.imu_callback, 10
        )

        self.pub_p_raw = self.create_publisher(Float32, "/imu/vibration/p_raw", 10)
        self.pub_mag_raw = self.create_publisher(Float32, "/imu/vibration/mag_raw", 10)

        # ===== CSV =====
        self.csv_file = open(self.csv_path, "w", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            "t",
            "wx", "wy", "wz",
            "mag_raw",
            "p_raw"
        ])
        self.csv_file.flush()

        self.get_logger().info(
            f"IMU原始数据采集节点已启动: topic={self.topic_name}, "
            f"fs={self.fs}Hz, RMS窗口={self.rms_window_sec}s"
        )
        self.get_logger().info(f"CSV保存路径: {self.csv_path}")

    def imu_callback(self, msg: Imu):
        # 原始陀螺仪角速度
        wx = msg.angular_velocity.x
        wy = msg.angular_velocity.y
        wz = msg.angular_velocity.z

        # 原始三轴合成幅值
        mag_raw = math.sqrt(wx * wx + wy * wy + wz * wz)

        # 滑窗 RMS（对原始幅值做）
        self.mag_window.append(mag_raw)
        arr = np.array(self.mag_window, dtype=np.float64)
        p_raw = float(np.sqrt(np.mean(arr ** 2))) if len(arr) > 0 else 0.0

        t = time.time() - self.start_time

        # 发布
        msg_p = Float32()
        msg_p.data = p_raw
        self.pub_p_raw.publish(msg_p)

        msg_m = Float32()
        msg_m.data = mag_raw
        self.pub_mag_raw.publish(msg_m)

        # 保存 CSV
        self.csv_writer.writerow([t, wx, wy, wz, mag_raw, p_raw])

        # 降低 flush 频率
        self.counter += 1
        if self.counter % self.log_every_n == 0:
            self.csv_file.flush()
            self.get_logger().info(
                f"p_raw={p_raw:.4f}, mag_raw={mag_raw:.4f}, "
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

        # 避免重复 shutdown
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()