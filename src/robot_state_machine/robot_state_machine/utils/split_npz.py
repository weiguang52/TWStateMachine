import numpy as np
from pathlib import Path

def split_npz_simple(folder_path):
    folder = Path(folder_path)
    output = folder / "output"
    output.mkdir(exist_ok=True)
    
    counter = 0
    
    for npz_file in sorted(folder.glob("*.npz")):
        data = np.load(npz_file)
        for key in sorted(data.files):
            np.save(output / f"{counter}.npy", data[key])
            counter += 1
        print(f"已处理: {npz_file.name}")
    
    print(f"\n完成！共生成 {counter} 个.npy文件")

# 使用
split_npz_simple("/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/input")
