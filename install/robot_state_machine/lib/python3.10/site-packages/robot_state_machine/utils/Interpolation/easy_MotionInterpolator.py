# 两个动作之间的平滑过渡， 可检测碰撞； 插值时间 ＜= 0.01s
import sys
sys.path.insert(0, '/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/Interpolation')  # 根据实际路径调整
import joblib
import numpy as np
import torch
from phc.utils.torch_MMRAV6_Assembly_batch import Humanoid_Batch
import time

# 计时打印
class Timer:
    def __init__(self):
        self.start_time = time.time()   # 总开始时间
        self.last_time = self.start_time  # 最近一次 step 或 start 的时间
        self.section_name = "init"

    def start(self, name="section"):
        """开始一个新的计时段"""
        self.section_name = name
        self.last_time = time.time()
        print(f"\n--- Start [{name}] ---")

    def step(self, msg):
        """打印距离上一次 step/start 的时间"""
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        print(f"[{self.section_name}] +{dt:.4f}s : {msg}")

    def total(self):
        """打印从初始化开始的总时间"""
        total = time.time() - self.start_time
        print(f"\n=== Total Time: {total:.4f}s ===\n")

class HumanoidMotionInterpolator:
    def __init__(self, transition_times = 1.0): # transition_times 最大过渡时间设置
        self.transition_times = transition_times
        self.h1_fk = None
        self.torch_loaded = False
        self.safe_action = {
            "fps": 20,
            "dof": np.array([[
                -9.2105813e-02, -1.4053576e-01, -7.5029254e-02, -4.9787298e-01,
                -1.8033399e-03,  2.6645012e-08,  2.4473466e-01,  1.9085576e-01,
                2.4113551e-01, -7.0287412e-01,  2.5476969e-03, -2.6645012e-08,
                -9.5260747e-02, -4.0986693e-01,  8.9331567e-02,  1.7047387e-01,
                -4.6315446e-01,  2.5193274e-01, -7.0001018e-01,  0.0000000e+00,
                1.2521362e-01,  3.2662070e-01, -1.4043774e-01,  6.8266308e-01,
                0.0000000e+00, -1.6366319e-01, -1.3911568e-01, -1.4007068e-01
            ]], dtype=np.float32),

            "root_trans_offset": np.array([[
                -0.00312672, -0.17963827,  0.28149518
            ]], dtype=np.float32),

            "root_rot": np.array([[
                1.0, 0.0, 0.0, 0.0    
            ]], dtype=np.float32),
        }
        self.collision_pairs = [
        (18, 23), (18, 24), (18, 25),
        (19, 23), (19, 24), (19, 25),
        (20, 23), (20, 24), (20, 25),

        (18, 2), (18, 3), (18, 4), (18, 6), (18, 7), (18, 9), (18, 10), (18, 12),
        (19, 2), (19, 3), (19, 4), (19, 6), (19, 7), (19, 9), (19, 10), (19, 12),
        (20, 2), (20, 3), (20, 4), (20, 6), (20, 7), (20, 9), (20, 10), (20, 12),

        (23, 2), (23, 3), (23, 4), (23, 6), (23, 7), (23, 9), (23, 10), (23, 12),
        (24, 2), (24, 3), (24, 4), (24, 6), (24, 7), (24, 9), (24, 10), (24, 12),
        (25, 2), (25, 3), (25, 4), (25, 6), (25, 7), (25, 9), (25, 10), (25, 12),

        (2, 7), (2, 9), (2, 10), (2, 12),
        (3, 7), (3, 9), (3, 10), (3, 12),
        (4, 7), (4, 9), (4, 10), (4, 12),
        (6, 7), (6, 9), (6, 10), (6, 12),

        (13, 18), (13, 19), (13, 20), (13, 23), (13, 24), (13, 25),
        (15, 18), (15, 19), (15, 20), (15, 23), (15, 24), (15, 25),
        (26, 18), (26, 19), (26, 20), (26, 23), (26, 24), (26, 25),
        (28, 18), (28, 19), (28, 20), (28, 23), (28, 24), (28, 25)
    ]
        self.collision_thresholds = {
        (18, 23): 0.03, (18, 24): 0.03, (18, 25): 0.03,
        (19, 23): 0.03, (19, 24): 0.03, (19, 25): 0.03,
        (20, 23): 0.03, (20, 24): 0.03, (20, 25): 0.03,

        (18, 2): 0.03, (18, 3): 0.03, (18, 4): 0.03, (18, 6): 0.03,
        (18, 7): 0.03, (18, 9): 0.03, (18, 10): 0.03, (18, 12): 0.03,

        (19, 2): 0.03, (19, 3): 0.03, (19, 4): 0.03, (19, 6): 0.03,
        (19, 7): 0.03, (19, 9): 0.03, (19, 10): 0.03, (19, 12): 0.03,

        (20, 2): 0.03, (20, 3): 0.03, (20, 4): 0.03, (20, 6): 0.03,
        (20, 7): 0.03, (20, 9): 0.03, (20, 10): 0.03, (20, 12): 0.03,

        (23, 2): 0.03, (23, 3): 0.03, (23, 4): 0.03, (23, 6): 0.03,
        (23, 7): 0.03, (23, 9): 0.03, (23, 10): 0.03, (23, 12): 0.03,

        (24, 2): 0.03, (24, 3): 0.03, (24, 4): 0.03, (24, 6): 0.03,
        (24, 7): 0.03, (24, 9): 0.03, (24, 10): 0.03, (24, 12): 0.03,

        (25, 2): 0.03, (25, 3): 0.03, (25, 4): 0.03, (25, 6): 0.03,
        (25, 7): 0.03, (25, 9): 0.03, (25, 10): 0.03, (25, 12): 0.03,

        (2, 7): 0.03, (2, 9): 0.03, (2, 10): 0.03, (2, 12): 0.03,
        (3, 7): 0.03, (3, 9): 0.03, (3, 10): 0.03, (3, 12): 0.03,
        (4, 7): 0.03, (4, 9): 0.03, (4, 10): 0.03, (4, 12): 0.03,
        (6, 7): 0.03, (6, 9): 0.03, (6, 10): 0.03, (6, 12): 0.03,

        (13, 18): 0.05, (13, 19): 0.05, (13, 20): 0.05,
        (13, 23): 0.05, (13, 24): 0.05, (13, 25): 0.05,

        (15, 18): 0.05, (15, 19): 0.05, (15, 20): 0.05,
        (15, 23): 0.05, (15, 24): 0.05, (15, 25): 0.05,

        (26, 18): 0.05, (26, 19): 0.05, (26, 20): 0.05,
        (26, 23): 0.05, (26, 24): 0.05, (26, 25): 0.05,

        (28, 18): 0.05, (28, 19): 0.05, (28, 20): 0.05,
        (28, 23): 0.05, (28, 24): 0.05, (28, 25): 0.05
        }
        self.MMRAV6_rotation_axis = None
        idx_A, idx_B, thresholds = [], [], []
        for pair in self.collision_pairs:
            idx_A.append(pair[0])
            idx_B.append(pair[1])
            thresh = self.collision_thresholds.get(pair, 0.03) # 默认 0.03
            thresholds.append(thresh)
            
        # 存为 Tensor (注意：实际使用时需确保 device 一致)
        self.coll_idx_A = torch.tensor(idx_A, dtype=torch.long)
        self.coll_idx_B = torch.tensor(idx_B, dtype=torch.long)
        self.coll_thresh = torch.tensor(thresholds, dtype=torch.float32)

    def _ensure_fk_loaded(self):
        """仅在需要碰撞检测时调用"""
        if self.h1_fk is None:
            self.h1_fk = Humanoid_Batch()
            self.MMRAV6_rotation_axis = torch.tensor([[ 0.0000e+00,  1.0000e+00,  0.0000e+00],#left_hip_pitch_joint
                                        [-1.0000e+00,  0.0000e+00,  0.0000e+00], #left_hip_roll_joint
                                        [ 0.0000e+00,  0.0000e+00, -1.0000e+00], #left_hip_yaw_joint
                                        [ 0.0000e+00, -1.0000e+00,  0.0000e+00], #left_knee_pitch_joint
                                        [ 0.0000e+00,  0.0000e+00, -1.0000e+00], #left_ankle_yaw_joint
                                        [ 0.0000e+00,  1.0000e+00,  0.0000e+00], #left_ankle_pitch_joint
                                        [ 0.0000e+00, -1.0000e+00,  0.0000e+00], # right_hip_pitch_joint
                                        [-1.0000e+00,  0.0000e+00,  0.0000e+00], # right_hip_roll_joint
                                        [ 0.0000e+00,  0.0000e+00, -1.0000e+00], # right_hip_yaw_joint
                                        [ 0.0000e+00, -1.0000e+00,  0.0000e+00], # right_knee_pitch_joint
                                        [ 0.0000e+00,  0.0000e+00, -1.0000e+00], #right_ankle_yaw_joint
                                        [ 0.0000e+00, -1.0000e+00,  0.0000e+00], #right_ankle_pitch_joint
                                        [ 0.0000e+00,  0.0000e+00,  1.0000e+00], #waist_yaw_joint
                                        [ 0.0000e+00, -1.0000e+00,  0.0000e+00], #waist_pitch_joint
                                        [-1.0000e+00,  0.0000e+00,  0.0000e+00], #waist_roll_joint
                                        [ 0.0000e+00,  1.0000e+00,  0.0000e+00], # left_shoulder_pitch_joint
                                        [-1.0000e+00,  0.0000e+00,  0.0000e+00], #left_shoulder_roll_joint
                                        [ 0.0000e+00,  0.0000e+00, -1.0000e+00], # left_shoulder_yaw_joint
                                        [ 0.0000e+00,  1.0000e+00,  0.0000e+00], #left_elbow_pitch_joint
                                        [ 0.0000e+00,  0.0000e+00, -1.0000e+00], # left_wrist_yaw_joint
                                        [ 0.0000e+00, -1.0000e+00,  0.0000e+00], #right_shoulder_pitch_joint
                                        [-1.0000e+00,  0.0000e+00,  0.0000e+00], # right_shoulder_roll_joint
                                        [ 0.0000e+00,  0.0000e+00, -1.0000e+00], # right_shoulder_yaw_joint
                                        [ 0.0000e+00, -1.0000e+00,  0.0000e+00], #right_elbow_pitch_join
                                        [ 0.0000e+00,  0.0000e+00, -1.0000e+00], #right_wrist_yaw_joint
                                        [ 0.0000e+00,  0.0000e+00,  1.0000e+00], # neck_yaw_joint
                                        [-1.0000e+00,  0.0000e+00,  0.0000e+00], # neck_roll_joint
                                        [ 0.0000e+00,  1.0000e+00,  0.0000e+00], #neck_pitch_joint
                                        [-1.0000e+00,  0.0000e+00,  0.0000e+00], # left_ear_fix
                                        [-1.0000e+00,  1.1910e-04,  0.0000e+00] # right_ear.
                                        ])

    def is_collision(self, transition):
        self._ensure_fk_loaded()
        dof = transition["dof"]                     # shape [T, J]
        T = dof.shape[0]
        root_pos = transition["root_trans_offset"] # shape [T, 3]
        root_pos_torch = torch.from_numpy(root_pos).float()
        dof_torch = torch.from_numpy(dof).float()
        dof_torch = dof_torch.unsqueeze(0).unsqueeze(-1) # → [1, T, 28, 1]
        zeros_to_add = torch.zeros(dof_torch.shape[0],dof_torch.shape[1],2,dof_torch.shape[3], device=dof_torch.device)
        dof_pos_new_expanded = torch.cat([dof_torch, zeros_to_add], dim=-2)
        pose_aa_h1_new = torch.cat([root_pos_torch[None, :, None], self.MMRAV6_rotation_axis * dof_pos_new_expanded, torch.zeros((1, T, 2, 3))], axis=2)
        fk_return = self.h1_fk.fk_batch(pose_aa_h1_new,root_pos_torch[None, ])
        positions = fk_return["global_translation"]
        positions = positions[0]  # → [T, 31, 3]
        if self.coll_idx_A.device != positions.device:
            self.coll_idx_A = self.coll_idx_A.to(positions.device)
            self.coll_idx_B = self.coll_idx_B.to(positions.device)
            self.coll_thresh = self.coll_thresh.to(positions.device)
        pos_A = positions[:, self.coll_idx_A]
        pos_B = positions[:, self.coll_idx_B]
        dists = torch.norm(pos_A - pos_B, dim=-1)
        # 比较阈值，只要有任意一个小于阈值就是碰撞
        if (dists < self.coll_thresh).any():
            return True
        return False
    
    def smooth_transition_boundary(self, dof_full, window=7):
        T, J = dof_full.shape
        half = window // 2
        dof_smoothed = dof_full.copy()
        # ---- 前段平滑 A_end & T_start ----
        for i in range(window * 2):  # 两段范围共 2 * window
            left = max(0, i - half)
            right = min(T, i + half + 1)
            dof_smoothed[i] = dof_full[left:right].mean(axis=0)
        # ---- 后段平滑 T_end & B_start ----
        for i in range(T - window * 2, T):
            left = max(0, i - half)
            right = min(T, i + half + 1)
            dof_smoothed[i] = dof_full[left:right].mean(axis=0)
        return dof_smoothed

    # 纯 Numpy 实现 Slerp，移除 SciPy 依赖
    def interpolate_root_rot(self, rot_start, rot_end, num_frames):
        rot_start = np.asarray(rot_start)
        rot_end = np.asarray(rot_end)
        # 归一化（防止四元数漂移）
        rot_start = rot_start / np.linalg.norm(rot_start)
        rot_end = rot_end / np.linalg.norm(rot_end)
        # 计算点积
        dot = np.dot(rot_start, rot_end)
        # 确保走最短路径（如果点积为负，反转其中一个四元数）
        if dot < 0.0:
            rot_end = -rot_end
            dot = -dot
        # 限制范围防止数值误差导致 acos 越界
        dot = np.clip(dot, -1.0, 1.0)
        # 特殊情况：非常接近则直接线性插值（避免除以零）
        if dot > 0.9995:
            # 简单的线性插值并归一化
            t = np.linspace(0, 1, num_frames)[:, None]
            result = (1.0 - t) * rot_start + t * rot_end
            return result / np.linalg.norm(result, axis=1, keepdims=True)
        # 标准 Slerp 公式
        theta_0 = np.arccos(dot)
        sin_theta_0 = np.sin(theta_0)
        t = np.linspace(0, 1, num_frames)[:, None]
        theta = theta_0 * t
        sin_theta = np.sin(theta)
        s0 = np.cos(theta) - dot * sin_theta / sin_theta_0
        s1 = sin_theta / sin_theta_0
        
        return (s0 * rot_start) + (s1 * rot_end)

    # 统一计算权重
    def get_quintic_params(self, q_start, q_end, num_frames):
        t = np.linspace(0, 1, num_frames)
        w = 6 * t**5 - 15 * t**4 + 10 * t**3
        w = w[:, None]
        return (1-w) * q_start + w * q_end

    # 提取重采样逻辑为类方法，供 run 和 concatenate_actions 使用
    def resample_action_to_fps(self, action, target_fps, index=None):
        src_fps = action["fps"]
        dof = action["dof"]                      
        root_pos = action["root_trans_offset"]   
        root_rot = action["root_rot"]            
        T_old = dof.shape[0]

        duration = (T_old - 1) / src_fps
        T_new = int(np.round(duration * target_fps)) + 1

        t_old = np.linspace(0, duration, T_old)
        t_new = np.linspace(0, duration, T_new)

        dof_new = np.zeros((T_new, dof.shape[1]))
        for j in range(dof.shape[1]):
            dof_new[:, j] = np.interp(t_new, t_old, dof[:, j])

        root_pos_new = np.zeros((T_new, 3))
        for k in range(3):
            root_pos_new[:, k] = np.interp(t_new, t_old, root_pos[:, k])

        # 使用 NLERP 进行重采样
        root_rot_new = np.zeros((T_new, 4))
        for k in range(4):
            root_rot_new[:, k] = np.interp(t_new, t_old, root_rot[:, k])
        norm = np.linalg.norm(root_rot_new, axis=1, keepdims=True)
        root_rot_new /= norm
        
        if index is not None:
            t_index = t_old[index]                           
            index_new = np.argmin(np.abs(t_new - t_index))   
        else:
            index_new = None
        
        new_action = dict(action) 
        new_action["fps"] = target_fps
        new_action["dof"] = dof_new
        new_action["root_trans_offset"] = root_pos_new
        new_action["root_rot"] = root_rot_new
        return new_action, index_new

    # 生成中间过渡帧数据
    def _generate_transition(self, action_A, action_B, num_frames, index_A, index_B, fps):
        q_start = action_A['dof'][index_A]
        q_end = action_B['dof'][index_B]
        root_start = action_A['root_trans_offset'][index_A]
        root_end = action_B['root_trans_offset'][index_B]
        rot_start = action_A['root_rot'][index_A]
        rot_end = action_B['root_rot'][index_B]

        transition_dof = self.get_quintic_params(q_start, q_end, num_frames)
        transition_root = self.get_quintic_params(root_start, root_end, num_frames)
        transition_rot = self.interpolate_root_rot(rot_start, rot_end, num_frames)

        return {
            'fps': fps,
            'dof': transition_dof,
            'root_trans_offset': transition_root,
            'root_rot': transition_rot
        }

    def run(self, action_A, action_B, is_smooth = True, target_fps=20, index_A=None, index_B=None):
        if index_A is None:
            index_A = len(action_A["dof"]) - 1
        if index_B is None:
            index_B = 0
        action_A_fps = action_A['fps']
        action_B_fps = action_B['fps']
        work_fps = max(target_fps,action_A_fps,action_B_fps)
        # 1. 如果 FPS 不一致，先在这里统一重采样，避免后面重复处理
        if action_A_fps != work_fps:
            action_A, index_A = self.resample_action_to_fps(action_A, work_fps, index_A)
        if action_B_fps != work_fps:
            action_B, index_B = self.resample_action_to_fps(action_B, work_fps, index_B)

        # 2. 计算过渡时间
        q_start = action_A['dof'][index_A]
        q_end = action_B['dof'][index_B]
        root_start = action_A['root_trans_offset'][index_A]
        root_end = action_B['root_trans_offset'][index_B]
        rot_start = action_A['root_rot'][index_A]
        rot_end = action_B['root_rot'][index_B]
        trans_time = self.compute_transition_time(q_start,q_end,root_start,root_end,rot_start,rot_end)
        num_frames = int(trans_time * work_fps)

        # 3. 生成过渡帧（只计算一次）
        transition_data = self._generate_transition(action_A, action_B, num_frames, index_A, index_B, work_fps)
        transition_data['fps'] = work_fps

        # 4. 检测碰撞
        if self.is_collision(transition_data):
            print("产生碰撞，切换为 Safe 模式 (间接过渡)")
            # 这里调用 safe，safe 内部会处理具体的拼接，无需重复计算
            return self.safe_concatenate_actions(action_A, action_B, is_smooth, target_fps, index_A, index_B)

        print("无碰撞，使用 Direct 模式 (直接拼接)")
        # 5. 直接拼接 (Stitching)，不再调用 concatenate_actions 避免重算
        A_dof, A_pos, A_rot = action_A["dof"], action_A["root_trans_offset"], action_A["root_rot"]
        B_dof, B_pos, B_rot = action_B["dof"], action_B["root_trans_offset"], action_B["root_rot"]
        T_dof, T_pos, T_rot = transition_data["dof"], transition_data["root_trans_offset"], transition_data["root_rot"]

        # 拼接：A[:index+1] + Transition[1:] + B[index+1:]
        dof_full = np.concatenate([A_dof[:index_A + 1], T_dof[1:], B_dof[index_B + 1:]], axis=0)
        if is_smooth:
            dof_full = self.smooth_transition_boundary(dof_full, window=7)

        pos_full = np.concatenate([A_pos[:index_A + 1], T_pos[1:], B_pos[index_B + 1:]], axis=0)
        rot_full = np.concatenate([A_rot[:index_A + 1], T_rot[1:], B_rot[index_B + 1:]], axis=0)

        return {
            "fps": work_fps,
            "dof": dof_full,
            "root_trans_offset": pos_full,
            "root_rot": rot_full
        }

    # 仍然保留此函数作为手动直接调用的接口，或者给 safe 方法内部调用
    def concatenate_actions(self, action_A, action_B, is_smooth=True, transition_times=1.0, target_fps=20, index_A=None, index_B=None):
        if index_A is None: index_A = len(action_A["dof"]) - 1
        if index_B is None: index_B = 0

        action_A_fps = action_A['fps']
        action_B_fps = action_B['fps']
        work_fps = max(target_fps, action_A_fps, action_B_fps)
        
        if action_A_fps != work_fps:
            action_A, index_A = self.resample_action_to_fps(action_A, work_fps, index_A)
        if action_B_fps != work_fps:
            action_B, index_B = self.resample_action_to_fps(action_B, work_fps, index_B)

        num_frames = int(transition_times * work_fps)
        transition_data = self._generate_transition(action_A, action_B, num_frames, index_A, index_B, work_fps)
        
        # 拼接
        dof_full = np.concatenate([action_A["dof"][:index_A + 1], transition_data["dof"][1:], action_B["dof"][index_B + 1:]], axis=0)
        if is_smooth:
            dof_full = self.smooth_transition_boundary(dof_full, window=7)
        pos_full = np.concatenate([action_A["root_trans_offset"][:index_A + 1], transition_data["root_trans_offset"][1:], action_B["root_trans_offset"][index_B + 1:]], axis=0)
        rot_full = np.concatenate([action_A["root_rot"][:index_A + 1], transition_data["root_rot"][1:], action_B["root_rot"][index_B + 1:]], axis=0)

        return {
            "fps": work_fps,
            "dof": dof_full,
            "root_trans_offset": pos_full,
            "root_rot": rot_full
        }

    def compute_transition_time(self, q_start, q_end, root_start, root_end, rot_start, rot_end):

        # ---- 关节差异 ----
        joint_diff = np.linalg.norm(q_start - q_end)
        joint_norm = min(joint_diff / 2.0, 1.0)  # 假设最大关节差最大小取 2 rad

        # ---- root 平移差异 ----
        pos_diff = np.linalg.norm(root_start - root_end)
        pos_norm = min(pos_diff / 0.2, 1.0)      # 假设 20cm 归一化

        # ---- root 旋转角差 ----
        q1 = rot_start / np.linalg.norm(rot_start)
        q2 = rot_end / np.linalg.norm(rot_end)
        dot = np.clip(np.abs(np.dot(q1, q2)), -1.0, 1.0)
        rot_diff = 2.0 * np.arccos(dot)
        rot_norm = min(rot_diff / np.pi, 1.0)

        # ---- 综合差异 ----
        motion_diff = 0.6 * joint_norm + 0.2 * pos_norm + 0.2 * rot_norm
        motion_diff = min(motion_diff, 1.0)

        # ---- 实际过渡时间 ----
        t_min = 0.5   # 最短 50 ms
        t_max = self.transition_times

        transition_time = t_min + motion_diff * (t_max - t_min)
        return transition_time

    def safe_concatenate_actions(self, action_A, action_B, is_smooth=True, target_fps=20, index_A=None, index_B=None):
        if index_A is None: index_A = len(action_A["dof"]) - 1
        if index_B is None: index_B = 0

        self.safe_action["root_rot"][0] = action_A["root_rot"][index_A]
        qA = action_A["dof"][index_A]
        qS = self.safe_action["dof"][0]
        rootA = action_A["root_trans_offset"][index_A]
        rootS = self.safe_action["root_trans_offset"][0]
        rotA = action_A["root_rot"][index_A]
        rotS = self.safe_action["root_rot"][0]
        t1 = self.compute_transition_time(qA, qS, rootA, rootS, rotA, rotS)
        print(f"Safe模式 - 第一段过渡时间: {t1:.4f}")
        
        part1 = self.concatenate_actions(
            action_A, self.safe_action, is_smooth, t1, target_fps, index_A, 0
        )
        
        qS = self.safe_action["dof"][0]
        qB = action_B["dof"][index_B]
        rootS = self.safe_action["root_trans_offset"][0]
        rootB = action_B["root_trans_offset"][index_B]
        rotS = self.safe_action["root_rot"][0]
        rotB = action_B["root_rot"][index_B]
        t2 = self.compute_transition_time(qS, qB, rootS, rootB, rotS, rotB)
        print(f"Safe模式 - 第二段过渡时间: {t2:.4f}")
        
        part2 = self.concatenate_actions(
            self.safe_action, action_B, is_smooth, t2, target_fps, 0, index_B
        )
        
        final = {
            "fps": target_fps,
            "dof": np.concatenate([part1["dof"], part2["dof"][1:]], axis=0),
            "root_trans_offset": np.concatenate([part1["root_trans_offset"], part2["root_trans_offset"][1:]], axis=0),
            "root_rot": np.concatenate([part1["root_rot"], part2["root_rot"][1:]], axis=0),
        }
        return final
    

if __name__ == "__main__":
    timer = Timer()
    timer.start("初始化过程")

    interpolator = HumanoidMotionInterpolator()
    timer.step("加载插值器完成")

    action_A = joblib.load("input/right-back.pkl")
    print("动作A的总帧数：",len(action_A["dof"]))
    action_B = joblib.load("input/right-front.pkl")
    print("动作B的总帧数：",len(action_B["dof"]))
    timer.step("导入文件完成")

    full_action = interpolator.run(action_A,action_B, index_A=None,index_B=None, is_smooth=True, target_fps=20)
    print("插值合并后动作总帧数为：", len(full_action["dof"]))
    timer.step("生成合并轨迹完成")
    
    # 保存结果
    joblib.dump(full_action, "output/result.pkl")
    timer.total()