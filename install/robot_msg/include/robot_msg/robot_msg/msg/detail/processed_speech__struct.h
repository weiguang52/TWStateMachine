// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_msg:msg/ProcessedSpeech.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__PROCESSED_SPEECH__STRUCT_H_
#define ROBOT_MSG__MSG__DETAIL__PROCESSED_SPEECH__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'audio_data'
#include "rosidl_runtime_c/primitives_sequence.h"
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in msg/ProcessedSpeech in the package robot_msg.
/**
  * 处理后的语音数据
 */
typedef struct robot_msg__msg__ProcessedSpeech
{
  /// 处理后的音频数据
  rosidl_runtime_c__uint8__Sequence audio_data;
  /// 采样率
  uint32_t sample_rate;
  /// 声道数
  uint32_t channels;
  /// 时长(秒)
  float duration;
  /// 降噪前噪声等级
  float noise_level_before;
  /// 降噪后噪声等级
  float noise_level_after;
  builtin_interfaces__msg__Time timestamp;
} robot_msg__msg__ProcessedSpeech;

// Struct for a sequence of robot_msg__msg__ProcessedSpeech.
typedef struct robot_msg__msg__ProcessedSpeech__Sequence
{
  robot_msg__msg__ProcessedSpeech * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__msg__ProcessedSpeech__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_MSG__MSG__DETAIL__PROCESSED_SPEECH__STRUCT_H_
