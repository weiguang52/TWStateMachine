// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_msg:msg/ExtremeSensorAlert.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__STRUCT_H_
#define ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'sensor_type'
// Member 'alert_level'
// Member 'alert_type'
// Member 'description'
#include "rosidl_runtime_c/string.h"
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in msg/ExtremeSensorAlert in the package robot_msg.
/**
  * 极端传感器数据报警消息
 */
typedef struct robot_msg__msg__ExtremeSensorAlert
{
  /// 传感器类型 (temperature, humidity, combined)
  rosidl_runtime_c__String sensor_type;
  /// 报警级别 (normal, warning, critical, danger)
  rosidl_runtime_c__String alert_level;
  /// 报警类型 (high, low, out_of_range)
  rosidl_runtime_c__String alert_type;
  /// 当前值
  double current_value;
  /// 阈值
  double threshold_value;
  /// 描述信息
  rosidl_runtime_c__String description;
  /// 时间戳
  builtin_interfaces__msg__Time timestamp;
  /// 是否为活跃报警
  bool is_active;
  /// 报警ID（用于追踪）
  uint32_t alert_id;
} robot_msg__msg__ExtremeSensorAlert;

// Struct for a sequence of robot_msg__msg__ExtremeSensorAlert.
typedef struct robot_msg__msg__ExtremeSensorAlert__Sequence
{
  robot_msg__msg__ExtremeSensorAlert * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__msg__ExtremeSensorAlert__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__STRUCT_H_
