// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_msg:srv/GetTemperatureAndHumidity.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__SRV__DETAIL__GET_TEMPERATURE_AND_HUMIDITY__STRUCT_H_
#define ROBOT_MSG__SRV__DETAIL__GET_TEMPERATURE_AND_HUMIDITY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/GetTemperatureAndHumidity in the package robot_msg.
typedef struct robot_msg__srv__GetTemperatureAndHumidity_Request
{
  uint8_t structure_needs_at_least_one_member;
} robot_msg__srv__GetTemperatureAndHumidity_Request;

// Struct for a sequence of robot_msg__srv__GetTemperatureAndHumidity_Request.
typedef struct robot_msg__srv__GetTemperatureAndHumidity_Request__Sequence
{
  robot_msg__srv__GetTemperatureAndHumidity_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__srv__GetTemperatureAndHumidity_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'message'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/GetTemperatureAndHumidity in the package robot_msg.
typedef struct robot_msg__srv__GetTemperatureAndHumidity_Response
{
  double temperature;
  double humidity;
  bool success;
  rosidl_runtime_c__String message;
} robot_msg__srv__GetTemperatureAndHumidity_Response;

// Struct for a sequence of robot_msg__srv__GetTemperatureAndHumidity_Response.
typedef struct robot_msg__srv__GetTemperatureAndHumidity_Response__Sequence
{
  robot_msg__srv__GetTemperatureAndHumidity_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_msg__srv__GetTemperatureAndHumidity_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_MSG__SRV__DETAIL__GET_TEMPERATURE_AND_HUMIDITY__STRUCT_H_
