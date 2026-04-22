#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
端侧测试一体化脚本：
  npy -> IK -> 插值(100Hz) -> 串口下发电机

支持两种读取方式：
  1) 在线：监控 /tmp/robot_action.npy，文件更新就追加帧
  2) 离线：直接加载一个 npy 文件作为 motion 序列

下发方式：
  - 直接用 admittance_calculate.py 里的 RobotController 下发
  - 复用 AdmittanceControlNode.joint_angles_to_board_mapping 做“关节->板/电机”映射

注意：
  - IK/插值相关依赖 robot_state_machine.utils.*，运行环境需和 main_node_offline_npy.py 一致
"""

import os
import time
import argparse
import threading
from queue import Queue, Empty

import numpy as np

# ====== 复用：在线 npy loader（来自 online_npy_test.py）=====
from online_npy_test import OnlineNPYLoader  # :contentReference[oaicite:3]{index=3}

# ====== 复用：IK + 插值（来自 main_node_offline_npy.py 引用的同一套工具链）=====
from robot_state_machine.utils.IK_Redirection.ik_redirection_new import H1PinkSolver
from robot_state_machine.utils.cubic_spline import JointTrajectoryInterpolator

# ====== 复用：电机串口协议 & 板映射（来自 admittance_calculate.py）=====
from utils.admittance_calculate import AdmittanceControlNode
from utils.robot_protocol import RobotController, SerialConfig


class EdgeSideTester:
    """
    端侧测试主类（不强依赖 ROS2，便于直接 python 运行）
    """

    def __init__(
        self,
        urdf_path: str,
        mode: str,
        npy_path: str,
        offline_npy: str,
        cut_frame_num: int,
        planning_freq: float,
        send_freq: float,
        serial_port: str,
        baudrate: int,
        only_legs: bool,
        dry_run: bool,
        verbose: bool,
    ):
        self.urdf_path = urdf_path
        self.mode = mode
        self.npy_path = npy_path
        self.offline_npy = offline_npy
        self.cut_frame_num = cut_frame_num
        self.planning_freq = planning_freq
        self.send_freq = send_freq
        self.only_legs = only_legs
        self.dry_run = dry_run
        self.verbose = verbose

        # Debug: 上一帧板1/2的角度（用于看是否在变化）
        self._prev_board_ab = {}   # {board_id: (a01, b01)}
        self._dbg_every_n = 10     # 每N帧打印一次（避免刷屏）

        self.dbg_npy_nodes = [19, 21]   # 右臂两个节点的索引(0~21) 你后面再改
        self.dbg_print_every_batch = 1  # 每个batch都打印，嫌吵就改大一点
        self._dbg_batch_idx = 0



        # ========== IK ==========
        self.ik_solver = H1PinkSolver(self.urdf_path)

        # ========== 插值器 ==========
        self.joint_names = [f"joint_{i}" for i in range(28)]
        self.trajectory_interpolator = JointTrajectoryInterpolator(
            joint_names=self.joint_names,
            planning_freq=self.planning_freq,
            admittance_freq=self.send_freq,
        )

        # ========== 复用板号映射函数（不触发 ROS Node 初始化） ==========
        # 直接借用 AdmittanceControlNode.joint_angles_to_board_mapping(self, ...)
        self._map_helper = AdmittanceControlNode.__new__(AdmittanceControlNode)

        # ========== 串口 ==========
        self.robot = None
        if not self.dry_run:
            cfg = SerialConfig(
                port=serial_port,
                baudrate=baudrate,
                timeout=1.0,
                write_timeout=1.0,
            )
            self.robot = RobotController(cfg)
            self.robot.response_timeout = 1.0
            # self.robot.command_interval = 1.0 / self.send_freq
            self.robot.command_interval = 0.0
            self.robot.retry_count = 1
            if not self.robot.open_serial():
                raise RuntimeError(f"串口打开失败：{serial_port} @ {baudrate}")

        # ========== 数据通道 ==========
        self.running = True
        self.q_raw_motion = Queue(maxsize=50)     # npy帧批次 (T,J,C)
        self.q_send_frames = Queue(maxsize=500)   # 已插值后的 28DOF 角度帧（deg）

        # ========== 在线 loader ==========
        self.loader = None
        if self.mode == "online":
            self.loader = OnlineNPYLoader(
                npy_path=self.npy_path,
                logger=self._log,
                poll_interval=0.05,
                stable_wait=0.05,
                allow_pickle=True,
                max_keep_frames=5000,
            )
            self.loader.start()

        # ========== 线程 ==========
        self.th_load = threading.Thread(target=self._thread_load_loop, daemon=True)
        self.th_proc = threading.Thread(target=self._thread_process_loop, daemon=True)
        self.th_send = threading.Thread(target=self._thread_send_loop, daemon=True)

        self.stats = {
            "raw_frames_in": 0,
            "ik_batches": 0,
            "interp_frames_out": 0,
            "sent_frames": 0,
            "start_time": time.time(),
        }

    # ----------------- 日志 -----------------
    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def _dbg_print_npy_nodes(self, motion_batch: np.ndarray):
        """
        motion_batch: (T, J, C) 其中 J=22, C=3
        打印两个节点 xyz 在该 batch 内的变化情况
        """
        if motion_batch is None:
            return
        if not hasattr(self, "dbg_npy_nodes") or not self.dbg_npy_nodes:
            return

        if motion_batch.ndim != 3:
            print(f"[DBG][NPY] unexpected shape={motion_batch.shape}")
            return

        T, J, C = motion_batch.shape
        if C < 3:
            print(f"[DBG][NPY] C={C}<3, cannot read xyz")
            return

        self._dbg_batch_idx = getattr(self, "_dbg_batch_idx", 0) + 1
        if self._dbg_batch_idx % getattr(self, "dbg_print_every_batch", 1) != 0:
            return

        for node_id in self.dbg_npy_nodes:
            if node_id < 0 or node_id >= J:
                print(f"[DBG][NPY] node_id={node_id} out of range (J={J})")
                continue

            p = motion_batch[:, node_id, 0:3].astype(np.float64)  # (T,3)
            p0 = p[0]
            p1 = p[-1]
            dp = p1 - p0
            dist = float(np.linalg.norm(dp))

            # 每帧步进位移统计
            if T >= 2:
                step = p[1:] - p[:-1]
                step_norm = np.linalg.norm(step, axis=1)
                avg_step = float(step_norm.mean())
                max_step = float(step_norm.max())
            else:
                avg_step = 0.0
                max_step = 0.0

            print(
                f"[DBG][NPY][node{node_id}] "
                f"p0=({p0[0]:+.4f},{p0[1]:+.4f},{p0[2]:+.4f}) "
                f"p1=({p1[0]:+.4f},{p1[1]:+.4f},{p1[2]:+.4f}) "
                f"Δ=({dp[0]:+.4f},{dp[1]:+.4f},{dp[2]:+.4f}) "
                f"|Δ|={dist:.5f} avg_step={avg_step:.5f} max_step={max_step:.5f} "
                f"T={T}"
            )

    # ----------------- 启动/停止 -----------------
    def start(self):
        self.th_load.start()
        self.th_proc.start()
        self.th_send.start()

        print(
            "\n[EdgeSideTester] started\n"
            f"  mode={self.mode}\n"
            f"  send_freq={self.send_freq}Hz, planning_freq={self.planning_freq}Hz\n"
            f"  only_legs={self.only_legs}, dry_run={self.dry_run}\n"
        )

    def stop(self):
        self.running = False
        try:
            if self.loader:
                self.loader.stop()
        except Exception:
            pass
        try:
            if self.robot:
                self.robot.close_serial()
        except Exception:
            pass

    # ----------------- 线程1：读取 npy -> raw motion 批次 -----------------
    def _thread_load_loop(self):
        if self.mode == "offline":
            # 离线：一次性加载整段 motion，并按 cut_frame_num 分批塞进队列
            if not os.path.exists(self.offline_npy):
                raise FileNotFoundError(self.offline_npy)

            data = np.load(open(self.offline_npy, "rb"), allow_pickle=True)
            # 与 main_node_offline_npy.py 的 OfflineNPYLoader 约定一致：data 是 (T, J, C) motion 序列 :contentReference[oaicite:4]{index=4}
            motion = data
            T = len(motion)
            idx = 0
            while self.running and idx < T:
                batch = motion[idx : idx + self.cut_frame_num]
                idx += self.cut_frame_num
                self._put_raw_batch(batch)
                time.sleep(0.01)
            return

        # 在线：持续 pop_frames
        while self.running:
            try:
                frames = self.loader.pop_frames(self.cut_frame_num)
                if frames is None:
                    time.sleep(0.02)
                    continue
                self._put_raw_batch(frames)
            except Exception as e:
                print(f"[LoadThread] error: {e}")
                time.sleep(0.1)

    def _put_raw_batch(self, batch_frames: np.ndarray):
        # batch_frames: (T,J,C)
        try:
            self.q_raw_motion.put(batch_frames, timeout=0.2)
            self.stats["raw_frames_in"] += len(batch_frames)
            self._log(f"[LoadThread] queued raw batch: {batch_frames.shape}, q_raw={self.q_raw_motion.qsize()}")
        except Exception:
            time.sleep(0.02)

    # ----------------- 线程2：IK + 插值 -> 100Hz 关节角帧 -----------------
    def _thread_process_loop(self):
        while self.running:
            try:
                try:
                    motion_batch = self.q_raw_motion.get(timeout=0.2)
                except Empty:
                    continue

                # ✅ 先看 npy 本身右臂节点有没有动
                self._dbg_print_npy_nodes(motion_batch)
                # 1) IK（复用 main_node_offline_npy.py 同款接口：H1PinkSolver.process_motion(motion)）:contentReference[oaicite:5]{index=5}
                ik_res = self.ik_solver.process_motion(motion_batch)

                # # =========== 导出逆解后的 txt 文件，用于可视化验证逆解正确性===============
                out_dir = "/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/output"
                
                joint_txt_path = os.path.join(out_dir, "robot_joint_cmd_frames.txt")
                dof_real = ik_res.get("dof_real", None)
                os.makedirs(out_dir, exist_ok=True)
                # 1) 保存完整结果
                print(f"Saved to {out_dir}")

                # TXT：每帧一行，便于日志查看
                with open(joint_txt_path, "w") as f:
                    for i in range(dof_real.shape[0]):
                        f.write(f"frame {i:06d}: " + " ".join([f"{v:.3f}" for v in dof_real[i]]) + "\n")
                print(f"Saved joint cmd frames (txt) to {joint_txt_path}")

                # # ====================================

                dof_real = ik_res["dof_real"]  # (T,28)，单位：deg
                self.stats["ik_batches"] += 1

                # 2) 三次样条插值到 send_freq（复用 JointTrajectoryInterpolator 用法）:contentReference[oaicite:6]{index=6}
                joint_trajectory = {}
                for i, jn in enumerate(self.joint_names):
                    joint_trajectory[jn] = (dof_real[:, i] * np.pi / 180.0).tolist()

                self.trajectory_interpolator.load_planning_trajectory(joint_trajectory)
                ts, traj = self.trajectory_interpolator.get_full_interpolated_trajectory()
                num_out = len(ts)

                # 3) 输出帧：每帧 28 个角度（deg）
                for k in range(num_out):
                    angles_rad = np.array([traj[jn][k] for jn in self.joint_names], dtype=np.float64)
                    angles_deg = angles_rad * 180.0 / np.pi
                    try:
                        self.q_send_frames.put(angles_deg, timeout=0.2)
                        self.stats["interp_frames_out"] += 1
                    except Exception:
                        break

                self._log(f"[ProcThread] IK+interp done: in={len(motion_batch)} -> out={num_out}, q_send={self.q_send_frames.qsize()}")

            except Exception as e:
                print(f"[ProcThread] error: {e}")
                time.sleep(0.1)

    # ----------------- 线程3：100Hz 下发电机 -----------------
    def _thread_send_loop(self):
        target_period = 1.0 / float(self.send_freq)
        last_print = time.time()

        while self.running:
            t0 = time.time()
            try:
                try:
                    angles_deg = self.q_send_frames.get(timeout=0.2)
                except Empty:
                    continue

                # 复用 admittance_calculate.py 的映射：joint_angles_to_board_mapping(angles, only_legs) :contentReference[oaicite:7]{index=7}
                board_map = AdmittanceControlNode.joint_angles_to_board_mapping(
                    self._map_helper, angles_deg, self.only_legs
                )

                # ===== DEBUG: 在 IK 结果后叠加一个随时间变化的偏置（每 20 帧 +5°，也就是每秒 +5°）=====
                # sent_frames 是 100Hz 的发送计数，因此每 100 帧=1秒；你要的是“插值前每 20 帧+5°”，
                # 但在你当前结构里最稳定的做法是：按“每 100 帧 +5°”实现“每秒 +5°”
                # 如果你坚持“每 20 帧 +5°”，把 100 改成 20 即可（会变成每 0.2秒 +5°）
                # ===== DEBUG: 每秒 +5°（用真实时间，不受串口阻塞影响）=====
                if not hasattr(self, "_off_t0"):
                    self._off_t0 = time.time()

                elapsed_s = time.time() - self._off_t0
                offset_deg = 5.0 * elapsed_s   # 线性：5 deg / sec
                # offset_deg = 5.0 * int(elapsed_s)  # 阶梯：每秒跳 +5°

                def _wrap360(x: float) -> float:
                    return float((x % 360.0 + 360.0) % 360.0)

                # 先只动板1的 A01
                if 1 in board_map:
                    a01, b01 = board_map[1]
                    board_map[1] = (_wrap360(float(a01) + offset_deg), float(b01))

                if (self.stats["sent_frames"] % self._dbg_every_n) == 0:
                    print(f"[DBG][OFF] sent_frames={self.stats['sent_frames']} offset_deg={offset_deg:+.2f}")
                # ===== DEBUG END =====


                # ===== Debug: 输出板1/2对应电机的 IK(实际是IK+插值后的关节角 -> 映射到板)结果 =====
                for bid in (1, 2):
                    if bid not in board_map:
                        continue
                    a01, b01 = board_map[bid]

                    prev = self._prev_board_ab.get(bid, None)
                    if prev is None:
                        da, db = 0.0, 0.0
                    else:
                        da, db = float(a01 - prev[0]), float(b01 - prev[1])

                    # 控制打印频率，避免100Hz刷屏
                    if (self.stats["sent_frames"] % self._dbg_every_n) == 0:
                        print(
                            f"[DBG][board{bid}] A01={float(a01):8.3f} deg  B01={float(b01):8.3f} deg"
                            f" | dA={da:+7.3f} dB={db:+7.3f}"
                        )

                    self._prev_board_ab[bid] = (float(a01), float(b01))
                # ===== Debug end =====

                if self.dry_run:
                    # 只打印不下发
                    pass
                else:
                    # 下发每块板两个电机
                    for board_id, (a01, b01) in board_map.items():
                        _ = self.robot.send_single_motor_angles(
                            board_id,
                            float(a01),
                            float(b01),
                            retry=False,
                        )

                self.stats["sent_frames"] += 1

                # 低频状态打印
                if time.time() - last_print > 2.0:
                    elapsed = time.time() - self.stats["start_time"]
                    hz = self.stats["sent_frames"] / max(elapsed, 1e-6)
                    print(
                        f"[SendThread] sent={self.stats['sent_frames']} "
                        f"hz={hz:.1f} "
                        f"q_send={self.q_send_frames.qsize()} "
                        f"raw_in={self.stats['raw_frames_in']} "
                        f"ik_batches={self.stats['ik_batches']}"
                    )
                    last_print = time.time()

                # 控频
                dt = time.time() - t0
                st = target_period - dt
                if st > 0:
                    time.sleep(st)

            except Exception as e:
                print(f"[SendThread] error: {e}")
                time.sleep(0.1)

    # ----------------- 线程3：100Hz 下发电机 -----------------
    '''
    def _thread_send_loop(self):
        import contextlib  # 放这里避免你忘了在文件头加
        import sys

        @contextlib.contextmanager
        def _silence_print(enabled: bool):
            """enabled=True 时吞掉 stdout/stderr（用于屏蔽 RobotController 内部 print 刷屏）"""
            if not enabled:
                yield
                return
            with open(os.devnull, "w") as fnull:
                with contextlib.redirect_stdout(fnull), contextlib.redirect_stderr(fnull):
                    yield

        def _wrap_0_360(a: float) -> float:
            """把角度归一化到 [0, 360) ，避免 RobotController 参数检查报负数"""
            return float(a % 360.0)

        target_period = 1.0 / float(self.send_freq)
        last_print = time.time()

        # 只发送前四块板：0~3（你要 0~4 就把 4 加进去）
        allowed_boards = (0, 1, 2, 3)

        # 更稳的“绝对时间”控频，避免偶发卡顿后一直追不上
        next_t = time.time()

        while self.running:
            try:
                try:
                    angles_deg = self.q_send_frames.get(timeout=0.2)
                except Empty:
                    # 队列空：不发送，等待下一批
                    continue

                # 复用 admittance_calculate.py 的映射：joint_angles_to_board_mapping
                board_map = AdmittanceControlNode.joint_angles_to_board_mapping(
                    self._map_helper, angles_deg, self.only_legs
                )

                if not self.dry_run and self.robot is not None:
                    # 默认不加 --verbose 时，吞掉 RobotController 内部 print（保持终端干净）
                    with _silence_print(enabled=not self.verbose):
                        for board_id in allowed_boards:
                            if board_id not in board_map:
                                continue

                            a01, b01 = board_map[board_id]

                            # 归一化到 0~360，避免负角导致“参数错误”刷日志
                            a01 = _wrap_0_360(float(a01))
                            b01 = _wrap_0_360(float(b01))

                            _ = self.robot.send_single_motor_angles(
                                int(board_id),
                                a01,
                                b01,
                                retry=False,
                            )

                self.stats["sent_frames"] += 1

                # 低频状态打印（每 2 秒一次）
                if time.time() - last_print > 2.0:
                    elapsed = time.time() - self.stats["start_time"]
                    hz = self.stats["sent_frames"] / max(elapsed, 1e-6)
                    print(
                        f"[SendThread] sent={self.stats['sent_frames']} "
                        f"hz={hz:.1f} "
                        f"q_send={self.q_send_frames.qsize()} "
                        f"raw_in={self.stats['raw_frames_in']} "
                        f"ik_batches={self.stats['ik_batches']} "
                        f"boards={allowed_boards}"
                    )
                    last_print = time.time()

                # ===== 控频：绝对时间节拍 =====
                next_t += target_period
                sleep_t = next_t - time.time()
                if sleep_t > 0:
                    time.sleep(sleep_t)
                else:
                    # 落后太多则重置节拍，避免越追越崩
                    if sleep_t < -0.5:
                        next_t = time.time()

            except Exception as e:
                print(f"[SendThread] error: {e}")
                time.sleep(0.1)
    '''

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["online", "offline"], default="online",
                    help="online: watch npy_path; offline: load offline_npy once")
    ap.add_argument("--npy_path", default="/tmp/robot_action.npy",
                    help="在线模式监听的 npy 文件路径")
    ap.add_argument("--offline_npy", default="",
                    help="离线模式读取的 npy 文件路径（shape 期望 (T,J,C)）")

    ap.add_argument("--urdf", required=True,
                    help="URDF 路径（与 IK 模块一致）")

    ap.add_argument("--cut", type=int, default=196,
                    help="每次从 npy 取多少帧做 IK/插值")
    ap.add_argument("--planning_freq", type=float, default=20.0,
                    help="规划频率（给 JointTrajectoryInterpolator）")
    ap.add_argument("--send_freq", type=float, default=100.0,
                    help="下发频率（插值到该频率）")

    ap.add_argument("--port", default="/dev/ttyUSB0", help="串口")
    ap.add_argument("--baud", type=int, default=115200, help="波特率")
    ap.add_argument("--only_legs", action="store_true",
                    help="只下发腿部（映射函数里 only_legs=True 时返回更少板）")
    ap.add_argument("--dry_run", action="store_true",
                    help="不下发串口，只跑全链路并打印状态")
    ap.add_argument("--verbose", action="store_true",
                    help="打印更详细日志")
    return ap.parse_args()


def main():
    args = parse_args()

    if args.mode == "offline" and not args.offline_npy:
        raise ValueError("offline 模式必须提供 --offline_npy")

    tester = EdgeSideTester(
        urdf_path=args.urdf,
        mode=args.mode,
        npy_path=args.npy_path,
        offline_npy=args.offline_npy,
        cut_frame_num=args.cut,
        planning_freq=args.planning_freq,
        send_freq=args.send_freq,
        serial_port=args.port,
        baudrate=args.baud,
        only_legs=args.only_legs,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    tester.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[EdgeSideTester] Ctrl+C, stopping...")
    finally:
        tester.stop()


if __name__ == "__main__":
    main()


'''
python3 ~/TWStateMachine/src/robot_state_machine/robot_state_machine/edge_min_hw_pipeline.py \
  --mode online \
  --npy_path /tmp/robot_action.npy \
  --urdf /home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data/Assembly/Assembly.SLDASM.urdf \
  --port /dev/ttyUSB0 --baud 115200
'''

'''
python3 ~/TWStateMachine/src/robot_state_machine/robot_state_machine/edge_min_hw_pipeline.py \
  --mode online \
  --npy_path /tmp/robot_action.npy \
  --urdf /home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data/Assembly/Assembly.SLDASM.urdf \
  --dry_run --verbose
'''