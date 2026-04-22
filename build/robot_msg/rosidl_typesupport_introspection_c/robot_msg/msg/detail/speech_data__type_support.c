// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from robot_msg:msg/SpeechData.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "robot_msg/msg/detail/speech_data__rosidl_typesupport_introspection_c.h"
#include "robot_msg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "robot_msg/msg/detail/speech_data__functions.h"
#include "robot_msg/msg/detail/speech_data__struct.h"


// Include directives for member types
// Member `audio_data`
#include "rosidl_runtime_c/primitives_sequence_functions.h"
// Member `timestamp`
#include "builtin_interfaces/msg/time.h"
// Member `timestamp`
#include "builtin_interfaces/msg/detail/time__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  robot_msg__msg__SpeechData__init(message_memory);
}

void robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_fini_function(void * message_memory)
{
  robot_msg__msg__SpeechData__fini(message_memory);
}

size_t robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__size_function__SpeechData__audio_data(
  const void * untyped_member)
{
  const rosidl_runtime_c__uint8__Sequence * member =
    (const rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return member->size;
}

const void * robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__get_const_function__SpeechData__audio_data(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__uint8__Sequence * member =
    (const rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return &member->data[index];
}

void * robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__get_function__SpeechData__audio_data(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__uint8__Sequence * member =
    (rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return &member->data[index];
}

void robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__fetch_function__SpeechData__audio_data(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const uint8_t * item =
    ((const uint8_t *)
    robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__get_const_function__SpeechData__audio_data(untyped_member, index));
  uint8_t * value =
    (uint8_t *)(untyped_value);
  *value = *item;
}

void robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__assign_function__SpeechData__audio_data(
  void * untyped_member, size_t index, const void * untyped_value)
{
  uint8_t * item =
    ((uint8_t *)
    robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__get_function__SpeechData__audio_data(untyped_member, index));
  const uint8_t * value =
    (const uint8_t *)(untyped_value);
  *item = *value;
}

bool robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__resize_function__SpeechData__audio_data(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__uint8__Sequence * member =
    (rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  rosidl_runtime_c__uint8__Sequence__fini(member);
  return rosidl_runtime_c__uint8__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_message_member_array[5] = {
  {
    "audio_data",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__SpeechData, audio_data),  // bytes offset in struct
    NULL,  // default value
    robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__size_function__SpeechData__audio_data,  // size() function pointer
    robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__get_const_function__SpeechData__audio_data,  // get_const(index) function pointer
    robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__get_function__SpeechData__audio_data,  // get(index) function pointer
    robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__fetch_function__SpeechData__audio_data,  // fetch(index, &value) function pointer
    robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__assign_function__SpeechData__audio_data,  // assign(index, value) function pointer
    robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__resize_function__SpeechData__audio_data  // resize(index) function pointer
  },
  {
    "sample_rate",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__SpeechData, sample_rate),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "channels",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__SpeechData, channels),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "duration",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_msg__msg__SpeechData, duration),  // bytes offset in struct
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
    offsetof(robot_msg__msg__SpeechData, timestamp),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_message_members = {
  "robot_msg__msg",  // message namespace
  "SpeechData",  // message name
  5,  // number of fields
  sizeof(robot_msg__msg__SpeechData),
  robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_message_member_array,  // message members
  robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_init_function,  // function to initialize message memory (memory has to be allocated)
  robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_message_type_support_handle = {
  0,
  &robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_robot_msg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, robot_msg, msg, SpeechData)() {
  robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_message_member_array[4].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, builtin_interfaces, msg, Time)();
  if (!robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_message_type_support_handle.typesupport_identifier) {
    robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &robot_msg__msg__SpeechData__rosidl_typesupport_introspection_c__SpeechData_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
