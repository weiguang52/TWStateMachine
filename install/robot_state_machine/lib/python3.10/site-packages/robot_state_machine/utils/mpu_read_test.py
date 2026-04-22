#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import math
from smbus2 import SMBus, i2c_msg
import errno

# ====== 基本配置（按你现在已验证通过的）======
I2C_BUS = 5
MPU_ADDR = 0x68  # AD0=GND/悬空一般是0x68；若AD0=VDD则0x69

# ====== 寄存器（MPU6050 常用寄存器映射）======
REG_SMPLRT_DIV   = 0x19
REG_CONFIG       = 0x1A
REG_GYRO_CONFIG  = 0x1B
REG_ACCEL_CONFIG = 0x1C
REG_INT_ENABLE   = 0x38
REG_INT_STATUS   = 0x3A

REG_ACCEL_XOUT_H = 0x3B  # 从这里开始 burst 读 14 字节：acc(6)+temp(2)+gyro(6)
REG_PWR_MGMT_1   = 0x6B
REG_WHO_AM_I     = 0x75

# ====== 量程对应的灵敏度（LSB per unit）======
# accel AFS_SEL: 0=±2g,1=±4g,2=±8g,3=±16g
ACC_LSB_PER_G = {0: 16384.0, 1: 8192.0, 2: 4096.0, 3: 2048.0}
# gyro FS_SEL: 0=±250,1=±500,2=±1000,3=±2000 (deg/s)
GYR_LSB_PER_DPS = {0: 131.0, 1: 65.5, 2: 32.8, 3: 16.4}


def to_int16(msb: int, lsb: int) -> int:
    """两个字节转 int16（补码）"""
    v = (msb << 8) | lsb
    return v - 65536 if v >= 32768 else v


class MPU6050:
    def __init__(self,
                 bus: int = I2C_BUS,
                 addr: int = MPU_ADDR,
                 accel_fs: int = 0,      # 0=±2g
                 gyro_fs: int = 0,       # 0=±250 dps
                 dlpf_cfg: int = 2,      # 0~6 常用，2一般比较稳
                 sample_rate_hz: int = 100):
        self.bus_id = bus
        self.addr = addr
        self.accel_fs = accel_fs
        self.gyro_fs = gyro_fs
        self.dlpf_cfg = dlpf_cfg
        self.sample_rate_hz = sample_rate_hz

        self.bus = SMBus(self.bus_id)

        # 偏置（可校准）
        self.gyro_bias_dps = [0.0, 0.0, 0.0]
        self.accel_bias_g = [0.0, 0.0, 0.0]

        # 姿态估计状态
        self.pitch = 0.0
        self.roll = 0.0
        self._last_t = None

    def close(self):
        self.bus.close()

    def w8(self, reg: int, val: int, retry: int = 10, delay: float = 0.01):
        last_e = None
        for _ in range(retry):
            try:
                self.bus.write_byte_data(self.addr, reg, val & 0xFF)
                return
            except OSError as e:
                last_e = e
                # 对 Errno 121 做重试（NACK/Remote I/O）
                if getattr(e, "errno", None) == errno.EREMOTEIO:
                    time.sleep(delay)
                    continue
                raise
        raise last_e

    def r8(self, reg: int, retry: int = 10, delay: float = 0.01) -> int:
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

    def _reopen_bus_and_reinit(self):
        try:
            self.bus.close()
        except Exception:
            pass
        time.sleep(0.05)
        self.bus = SMBus(self.bus_id)
        # 重新初始化最小集合：唤醒 + 基本寄存器
        self.w8(REG_PWR_MGMT_1, 0x01)      # PLL clock, sleep=0
        time.sleep(0.05)
        self.w8(REG_CONFIG, self.dlpf_cfg & 0x07)
        gyro_rate = 8000 if self.dlpf_cfg == 0 else 1000
        div = int(round(gyro_rate / self.sample_rate_hz - 1))
        div = max(0, min(255, div))
        self.w8(REG_SMPLRT_DIV, div)
        self.w8(REG_GYRO_CONFIG, (self.gyro_fs & 0x03) << 3)
        self.w8(REG_ACCEL_CONFIG, (self.accel_fs & 0x03) << 3)
        time.sleep(0.02)

    def rblock(self, reg: int, n: int, retry: int = 10, delay: float = 0.003) -> list[int]:
        last_e = None
        for k in range(retry):
            try:
                w = i2c_msg.write(self.addr, [reg & 0xFF])
                r = i2c_msg.read(self.addr, n)
                self.bus.i2c_rdwr(w, r)
                data = list(r)

                # 简单 sanity check：避免全 0 数据进入滤波（可选）
                if all(x == 0x00 for x in data):
                    raise OSError(errno.EREMOTEIO, "all-zero read (treat as transient)")

                return data

            except (OSError, TimeoutError) as e:
                last_e = e
                err = getattr(e, "errno", None)

                # 121: Remote I/O / NACK
                # 110: timed out
                if err in (errno.EREMOTEIO, errno.ETIMEDOUT) or isinstance(e, TimeoutError):
                    time.sleep(delay)

                    # 对超时，做一次“重开总线+重初始化”
                    if err == errno.ETIMEDOUT or isinstance(e, TimeoutError):
                        self._reopen_bus_and_reinit()

                    continue

                raise
        raise last_e

    def initialize(self):
        # 先读 WHO_AM_I，确认设备在应答
        who = self.r8(REG_WHO_AM_I)
        if who not in (0x68, 0x69):
            raise RuntimeError(f"Unexpected WHO_AM_I: 0x{who:02X}")

        # 用 PLL 时钟更稳（很多板子 0x01 比 0x00 更可靠）
        # bit6 SLEEP=0，CLKSEL=1
        self.w8(REG_PWR_MGMT_1, 0x01)
        time.sleep(0.10)

        # DLPF
        self.w8(REG_CONFIG, self.dlpf_cfg & 0x07)
        time.sleep(0.02)

        # SampleRate = GyroRate/(1+DIV)
        gyro_rate = 8000 if self.dlpf_cfg == 0 else 1000
        div = int(round(gyro_rate / self.sample_rate_hz - 1))
        div = max(0, min(255, div))
        self.w8(REG_SMPLRT_DIV, div)
        time.sleep(0.02)

        # 量程
        self.w8(REG_GYRO_CONFIG, (self.gyro_fs & 0x03) << 3)
        time.sleep(0.01)
        self.w8(REG_ACCEL_CONFIG, (self.accel_fs & 0x03) << 3)
        time.sleep(0.01)

        self._last_t = time.time()

    def read_raw(self):
        # 读 accel(6) + temp(2)
        b1 = self.rblock(REG_ACCEL_XOUT_H, 8)  # 0x3B..0x42
        ax = to_int16(b1[0], b1[1])
        ay = to_int16(b1[2], b1[3])
        az = to_int16(b1[4], b1[5])
        t  = to_int16(b1[6], b1[7])

        # 读 gyro(6)
        b2 = self.rblock(0x43, 6)  # GYRO_XOUT_H..ZOUT_L
        gx = to_int16(b2[0], b2[1])
        gy = to_int16(b2[2], b2[3])
        gz = to_int16(b2[4], b2[5])

        return ax, ay, az, t, gx, gy, gz

    def read_scaled(self):
        """返回：acc(g), gyro(dps), temp(C)"""
        ax, ay, az, t, gx, gy, gz = self.read_raw()

        a_scale = ACC_LSB_PER_G[self.accel_fs]
        g_scale = GYR_LSB_PER_DPS[self.gyro_fs]

        ax_g = ax / a_scale - self.accel_bias_g[0]
        ay_g = ay / a_scale - self.accel_bias_g[1]
        az_g = az / a_scale - self.accel_bias_g[2]

        gx_dps = gx / g_scale - self.gyro_bias_dps[0]
        gy_dps = gy / g_scale - self.gyro_bias_dps[1]
        gz_dps = gz / g_scale - self.gyro_bias_dps[2]

        temp_c = t / 340.0 + 36.53
        return (ax_g, ay_g, az_g), (gx_dps, gy_dps, gz_dps), temp_c

    def calibrate_stationary(self, seconds: float = 2.0, hz: int = 100):
        """静止校准：估计 gyro 零偏 + accel 均值偏置（简单版）"""
        n = max(20, int(seconds * hz))
        dt = 1.0 / hz

        sum_ax = sum_ay = sum_az = 0.0
        sum_gx = sum_gy = sum_gz = 0.0

        # 临时清零偏置再采样
        self.gyro_bias_dps = [0.0, 0.0, 0.0]
        self.accel_bias_g = [0.0, 0.0, 0.0]

        for _ in range(n):
            (ax, ay, az), (gx, gy, gz), _ = self.read_scaled()
            sum_ax += ax; sum_ay += ay; sum_az += az
            sum_gx += gx; sum_gy += gy; sum_gz += gz
            time.sleep(dt)

        self.accel_bias_g = [sum_ax/n, sum_ay/n, sum_az/n]
        self.gyro_bias_dps = [sum_gx/n, sum_gy/n, sum_gz/n]

    def update_orientation(self, alpha: float = 0.98):
        """
        简单互补滤波：用 gyro 积分 + accel 修正，输出 pitch/roll（度）
        注意：yaw 仅靠 MPU6050 的 gyro 会漂移（无磁力计），这里只做 pitch/roll。
        """
        now = time.time()
        dt = max(1e-4, now - (self._last_t or now))
        self._last_t = now

        (ax, ay, az), (gx, gy, gz), temp = self.read_scaled()

        # accel 估计角度（度）
        # roll: 绕X轴？这里按常见定义：roll=atan2(ay,az), pitch=atan2(-ax, sqrt(ay^2+az^2))
        roll_acc = math.degrees(math.atan2(ay, az))
        pitch_acc = math.degrees(math.atan2(-ax, math.sqrt(ay*ay + az*az)))

        # gyro 积分（deg/s -> deg）
        self.roll += gx * dt
        self.pitch += gy * dt

        # 互补融合
        self.roll = alpha * self.roll + (1 - alpha) * roll_acc
        self.pitch = alpha * self.pitch + (1 - alpha) * pitch_acc

        return {
            "acc_g": (ax, ay, az),
            "gyro_dps": (gx, gy, gz),
            "temp_c": temp,
            "roll_deg": self.roll,
            "pitch_deg": self.pitch,
            # yaw_deg 不输出：无磁力计会漂移
        }


def main():
    imu = MPU6050(bus=I2C_BUS, addr=MPU_ADDR, accel_fs=0, gyro_fs=0, dlpf_cfg=2, sample_rate_hz=100)
    try:
        imu.initialize()
        print("MPU6050 init OK. Calibrating 2s (keep still)...")
        imu.calibrate_stationary(seconds=2.0, hz=200)
        print(f"gyro_bias(dps)={imu.gyro_bias_dps}, accel_bias(g)={imu.accel_bias_g}")

        while True:
            out = imu.update_orientation(alpha=0.98)
            ax, ay, az = out["acc_g"]
            gx, gy, gz = out["gyro_dps"]
            print(
                f"T={out['temp_c']:.2f}C | "
                f"acc[g]=({ax:+.3f},{ay:+.3f},{az:+.3f}) | "
                f"gyro[dps]=({gx:+.2f},{gy:+.2f},{gz:+.2f}) | "
                f"roll={out['roll_deg']:+.2f}°, pitch={out['pitch_deg']:+.2f}°"
            )
            time.sleep(0.01)  # 打印频率可自行调
    finally:
        imu.close()


if __name__ == "__main__":
    main()