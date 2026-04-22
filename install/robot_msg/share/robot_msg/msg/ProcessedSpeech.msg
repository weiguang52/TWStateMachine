# 处理后的语音数据
uint8[] audio_data          # 处理后的音频数据
uint32 sample_rate          # 采样率
uint32 channels             # 声道数
float32 duration            # 时长(秒)
float32 noise_level_before  # 降噪前噪声等级
float32 noise_level_after   # 降噪后噪声等级
builtin_interfaces/Time timestamp