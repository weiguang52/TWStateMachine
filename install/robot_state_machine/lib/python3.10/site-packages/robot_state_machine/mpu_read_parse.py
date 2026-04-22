#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROS2 节点：读取 MPU6050 原始数据并发布到 /imu/raw 话题。

话题
----
发布：/imu/raw  (sensor_msgs/msg/Imu)
  - header.stamp        : ROS2 时间戳
  - linear_acceleration : 加速度计 [m/s²]（已减去偏置）
  - angular_velocity    : 陀螺仪   [rad/s]（已减去偏置）
  - orientation         : 全零（姿态解算由 solver 节点负责）

注意
----
- 本节点只负责数据采集和单位换算，不做任何姿态估计
- MPU6050 原始量程：accel = g，gyro = dps；本节点统一换算为 SI 单位后发布
- 启动前请确认 I2C 总线号和设备地址

"""

import time
import math
import errno

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Header

from smbus2 import SMBus, i2c_msg

# ══════════════════════════════════════════════════════════════════════════════
# 硬件配置
# ══════════════════════════════════════════════════════════════════════════════

I2C_BUS  = 5
MPU_ADDR = 0x68   # AD0=GND → 0x68；AD0=VDD → 0x69

# MPU6050 寄存器
REG_SMPLRT_DIV   = 0x19
REG_CONFIG       = 0x1A
REG_GYRO_CONFIG  = 0x1B
REG_ACCEL_CONFIG = 0x1C
REG_ACCEL_XOUT_H = 0x3B
REG_GYRO_XOUT_H  = 0x43
REG_PWR_MGMT_1   = 0x6B
REG_WHO_AM_I     = 0x75

# 量程灵敏度
ACC_LSB_PER_G    = {0: 16384.0, 1: 8192.0, 2: 4096.0, 3: 2048.0}
GYR_LSB_PER_DPS  = {0: 131.0,   1: 65.5,   2: 32.8,   3: 16.4}

G_TO_MS2  = 9.80665          # 1g → m/s²
DPS_TO_RPS = math.pi / 180.0 # deg/s → rad/s


# ══════════════════════════════════════════════════════════════════════════════
# MPU6050 驱动（纯采集，无姿态解算）
# ══════════════════════════════════════════════════════════════════════════════

def _to_int16(msb: int, lsb: int) -> int:
    v = (msb << 8) | lsb
    return v - 65536 if v >= 32768 else v


class MPU6050:
    def __init__(
        self,
        bus: int = I2C_BUS,
        addr: int = MPU_ADDR,
        accel_fs: int = 0,       # 0=±2g
        gyro_fs: int = 0,        # 0=±250 dps
        dlpf_cfg: int = 2,       # DLPF 配置（2 较稳定）
        sample_rate_hz: int = 100,
    ):
        self.bus_id         = bus
        self.addr           = addr
        self.accel_fs       = accel_fs
        self.gyro_fs        = gyro_fs
        self.dlpf_cfg       = dlpf_cfg
        self.sample_rate_hz = sample_rate_hz

        self.bus = SMBus(self.bus_id)

        # 偏置（静止校准后填充）
        self.gyro_bias_dps  = [0.0, 0.0, 0.0]
        self.accel_bias_g   = [0.0, 0.0, 0.0]

    def close(self):
        self.bus.close()

    # ── 底层 I2C 读写（含重试）────────────────────────────────────────────────

    def _w8(self, reg: int, val: int, retry: int = 10, delay: float = 0.01):
        last_e = None
        for _ in range(retry):
            try:
                self.bus.write_byte_data(self.addr, reg, val & 0xFF)
                return
            except OSError as e:
                last_e = e
                if getattr(e, "errno", None) == errno.EREMOTEIO:
                    time.sleep(delay)
                    continue
                raise
        raise last_e

    def _r8(self, reg: int, retry: int = 10, delay: float = 0.01) -> int:
        last_e = None
        for _ in range(retry):
            try:
                return self.bus.read_byte_data(self.addr, reg) & 0xFF
            except OSError as e:
                last_e = e
                if getattr(e, "errno", None) == errno.EREMOTEIO:
                    time.sleep(delay)
                    continue
                raise
        raise last_e

    def _rblock(self, reg: int, n: int, retry: int = 10, delay: float = 0.003) -> list:
        last_e = None
        for k in range(retry):
            try:
                w = i2c_msg.write(self.addr, [reg & 0xFF])
                r = i2c_msg.read(self.addr, n)
                self.bus.i2c_rdwr(w, r)
                data = list(r)
                if all(x == 0x00 for x in data):
                    raise OSError(errno.EREMOTEIO, "all-zero read (transient)")
                return data
            except (OSError, TimeoutError) as e:
                last_e = e
                err = getattr(e, "errno", None)
                if err in (errno.EREMOTEIO, errno.ETIMEDOUT) or isinstance(e, TimeoutError):
                    time.sleep(delay)
                    if err == errno.ETIMEDOUT or isinstance(e, TimeoutError):
                        self._reopen_and_reinit()
                    continue
                raise
        raise last_e

    def _reopen_and_reinit(self):
        try:
            self.bus.close()
        except Exception:
            pass
        time.sleep(0.05)
        self.bus = SMBus(self.bus_id)
        self._w8(REG_PWR_MGMT_1, 0x01)
        time.sleep(0.05)
        self._w8(REG_CONFIG, self.dlpf_cfg & 0x07)
        gyro_rate = 8000 if self.dlpf_cfg == 0 else 1000
        div = max(0, min(255, int(round(gyro_rate / self.sample_rate_hz - 1))))
        self._w8(REG_SMPLRT_DIV, div)
        self._w8(REG_GYRO_CONFIG,  (self.gyro_fs  & 0x03) << 3)
        self._w8(REG_ACCEL_CONFIG, (self.accel_fs & 0x03) << 3)
        time.sleep(0.02)

    # ── 初始化 ────────────────────────────────────────────────────────────────

    def initialize(self):
        who = self._r8(REG_WHO_AM_I)
        if who not in (0x68, 0x69):
            raise RuntimeError(f"WHO_AM_I 异常: 0x{who:02X}，请检查 I2C 连接")

        self._w8(REG_PWR_MGMT_1, 0x01)   # 唤醒，使用 PLL 时钟
        time.sleep(0.10)
        self._w8(REG_CONFIG, self.dlpf_cfg & 0x07)
        time.sleep(0.02)

        gyro_rate = 8000 if self.dlpf_cfg == 0 else 1000
        div = max(0, min(255, int(round(gyro_rate / self.sample_rate_hz - 1))))
        self._w8(REG_SMPLRT_DIV, div)
        time.sleep(0.02)

        self._w8(REG_GYRO_CONFIG,  (self.gyro_fs  & 0x03) << 3)
        time.sleep(0.01)
        self._w8(REG_ACCEL_CONFIG, (self.accel_fs & 0x03) << 3)
        time.sleep(0.01)

    # ── 数据读取 ──────────────────────────────────────────────────────────────

    def read_raw(self) -> tuple:
        """返回原始 int16：(ax, ay, az, temp, gx, gy, gz)"""
        b1 = self._rblock(REG_ACCEL_XOUT_H, 8)   # accel(6) + temp(2)
        ax = _to_int16(b1[0], b1[1])
        ay = _to_int16(b1[2], b1[3])
        az = _to_int16(b1[4], b1[5])
        t  = _to_int16(b1[6], b1[7])

        b2 = self._rblock(REG_GYRO_XOUT_H, 6)    # gyro(6)
        gx = _to_int16(b2[0], b2[1])
        gy = _to_int16(b2[2], b2[3])
        gz = _to_int16(b2[4], b2[5])

        return ax, ay, az, t, gx, gy, gz

    def read_si(self) -> tuple:
        """
        返回 SI 单位数据：
          accel_ms2  : (ax, ay, az) [m/s²]，已减偏置
          gyro_rps   : (gx, gy, gz) [rad/s]，已减偏置
          temp_c     : 温度 [°C]
        """
        ax, ay, az, t, gx, gy, gz = self.read_raw()

        a_scale = ACC_LSB_PER_G[self.accel_fs]
        g_scale = GYR_LSB_PER_DPS[self.gyro_fs]

        ax_ms2 = (ax / a_scale - self.accel_bias_g[0]) * G_TO_MS2
        ay_ms2 = (ay / a_scale - self.accel_bias_g[1]) * G_TO_MS2
        az_ms2 = (az / a_scale - self.accel_bias_g[2]) * G_TO_MS2

        gx_rps = (gx / g_scale - self.gyro_bias_dps[0]) * DPS_TO_RPS
        gy_rps = (gy / g_scale - self.gyro_bias_dps[1]) * DPS_TO_RPS
        gz_rps = (gz / g_scale - self.gyro_bias_dps[2]) * DPS_TO_RPS

        temp_c = t / 340.0 + 36.53

        return (ax_ms2, ay_ms2, az_ms2), (gx_rps, gy_rps, gz_rps), temp_c

    # ── 静止校准 ──────────────────────────────────────────────────────────────

    def calibrate_stationary(self, seconds: float = 2.0, logger=None):
        """
        静止状态下采集均值作为偏置。
        请确保校准期间机器人完全静止。
        accel 偏置在 g 域做，以便后续 read_si() 中直接相减再换算。
        """
        n = max(20, int(seconds * self.sample_rate_hz))
        dt = 1.0 / self.sample_rate_hz

        # 临时清零
        self.gyro_bias_dps = [0.0, 0.0, 0.0]
        self.accel_bias_g  = [0.0, 0.0, 0.0]

        a_scale = ACC_LSB_PER_G[self.accel_fs]
        g_scale = GYR_LSB_PER_DPS[self.gyro_fs]

        sum_ax = sum_ay = sum_az = 0.0
        sum_gx = sum_gy = sum_gz = 0.0

        for _ in range(n):
            ax, ay, az, _, gx, gy, gz = self.read_raw()
            sum_ax += ax / a_scale
            sum_ay += ay / a_scale
            sum_az += az / a_scale
            sum_gx += gx / g_scale
            sum_gy += gy / g_scale
            sum_gz += gz / g_scale
            time.sleep(dt)

        # accel 偏置：x/y 均值直接作为偏置，z 轴减去 1g（重力方向）
        self.accel_bias_g  = [sum_ax/n, sum_ay/n, sum_az/n - 1.0]
        self.gyro_bias_dps = [sum_gx/n, sum_gy/n, sum_gz/n]

        if logger:
            logger.info(
                f"校准完成 | gyro_bias(dps)={[f'{v:.4f}' for v in self.gyro_bias_dps]} "
                f"| accel_bias(g)={[f'{v:.4f}' for v in self.accel_bias_g]}"
            )


# ══════════════════════════════════════════════════════════════════════════════
# ROS2 发布节点
# ══════════════════════════════════════════════════════════════════════════════

class ImuPublisherNode(Node):
    """
    ROS2 节点：MPU6050 → /imu/raw

    参数（ros2 param）
    -----------------
    i2c_bus        : int   I2C 总线号（默认 5）
    imu_addr       : int   I2C 地址（默认 0x68）
    accel_fs       : int   加速度量程选择 0~3（默认 0 = ±2g）
    gyro_fs        : int   陀螺量程选择 0~3（默认 0 = ±250dps）
    dlpf_cfg       : int   DLPF 配置 0~6（默认 2）
    sample_rate_hz : int   采样率（默认 100Hz）
    calib_seconds  : float 静止校准时长（默认 2.0s，设为 0 跳过）
    frame_id       : str   header.frame_id（默认 "imu_link"）
    """

    def __init__(self):
        super().__init__("mpu_imu_publisher")

        # ── 声明 ROS2 参数 ────────────────────────────────────────
        self.declare_parameter("i2c_bus",        I2C_BUS)
        self.declare_parameter("imu_addr",       MPU_ADDR)
        self.declare_parameter("accel_fs",       0)
        self.declare_parameter("gyro_fs",        0)
        self.declare_parameter("dlpf_cfg",       2)
        self.declare_parameter("sample_rate_hz", 100)           # 采样频率
        self.declare_parameter("calib_seconds",  4.0)           # 静止校准时间
        self.declare_parameter("frame_id",       "imu_link")

        bus        = self.get_parameter("i2c_bus").value
        addr       = self.get_parameter("imu_addr").value
        accel_fs   = self.get_parameter("accel_fs").value
        gyro_fs    = self.get_parameter("gyro_fs").value
        dlpf_cfg   = self.get_parameter("dlpf_cfg").value
        hz         = self.get_parameter("sample_rate_hz").value
        calib_sec  = self.get_parameter("calib_seconds").value
        self._frame_id = self.get_parameter("frame_id").value

        # ── 初始化硬件 ────────────────────────────────────────────
        self.get_logger().info(f"初始化 MPU6050 @ I2C-{bus} 0x{addr:02X} ...")
        self._mpu = MPU6050(
            bus=bus, addr=addr,
            accel_fs=accel_fs, gyro_fs=gyro_fs,
            dlpf_cfg=dlpf_cfg, sample_rate_hz=hz,
        )
        self._mpu.initialize()
        self.get_logger().info("MPU6050 初始化完成")

        # ── 静止校准 ──────────────────────────────────────────────
        if calib_sec > 0:
            self.get_logger().info(f"静止校准 {calib_sec:.1f}s，请保持机器人静止...")
            self._mpu.calibrate_stationary(
                seconds=calib_sec,
                logger=self.get_logger(),
            )
        else:
            self.get_logger().warn("跳过校准（calib_seconds=0），偏置默认为零")

        # ── ROS2 发布者 ───────────────────────────────────────────
        self._pub = self.create_publisher(Imu, "/imu/raw", 10)

        # ── 定时器：按采样率驱动发布 ──────────────────────────────
        self._timer = self.create_timer(1.0 / hz, self._timer_cb)
        self.get_logger().info(f"开始发布 /imu/raw @ {hz}Hz")

    def _timer_cb(self):
        try:
            accel, gyro, temp = self._mpu.read_si()
        except Exception as e:
            self.get_logger().warn(f"IMU 读取失败: {e}", throttle_duration_sec=1.0)
            return

        msg = Imu()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id

        # 加速度 [m/s²]
        msg.linear_acceleration.x = accel[0]
        msg.linear_acceleration.y = accel[1]
        msg.linear_acceleration.z = accel[2]

        # 角速度 [rad/s]
        msg.angular_velocity.x = gyro[0]
        msg.angular_velocity.y = gyro[1]
        msg.angular_velocity.z = gyro[2]

        # 姿态由 solver 节点解算，此处填零（协方差 -1 表示未知）
        msg.orientation_covariance[0] = -1.0

        # 协方差对角元素（简单估计，可根据实际噪声标定后填写）
        # accel 噪声 ≈ 0.01 m/s²，gyro 噪声 ≈ 0.001 rad/s
        for i in (0, 4, 8):
            msg.linear_acceleration_covariance[i]  = 1e-4
            msg.angular_velocity_covariance[i]     = 1e-6

        self._pub.publish(msg)

    def destroy_node(self):
        self._mpu.close()
        super().destroy_node()


# ══════════════════════════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════════════════════════

def main(args=None):
    rclpy.init(args=args)
    node = ImuPublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()