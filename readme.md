# TWStateMachine

基于 ROS 2 的机器人状态机与在线动作执行系统。

`TWStateMachine` 用于接收上游生成的动作结果，并将其转换为机器人可执行的关节指令；同时结合视觉、音频、点云与打断信号，实现在线动作切换、平滑过渡和下游控制发送。当前版本的核心主逻辑为 `main_node_online_v2.py`。

---

## 项目概述

本仓库面向机器人动作执行场景，提供以下能力：

- 在线读取上游动作数据
- 基于 IK 的动作重定向与插值处理
- 双线程双队列的动作调度与实时发送
- 基于 ROS 2 的多节点协同
- 支持视觉、音频、点云与打断信号输入
- 对接下游导纳控制与底层串口发送

---

## 工作空间结构

仓库采用标准 ROS 2 workspace 结构，`src` 下主要包含以下包：

```text
src/
├── robot_state_machine/
├── robot_msg/
└── robot_comm/
```

### `robot_state_machine`

主控制包，包含状态机主节点、联调测试节点、搜索/扫描/避障模块及相关工具代码。

### `robot_msg`

自定义消息与服务定义包。

### `robot_comm`

通信相关配套包，用于扩展外围数据采集与上报能力。

---

## 当前启动方式

当前系统通过以下 launch 文件启动：

```bash
ros2 launch robot_state_machine robot_state_machine.launch.py
```

该 launch 默认启动以下节点：

- `main_node` → `main_node_online_v2.py`
- `out_node` → `out_node.py`
- `send_node` → `utils/admittance_calculate.py`

---

## 核心节点说明

## 1. `main_node_online_v2.py`

当前版本的主状态机节点，也是本仓库的核心逻辑入口。

### 主要职责

- 监听上游动作文件（当前默认路径为 `/tmp/robot_action.npy`）
- 对动作数据执行 IK 重定向与插值
- 使用双线程双队列完成“动作处理”和“实时发送”解耦
- 接收视觉、音频、点云和打断信号
- 发布机器人关节控制指令

### 主流程

主节点可以概括为以下执行链路：

```text
上游动作文件 -> 动作读取 -> IK/插值 -> 命令帧生成 -> 实时发送 -> 下游控制
```

### 线程模型

系统采用双线程双队列结构：

#### 线程 A：动作处理线程

负责：

- 读取新动作数据
- 执行 IK 与插值
- 生成标准命令帧
- 将结果写入队列 A

#### 线程 B：实时发送线程

负责：

- 以固定频率从队列中取出命令帧
- 在低水位时从队列 A 批量补帧
- 将结果发送至下游控制链路
- 在打断场景下保持执行连续性

### 打断机制

当前版本支持在线打断与平滑切换，逻辑如下：

- 线程 B 在收到打断后，先复制当前剩余执行帧，保证旧动作不断流
- 线程 A 清理旧缓存并等待新动作
- 新动作到达后，线程 A 基于“旧动作末帧”和“新动作首帧”做过渡插值
- 最终实现平滑切换，而不是直接跳变

该机制适用于机器人在线重规划和实时动作替换场景。

---

## 2. `out_node.py`

联调与仿真测试节点，用于在没有完整外部系统时模拟输入信号。

### 主要作用

- 模拟视觉输入
- 模拟音频输入
- 模拟点云输入
- 模拟搜索命令
- 模拟打断信号

### 适用场景

- 本地联调
- 状态机逻辑验证
- 话题接口验证
- 无真实感知系统时的联通测试

---

## 3. `admittance_calculate.py`

该节点在 launch 中以 `send_node` 启动，承担下游导纳控制与底层发送职责。

### 主要职责

- 订阅主节点发布的关节命令
- 执行导纳控制与碰撞处理
- 对接底层控制协议
- 发布机器人反馈信息

可以将其理解为：

- `main_node_online_v2.py` 负责“生成要执行什么”
- `admittance_calculate.py` 负责“安全地发送到机器人底层”

---

## ROS 2 话题说明

### 主节点订阅

- `/search_command`
- `/vision_info`
- `/audio_info`
- `/point_cloud`
- `/interrupt_signal`

### 主节点发布

- `/current_state`
- `/joint_command`
- `/robot_feedback`

### 发送节点订阅 / 发布

- 订阅：`/joint_command`
- 发布：`/robot_feedback`

---

## 系统链路示意

```text
上游动作文件(/tmp/robot_action.npy)
        |
        v
main_node_online_v2.py
  - 动作读取
  - IK重定向
  - 插值与状态调度
  - 感知输入融合
  - 发布 /joint_command
        |
        v
admittance_calculate.py
  - 导纳控制
  - 碰撞处理
  - 下游协议发送
  - 发布 /robot_feedback

out_node.py
  - 用于仿真和联调
  - 模拟外部输入话题
```

### 最小可运行组合

如果仅需跑通主链路，最小组合如下：

- `main_node_online_v2.py`
- `admittance_calculate.py`

如果需要仿真联调，则再加入：

- `out_node.py`

---

## 上游动作输入

当前主节点默认从以下路径读取动作数据：

```bash
/tmp/robot_action.npy
```

如果上游系统负责生成动作，只需按照约定写入该文件，主节点即可自动加载并执行后续处理。

---

## 依赖环境

本项目基于 ROS 2 Python 包构建，`robot_state_machine` 为 `ament_python` 包。

主要 ROS 依赖包括：

- `rclpy`
- `std_msgs`
- `geometry_msgs`
- `sensor_msgs`

此外，运行过程中还依赖若干 Python 算法与工具库。

```bash
conda create -n gvhmr python=3.10
conda activate gvhmr
```

其中gvhmr为环境名称，可自修修改

```bash
pip install chumpy==0.70 --no-build-isolation
pip install pin-pink
```

然后手动 pip install 以下功能包：

```bash
pip install contourpy==1.3.2
```

```bash
pip install fvcore==0.1.5.post20221221
```

```bash
pip install gymnasium==1.2.3
```

```bash
pip install imageio==2.34.1
```

```bash
pip install lapx==0.9.4
```

```bash
pip install lightning==2.3.0
```

```bash
pip install torchmetrics==1.8.2
```

```bash
pip install matplotlib==3.10.8
```

```bash
pip install mediapy==1.2.5
```

```bash
pip install mujoco==3.4.0
```

```bash
pip install numpy-stl==3.2.0
```

```bash
pip install opencv-python==4.11.0.86
```

```bash
pip install pandas==2.3.3
```

```bash
pip install pycolmap==3.13.0
```

```bash
pip install qpsolvers==4.8.2
```

```bash
pip install quadprog==0.1.13
```

```bash
pip install scipy==1.15.3
```

```bash
pip install seaborn==0.13.2
```

```bash
pip install torchvision==0.18.0
```

```bash
pip install transforms3d==0.4.2
```

```bash
pip install trimesh==4.11.0
```

```bash
pip install ultralytics==8.2.42
```

```bash
pip install ultralytics-thop==2.0.18
```

```bash
pip install wis3d==1.0.1
```

然后执行环境配置文件中其他功能包的安装：

```bash
cd /home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/python_env_set
conda env create -f environment.yml
```

然后确定 CUDA 是否安装

```bash
python -c "import torch; print('PyTorch版本：', torch.__version__); print('CUDA可用：', torch.cuda.is_available())"
>> PyTorch版本： 2.3.0+cu121
>> CUDA可用： True
```

确定安装后，执行：

```bash
sudo apt update && sudo apt install -y gcc g++ libpng-dev libjpeg-dev
```

```bash
pip install pybind11 fvcore iopath numpy==2.2.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

安装PyTorch3D：

```bash
pip install "git+https://github.com/facebookresearch/pytorch3d.git" --no-build-isolation -i https://pypi.tuna.tsinghua.edu.cn/simple
```

安装 smplx

```bash
cd smplx-master/

pip install -e .
```

安装 smpl_sim

```bash
cd ..

cd SMPLSim-master/

pip install -e .
```

最后把numpy版本更改过来

```bash
pip uninstall numpy -y

pip install numpy==1.23.5
```

---

## 推荐使用方式

### 本地联调

适用于状态机逻辑验证与动作切换测试：

```bash
source install/setup.bash
ros2 launch robot_state_machine robot_state_machine.launch.py
```
