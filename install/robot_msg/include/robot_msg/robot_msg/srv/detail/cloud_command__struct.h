// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_msg:srv/CloudCommand.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__STRUCT_H_
#define ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'target_service'
// Member 'payload_json'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/CloudCommand in the package robot_msg.
typedef struct robot_msg__srv__CloudCommand_Request
{
  /// 目标服务名，例如 /upload_image
  rosidl_runtime_c__String target_service;
  /// 输入参数json
  rosidl_runtime_c__String payload_json;
} robot_msg__srv__CloudCommand_Request;

// Struct for a sequence of robot_msg__srv__CloudCommand_Request.
typedef struct robot_msg__srv__CloudCommand_Request__Sequence
{
  robot_msg__srv__CloudCommand_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__srv__CloudCommand_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'response_json'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/CloudCommand in the package robot_msg.
typedef struct robot_msg__srv__CloudCommand_Response
{
  /// 输出参数json
  rosidl_runtime_c__String response_json;
} robot_msg__srv__CloudCommand_Response;

// Struct for a sequence of robot_msg__srv__CloudCommand_Response.
typedef struct robot_msg__srv__CloudCommand_Response__Sequence
{
  robot_msg__srv__CloudCommand_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__srv__CloudCommand_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__STRUCT_H_
