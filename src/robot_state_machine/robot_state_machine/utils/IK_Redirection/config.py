import torch
import numpy as np
# 配置参数
class H1Config:
    # DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    DEVICE = torch.device("cpu") # IK 通常在 CPU 上跑得很快，不需要 CUDA
    FACE_KEYPOINTS = ['nose', 'right_eye', 'left_eye', 'right_ear', 'left_ear']
    SMPL_BONE_ORDER = [
        "pelvis", "left_hip", "right_hip", "spine1", "left_knee", "right_knee", "spine2",
        "left_ankle", "right_ankle", "spine3", "left_foot", "right_foot", "neck",
        "left_collar", "right_collar", "head", "left_shoulder", "right_shoulder",
        "left_elbow", "right_elbow", "left_wrist", "right_wrist", "left_hand", "right_hand"
    ] + FACE_KEYPOINTS
    H1_NODE_NAMES = ['base_link', 'left_hip_linkage', 'left_thigh', 'left_knee_linkage', 
                     'left_calf', 'left_ankle', 'left_foot', 'right_hip_linkage',
                     'right_thigh', 'right_knee_linkage', 'right_calf', 'right_ankle', 'right_foot',
                    'waist', 'waist_gearbox', 'chest', 'left_shoulder_linkage', 'left_upper_arm',
                    'left_elbow_linkage', 'left_force_arm', 'left_hand', 'right_shoulder_linkage', 'right_upper_arm',
                    'right_elbow_linkage', 'right_force_arm', 'right_hand', 'neck', 'neck_linkage',
                    'head', 'left_ear', 'right_ear']
    # [CRITICAL] 物理关节顺序 (Legs First)
    H1_JOINT_NAMES = [
        # Left Leg (0-5)
        'left_hip_pitch_joint', 'left_hip_roll_joint', 'left_hip_yaw_joint', 
        'left_knee_pitch_joint', 'left_ankle_yaw_joint', 'left_ankle_pitch_joint',
        # Right Leg (6-11)
        'right_hip_pitch_joint', 'right_hip_roll_joint', 'right_hip_yaw_joint', 
        'right_knee_pitch_joint', 'right_ankle_yaw_joint', 'right_ankle_pitch_joint',
        # Waist (12-14)
        'waist_yaw_joint', 'waist_pitch_joint', 'waist_roll_joint',
        # Left Arm (15-19)
        'left_shoulder_pitch_joint', 'left_shoulder_roll_joint', 'left_shoulder_yaw_joint', 
        'left_elbow_pitch_joint', 'left_wrist_yaw_joint',
        # Right Arm (20-24)
        'right_shoulder_pitch_joint', 'right_shoulder_roll_joint', 'right_shoulder_yaw_joint', 
        'right_elbow_pitch_joint', 'right_wrist_yaw_joint',
        # Neck (25-27)
        'neck_yaw_joint', 'neck_roll_joint', 'neck_pitch_joint'
    ]
    # Pick List
    H1_PICK_NAMES = [
        "left_hip_linkage","left_calf", "left_foot", 
        "right_hip_linkage" ,'right_calf', 'right_foot',
        "left_upper_arm", "left_elbow_linkage", "left_hand", 
        "right_upper_arm", "right_elbow_linkage", "right_hand",
        "neck_linkage",'left_ear', 'right_ear'
    ]
    SMPL_PICK_NAMES = [
        "left_hip",  "left_knee", "left_ankle", 
        "right_hip", "right_knee", "right_ankle",
        "left_shoulder", "left_elbow", "left_hand", 
        "right_shoulder", "right_elbow", "right_hand", 
        "neck", 'left_ear','right_ear'
    ]
    
    TRACKING_PAIRS = [
        # 手臂
        ("left_upper_arm", "left_shoulder"),   
        ("right_upper_arm", "right_shoulder"),

        ("left_force_arm", "left_elbow"),   
        ("right_force_arm", "right_elbow"),

        ("left_hand", "left_wrist"),
        ("right_hand", "right_wrist"),
        
        # 腿部
        ("left_calf", "left_knee"),
        ("right_calf", "right_knee"),
        
        ("left_foot", "left_ankle"),  
        ("right_foot", "right_ankle"),

        ("right_thigh", "right_hip"),
        ("left_thigh", "left_hip"),

        # --- 头部 (解决头乱动) ---
        # ("neck_linkage", "neck"),
        # ("left_ear", "left_ear"),
        # ("right_ear", "right_ear"),
        # ("waist", "pelvis")
    ]

    STAND_JOINT_ANGLES = np.array([
        -0.0922, -0.1397, -0.0729, -0.4977, -0.0018,  0.    ,  0.251 ,  0.1775,
        0.1933, -0.7071,  0.0026, -0.    , -0.0917, -0.409 ,  0.0834,  0.1708,
        -0.4421,  0.1861, -0.6999,  0.    ,  0.1081,  0.3286, -0.1212,  0.7171,
        0.    , -0.1469, -0.12  , -0.1239
    ], dtype=np.float32)
    USER_DATA_DICT = dict(zip(H1_JOINT_NAMES, STAND_JOINT_ANGLES))

def load_data(data_path):
    entry_data = dict(np.load(open(data_path, "rb"), allow_pickle=True))
    if 'mocap_framerate' not in entry_data: return None
    framerate = entry_data['mocap_framerate']
    root_trans = entry_data['trans']
    pose_aa = np.concatenate([entry_data['poses'][:, :66], np.zeros((root_trans.shape[0], 6))], axis=-1)
    return {
        "pose_aa": pose_aa, 
        "gender": entry_data['gender'],
        "trans": root_trans, 
        "betas": entry_data['betas'], 
        "fps": framerate
    }
