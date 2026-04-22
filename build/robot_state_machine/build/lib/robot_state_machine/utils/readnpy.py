import numpy as np
from pathlib import Path

def npy_to_txt_fixed(folder_path, output_folder=None):
    """
    修复版本：处理包含对象数组的.npy文件
    """
    folder_path = Path(folder_path)
    
    if output_folder is None:
        output_folder = folder_path / "txt_output"
    else:
        output_folder = Path(output_folder)
    
    output_folder.mkdir(exist_ok=True)
    
    npy_files = sorted(folder_path.glob("*.npy"))
    print(f"找到 {len(npy_files)} 个.npy文件")
    
    for npy_file in npy_files:
        try:
            # 先尝试不允许pickle加载
            try:
                data = np.load(npy_file, allow_pickle=False)
            except ValueError:
                # 如果失败，允许pickle加载
                print(f"检测到对象数组，使用allow_pickle=True加载: {npy_file.name}")
                data = np.load(npy_file, allow_pickle=True)
            
            txt_file = output_folder / f"{npy_file.stem}.txt"
            
            # 处理不同类型的数据
            if data.dtype == 'object':
                # 对象数组，转换为字符串保存
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Object array, shape: {data.shape}\n")
                    if data.ndim == 0:
                        # 标量对象
                        f.write(str(data.item()) + '\n')
                    else:
                        # 多维对象数组
                        flat_data = data.flatten()
                        for item in flat_data:
                            f.write(str(item) + '\n')
            else:
                # 数值数组，正常保存
                if data.ndim == 1:
                    np.savetxt(txt_file, data, fmt='%.6f')
                elif data.ndim == 2:
                    np.savetxt(txt_file, data, fmt='%.6f')
                else:
                    with open(txt_file, 'w') as f:
                        f.write(f"# Original shape: {data.shape}\n")
                        np.savetxt(f, data.flatten(), fmt='%.6f')
            
            print(f"转换完成: {npy_file.name} -> {txt_file.name} (shape: {data.shape}, dtype: {data.dtype})")
            
        except Exception as e:
            print(f"转换失败: {npy_file.name} - {e}")
    
    print(f"\n完成！所有文件已保存到: {output_folder}")

# 使用
npy_to_txt_fixed("/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/input")
