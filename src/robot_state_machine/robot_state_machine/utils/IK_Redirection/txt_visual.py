import time
import numpy as np
import pinocchio as pin
import os

from pinocchio.visualize import MeshcatVisualizer

def load_txt_28d(txt_path: str) -> np.ndarray:
    """
    读取类似：
      frame 000000: -6.644 -9.836 ... (共28个)
    或者：
      -6.644 -9.836 ... (共28个)
    """
    rows = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            # 1) 去掉 "frame xxxx:" 之类的行头
            if ":" in line:
                line = line.split(":", 1)[1].strip()

            # 2) 支持逗号分隔
            line = line.replace(",", " ")

            parts = [p for p in line.split() if p]

            # 3) 有些文件末尾可能多了东西，这里严格要求 28
            if len(parts) != 28:
                raise ValueError(
                    f"第{line_no}行不是28个数：{len(parts)} -> {line[:120]}..."
                )

            rows.append([float(x) for x in parts])

    arr = np.array(rows, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 28:
        raise ValueError(f"期望 [N,28]，得到 {arr.shape}")
    return arr

def main():
    urdf_path = "data/Assembly/Assembly.SLDASM.urdf"
    txt_path  = "output/robot_joint_cmd_frames.txt"

    fps = 20.0
    dt = 1.0 / fps

    # 1) 读 txt（deg）
    dof_deg = load_txt_28d(txt_path)
    dof_rad = np.deg2rad(dof_deg)

    package_dirs = [os.path.abspath("./data/Assembly")]
    # 2) 建机器人模型（和你IK一致：FreeFlyer）
    robot = pin.RobotWrapper.BuildFromURDF(
        urdf_path,
        package_dirs=package_dirs,
        root_joint=pin.JointModelFreeFlyer()
    )
    model = robot.model
    data = robot.data
    visual_model = robot.visual_model
    collision_model = robot.collision_model

    # 3) 这 28 个关节名的顺序必须和输出 txt 的顺序一致
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
    if len(H1_JOINT_NAMES) != 28:
        raise ValueError("H1_JOINT_NAMES 必须是 28 个关节名（按txt列顺序）")
        
    # === 新增：不控制的关节集合 ===
    SKIP_JOINTS = {'waist_yaw_joint', 'waist_pitch_joint', 'waist_roll_joint'}
    # joint 名 -> joint id
    joint_name_to_id = {name: model.getJointId(name) for name in model.names}

    # === 修改：只挑“要控制”的关节，并记录它在txt里的列号 ===
    target_joint_ids = []
    target_cols = []  # dof_rad 的列索引
    for col, jn in enumerate(H1_JOINT_NAMES):
        if jn in SKIP_JOINTS:
            continue
        if jn not in joint_name_to_id:
            raise KeyError(f"URDF 里找不到 joint 名称: {jn}")
        target_joint_ids.append(joint_name_to_id[jn])
        target_cols.append(col)

    # 4) Meshcat 可视化
    viz = MeshcatVisualizer(robot.model, robot.collision_model, robot.visual_model)
    viz.initViewer(open=True)
    viz.loadViewerModel()  # 若URDF能找到mesh会显示网格；否则也能显示坐标系/连杆

    q0 = pin.neutral(model)

    print("Playing... (Ctrl+C 退出)")
    while True:
        for i in range(dof_rad.shape[0]):
            q = q0.copy()

            # === 修改：按 target_cols 去取对应列 ===
            for jid, col in zip(target_joint_ids, target_cols):
                idx_q = model.joints[jid].idx_q
                nq = model.joints[jid].nq
                if nq != 1:
                    raise RuntimeError(f"关节 {model.names[jid]} nq={nq}，只处理 nq=1。")
                q[idx_q] = dof_rad[i, col]

            viz.display(q)
            time.sleep(dt)

if __name__ == "__main__":
    main()