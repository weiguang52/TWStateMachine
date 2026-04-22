# 三次样条插值，让逆解重定向后的动作序列满足导纳控制频率要求
import numpy as np
from scipy.interpolate import CubicSpline
import time
from typing import List, Dict, Tuple


class JointTrajectoryInterpolator:
    """
    关节轨迹三次样条插值器：适配规划层与导纳控制层的频率差异
    """
    def __init__(self, joint_names: List[str], planning_freq: float, admittance_freq: float):
        """
        初始化插值器
        :param joint_names: 关节名称列表（如["joint1", "joint2", ...]）
        :param planning_freq: 规划层发布频率 (Hz)
        :param admittance_freq: 导纳控制层发布频率 (Hz)
        """
        self.joint_names = joint_names
        self.num_joints = len(joint_names)
        self.planning_freq = planning_freq  # 规划层频率
        self.admittance_freq = admittance_freq  # 导纳层频率
        
        # 插值核心参数
        self.cs_list = []  # 每个关节对应的三次样条插值函数
        self.t_planning = None  # 规划层轨迹的时间戳
        self.t_admittance = None  # 导纳层需要的时间戳
        self.is_trajectory_loaded = False

    def load_planning_trajectory(self, joint_trajectory: Dict[str, List[float]]) -> None:
        """
        加载规划层发布的关节轨迹数据
        :param joint_trajectory: 字典格式，key=关节名，value=该关节的角度序列
        """
        # 校验输入轨迹的完整性
        for joint in self.joint_names:
            if joint not in joint_trajectory:
                raise ValueError(f"缺失关节 {joint} 的轨迹数据")
        
        # 生成规划层的时间戳（假设轨迹从t=0开始，按规划频率均匀分布）
        trajectory_length = len(joint_trajectory[self.joint_names[0]])
        self.t_planning = np.linspace(
            0, 
            (trajectory_length - 1) / self.planning_freq, 
            trajectory_length
        )
        
        # 为每个关节构建三次样条插值函数（自然边界条件：二阶导数为0）
        self.cs_list = []
        for joint in self.joint_names:
            joint_angles = np.array(joint_trajectory[joint])
            # CubicSpline：输入时间戳+角度，输出插值函数
            cs = CubicSpline(self.t_planning, joint_angles, bc_type='natural')
            self.cs_list.append(cs)
        
        # 生成导纳层需要的时间戳（覆盖规划轨迹的完整时间，按导纳频率均匀分布）
        max_t = self.t_planning[-1]
        self.t_admittance = np.arange(0, max_t + 1/self.admittance_freq, 1/self.admittance_freq)
        
        self.is_trajectory_loaded = True
        print(f"成功加载规划轨迹：{trajectory_length} 个点，时间跨度 {max_t:.2f}s")
        print(f"插值后导纳层轨迹：{len(self.t_admittance)} 个点，发布频率 {self.admittance_freq}Hz")

    def get_interpolated_joint_angle(self, t: float) -> Dict[str, float]:
        """
        获取指定时间点的插值后关节角度
        :param t: 目标时间（s）
        :return: 字典，key=关节名，value=插值后的角度（rad）
        """
        if not self.is_trajectory_loaded:
            raise RuntimeError("请先加载规划层轨迹数据")
        
        # 限制时间范围在轨迹内
        t_clamped = np.clip(t, self.t_planning[0], self.t_planning[-1])
        
        # 对每个关节插值
        joint_angles = {}
        for idx, joint in enumerate(self.joint_names):
            joint_angles[joint] = float(self.cs_list[idx](t_clamped))
        
        return joint_angles

    def get_full_interpolated_trajectory(self) -> Tuple[np.ndarray, Dict[str, List[float]]]:
        """
        获取完整的插值后轨迹
        :return: (导纳层时间戳数组, 插值后的关节角度字典)
        """
        if not self.is_trajectory_loaded:
            raise RuntimeError("请先加载规划层轨迹数据")
        
        full_trajectory = {}
        for idx, joint in enumerate(self.joint_names):
            full_trajectory[joint] = self.cs_list[idx](self.t_admittance).tolist()
        
        return self.t_admittance, full_trajectory


# -------------------------- 测试示例 --------------------------
def test_interpolator():
    # 1. 模拟规划层数据：6关节机器人，规划频率5Hz，生成10个轨迹点
    joint_names = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
    planning_freq = 5.0  # 规划层5Hz
    admittance_freq = 100.0  # 导纳控制层100Hz（高频）
    
    # 生成模拟的规划层关节轨迹（正弦曲线模拟关节运动）
    trajectory_length = 10
    t_planning_demo = np.linspace(0, (trajectory_length-1)/planning_freq, trajectory_length)
    joint_trajectory_demo = {}
    for i, joint in enumerate(joint_names):
        # 不同关节用不同频率的正弦曲线，模拟真实轨迹
        joint_trajectory_demo[joint] = np.sin(2 * np.pi * (i+1) * t_planning_demo).tolist()
    
    # 2. 初始化插值器并加载轨迹
    interpolator = JointTrajectoryInterpolator(joint_names, planning_freq, admittance_freq)
    interpolator.load_planning_trajectory(joint_trajectory_demo)
    
    # 3. 获取完整插值轨迹
    t_adm, full_traj = interpolator.get_full_interpolated_trajectory()
    
    # 4. 模拟导纳控制层按频率发布数据
    print("\n模拟导纳控制层发布插值后数据（前10个点）：")
    for i in range(10):
        t = t_adm[i]
        angles = interpolator.get_interpolated_joint_angle(t)
        # 模拟发布延迟（按导纳频率）
        time.sleep(1/admittance_freq)
        print(f"时间 {t:.3f}s | joint1: {angles['joint1']:.4f}rad | joint2: {angles['joint2']:.4f}rad")
    
    # 5. 验证插值效果（输出关键信息）
    print(f"\n插值验证：")
    print(f"规划层轨迹点数：{len(t_planning_demo)}")
    print(f"导纳层轨迹点数：{len(t_adm)}")
    print(f"插值后joint1第一个点：{full_traj['joint1'][0]:.4f}rad（与规划层一致）")
    print(f"插值后joint1最后一个点：{full_traj['joint1'][-1]:.4f}rad（与规划层一致）")


if __name__ == "__main__":
    # 安装依赖（若未安装）：pip install numpy scipy
    test_interpolator()