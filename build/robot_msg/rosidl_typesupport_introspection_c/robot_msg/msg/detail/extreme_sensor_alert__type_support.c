// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from robot_msg:msg/ExtremeSensorAlert.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "robot_msg/msg/detail/extreme_sensor_alert__rosidl_typesupport_introspection_c.h"
#include "robot_msg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "robot_msg/msg/detail/extreme_sensor_alert__functions.h"
#include "robot_msg/msg/detail/extreme_sensor_alert__struct.h"


// Include directives for member types
// Member `sensor_type`
// Member `alert_level`
// Member `alert_type`
// Member `description`
#include "rosidl_runtime_c/string_functions.h"
// Member `timestamp`
#include "builtin_interfaces/msg/time.h"
// Member `timestamp`
#include "builtin_interfaces/msg/detail/time__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  robot_msg__msg__ExtremeSensorAlert__init(message_memory);
}

void robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_fini_function(void * message_memory)
{
  robot_msg__msg__ExtremeSensorAlert__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_message_member_array[9] = {
  {
    "sensor_type",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__ExtremeSensorAlert, sensor_type),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "alert_level",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__ExtremeSensorAlert, alert_level),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "alert_type",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__ExtremeSensorAlert, alert_type),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "current_value",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__ExtremeSensorAlert, current_value),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "threshold_value",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__ExtremeSensorAlert, threshold_value),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "description",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__ExtremeSensorAlert, description),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "timestamp",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__ExtremeSensorAlert, timestamp),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "is_active",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__ExtremeSensorAlert, is_active),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "alert_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__ExtremeSensorAlert, alert_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_message_members = {
  "robot_msg__msg",  // message namespace
  "ExtremeSensorAlert",  // message name
  9,  // number of fields
  sizeof(robot_msg__msg__ExtremeSensorAlert),
  robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_message_member_array,  // message members
  robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_init_function,  // function to initialize message memory (memory has to be allocated)
  robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_message_type_support_handle = {
  0,
  &robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_robot_msg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, robot_msg, msg, ExtremeSensorAlert)() {
  robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_message_member_array[6].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, builtin_interfaces, msg, Time)();
  if (!robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_message_type_support_handle.typesupport_identifier) {
    robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &robot_msg__msg__ExtremeSensorAlert__rosidl_typesupport_introspection_c__ExtremeSensorAlert_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
