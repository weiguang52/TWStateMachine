// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_msg:msg/SoundLocation.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__STRUCT_H_
#define ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in msg/SoundLocation in the package robot_msg.
/**
  * 声源位置消息
 */
typedef struct robot_msg__msg__SoundLocation
{
  /// 方位角 (度) -90到+90度，负值表示左侧，正值表示右侧
  double azimuth;
  /// 仰角 (度) 对于双麦克风阵列通常为0
  double elevation;
  /// 距离 (米) 对于双麦克风阵列难以准确测量，通常为0
  double distance;
  /// 置信度 (0-1) 0表示不确定，1表示高度确定
  double confidence;
  /// 检测时间戳
  builtin_interfaces__msg__Time timestamp;
} robot_msg__msg__SoundLocation;

// Struct for a sequence of robot_msg__msg__SoundLocation.
typedef struct robot_msg__msg__SoundLocation__Sequence
{
  robot_msg__msg__SoundLocation * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__msg__SoundLocation__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__STRUCT_H_
