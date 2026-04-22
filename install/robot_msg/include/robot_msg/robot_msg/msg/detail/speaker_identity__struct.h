// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_msg:msg/SpeakerIdentity.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__STRUCT_H_
#define ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'speaker_id'
// Member 'speaker_name'
#include "rosidl_runtime_c/string.h"
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in msg/SpeakerIdentity in the package robot_msg.
/**
  * 说话人身份识别结果
 */
typedef struct robot_msg__msg__SpeakerIdentity
{
  /// 说话人ID
  rosidl_runtime_c__String speaker_id;
  /// 说话人姓名 (如果已知)
  rosidl_runtime_c__String speaker_name;
  /// 置信度
  float confidence;
  /// 是否为注册用户
  bool is_registered;
  builtin_interfaces__msg__Time timestamp;
} robot_msg__msg__SpeakerIdentity;

// Struct for a sequence of robot_msg__msg__SpeakerIdentity.
typedef struct robot_msg__msg__SpeakerIdentity__Sequence
{
  robot_msg__msg__SpeakerIdentity * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__msg__SpeakerIdentity__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__STRUCT_H_
