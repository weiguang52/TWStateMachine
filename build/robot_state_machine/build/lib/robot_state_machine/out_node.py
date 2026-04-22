#!/usr/bin/env python3
"""
外部模拟节点 - 双线程架构测试版 + 打断信号测试
用于测试main_node.py的双线程架构和打断策略
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import time
import json
import random
import numpy as np

class OutNode(Node):
    def __init__(self):
        super().__init__('out_node')
        
        # ========== 话题发布 ==========
        self.search_cmd_pub = self.create_publisher(Bool, '/search_command', 10)
        self.vision_pub = self.create_publisher(String, '/vision_info', 10)
        self.audio_pub = self.create_publisher(String, '/audio_info', 10)
        self.point_cloud_pub = self.create_publisher(String, '/point_cloud', 10)
        
        # ========== 新增：打断信号发布 ==========
        self.interrupt_pub = self.create_publisher(Bool, '/interrupt_signal', 10)
        
        # ========== 模拟参数 ==========
        self.simulation_time = 0.0
        self.target_visible = False
        self.obstacle_present = False
        self.search_command_sent = False
        
        # 目标位置（用于模拟跟随）
        self.target_angle = 0.0  # 目标相对角度（度）
        self.target_distance = 1.5  # 目标距离（米）
        self.target_moving = False  # 目标是否在移动
        
        # ========== 打断测试参数 ==========
        self.interrupt_count = 0  # 已发送的打断信号数量
        self.last_interrupt_time = 0.0  # 上次发送打断信号的时间
        
        # ========== 测试场景选择 ==========
        # 可选场景：
        # "normal" - 正常执行（无干扰）
        # "follow" - 跟随测试（目标移动）
        # "search" - 搜寻测试
        # "obstacle" - 避障测试
        # "interrupt" - 打断信号测试（新增）
        # "combined" - 综合测试
        # "interrupt_stress" - 打断压力测试（新增）
        self.test_scenario = "normal"
        
        # ========== 定时器 ==========
        # 主循环：每0.1秒更新一次
        self.timer = self.create_timer(0.1, self.simulation_loop)
        
        # 高频传感器数据发布：每0.01秒（100Hz）
        self.sensor_timer = self.create_timer(0.01, self.publish_sensor_data)
        
        self.get_logger().info('='*70)
        self.get_logger().info('外部模拟节点启动（双线程架构测试版 + 打断信号）')
        self.get_logger().info(f'测试场景: {self.test_scenario}')
        self.get_logger().info('='*70)
        
        self._print_scenario_description()
    
    def _print_scenario_description(self):
        """打印场景描述"""
        scenarios = {
            "normal": """
正常执行场景：
  - 持续发布传感器数据
  - 无目标、无障碍物
  - 测试线程A正常处理云端动作
            """,
            "follow": """
跟随测试场景：
  - 0-5s: 无目标
  - 5s: 目标出现在前方
  - 10s: 目标开始向右移动（模拟跟随）
  - 20s: 目标停止移动
  - 25s: 目标消失
  - 30s: 目标再次出现
            """,
            "search": """
搜寻测试场景：
  - 0-3s: 无目标
  - 3s: 发送搜寻命令
  - 5s: 检测到声音（DOA方向）
  - 8s: 目标出现（验证搜寻成功）
  - 15s: 目标消失
  - 18s: 再次发送搜寻命令
            """,
            "obstacle": """
避障测试场景：
  - 0-5s: 正常执行
  - 5s: 前方出现障碍物（0.6米）
  - 10s: 障碍物消失
  - 15s: 侧方出现障碍物
  - 20s: 障碍物消失
            """,
            "interrupt": """
打断信号测试场景：
  - 0-3s: 正常执行，线程A加载数据
  - 3s: 发送第1次打断信号（测试基本打断功能）
  - 8s: 目标出现，进入跟随状态
  - 12s: 发送第2次打断信号（测试跟随状态下的打断）
  - 18s: 目标消失
  - 20s: 发送第3次打断信号（测试无目标状态下的打断）
  - 25s: 目标再次出现
  - 28s: 发送第4次打断信号（测试连续打断）
  - 30s: 发送第5次打断信号（测试快速连续打断）
  - 35s: 测试结束
            """,
            "interrupt_stress": """
打断压力测试场景：
  - 0-2s: 正常执行
  - 2-10s: 每2秒发送一次打断信号（高频打断）
  - 10-15s: 目标出现，跟随状态下高频打断
  - 15-20s: 每1秒发送一次打断信号（极高频打断）
  - 20-25s: 目标消失，继续高频打断
  - 25-30s: 恢复正常，测试系统稳定性
            """,
            "combined": """
综合测试场景（含打断）：
  - 0-5s: 正常执行，无目标
  - 5s: 目标出现，进入跟随状态
  - 8s: 发送打断信号（测试跟随中打断）
  - 10s: 目标移动（测试跟随命令合并）
  - 15s: 出现障碍物（测试避障）
  - 17s: 发送打断信号（测试避障中打断）
  - 18s: 障碍物消失
  - 20s: 目标消失
  - 23s: 发送搜寻命令
  - 25s: 检测到声音
  - 26s: 发送打断信号（测试搜寻中打断）
  - 28s: 目标再次出现
  - 32s: 发送最后一次打断信号
  - 35s: 目标消失，恢复正常执行
            """
        }
        
        desc = scenarios.get(self.test_scenario, "未知场景")
        self.get_logger().info(desc)
    
    def simulation_loop(self):
        """模拟主循环（慢速，控制场景变化）"""
        self.simulation_time += 0.1
        t = self.simulation_time
        
        # 根据场景执行不同的逻辑
        if self.test_scenario == "normal":
            self._normal_scenario(t)
        elif self.test_scenario == "follow":
            self._follow_scenario(t)
        elif self.test_scenario == "search":
            self._search_scenario(t)
        elif self.test_scenario == "obstacle":
            self._obstacle_scenario(t)
        elif self.test_scenario == "interrupt":
            self._interrupt_scenario(t)
        elif self.test_scenario == "interrupt_stress":
            self._interrupt_stress_scenario(t)
        elif self.test_scenario == "combined":
            self._combined_scenario(t)
    
    def publish_sensor_data(self):
        """高频发布传感器数据（100Hz）"""
        # 发布视觉、听觉、点云数据
        self.publish_vision_info()
        self.publish_audio_info()
        self.publish_point_cloud()
    
    # ========================================================================
    # 打断信号发送函数
    # ========================================================================
    
    def send_interrupt_signal(self, reason="测试"):
        """发送打断信号"""
        self.interrupt_count += 1
        self.last_interrupt_time = self.simulation_time
        
        interrupt_msg = Bool()
        interrupt_msg.data = True
        self.interrupt_pub.publish(interrupt_msg)
        
        self.get_logger().info(
            f'\n🚨 [模拟-打断] >>> 发送第{self.interrupt_count}次打断信号 ({reason}) <<<'
        )

        time.sleep(0.001)  # 1ms延迟
        interrupt_msg.data = False
        self.interrupt_pub.publish(interrupt_msg)
    
    # ========================================================================
    # 测试场景实现
    # ========================================================================
    
    def _normal_scenario(self, t):
        """正常执行场景"""
        # 无特殊事件，只发布传感器数据
        pass
    
    def _follow_scenario(self, t):
        """跟随测试场景"""
        
        # 5秒：目标出现
        if 5.0 <= t < 5.1:
            if not self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标出现（前方0°）<<<')
                self.target_visible = True
                self.target_angle = 0.0
                self.target_distance = 1.5
        
        # 10秒：目标开始向右移动
        if 10.0 <= t < 10.1:
            self.get_logger().info('\n[模拟] >>> 目标开始向右移动 <<<')
            self.target_moving = True
        
        # 目标移动逻辑
        if self.target_moving and self.target_visible:
            # 模拟目标以5度/秒的速度向右移动
            self.target_angle += 0.5  # 0.1秒 × 5度/秒 = 0.5度
            if self.target_angle > 45:
                self.target_angle = 45  # 限制在45度
        
        # 20秒：目标停止移动
        if 20.0 <= t < 20.1:
            if self.target_moving:
                self.get_logger().info('\n[模拟] >>> 目标停止移动 <<<')
                self.target_moving = False
        
        # 25秒：目标消失
        if 25.0 <= t < 25.1:
            if self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标消失 <<<')
                self.target_visible = False
        
        # 30秒：目标再次出现
        if 30.0 <= t < 30.1:
            if not self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标再次出现 <<<')
                self.target_visible = True
                self.target_angle = -20.0  # 左侧20度
    
    def _search_scenario(self, t):
        """搜寻测试场景"""
        
        # 3秒：发送搜寻命令
        if 3.0 <= t < 3.1 and not self.search_command_sent:
            self.get_logger().info('\n[模拟] >>> 发送搜寻命令 <<<')
            search_msg = Bool()
            search_msg.data = True
            self.search_cmd_pub.publish(search_msg)
            self.search_command_sent = True
        
        # 8秒：目标出现（搜寻成功）
        if 8.0 <= t < 8.1:
            if not self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标出现（搜寻成功）<<<')
                self.target_visible = True
                self.target_angle = 30.0
        
        # 15秒：目标消失
        if 15.0 <= t < 15.1:
            if self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标消失 <<<')
                self.target_visible = False
        
        # 18秒：再次发送搜寻命令
        if 18.0 <= t < 18.1:
            self.get_logger().info('\n[模拟] >>> 再次发送搜寻命令 <<<')
            search_msg = Bool()
            search_msg.data = True
            self.search_cmd_pub.publish(search_msg)
            self.search_command_sent = False
    
    def _obstacle_scenario(self, t):
        """避障测试场景"""
        
        # 5秒：前方出现障碍物
        if 5.0 <= t < 5.1:
            self.get_logger().info('\n[模拟] >>> 前方出现障碍物（0.6米）<<<')
            self.obstacle_present = True
        
        # 10秒：障碍物消失
        if 10.0 <= t < 10.1:
            if self.obstacle_present:
                self.get_logger().info('\n[模拟] >>> 障碍物消失 <<<')
                self.obstacle_present = False
        
        # 15秒：侧方出现障碍物
        if 15.0 <= t < 15.1:
            self.get_logger().info('\n[模拟] >>> 侧方出现障碍物 <<<')
            self.obstacle_present = True
        
        # 20秒：障碍物消失
        if 20.0 <= t < 20.1:
            if self.obstacle_present:
                self.get_logger().info('\n[模拟] >>> 障碍物消失 <<<')
                self.obstacle_present = False
    
    def _interrupt_scenario(self, t):
        """打断信号测试场景"""
        
        # 3秒：发送第1次打断信号
        if 5.0 <= t < 5.1:
            self.send_interrupt_signal("基本打断功能测试")
        
        # 8秒：目标出现
        if 8.0 <= t < 8.1:
            if not self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标出现，进入跟随状态 <<<')
                self.target_visible = True
                self.target_angle = 15.0
                self.target_distance = 1.2
        
        # 12秒：发送第2次打断信号（跟随状态下）
        if 12.0 <= t < 12.1:
            self.send_interrupt_signal("跟随状态下打断测试")
        
        # 18秒：目标消失
        if 18.0 <= t < 18.1:
            if self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标消失 <<<')
                self.target_visible = False
        
        # 20秒：发送第3次打断信号（无目标状态）
        if 20.0 <= t < 20.1:
            self.send_interrupt_signal("无目标状态下打断测试")
        
        # 25秒：目标再次出现
        if 25.0 <= t < 25.1:
            if not self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标再次出现 <<<')
                self.target_visible = True
                self.target_angle = -25.0
        
        # 28秒：发送第4次打断信号
        if 28.0 <= t < 28.1:
            self.send_interrupt_signal("连续打断测试-1")
        
        # 30秒：发送第5次打断信号（快速连续）
        if 30.0 <= t < 30.1:
            self.send_interrupt_signal("连续打断测试-2")
        
        # 35秒：测试结束提示
        if 35.0 <= t < 35.1:
            self.get_logger().info(
                f'\n✅ [模拟] >>> 打断测试完成！共发送{self.interrupt_count}次打断信号 <<<'
            )
    
    def _interrupt_stress_scenario(self, t):
        """打断压力测试场景"""
        
        # 2-10秒：每2秒发送一次打断信号
        if 2.0 <= t < 10.0:
            if int((t - 2.0) * 10) % 20 == 0 and t - self.last_interrupt_time >= 1.9:
                self.send_interrupt_signal(f"高频打断-{int((t-2)/2)+1}")
        
        # 10秒：目标出现
        if 10.0 <= t < 10.1:
            if not self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标出现，跟随状态下高频打断测试 <<<')
                self.target_visible = True
                self.target_angle = 0.0
        
        # 15-20秒：每1秒发送一次打断信号（极高频）
        if 15.0 <= t < 20.0:
            if int((t - 15.0) * 10) % 10 == 0 and t - self.last_interrupt_time >= 0.9:
                self.send_interrupt_signal(f"极高频打断-{int(t-15)+1}")
        
        # 20秒：目标消失
        if 20.0 <= t < 20.1:
            if self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标消失，继续高频打断 <<<')
                self.target_visible = False
        
        # 20-25秒：继续高频打断
        if 20.0 <= t < 25.0:
            if int((t - 20.0) * 10) % 15 == 0 and t - self.last_interrupt_time >= 1.4:
                self.send_interrupt_signal(f"无目标高频打断-{int((t-20)/1.5)+1}")
        
        # 25秒：恢复正常
        if 25.0 <= t < 25.1:
            self.get_logger().info(
                f'\n✅ [模拟] >>> 压力测试完成！共发送{self.interrupt_count}次打断信号，系统稳定性测试中... <<<'
            )
        
        # 30秒：最终报告
        if 30.0 <= t < 30.1:
            self.get_logger().info(
                f'\n🎯 [模拟] >>> 压力测试结束！总计{self.interrupt_count}次打断信号 <<<'
            )
    
    def _combined_scenario(self, t):
        """综合测试场景（含打断）"""
        
        # 5秒：目标出现
        if 5.0 <= t < 5.1:
            if not self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标出现，进入跟随状态 <<<')
                self.target_visible = True
                self.target_angle = 0.0
                self.target_distance = 1.5
        
        # 8秒：发送打断信号（跟随中打断）
        if 8.0 <= t < 8.1:
            self.send_interrupt_signal("跟随状态中打断")
        
        # 10秒：目标开始移动
        if 10.0 <= t < 10.1:
            self.get_logger().info('\n[模拟] >>> 目标开始移动（测试跟随命令合并）<<<')
            self.target_moving = True
        
        # 目标移动逻辑
        if self.target_moving and self.target_visible and 10.0 <= t < 20.0:
            self.target_angle += 0.3  # 3度/秒
            if self.target_angle > 30:
                self.target_angle = 30
        
        # 15秒：出现障碍物
        if 15.0 <= t < 15.1:
            self.get_logger().info('\n[模拟] >>> 出现障碍物（测试避障）<<<')
            self.obstacle_present = True
        
        # 17秒：发送打断信号（避障中打断）
        if 17.0 <= t < 17.1:
            self.send_interrupt_signal("避障状态中打断")
        
        # 18秒：障碍物消失
        if 18.0 <= t < 18.1:
            if self.obstacle_present:
                self.get_logger().info('\n[模拟] >>> 障碍物消失 <<<')
                self.obstacle_present = False
                self.target_moving = False  # 停止移动
        
        # 20秒：目标消失
        if 20.0 <= t < 20.1:
            if self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标消失 <<<')
                self.target_visible = False
        
        # 23秒：发送搜寻命令
        if 23.0 <= t < 23.1 and not self.search_command_sent:
            self.get_logger().info('\n[模拟] >>> 发送搜寻命令 <<<')
            search_msg = Bool()
            search_msg.data = True
            self.search_cmd_pub.publish(search_msg)
            self.search_command_sent = True
        
        # 26秒：发送打断信号（搜寻中打断）
        if 26.0 <= t < 26.1:
            self.send_interrupt_signal("搜寻状态中打断")
        
        # 28秒：目标再次出现
        if 28.0 <= t < 28.1:
            if not self.target_visible:
                self.get_logger().info('\n[模拟] >>> 目标再次出现（搜寻成功）<<<')
                self.target_visible = True
                self.target_angle = -15.0
                self.search_command_sent = False
        
        # 32秒：发送最后一次打断信号
        if 32.0 <= t < 32.1:
            self.send_interrupt_signal("综合测试最终打断")
        
        # 35秒：目标消失
        if 35.0 <= t < 35.1:
            if self.target_visible:
                self.get_logger().info(
                    f'\n✅ [模拟] >>> 综合测试完成！目标消失，恢复正常执行 '
                    f'(共{self.interrupt_count}次打断) <<<'
                )
                self.target_visible = False
    
    # ========================================================================
    # 传感器数据发布（100Hz）
    # ========================================================================
    
    def publish_vision_info(self):
        """发布视觉信息"""
        # 添加少量随机噪声模拟真实传感器
        noise_angle = random.uniform(-2, 2) if self.target_visible else 0
        noise_distance = random.uniform(-0.1, 0.1) if self.target_visible else 0
        
        vision_data = {
            "timestamp": self.simulation_time,
            "face_detected": self.target_visible,
            "face_id": "user_001" if self.target_visible else None,
            "position": {
                "x": self.target_distance * np.cos(np.radians(self.target_angle)) + noise_distance if self.target_visible else None,
                "y": self.target_distance * np.sin(np.radians(self.target_angle)) if self.target_visible else None,
                "z": 0.5 if self.target_visible else None,
                "angle": self.target_angle + noise_angle if self.target_visible else None,
                "distance": self.target_distance + noise_distance if self.target_visible else None
            },
            "confidence": 0.95 if self.target_visible else 0.0
        }
        
        msg = String()
        msg.data = json.dumps(vision_data)
        self.vision_pub.publish(msg)
    
    def publish_audio_info(self):
        """发布听觉信息"""
        # 当目标不可见时，有30%概率听到声音（用于搜寻场景）
        sound_detected = False
        doa_direction = None
        
        if not self.target_visible and self.search_command_sent:
            # 搜寻模式下，有更高概率检测到声音
            if random.random() < 0.5:
                sound_detected = True
                # DOA方向指向目标可能出现的位置
                doa_direction = random.uniform(20, 40)  # 右侧20-40度
        elif self.target_visible:
            # 目标可见时，偶尔也能听到声音
            if random.random() < 0.2:
                sound_detected = True
                doa_direction = self.target_angle + random.uniform(-5, 5)
        
        audio_data = {
            "timestamp": self.simulation_time,
            "sound_detected": sound_detected,
            "voice_id": "user_001" if sound_detected else None,
            "doa_direction": doa_direction,
            "direction": doa_direction,
            "intensity": random.uniform(0.5, 1.0) if sound_detected else 0.0,
            "confidence": 0.85 if sound_detected else 0.0
        }
        
        msg = String()
        msg.data = json.dumps(audio_data)
        self.audio_pub.publish(msg)
    
    def publish_point_cloud(self):
        """发布点云信息（用于避障）"""
        if self.obstacle_present:
            # 模拟障碍物数据
            obstacle_x = 0.6  # 前方0.6米
            obstacle_y = random.uniform(-0.1, 0.1)  # 轻微偏移
            obstacle_z = 0.5
            
            # 计算距离
            min_distance = np.sqrt(obstacle_x**2 + obstacle_y**2 + obstacle_z**2)
            
            point_cloud_data = {
                "timestamp": self.simulation_time,
                "obstacle_detected": True,
                "min_distance": min_distance,
                "obstacle_position": {
                    "x": obstacle_x,
                    "y": obstacle_y,
                    "z": obstacle_z
                },
                # 添加包络信息（供避障模块使用）
                "envelope": {
                    "type": "sphere",
                    "center": [obstacle_x, obstacle_y, obstacle_z],
                    "radius": 0.2
                }
            }
        else:
            # 无障碍物
            point_cloud_data = {
                "timestamp": self.simulation_time,
                "obstacle_detected": False,
                "min_distance": 5.0,
                "obstacle_position": None,
                "envelope": None
            }
        
        msg = String()
        msg.data = json.dumps(point_cloud_data)
        self.point_cloud_pub.publish(msg)
    
    # ========================================================================
    # 状态监控
    # ========================================================================
    
    def print_status(self):
        """打印当前状态（周期性调用）"""
        if int(self.simulation_time) % 5 == 0 and int(self.simulation_time * 10) % 10 == 0:
            status = f"""
[状态] t={self.simulation_time:.1f}s
  - 目标: {'可见' if self.target_visible else '不可见'}
  - 角度: {self.target_angle:.1f}°
  - 移动: {'是' if self.target_moving else '否'}
  - 障碍物: {'存在' if self.obstacle_present else '无'}
  - 搜寻命令: {'已发送' if self.search_command_sent else '未发送'}
  - 打断次数: {self.interrupt_count}
            """
            self.get_logger().info(status)


def main(args=None):
    rclpy.init(args=args)
    node = OutNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
