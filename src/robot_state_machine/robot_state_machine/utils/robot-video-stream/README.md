# robot-video-stream

**云端机器人视频流中转服务** ：本项目是一个基于 **ZeroMQ (ZMQ)** 的轻量级视频流传输通道。它主要部署在云端，作为**视频中转代理 (Broker)** ，负责接收端侧机器人的实时视频流，并将其以 **PUB-SUB** 模式广播给云端的 AI 模型、动作规划等其他业务。

## 📂 项目结构

**Plaintext**

```
.
├── cloud-broker.py         # [核心服务] 云端视频中转代理，需在云服务器长期运行
├── config.yaml             # [配置文件] 全局网络与参数配置
├── requirements.txt        # 依赖包列表
├── utils/                  # 工具模块
│   └── config.py           # 配置加载器
├── examples/               # [开发示例] 供机器人端和业务端参考
│   ├── robot-producer.py   # 机器人端推流代码示例 (Producer)
│   └── cloud-consumer.py   # 云端业务方拉流代码示例 (Consumer)
└── README.md               # 项目说明文档
```

## 🏗 架构说明

本项目采用 **PUB-SUB-PROXY** 模式，实现机器人与业务逻辑的完全解耦：

**Code snippet**

```
graph LR
    subgraph "Robot Side (Producer)"
        R1[Robot A] -- TCP:5555 --> B
        R2[Robot B] -- TCP:5555 --> B
    end

    subgraph "Cloud Server"
        B((Cloud Broker))
    end

    subgraph "Cloud Business (Consumer)"
        B -- TCP:5556 --> AI[AI Model / VLM]
        B -- TCP:5556 --> WEB[Web Backend]
        B -- TCP:5556 --> DEV[Developer Monitor]
    end

    style B fill:#f96,stroke:#333,stroke-width:2px
```

* **Robot Producer** : 采集图像 -> JPEG 压缩 -> ZMQ 推送。
* **Cloud Broker** : 监听 `5555` 端口接收数据，通过 `5556` 端口广播数据。
* **Cloud Consumer** : 订阅 `5556` 端口，获取特定机器人的实时视频帧。

---

## 🚀 快速开始

### 1. 环境安装

在云端服务器和本地开发机上均需安装依赖：

**Bash**

```
pip install -r requirements.txt
```

### 2. 部署云端服务 (Ops / Cloud Dev)

1. 修改 `config.yaml` 中的网络配置（通常云端监听 `0.0.0.0` 即可）。
2. 启动中转服务：

**Bash**

```
# 建议使用 systemd 或 docker 在后台运行
python cloud-broker.py
```

> **注意** ：请务必在云服务器的安全组/防火墙中放行 **TCP 5555** (入站) 和 **TCP 5556** (出站/内网) 端口。

### 3. 机器人接入 (Robot Dev)

机器人端开发请参考 `examples/robot-producer.py`。

**核心逻辑：**

* 读取 `config.yaml` 中的云端 IP。
* 使用 ZMQ `PUB` Socket 连接云端 `5555` 端口。
* 发送 Multipart 消息：`[Robot_ID, JPEG_Data]`。

### 4. 业务方接入 (AI / Web Dev)

AI 模型或后台开发请参考 `examples/cloud-consumer.py`。

**核心逻辑：**

* 使用 ZMQ `SUB` Socket 连接云端 `5556` 端口（如果是内网通信，延迟极低）。
* 订阅特定机器人的 Topic（即 Robot ID），或订阅 `""` 接收所有机器人的流。

---

## ⚙️ 配置说明 (`config.yaml`)

**YAML**

```
network:
  broker_ip: "127.0.0.1"   # 机器人连接的目标IP (部署时请改为云端公网IP)
  robot_in_port: 5555      # 机器人推流端口
  client_out_port: 5556    # 业务方订阅端口

robot:
  id: "robot_alpha"        # 机器人唯一标识 (作为 Topic)
  camera:
    width: 640             # 推荐分辨率
    height: 480
    fps: 5                 # 推荐帧率 (AI场景 3-5 FPS 足够)
  encoding:
    quality: 80            # JPEG 压缩质量 (1-100)
```

## 📡 通信协议

如果你不使用 Python，也可以通过标准 ZMQ 库接入。通信协议如下：

* **Socket 类型** :
* 推流端: `PUB`
* 拉流端: `SUB`
* **消息格式** : ZMQ Multipart Message (2 帧)

| **帧序号**  | **内容含义** | **数据类型** | **说明**                            |
| ----------------- | ------------------ | ------------------ | ----------------------------------------- |
| **Frame 1** | **Topic**    | `bytes`          | 机器人的唯一 ID (例如 `b"robot_alpha"`) |
| **Frame 2** | **Payload**  | `bytes`          | 标准 JPEG 图片二进制流                    |

## 📊 性能参考

在推荐配置 (640x480, 5 FPS, MJPEG Q=80) 下：

* **单机带宽** : 约 1.5 Mbps ~ 2.5 Mbps (上行)
* **端到端延迟** : < 100ms (取决于网络抖动)
* **丢包策略** : 实时性优先。当网络拥堵时，Broker 和 Robot 会自动丢弃旧帧，确保 Consumer 永远拿到最新画面。

---

## 🛠 常见问题

**Q: 为什么 Consumer 收不到数据？**

A: 首先检查以下两项：

1. 检查云端防火墙是否放行 `5555` 和 `5556`。
2. 检查 `config.yaml` 中的 `broker_ip` 是否正确（机器人端需填公网 IP，云端本地测试填 `127.0.0.1`）。

**Q: 画面有延迟怎么办？**

A: 本项目默认开启了低水位线 (`SNDHWM=2`, `RCVHWM=1`) 和 `CONFLATE` 模式。如果仍有延迟，请检查 Robot 端 CPU 是否过载，或网络上行带宽是否跑满。

**Q: 如何区分多台机器人？**

A: 修改 `config.yaml` 中的 `robot.id`。Consumer 可以通过 `socket.setsockopt_string(zmq.SUBSCRIBE, "robot_id")` 来过滤特定机器人的数据。
