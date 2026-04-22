import sys
sys.path.insert(0, '/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection')

import numpy as np
import os
import time
import joblib
import smplx
import torch
import config
from config import H1Config
import pinocchio as pin
import pink
import pink.tasks
from scipy.ndimage import gaussian_filter1d
from scipy.spatial.transform import Rotation as sRot


def load_data(data_path: str) -> np.ndarray:
    """
    兼容：
      - (22,3,T)
      - (T,22,3)
      - (1,22,3,T)
      - dict{"motion": ...} 其中 motion 形状同上
    返回统一为 (T,22,3)
    """
    obj = np.load(open(data_path, "rb"), allow_pickle=True)

    if isinstance(obj, np.ndarray) and obj.shape == () and obj.dtype == object:
        obj = obj.item()

    if isinstance(obj, dict):
        if "motion" not in obj:
            raise ValueError(f"Loaded dict has no 'motion'. keys={list(obj.keys())}")
        motion = np.asarray(obj["motion"])
    else:
        motion = np.asarray(obj)

    if motion.ndim == 4 and motion.shape[1:3] == (22, 3):
        # (1,22,3,T) -> (T,22,3)
        seq = motion[0].transpose(2, 0, 1)
    elif motion.ndim == 3 and motion.shape[0:2] == (22, 3):
        # (22,3,T) -> (T,22,3)
        seq = motion.transpose(2, 0, 1)
    elif motion.ndim == 3 and motion.shape[1:3] == (22, 3):
        seq = motion
    else:
        raise ValueError(f"Unsupported motion shape: {motion.shape}")

    return seq


def get_pelvis_orientation(pelvis, left_hip, right_hip):
    lateral_vec = left_hip - right_hip
    y_axis = lateral_vec / (np.linalg.norm(lateral_vec) + 1e-6)

    up_vec = np.array([0, 0, 1.0])

    x_axis = np.cross(y_axis, up_vec)
    x_axis = x_axis / (np.linalg.norm(x_axis) + 1e-6)

    y_axis = np.cross(up_vec, x_axis)
    y_axis = y_axis / (np.linalg.norm(y_axis) + 1e-6)

    return np.stack([x_axis, y_axis, up_vec], axis=1)


class H1PinkSolver:
    def __init__(self, urdf_path: str):
        self.device = H1Config.DEVICE

        self.robot = pin.RobotWrapper.BuildFromURDF(
            urdf_path,
            package_dirs=[os.path.dirname(urdf_path)],
            root_joint=pin.JointModelFreeFlyer()
        )
        self.model = self.robot.model
        self.data = self.robot.data

        # --- q_ref 初始化 ---
        self.q_ref = pin.neutral(self.model)
        for name, value in H1Config.USER_DATA_DICT.items():
            if self.model.existJointName(name):
                joint_id = self.model.getJointId(name)
                q_idx = self.model.joints[joint_id].idx_q
                self.q_ref[q_idx] = value
            else:
                print(f"[WARN] URDF 中找不到关节 {name}，已忽略")

        self.configuration = pink.Configuration(self.model, self.data, self.q_ref)

        self.smpl_model = smplx.create(
            model_path='/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data',
            model_type='smpl',
            gender='neutral',
            use_hands=False,
            use_feet_keypoints=False,
            batch_size=1
        )

        # --- robot dims（保留左右臂不对称）---
        self.robot_dims_legs = {
            'thigh': 0.0832,
            'calf': 0.1105,
            'hip_offset': 0.04326
        }
        self.robot_dims_left_arm = {
            'upper_arm': 0.069842,
            'forearm': 0.053359,
        }
        self.robot_dims_right_arm = {
            'upper_arm': 0.075791,
            'forearm': 0.047394,
        }

        # --- scale ---
        self.scale = 0.24658347237104405
        self.scale_upper_right = 0.269774
        self.scale_upper_left = 0.260940

        # --- 建立 joint_name -> q索引 映射（必须先建，后面会用）---
        self.joint_q_idx = {}
        for pin_idx, name in enumerate(self.model.names):
            if name in H1Config.H1_JOINT_NAMES:
                self.joint_q_idx[name] = self.model.joints[pin_idx].idx_q

        # --- tasks ---
        self.tasks = []
        self.ik_tasks = {}

        # pelvis（waist）任务
        self.pelvis_task = pink.tasks.FrameTask("waist", position_cost=10.0, orientation_cost=50.0)
        self.pelvis_task.set_target(pin.SE3.Identity())
        self.tasks.append(self.pelvis_task)

        # limb 位置追踪任务
        for link_name, smpl_name in H1Config.TRACKING_PAIRS:
            pos_cost = 1.0
            rot_cost = 0.0

            if "hand" in link_name:
                pos_cost = 15.0
                rot_cost = 0.0
            elif "foot" in link_name or "calf" in link_name:
                pos_cost = 10.0
                rot_cost = 1.0
            elif "thigh" in link_name:
                pos_cost = 10.0
                rot_cost = 0.0
            elif "upper_arm" in link_name:
                pos_cost = 12.0
                rot_cost = 0.0
            elif "force_arm" in link_name:
                pos_cost = 30.0
                rot_cost = 0.0
            elif "neck" in link_name or "ear" in link_name:
                pos_cost = 2.0
                rot_cost = 0.1
            elif "waist" in link_name:
                pos_cost = 1.0
                rot_cost = 0.1

            if self.model.existFrame(link_name):
                task = pink.tasks.FrameTask(link_name, position_cost=pos_cost, orientation_cost=rot_cost)
                self.tasks.append(task)
                self.ik_tasks[smpl_name] = task
            else:
                print(f"[WARN] 跳过: URDF 中找不到 Link [{link_name}]")

        # --- posture task：用向量 cost，给 shoulder_yaw 提权 ---
        # self.posture_task = pink.tasks.PostureTask(self.model)
        # self.posture_task.set_target(self.q_ref)

        # base_dofs = 6
        # posture_dim = self.model.nv - base_dofs
        # posture_cost = np.full(posture_dim, 0.05, dtype=float)

        # # 给 shoulder_yaw 更强约束（先用 2.0 比较稳）
        # for jn in ["left_shoulder_yaw_joint", "right_shoulder_yaw_joint"]:
        #     if self.model.existJointName(jn):
        #         jid = self.model.getJointId(jn)
        #         v_idx = self.model.joints[jid].idx_v
        #         local = v_idx - base_dofs
        #         if 0 <= local < posture_dim:
        #             posture_cost[local] = 2.0
        #     else:
        #         print(f"[PostureCost] joint not found: {jn}")

        # self.posture_task.cost = posture_cost
        # self.tasks.append(self.posture_task)
        self.posture_task = pink.tasks.PostureTask(self.model)
        self.posture_task.set_target(self.q_ref)
        self.posture_task.cost = 0.05 # 权重很低，作为软约束
        self.tasks.append(self.posture_task)

        # --- SMPL index mapping ---
        self.smpl_indices = {name: H1Config.SMPL_BONE_ORDER.index(name) for _, name in H1Config.TRACKING_PAIRS}

        # --- arm joint limits（修正单位 + wrist_yaw 放宽）---
        ARM_JOINT_LIMITS = {
            'left_shoulder_pitch_joint': (-np.pi/2, np.pi/2),
            'left_shoulder_roll_joint':  (-np.pi, 0.0),
            'left_shoulder_yaw_joint':   (-np.pi/2, np.pi/2),
            'left_elbow_pitch_joint':    (-np.pi/2, 0.0),
            'left_wrist_yaw_joint':      (-np.pi/2, np.pi/2),

            'right_shoulder_pitch_joint': (-np.pi/2, np.pi/2),
            'right_shoulder_roll_joint':  (0.0, np.pi),
            'right_shoulder_yaw_joint':   (-np.pi/2, np.pi/2),
            'right_elbow_pitch_joint':    (0.0, np.pi/2),
            'right_wrist_yaw_joint':      (-np.pi/2, np.pi/2),
        }

        for joint_name, (lo, hi) in ARM_JOINT_LIMITS.items():
            if joint_name in self.joint_q_idx:
                q_idx = self.joint_q_idx[joint_name]
                self.model.lowerPositionLimit[q_idx] = lo
                self.model.upperPositionLimit[q_idx] = hi

        # --- indices for yaw estimation ---
        self._smpl_l_shoulder_idx = H1Config.SMPL_BONE_ORDER.index('left_shoulder')
        self._smpl_l_elbow_idx    = H1Config.SMPL_BONE_ORDER.index('left_elbow')
        self._smpl_r_shoulder_idx = H1Config.SMPL_BONE_ORDER.index('right_shoulder')
        self._smpl_r_elbow_idx    = H1Config.SMPL_BONE_ORDER.index('right_elbow')

        # 右侧 yaw 符号：运行时第0帧自动判断一次后固定
        self._right_yaw_sign = 1.0

    def apply_bone_retargeting(self, smpl_joints, robot_dims_legs, robot_dims_left_arm, robot_dims_right_arm):
        new_joints = smpl_joints.copy()
        idx_root = 0

        idx_l_hip = H1Config.SMPL_BONE_ORDER.index('left_hip')
        idx_l_knee = H1Config.SMPL_BONE_ORDER.index('left_knee')
        idx_l_ankle = H1Config.SMPL_BONE_ORDER.index('left_ankle')

        idx_r_hip = H1Config.SMPL_BONE_ORDER.index('right_hip')
        idx_r_knee = H1Config.SMPL_BONE_ORDER.index('right_knee')
        idx_r_ankle = H1Config.SMPL_BONE_ORDER.index('right_ankle')

        idx_l_shoulder = H1Config.SMPL_BONE_ORDER.index('left_shoulder')
        idx_l_elbow = H1Config.SMPL_BONE_ORDER.index('left_elbow')
        idx_l_wrist = H1Config.SMPL_BONE_ORDER.index('left_wrist')

        idx_r_shoulder = H1Config.SMPL_BONE_ORDER.index('right_shoulder')
        idx_r_elbow = H1Config.SMPL_BONE_ORDER.index('right_elbow')
        idx_r_wrist = H1Config.SMPL_BONE_ORDER.index('right_wrist')

        # pelvis -> hips
        vec_l_pelvis = smpl_joints[:, idx_l_hip] - smpl_joints[:, idx_root]
        dir_l_pelvis = vec_l_pelvis / (np.linalg.norm(vec_l_pelvis, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_l_hip] = new_joints[:, idx_root] + dir_l_pelvis * robot_dims_legs['hip_offset']

        vec_r_pelvis = smpl_joints[:, idx_r_hip] - smpl_joints[:, idx_root]
        dir_r_pelvis = vec_r_pelvis / (np.linalg.norm(vec_r_pelvis, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_r_hip] = new_joints[:, idx_root] + dir_r_pelvis * robot_dims_legs['hip_offset']

        # left leg
        vec_l_thigh = smpl_joints[:, idx_l_knee] - smpl_joints[:, idx_l_hip]
        dir_l_thigh = vec_l_thigh / (np.linalg.norm(vec_l_thigh, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_l_knee] = new_joints[:, idx_l_hip] + dir_l_thigh * robot_dims_legs['thigh']

        vec_l_calf = smpl_joints[:, idx_l_ankle] - smpl_joints[:, idx_l_knee]
        dir_l_calf = vec_l_calf / (np.linalg.norm(vec_l_calf, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_l_ankle] = new_joints[:, idx_l_knee] + dir_l_calf * robot_dims_legs['calf']

        # right leg
        vec_r_thigh = smpl_joints[:, idx_r_knee] - smpl_joints[:, idx_r_hip]
        dir_r_thigh = vec_r_thigh / (np.linalg.norm(vec_r_thigh, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_r_knee] = new_joints[:, idx_r_hip] + dir_r_thigh * robot_dims_legs['thigh']

        vec_r_calf = smpl_joints[:, idx_r_ankle] - smpl_joints[:, idx_r_knee]
        dir_r_calf = vec_r_calf / (np.linalg.norm(vec_r_calf, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_r_ankle] = new_joints[:, idx_r_knee] + dir_r_calf * robot_dims_legs['calf']

        # left arm
        vec_l_arm = smpl_joints[:, idx_l_elbow] - smpl_joints[:, idx_l_shoulder]
        dir_l_arm = vec_l_arm / (np.linalg.norm(vec_l_arm, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_l_elbow] = new_joints[:, idx_l_shoulder] + dir_l_arm * robot_dims_left_arm['upper_arm']

        vec_l_forearm = smpl_joints[:, idx_l_wrist] - smpl_joints[:, idx_l_elbow]
        dir_l_forearm = vec_l_forearm / (np.linalg.norm(vec_l_forearm, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_l_wrist] = new_joints[:, idx_l_elbow] + dir_l_forearm * robot_dims_left_arm['forearm']

        # right arm
        vec_r_arm = smpl_joints[:, idx_r_elbow] - smpl_joints[:, idx_r_shoulder]
        dir_r_arm = vec_r_arm / (np.linalg.norm(vec_r_arm, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_r_elbow] = new_joints[:, idx_r_shoulder] + dir_r_arm * robot_dims_right_arm['upper_arm']

        vec_r_forearm = smpl_joints[:, idx_r_wrist] - smpl_joints[:, idx_r_elbow]
        dir_r_forearm = vec_r_forearm / (np.linalg.norm(vec_r_forearm, axis=-1, keepdims=True) + 1e-6)
        new_joints[:, idx_r_wrist] = new_joints[:, idx_r_elbow] + dir_r_forearm * robot_dims_right_arm['forearm']

        return new_joints

    def process_motion(self, target_motion: np.ndarray):
        start_time = time.time()

        N = len(target_motion)
        target_motion = torch.from_numpy(target_motion).float()

        # 22 -> 29 padding + 坐标旋转
        if target_motion.shape[1] == 22:
            padding = torch.zeros((N, 7, 3), dtype=target_motion.dtype)
            target_motion = torch.cat([target_motion, padding], dim=1)

            quat = [0.5, 0.5, 0.5, 0.5]
            r = sRot.from_quat(quat)
            rot_matrix = torch.from_numpy(r.as_matrix()).float()
            target_motion = torch.matmul(target_motion, rot_matrix.t())

        smpl_raw_seq = target_motion.detach().cpu().numpy()
        _, num_joints, _ = smpl_raw_seq.shape

        # scale per joint (upper arms separate)
        pos_smpl_root = smpl_raw_seq[:, 0:1, :]
        scales = np.full(num_joints, self.scale, dtype=float)
        upper_right_idxs = [14, 17, 19, 21, 23]
        upper_left_idxs = [13, 16, 18, 20, 22]
        for idx in upper_left_idxs:
            if idx < num_joints:
                scales[idx] = self.scale_upper_left
        for idx in upper_right_idxs:
            if idx < num_joints:
                scales[idx] = self.scale_upper_right
        scales = scales.reshape(1, num_joints, 1)

        smpl_joints_local = (smpl_raw_seq - pos_smpl_root) * scales

        # align to waist initial
        T_waist_init = self.configuration.get_transform_frame_to_world("waist")
        waist_pos = T_waist_init.translation
        waist_offset = waist_pos.reshape(1, 1, 3)
        smpl_joints_target = smpl_joints_local + waist_offset

        # bone retarget
        smpl_joints_target = self.apply_bone_retargeting(
            smpl_joints_target,
            self.robot_dims_legs,
            self.robot_dims_left_arm,
            self.robot_dims_right_arm
        )

        # IK loop
        dt = 0.05
        solver = pink.solve_ik

        dof_results = []
        h1_cartesian_seq = []
        target_node_names = H1Config.H1_NODE_NAMES
        all_root_quat = []

        print(f"Starting IK for {N} frames...")

        for i in range(N):
            # pelvis target
            target_origin = smpl_joints_target[i, 0]
            p_root = smpl_joints_target[i, 0]
            p_l_hip = smpl_joints_target[i, 1]
            p_r_hip = smpl_joints_target[i, 2]
            target_rot_mat = get_pelvis_orientation(p_root, p_l_hip, p_r_hip)
            self.pelvis_task.set_target(pin.SE3(target_rot_mat, target_origin))

            # ===== shoulder_yaw estimation in pelvis-local =====
            l_arm_vec = smpl_joints_target[i, self._smpl_l_elbow_idx] - smpl_joints_target[i, self._smpl_l_shoulder_idx]
            r_arm_vec = smpl_joints_target[i, self._smpl_r_elbow_idx] - smpl_joints_target[i, self._smpl_r_shoulder_idx]

            Rt = target_rot_mat.T  # world -> pelvis
            l_vec_local = Rt @ l_arm_vec
            r_vec_local = Rt @ r_arm_vec

            l_n = l_vec_local / (np.linalg.norm(l_vec_local) + 1e-6)
            r_n = r_vec_local / (np.linalg.norm(r_vec_local) + 1e-6)

            # 在 pelvis 坐标的 (Y,Z) 平面算偏转角
            l_yaw_est = np.arctan2(l_n[1], -l_n[2])
            r_yaw_est = np.arctan2(r_n[1], -r_n[2])

            # 第0帧自动判断右侧是否需要取负号（固定一次，避免每帧跳）
            if self._right_yaw_sign is None:
                err_plus = abs(l_yaw_est + r_yaw_est)
                err_minus = abs(l_yaw_est - r_yaw_est)
                self._right_yaw_sign = -1.0 if err_minus < err_plus else +1.0
                print(f"[YawSign] choose right_yaw_sign={self._right_yaw_sign} (err(+)= {np.rad2deg(err_plus):.2f}deg, err(-)= {np.rad2deg(err_minus):.2f}deg)")

            # 写入 q 初值（锁定解支）
            q_temp = self.configuration.q.copy()
            if 'left_shoulder_yaw_joint' in self.joint_q_idx:
                q_temp[self.joint_q_idx['left_shoulder_yaw_joint']] = l_yaw_est
            if 'right_shoulder_yaw_joint' in self.joint_q_idx:
                q_temp[self.joint_q_idx['right_shoulder_yaw_joint']] = self._right_yaw_sign * r_yaw_est
            self.configuration = pink.Configuration(self.model, self.data, q_temp)

            # 更新所有 limb 任务：只追位置，旋转随动
            for smpl_name, task in self.ik_tasks.items():
                if smpl_name in ["waist"]:
                    continue
                final_target_pos = smpl_joints_target[i, self.smpl_indices[smpl_name]]
                current_rot = self.configuration.get_transform_frame_to_world(task.frame).rotation
                task.set_target(pin.SE3(current_rot, final_target_pos))

            # ===== 关键：每帧更新 posture target，把 shoulder_yaw 拉向 yaw_est =====
            q_ref_frame = self.q_ref.copy()
            if 'left_shoulder_yaw_joint' in self.joint_q_idx:
                q_ref_frame[self.joint_q_idx['left_shoulder_yaw_joint']] = l_yaw_est
            if 'right_shoulder_yaw_joint' in self.joint_q_idx:
                q_ref_frame[self.joint_q_idx['right_shoulder_yaw_joint']] = self._right_yaw_sign * r_yaw_est
            self.posture_task.set_target(q_ref_frame)

            # solve
            velocity = solver(self.configuration, self.tasks, dt, solver="quadprog")
            self.configuration.integrate_inplace(velocity, dt)

            all_root_quat.append(self.configuration.q[3:7].copy())

            curr_q = self.configuration.q
            joints_rad = curr_q[7:] if self.model.nq > len(H1Config.H1_JOINT_NAMES) else curr_q
            dof_results.append(joints_rad.copy())

            # debug points
            current_frame_pos = []
            for link_name in target_node_names:
                if self.model.existFrame(link_name):
                    pos = self.configuration.get_transform_frame_to_world(link_name).translation.copy()
                    current_frame_pos.append(pos)
                else:
                    current_frame_pos.append(np.zeros(3))
            h1_cartesian_seq.append(current_frame_pos)

        dof_results = np.array(dof_results)

        print("Applying Gaussian Smoothing...")
        dof_results = gaussian_filter1d(dof_results, sigma=1.5, axis=0)

        # sim2real pack
        print("Packing joint outputs...")
        pin_names = [self.model.names[i] for i in range(self.model.njoints)]
        sim_dof_deg = np.zeros((N, 28))

        for pin_idx, name in enumerate(pin_names):
            if name in H1Config.H1_JOINT_NAMES:
                target_idx = H1Config.H1_JOINT_NAMES.index(name)
                q_idx = self.model.joints[pin_idx].idx_q
                if q_idx >= 7:
                    val = dof_results[:, q_idx - 7]
                    sim_dof_deg[:, target_idx] = np.rad2deg(val)

        # 你原本固定置零的两个关节（保留）
        sim_dof_deg[:, 5] = 0.0
        sim_dof_deg[:, 11] = 0.0

        real_dof_deg = sim_dof_deg.copy()

        print(f"Total time: {time.time() - start_time:.2f}s")
        return {
            "root_trans_offset": np.zeros((N, 3)),
            "dof": np.deg2rad(sim_dof_deg),
            "dof_real": real_dof_deg,
            "root_rot": np.array(all_root_quat),
            "fps": 20,
            "smpl_joints_target": smpl_joints_target,
            "h1_joint_pos": np.array(h1_cartesian_seq),
        }


def plot_arm_symmetry(dof_real, save_dir="output"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(save_dir, exist_ok=True)

    ARM_PAIRS = [
        (15, 20, "shoulder_pitch"),
        (16, 21, "shoulder_roll"),
        (17, 22, "shoulder_yaw"),
        (18, 23, "elbow_pitch"),
        (19, 24, "wrist_yaw"),
    ]

    N = dof_real.shape[0]
    frames = np.arange(N)

    n_pairs = len(ARM_PAIRS)
    fig, axes = plt.subplots(n_pairs, 1, figsize=(12, 3 * n_pairs), sharex=True)
    fig.suptitle("Arm Symmetric Joint Commands (deg)", fontsize=14, fontweight="bold")

    for ax, (l_idx, r_idx, joint_name) in zip(axes, ARM_PAIRS):
        l_data = dof_real[:, l_idx]
        r_data = dof_real[:, r_idx]

        ax.plot(frames, l_data, linewidth=1.8, label=f"left_{joint_name}")
        ax.plot(frames, r_data, linewidth=1.8, label=f"right_{joint_name}", linestyle="--")
        ax.plot(frames, -r_data, linewidth=0.8, alpha=0.35, linestyle=":", label=f"-right_{joint_name} (mirror ref)")

        ax.axhline(0, linewidth=0.6, linestyle="-")
        ax.set_ylabel("deg", fontsize=9)
        ax.set_title(joint_name, fontsize=10, loc="left")
        ax.legend(fontsize=8, loc="upper right", ncol=3)
        ax.grid(True, alpha=0.3)

        diff = np.abs(l_data + r_data)
        worst_frame = int(np.argmax(diff))
        ax.annotate(
            f"max|L+R|={diff[worst_frame]:.1f}° @f{worst_frame}",
            xy=(worst_frame, l_data[worst_frame]),
            xytext=(worst_frame + max(1, N // 20), l_data[worst_frame]),
            fontsize=7.5, color="darkorange",
            arrowprops=dict(arrowstyle="->", color="darkorange", lw=0.8),
        )

    axes[-1].set_xlabel("Frame", fontsize=10)
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    save_path = os.path.join(save_dir, "verifying_tmp.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[Plot] Saved arm symmetry figure to {save_path}")


if __name__ == "__main__":
    urdf_path = "data/Assembly/Assembly.SLDASM.urdf"
    data_path = "/tmp/robot_action.npy"
    # data_path = "input/motion_4.npy"
    # data_path = "input/robot_action.npy"
    output_path = "output/result.pkl"

    out_dir = os.path.dirname(output_path)
    joint_npy_path = os.path.join(out_dir, "robot_joint_cmd_frames.npy")
    joint_txt_path = os.path.join(out_dir, "robot_joint_cmd_frames.txt")

    motion = load_data(data_path)
    solver = H1PinkSolver(urdf_path)
    result = solver.process_motion(motion)

    os.makedirs(out_dir, exist_ok=True)
    joblib.dump(result, output_path)
    print(f"Saved to {output_path}")

    dof_real = np.asarray(result["dof_real"])
    np.save(joint_npy_path, dof_real)
    print(f"Saved joint cmd frames (npy) to {joint_npy_path}, shape={dof_real.shape}")

    with open(joint_txt_path, "w") as f:
        for i in range(dof_real.shape[0]):
            f.write(f"frame {i:06d}: " + " ".join([f"{v:.3f}" for v in dof_real[i]]) + "\n")
    print(f"Saved joint cmd frames (txt) to {joint_txt_path}")

    plot_arm_symmetry(dof_real, save_dir=out_dir)