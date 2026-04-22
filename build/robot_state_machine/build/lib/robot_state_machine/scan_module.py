#!/usr/bin/env python3
import time
import json

class ScanModule:
    def __init__(self, parent_node):
        self.parent_node = parent_node
        self.logger = parent_node.get_logger()
        
        # 扫描位置序列（简化版）
        self.scan_positions = [
            {"pan": 0.0, "tilt": 0.0, "duration": 2.0, "name": "中心"},
            {"pan": 0.5, "tilt": 0.3, "duration": 2.0, "name": "右上"},
            {"pan": -0.5, "tilt": 0.3, "duration": 2.0, "name": "左上"},
            {"pan": 0.0, "tilt": -0.3, "duration": 2.0, "name": "中下"},
        ]
        
        self.current_scan_index = 0
        self.scan_start_time = None
        self.position_start_time = None
        self.scan_complete = False
    
    def reset(self):
        """重置扫描模块"""
        self.logger.info('[扫描模块] 重置')
        self.current_scan_index = 0
        self.scan_start_time = time.time()
        self.position_start_time = time.time()
        self.scan_complete = False
    
    def execute(self, vision_info):
        """执行扫描逻辑"""
        if self.scan_complete:
            return True
        
        # 检查当前位置是否完成
        current_position = self.scan_positions[self.current_scan_index]
        elapsed = time.time() - self.position_start_time
        
        if elapsed < current_position["duration"]:
            # 当前位置还未完成，继续保持
            if elapsed < 0.1:  # 刚开始扫描这个位置
                self.logger.info(f'[扫描模块] 扫描位置: {current_position["name"]} (持续{current_position["duration"]}秒)')
            
            self.move_head_to_position(current_position)
            self.detect_objects(vision_info)
            
            return False
        else:
            # 当前位置完成，移动到下一个位置
            self.current_scan_index += 1
            
            if self.current_scan_index >= len(self.scan_positions):
                # 所有位置扫描完成
                self.logger.info('[扫描模块] ✓ 扫描完成！')
                self.scan_complete = True
                return True
            else:
                # 移动到下一个位置
                self.position_start_time = time.time()
                return False
    
    # ========== 模拟实现 ==========
    def move_head_to_position(self, position):
        """移动头部到指定位置（模拟）"""
        # 这里可以发布头部控制指令
        pass
    
    def detect_objects(self, vision_info):
        """检测物体（模拟）"""
        if vision_info is None:
            return
        
        try:
            data = json.loads(vision_info)
            if data.get("target_detected", False):
                self.logger.info(f'[扫描模块] 检测到物体！')
        except:
            pass
