# 声音类型识别结果
string sound_category       # 声音类别 (speech, music, noise, etc.)
string[] detected_sounds    # 检测到的具体声音类型
float32[] confidence_scores # 对应的置信度分数
builtin_interfaces/Time timestamp