import serial
import time

# ====== 配置区 ======
#选择对应的串口
PORT = '/dev/ttyUSB0'          # Windows: COM3, COM4...  Linux/macOS: /dev/ttyUSB0, /dev/ttyACM0
BAUDRATE = 115200      # 必须和 STM32 一致
SEND_BYTES = bytes([0x59,0x45,0x63,0x8d,0x0e,0xFF])#在这里编辑发送的数据
TIMEOUT_SEC = 0.1      # 接收超时（100ms 足够）
# ===================


def hex_str(data):
    return ' '.join(f'{b:02X}' for b in data)

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT_SEC)
    print(f"[INFO] Opened {PORT} at {BAUDRATE} baud")

    # 清空可能的残留数据
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # 记录发送时刻
    t_send_start = time.perf_counter()
    ser.write(SEND_BYTES)
    ser.flush()  # 确保数据全部送出（虽然对 USB 虚拟串口影响小）
    t_send_done = time.perf_counter()

    print(f"[SENT] {hex_str(SEND_BYTES)}")
    print(f"[INFO] Send took {(t_send_done - t_send_start)*1000:.2f} ms")

    # 等待回复（最多 TIMEOUT_SEC 秒）
    t_wait_start = time.perf_counter()
    while True:
        if ser.in_waiting > 0:
            break
        if time.perf_counter() - t_wait_start > TIMEOUT_SEC:
            print("[ERROR] Timeout! No response received.")
            ser.close()
            exit(1)

    # 读取所有可用数据（假设一次回完）
    response = ser.read(ser.in_waiting) or ser.read(len(SEND_BYTES))
    t_recv = time.perf_counter()
    delay_ms = (t_recv - t_send_done) * 1000
    print(f"[RECV] {hex_str(response)}")
    print(f"[INFO] Response delay: {delay_ms:.2f} ms")

    ser.close()

except serial.SerialException as e:
    print(f"[ERROR] Serial error: {e}")
except KeyboardInterrupt:
    print("\n[INFO] Aborted by user")
