import sys
sys.path.insert(0, '/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection')  # 根据实际路径调整
import numpy as np
import os
import sys
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
sys.path.append(os.getcwd())
stand_joint_angles = np.array([
    -0.0922, -0.1397, -0.0729, -0.4977, -0.0018,  0.    ,  0.251 ,  0.1775,
     0.1933, -0.7071,  0.0026, -0.    , -0.0917, -0.409 ,  0.0834,  0.1708,
    -0.4421,  0.1861, -0.6999,  0.    ,  0.1081,  0.3286, -0.1212,  0.7171,
     0.    , -0.1469, -0.12  , -0.1239
], dtype=np.float32)
USER_JOINT_NAMES = [
    # Left Leg
    'left_hip_pitch_joint', 'left_hip_roll_joint', 'left_hip_yaw_joint', 
    'left_knee_pitch_joint', 'left_ankle_yaw_joint', 'left_ankle_pitch_joint',
    # Right Leg
    'right_hip_pitch_joint', 'right_hip_roll_joint', 'right_hip_yaw_joint', 
    'right_knee_pitch_joint', 'right_ankle_yaw_joint', 'right_ankle_pitch_joint',
    # Waist
    'waist_yaw_joint', 'waist_pitch_joint', 'waist_roll_joint',
    # Left Arm
    'left_shoulder_pitch_joint', 'left_shoulder_roll_joint', 'left_shoulder_yaw_joint', 
    'left_elbow_pitch_joint', 'left_wrist_yaw_joint',
    # Right Arm
    'right_shoulder_pitch_joint', 'right_shoulder_roll_joint', 'right_shoulder_yaw_joint', 
    'right_elbow_pitch_joint', 'right_wrist_yaw_joint',
    # Neck
    'neck_yaw_joint', 'neck_roll_joint', 'neck_pitch_joint'
]
user_data_dict = dict(zip(USER_JOINT_NAMES, stand_joint_angles))
class H1PinkSolver:
    def __init__(self, urdf_path):
        # 初始化 Pinocchio 模型
        self.robot = pin.RobotWrapper.BuildFromURDF(urdf_path, package_dirs=[os.path.dirname(urdf_path)], root_joint=pin.JointModelFreeFlyer())
        self.model = self.robot.model
        self.data = self.robot.data
        self.q_ref = pin.neutral(self.model) 
        for name, value in user_data_dict.items():
            if self.model.existJointName(name):
                # 获取该关节在 q 向量中的起始索引
                joint_id = self.model.getJointId(name)
                q_idx = self.model.joints[joint_id].idx_q
                
                # 赋值
                self.q_ref[q_idx] = value
                # print(f"映射成功: {name} -> Index {q_idx} = {value}")
            else:
                print(f"⚠️ 警告: URDF 中找不到关节 {name}，已忽略")
        self.configuration = pink.Configuration(self.model, self.data, self.q_ref)
        # 初始化 SMPL 模型 (用于获取 Target)
        self.smpl_model = smplx.create(
            model_path='/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data', model_type='smpl', gender='neutral', 
            use_hands=False, use_feet_keypoints=False, batch_size=1
        )
        # 加载 Scale 和 Shape 参数
        self.shape_new, self.scale, self.off = joblib.load("/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data/Assembly/shape_optimized_smplx_v1.pkl")
        self.shape_new = self.shape_new.cpu() # 移回 CPU
        self.scale = self.scale.cpu()
        # 定义 Pink Tasks
        self.tasks = []
        self.ik_tasks = {} # 存储 Task 句柄以便后续更新 Target
        # [Task A] 锁死盆骨 
        self.pelvis_task = pink.tasks.FrameTask("base_link", position_cost=1.0, orientation_cost=20.0)
        self.pelvis_task.set_target(pin.SE3.Identity()) # 目标：原点，无旋转
        self.tasks.append(self.pelvis_task)
        # [Task B] 四肢追踪 
        # [Task B] 多点追踪
        for link_name, smpl_name in H1Config.TRACKING_PAIRS:
            # 默认权重
            pos_cost = 1.0
            rot_cost = 0.0
            
            # --- 针对不同部位调整权重 ---
            
            # 1. 手和脚 (End Effectors)：必须精准
            if "hand" in link_name or "foot" in link_name:
                pos_cost = 10.0  # 提高位置权重
                rot_cost = 0.0   # 旋转通常不追，靠手腕关节自己解算
            
            # 2. 膝盖和手肘 (Middle Joints)：主要用于引导方向
            elif "elbow" in link_name or "calf" in link_name:
                pos_cost = 1.0   # 权重低一点，允许有误差（因为臂长不一样）
                rot_cost = 0.0
            
            # 3. 头部/脖子：主要追旋转，位置次要
            elif "neck" in link_name or "ear" in link_name:
                pos_cost = 2.0   # 位置不重要，跟着脊柱走
                rot_cost = 0.1   # 关键：旋转要跟住！让头别乱歪
            elif "waist" in link_name:
                pos_cost = 1.0
                rot_cost = 0.1
            
            # 创建任务
            if self.model.existFrame(link_name):
                task = pink.tasks.FrameTask(link_name, position_cost=pos_cost, orientation_cost=rot_cost)
                self.tasks.append(task)
                self.ik_tasks[smpl_name] = task
            else:
                print(f"跳过: URDF 中找不到 Link [{link_name}]")
        # [Task C] 姿态保持 
        # 当没有目标时，尽量保持站立姿态，避免鬼畜
        self.posture_task = pink.tasks.PostureTask(self.model)
        self.posture_task.set_target(self.q_ref)
        self.posture_task.cost = 0.05 # 权重很低，作为软约束
        self.tasks.append(self.posture_task)
        # 获取 SMPL 索引
        self.smpl_indices = {name: H1Config.SMPL_BONE_ORDER.index(name) for _, name in H1Config.TRACKING_PAIRS}

    def _apply_sim2real_offsets(self, dof_deg):
        flip_list = [
            'left_elbow_joint', 
            'waist_roll_joint',
            'waist_yaw_joint',
            'left_hip_roll_joint',
            'left_ankle_pitch_joint'
        ]
        
        for name in flip_list:
            search_name = name
            if name == 'left_elbow_joint': search_name = 'left_elbow_pitch_joint'
            if name == 'right_elbow_joint': search_name = 'right_elbow_pitch_joint'

            if search_name in H1Config.H1_JOINT_NAMES:
                idx = H1Config.H1_JOINT_NAMES.index(search_name)
                dof_deg[..., idx] *= -1

        adjustments = {
            'left_shoulder_roll_joint': -90,
            'right_shoulder_roll_joint': +90,
            'left_elbow_joint': 90,   
            'right_elbow_joint': -90  
        }
        
        for name, delta in adjustments.items():
            search_name = name
            if name == 'left_elbow_joint': search_name = 'left_elbow_pitch_joint'
            if name == 'right_elbow_joint': search_name = 'right_elbow_pitch_joint'

            if search_name in H1Config.H1_JOINT_NAMES:
                idx = H1Config.H1_JOINT_NAMES.index(search_name)
                dof_deg[..., idx] += delta
        
        # 全局 Offset
        dof_deg += 160

    def process_motion(self, amass_data):
        start_time = time.time()
        # 降采样
        skip = int(amass_data['fps'] // 20)
        pose_aa_np = amass_data['pose_aa'][::skip, :66]
        N = pose_aa_np.shape[0]
        # SMPL Forward (批量计算所有 Target)
        trans = torch.zeros((N, 3)) # 保持位移为0
        pose_aa_torch = torch.from_numpy(np.concatenate((pose_aa_np[:, 3:66], np.zeros((N, 6))), axis=-1)).float()
        # 如果不加这个，SMPL 生成的目标点可能是躺着的
        rotvec = sRot.from_quat([0.5, 0.5, 0.5, 0.5]).as_rotvec()
        global_orient = torch.from_numpy(np.tile(rotvec, (N, 1))).float()
        # root rot 固定
        # global_orient = torch.zeros((N, 3)).float() 
        shape_expanded = self.shape_new.repeat(N, 1)
        print("Running SMPL Forward...")
        with torch.no_grad():
            output = self.smpl_model(body_pose=pose_aa_torch, global_orient=global_orient, betas=shape_expanded)
            smpl_joints = output.joints
            root_pos = smpl_joints[:, 0].unsqueeze(1).expand(-1, 29, -1)
            smpl_joints_target = (smpl_joints - root_pos) * self.scale.cpu() + root_pos
            smpl_joints_target = smpl_joints_target - root_pos
        # --- IK 求解循环 ---
        dt = 0.05 # 20fps -> 0.05s
        solver = pink.solve_ik
        dof_results = []
        h1_cartesian_seq = []
        target_node_names = H1Config.H1_NODE_NAMES
        print(f"Starting IK for {N} frames...")
        for i in range(N):
            # 获取当前帧 SMPL 的根节点绝对位置 (作为回缩的参考中心)
            current_smpl_root_abs = smpl_joints_target[i, 0].numpy()
            # 遍历更新任务
            for smpl_name, task in self.ik_tasks.items():
                idx = self.smpl_indices[smpl_name]
                # 获取该关节原始的绝对目标坐标
                target_pos_abs = smpl_joints_target[i, idx].numpy() 
                # 判断是否是手部/手臂 (容易过伸的部位)
                is_arm = "hand" in smpl_name or "wrist" in smpl_name or "elbow" in smpl_name
                if is_arm:
                    # === 核心防抖逻辑 ===
                    # 计算向量：从 SMPL根 -> SMPL手
                    vec_root_to_target = target_pos_abs - current_smpl_root_abs
                    # 缩放向量：缩短 5% (保留 95% 的长度)
                    vec_safe = vec_root_to_target * 0.95 
                    # 计算新的安全绝对坐标
                    final_target_pos = current_smpl_root_abs + vec_safe
                else:
                    # 脚部、头部等不需要缩放，直接追绝对坐标
                    final_target_pos = target_pos_abs
                # 构造目标并设置
                target_transform = pin.SE3(np.eye(3), final_target_pos)
                task.set_target(target_transform)
            # 求解 IK
            velocity = solver(self.configuration, self.tasks, dt, solver="quadprog")
            # 更新状态
            self.configuration.integrate_inplace(velocity, dt)
            # 保存结果 (q 包含了 root pose + joints)
            # Pinocchio 的 q 结构: [root_pos(3), root_quat(4), joint_1, joint_2 ...]
            curr_q = self.configuration.q
            if self.model.nq > len(H1Config.H1_JOINT_NAMES):
                # 假设是 Floating Base (7 + 19)
                joints_rad = curr_q[7:] 
            else:
                joints_rad = curr_q           
            dof_results.append(joints_rad.copy())

            # [新增] 2. 提取当前帧 H1 机器人各个关键点的三维坐标
            current_frame_pos = []
            for link_name in target_node_names:
                if self.model.existFrame(link_name):
                    # 获取该 Link 在世界坐标系下的变换矩阵 (SE3)，并只取平移部分 (translation)
                    pos = self.configuration.get_transform_frame_to_world(link_name).translation.copy()
                    current_frame_pos.append(pos)
                else:
                    current_frame_pos.append(np.zeros(3)) # 防止报错补0
            
            h1_cartesian_seq.append(current_frame_pos)
        dof_results = np.array(dof_results)
        print("Applying Gaussian Smoothing...")
        # sigma 控制平滑程度
        dof_results = gaussian_filter1d(dof_results, sigma=1.5, axis=0)
        # --- 后处理 (Sim2Real Offset) ---
        print("Applying Sim2Real Offsets...")
        pin_names = [self.model.names[i] for i in range(self.model.njoints)]
        sim_dof_deg = np.zeros((N, 28)) # 28个关节
        # 遍历 URDF 里的所有关节
        for pin_idx, name in enumerate(pin_names):
            if name in H1Config.H1_JOINT_NAMES:
                target_idx = H1Config.H1_JOINT_NAMES.index(name)
                # Pinocchio q索引查找
                q_idx = self.model.joints[pin_idx].idx_q
                if q_idx >= 7: # 跳过 Root
                    val = dof_results[:, q_idx - 7] 
                    sim_dof_deg[:, target_idx] = np.rad2deg(val)
        real_dof_deg = sim_dof_deg.copy()
        self._apply_sim2real_offsets(real_dof_deg)
        print(f"Total time: {time.time() - start_time:.2f}s")
        return {
            "root_trans_offset": np.zeros((N, 3)), # 根节点固定为 0
            "dof": np.deg2rad(sim_dof_deg),      # 存弧度用于可视化
            "dof_real": real_dof_deg,             # 存角度用于真机
            "root_rot": np.tile([0, 0, 0, 1], (N, 1)), # 根节点无旋转
            "fps": 20,
            
            # debug 可视化用
            "smpl_joints_target": smpl_joints_target.numpy(),
            "h1_joint_pos": np.array(h1_cartesian_seq)
        }

    def process_cloud_action_to_joint_angles(
        self,
        amass_data_or_path, 
        urdf_path="/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data/Assembly/Assembly.SLDASM.urdf",
        start_frame=None,
        end_frame=None
    ):
        """
        将AMASS数据处理成机器人可执行的关节角度命令
        
        Args:
            amass_data_or_path: str 或 dict
                - str: .npz文件路径
                - dict: AMASS数据字典 {
                    'trans': [N, 3],
                    'poses': [N, 66], 
                    'betas': [10],
                    'gender': str,
                    'mocap_framerate': int
                }
            
            urdf_path: 机器人URDF文件路径
            
            start_frame: int, optional
                起始帧索引（包含），用于截取部分帧
            
            end_frame: int, optional  
                结束帧索引（不包含），用于截取部分帧
        
        Returns:
            dict: {
                'dof_real': np.array([M, 28]),  # 关节角度（度），M为截取后的帧数
                'dof': np.array([M, 28]),       # 关节角度（弧度），用于可视化
                'fps': int,                      # 帧率 (20fps)
                'num_frames': int,               # 总帧数 M
                'root_trans_offset': np.array([M, 3]),  # 根节点位移
                'root_rot': np.array([M, 4]),    # 根节点旋转（四元数）
            }
        """
        try:
            # ========== 1. 加载或使用AMASS数据 ==========
            if isinstance(amass_data_or_path, str):
                # 从文件加载
                amass_data = config.load_data(amass_data_or_path)
                if amass_data is None:
                    raise ValueError(f"Failed to load AMASS data from {amass_data_or_path}")
            elif isinstance(amass_data_or_path, dict):
                # 直接使用传入的字典
                amass_data = amass_data_or_path
            else:
                raise TypeError(f"amass_data_or_path must be str or dict, got {type(amass_data_or_path)}")
            
            # 验证必需字段
            required_keys = ['trans', 'poses', 'betas', 'gender']
            for key in required_keys:
                if key not in amass_data:
                    raise ValueError(f"Missing required key: {key}")
            
            # ========== 2. 截取帧（如果需要）==========
            original_num_frames = len(amass_data['trans'])
            
            if start_frame is not None or end_frame is not None:
                # 处理默认值
                start_frame = start_frame if start_frame is not None else 0
                end_frame = end_frame if end_frame is not None else original_num_frames
                
                # 边界检查
                start_frame = max(0, min(start_frame, original_num_frames))
                end_frame = max(start_frame, min(end_frame, original_num_frames))
                
                # 截取数据
                amass_data_cut = {
                    'trans': amass_data['trans'][start_frame:end_frame],
                    'poses': amass_data['poses'][start_frame:end_frame],
                    'betas': amass_data['betas'],  # 形状参数不需要截取
                    'gender': amass_data['gender'],
                    'mocap_framerate': amass_data.get('mocap_framerate', 30)
                }
                
                print(f"[IK] 截取帧: {start_frame}~{end_frame-1} (共{end_frame-start_frame}帧，原始{original_num_frames}帧)")
            else:
                amass_data_cut = amass_data
            
            # ========== 3. 初始化IK求解器 ==========
            # solver = H1PinkSolver(urdf_path)
            
            # ========== 4. 处理动作（IK求解）==========
            result = self.process_motion(amass_data_cut)
            
            # ========== 5. 返回结果 ==========
            # result包含完整的调试信息，我们返回必需的字段
            return {
                'dof_real': result['dof_real'],           # [M, 28] 度数，用于真机
                'dof': result['dof'],                      # [M, 28] 弧度，用于可视化
                'fps': result['fps'],                      # 20
                'num_frames': len(result['dof_real']),    # M
                'root_trans_offset': result['root_trans_offset'],  # [M, 3]
                'root_rot': result['root_rot'],            # [M, 4]
            }
        
        except Exception as e:
            print(f"[IK] Error processing cloud action: {e}")
            import traceback
            traceback.print_exc()
            raise


    def batch_process_npz_files(self,npz_files, urdf_path, frames_per_batch=20):
        """
        批量处理多个.npz文件（用于离线测试）
        
        Args:
            npz_files: list of str, .npz文件路径列表
            urdf_path: 机器人URDF路径
            frames_per_batch: 每批处理的文件数
        
        Yields:
            dict: 每批处理结果
        
        Example:
            npz_files = ['data/3.npz'] * 10  # 10个相同的文件
            for result in batch_process_npz_files(npz_files, urdf_path, frames_per_batch=5):
                print(f"Processed {result['num_frames']} frames")
        """
        total_files = len(npz_files)
        
        for batch_start in range(0, total_files, frames_per_batch):
            batch_end = min(batch_start + frames_per_batch, total_files)
            batch_files = npz_files[batch_start:batch_end]
            
            print(f"\n[批处理] 处理文件 {batch_start}~{batch_end-1} (共{len(batch_files)}个)")
            
            # 加载并组合所有文件
            trans_list = []
            poses_list = []
            
            for npz_file in batch_files:
                data = np.load(npz_file, allow_pickle=True)
                # 假设每个文件包含完整的动作序列，我们取第一帧
                # 如果需要取全部帧，可以修改这里
                trans_list.append(data['trans'][0])  # [3]
                poses_list.append(data['poses'][0])  # [66]
            
            # 组合成批次
            first_data = np.load(batch_files[0], allow_pickle=True)
            amass_batch = {
                'trans': np.stack(trans_list, axis=0),      # [batch_size, 3]
                'poses': np.stack(poses_list, axis=0),      # [batch_size, 66]
                'betas': first_data['betas'],
                'gender': str(first_data['gender']),
                'mocap_framerate': int(first_data['mocap_framerate'])
            }
            
            # 处理这一批
            result = self.process_cloud_action_to_joint_angles(amass_batch, urdf_path)
            
            yield result
    
if __name__ == "__main__":
    urdf_path = "data/Assembly/Assembly.SLDASM.urdf"
    data_path = "input/kick_example.npy"
    output_path = "output/3_pink.pkl"
    
    amass_data = config.load_data(data_path)
    if amass_data is not None:
        solver = H1PinkSolver(urdf_path)
        result = solver.process_motion(amass_data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        joblib.dump(result, output_path)
        print(f"Saved to {output_path}")
    else:
        print("Failed to load Amass Data")

