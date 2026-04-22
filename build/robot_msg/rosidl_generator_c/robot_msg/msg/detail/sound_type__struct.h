// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_msg:msg/SoundType.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__STRUCT_H_
#define ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'sound_category'
// Member 'detected_sounds'
#include "rosidl_runtime_c/string.h"
// Member 'confidence_scores'
#include "rosidl_runtime_c/primitives_sequence.h"
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in msg/SoundType in the package robot_msg.
/**
  * 声音类型识别结果
 */
typedef struct robot_msg__msg__SoundType
{
  /// 声音类别 (speech, music, noise, etc.)
  rosidl_runtime_c__String sound_category;
  /// 检测到的具体声音类型
  rosidl_runtime_c__String__Sequence detected_sounds;
  /// 对应的置信度分数
  rosidl_runtime_c__float__Sequence confidence_scores;
  builtin_interfaces__msg__Time timestamp;
} robot_msg__msg__SoundType;

// Struct for a sequence of robot_msg__msg__SoundType.
typedef struct robot_msg__msg__SoundType__Sequence
{
  robot_msg__msg__SoundType * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__msg__SoundType__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__STRUCT_H_
