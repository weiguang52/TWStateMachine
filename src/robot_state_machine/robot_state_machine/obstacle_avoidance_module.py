#!/usr/bin/env python3
import json

class ObstacleAvoidanceModule:
    def __init__(self, parent_node):
        self.parent_node = parent_node
        self.logger = parent_node.get_logger()
        self.safe_distance = 0.8  # 安全距离：0.8米
        self.avoidance_count = 0
        self.obstacle_detected_flag = False
    
    def execute(self, point_cloud):
        """执行避障逻辑"""
        if point_cloud is None:
            return False
        
        try:
            data = json.loads(point_cloud)
            obstacle_detected = data.get("obstacle_detected", False)
            min_distance = data.get("min_distance", 5.0)
            
            # 检查是否有障碍物且距离小于安全距离
            if obstacle_detected and min_distance < self.safe_distance:
                self.avoidance_count += 1
                
                if not self.obstacle_detected_flag:
                    self.logger.info(f'[避障模块] ⚠ 检测到障碍物！距离: {min_distance:.2f}米')
                    self.obstacle_detected_flag = True
                
                # 每20次打印一次日志
                if self.avoidance_count % 20 == 0:
                    self.logger.info(f'[避障模块] 正在避障... (距离: {min_distance:.2f}米, 第{self.avoidance_count}次)')
                
                # 执行避障动作
                avoidance_cmd = self.generate_avoidance_command(data)
                self.publish_avoidance_command(avoidance_cmd)
                
                return True
            else:
                if self.obstacle_detected_flag:
                    self.logger.info(f'[避障模块] ✓ 障碍物已清除 (距离: {min_distance:.2f}米)')
                    self.obstacle_detected_flag = False
                    self.avoidance_count = 0
                
                return False
        
        except Exception as e:
            self.logger.error(f'[避障模块] 处理点云数据出错: {e}')
            return False
    
    # ========== 模拟实现 ==========
    def generate_avoidance_command(self, point_cloud_data):
        """生成避障命令（模拟）"""
        obstacle_pos = point_cloud_data.get("obstacle_position", {})
        
        if obstacle_pos:
            y = obstacle_pos.get("y", 0.0)
            
            # 简单避障逻辑：向障碍物反方向转
            if y > 0:
                # 障碍物在右边，向左转
                return {"linear": 0.0, "angular": 0.5}
            else:
                # 障碍物在左边，向右转
                return {"linear": 0.0, "angular": -0.5}
        else:
            # 停止
            return {"linear": 0.0, "angular": 0.0}
    
    def publish_avoidance_command(self, cmd):
        """发布避障命令（模拟）"""
        # 这里可以发布到 /cmd_vel 话题
        pass

    def generate_envelope(self, point_cloud_data):
        self.logger.info(f'生成包络信息')
        return point_cloud_data
