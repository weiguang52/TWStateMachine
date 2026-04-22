# 声源位置消息
float64 azimuth        # 方位角 (度) -90到+90度，负值表示左侧，正值表示右侧
float64 elevation      # 仰角 (度) 对于双麦克风阵列通常为0
float64 distance       # 距离 (米) 对于双麦克风阵列难以准确测量，通常为0
float64 confidence     # 置信度 (0-1) 0表示不确定，1表示高度确定
builtin_interfaces/Time timestamp  # 检测时间戳