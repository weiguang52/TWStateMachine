import numpy as np
from pathlib import Path

def inspect_npz_files(folder_path):
    """
    检查.npz文件的内容和结构
    """
    folder = Path(folder_path)
    
    for npz_file in sorted(folder.glob("*.npz")):
        print(f"\n=== 检查文件: {npz_file.name} ===")
        
        try:
            data = np.load(npz_file, allow_pickle=True)
            
            print(f"键的数量: {len(data.files)}")
            print(f"所有键: {list(data.files)}")
            
            if len(data.files) == 0:
                print("⚠️  这个.npz文件没有任何键！")
            else:
                for i, key in enumerate(data.files):
                    array_data = data[key]
                    print(f"\n键 {i+1}: '{key}'")
                    print(f"  形状: {array_data.shape}")
                    print(f"  数据类型: {array_data.dtype}")
                    print(f"  大小: {array_data.size}")
                    
                    # 显示前几个元素
                    if array_data.size > 0:
                        if array_data.ndim == 0:
                            print(f"  值: {array_data.item()}")
                        else:
                            flat_data = array_data.flatten()
                            preview = flat_data[:5] if len(flat_data) > 5 else flat_data
                            print(f"  前几个值: {preview}")
            
            data.close()
            
        except Exception as e:
            print(f"❌ 无法读取文件: {e}")

# 检查当前目录的.npz文件
inspect_npz_files("/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/input")
