// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from robot_msg:msg/SpeakerIdentity.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "robot_msg/msg/detail/speaker_identity__rosidl_typesupport_introspection_c.h"
#include "robot_msg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "robot_msg/msg/detail/speaker_identity__functions.h"
#include "robot_msg/msg/detail/speaker_identity__struct.h"


// Include directives for member types
// Member `speaker_id`
// Member `speaker_name`
#include "rosidl_runtime_c/string_functions.h"
// Member `timestamp`
#include "builtin_interfaces/msg/time.h"
// Member `timestamp`
#include "builtin_interfaces/msg/detail/time__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  robot_msg__msg__SpeakerIdentity__init(message_memory);
}

void robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_fini_function(void * message_memory)
{
  robot_msg__msg__SpeakerIdentity__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_message_member_array[5] = {
  {
    "speaker_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__SpeakerIdentity, speaker_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "speaker_name",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__SpeakerIdentity, speaker_name),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "confidence",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__SpeakerIdentity, confidence),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "is_registered",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__SpeakerIdentity, is_registered),  // bytes offset in struct
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
    offsetof(robot_msg__msg__SpeakerIdentity, timestamp),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_message_members = {
  "robot_msg__msg",  // message namespace
  "SpeakerIdentity",  // message name
  5,  // number of fields
  sizeof(robot_msg__msg__SpeakerIdentity),
  robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_message_member_array,  // message members
  robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_init_function,  // function to initialize message memory (memory has to be allocated)
  robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_message_type_support_handle = {
  0,
  &robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_robot_msg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, robot_msg, msg, SpeakerIdentity)() {
  robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_message_member_array[4].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, builtin_interfaces, msg, Time)();
  if (!robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_message_type_support_handle.typesupport_identifier) {
    robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &robot_msg__msg__SpeakerIdentity__rosidl_typesupport_introspection_c__SpeakerIdentity_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
