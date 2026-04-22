// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_msg:msg/SpeechData.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__STRUCT_H_
#define ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__STRUCT_H_

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

/// Struct defined in msg/SpeechData in the package robot_msg.
/**
  * 原始语音数据消息
 */
typedef struct robot_msg__msg__SpeechData
{
  /// 原始音频数据
  rosidl_runtime_c__uint8__Sequence audio_data;
  /// 采样率
  uint32_t sample_rate;
  /// 声道数
  uint32_t channels;
  /// 时长(秒)
  float duration;
  builtin_interfaces__msg__Time timestamp;
} robot_msg__msg__SpeechData;

// Struct for a sequence of robot_msg__msg__SpeechData.
typedef struct robot_msg__msg__SpeechData__Sequence
{
  robot_msg__msg__SpeechData * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__msg__SpeechData__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__STRUCT_H_
