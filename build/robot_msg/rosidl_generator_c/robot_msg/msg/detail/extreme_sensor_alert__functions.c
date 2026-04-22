// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_msg:msg/ExtremeSensorAlert.idl
// generated code does not contain a copyright notice
#include "robot_msg/msg/detail/extreme_sensor_alert__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `sensor_type`
// Member `alert_level`
// Member `alert_type`
// Member `description`
#include "rosidl_runtime_c/string_functions.h"
// Member `timestamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
robot_msg__msg__ExtremeSensorAlert__init(robot_msg__msg__ExtremeSensorAlert * msg)
{
  if (!msg) {
    return false;
  }
  // sensor_type
  if (!rosidl_runtime_c__String__init(&msg->sensor_type)) {
    robot_msg__msg__ExtremeSensorAlert__fini(msg);
    return false;
  }
  // alert_level
  if (!rosidl_runtime_c__String__init(&msg->alert_level)) {
    robot_msg__msg__ExtremeSensorAlert__fini(msg);
    return false;
  }
  // alert_type
  if (!rosidl_runtime_c__String__init(&msg->alert_type)) {
    robot_msg__msg__ExtremeSensorAlert__fini(msg);
    return false;
  }
  // current_value
  // threshold_value
  // description
  if (!rosidl_runtime_c__String__init(&msg->description)) {
    robot_msg__msg__ExtremeSensorAlert__fini(msg);
    return false;
  }
  // timestamp
  if (!builtin_interfaces__msg__Time__init(&msg->timestamp)) {
    robot_msg__msg__ExtremeSensorAlert__fini(msg);
    return false;
  }
  // is_active
  // alert_id
  return true;
}

void
robot_msg__msg__ExtremeSensorAlert__fini(robot_msg__msg__ExtremeSensorAlert * msg)
{
  if (!msg) {
    return;
  }
  // sensor_type
  rosidl_runtime_c__String__fini(&msg->sensor_type);
  // alert_level
  rosidl_runtime_c__String__fini(&msg->alert_level);
  // alert_type
  rosidl_runtime_c__String__fini(&msg->alert_type);
  // current_value
  // threshold_value
  // description
  rosidl_runtime_c__String__fini(&msg->description);
  // timestamp
  builtin_interfaces__msg__Time__fini(&msg->timestamp);
  // is_active
  // alert_id
}

bool
robot_msg__msg__ExtremeSensorAlert__are_equal(const robot_msg__msg__ExtremeSensorAlert * lhs, const robot_msg__msg__ExtremeSensorAlert * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // sensor_type
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->sensor_type), &(rhs->sensor_type)))
  {
    return false;
  }
  // alert_level
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->alert_level), &(rhs->alert_level)))
  {
    return false;
  }
  // alert_type
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->alert_type), &(rhs->alert_type)))
  {
    return false;
  }
  // current_value
  if (lhs->current_value != rhs->current_value) {
    return false;
  }
  // threshold_value
  if (lhs->threshold_value != rhs->threshold_value) {
    return false;
  }
  // description
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->description), &(rhs->description)))
  {
    return false;
  }
  // timestamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->timestamp), &(rhs->timestamp)))
  {
    return false;
  }
  // is_active
  if (lhs->is_active != rhs->is_active) {
    return false;
  }
  // alert_id
  if (lhs->alert_id != rhs->alert_id) {
    return false;
  }
  return true;
}

bool
robot_msg__msg__ExtremeSensorAlert__copy(
  const robot_msg__msg__ExtremeSensorAlert * input,
  robot_msg__msg__ExtremeSensorAlert * output)
{
  if (!input || !output) {
    return false;
  }
  // sensor_type
  if (!rosidl_runtime_c__String__copy(
      &(input->sensor_type), &(output->sensor_type)))
  {
    return false;
  }
  // alert_level
  if (!rosidl_runtime_c__String__copy(
      &(input->alert_level), &(output->alert_level)))
  {
    return false;
  }
  // alert_type
  if (!rosidl_runtime_c__String__copy(
      &(input->alert_type), &(output->alert_type)))
  {
    return false;
  }
  // current_value
  output->current_value = input->current_value;
  // threshold_value
  output->threshold_value = input->threshold_value;
  // description
  if (!rosidl_runtime_c__String__copy(
      &(input->description), &(output->description)))
  {
    return false;
  }
  // timestamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->timestamp), &(output->timestamp)))
  {
    return false;
  }
  // is_active
  output->is_active = input->is_active;
  // alert_id
  output->alert_id = input->alert_id;
  return true;
}

robot_msg__msg__ExtremeSensorAlert *
robot_msg__msg__ExtremeSensorAlert__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__ExtremeSensorAlert * msg = (robot_msg__msg__ExtremeSensorAlert *)allocator.allocate(sizeof(robot_msg__msg__ExtremeSensorAlert), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_msg__msg__ExtremeSensorAlert));
  bool success = robot_msg__msg__ExtremeSensorAlert__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_msg__msg__ExtremeSensorAlert__destroy(robot_msg__msg__ExtremeSensorAlert * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_msg__msg__ExtremeSensorAlert__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_msg__msg__ExtremeSensorAlert__Sequence__init(robot_msg__msg__ExtremeSensorAlert__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__ExtremeSensorAlert * data = NULL;

  if (size) {
    data = (robot_msg__msg__ExtremeSensorAlert *)allocator.zero_allocate(size, sizeof(robot_msg__msg__ExtremeSensorAlert), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_msg__msg__ExtremeSensorAlert__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_msg__msg__ExtremeSensorAlert__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
robot_msg__msg__ExtremeSensorAlert__Sequence__fini(robot_msg__msg__ExtremeSensorAlert__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      robot_msg__msg__ExtremeSensorAlert__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

robot_msg__msg__ExtremeSensorAlert__Sequence *
robot_msg__msg__ExtremeSensorAlert__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__ExtremeSensorAlert__Sequence * array = (robot_msg__msg__ExtremeSensorAlert__Sequence *)allocator.allocate(sizeof(robot_msg__msg__ExtremeSensorAlert__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_msg__msg__ExtremeSensorAlert__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_msg__msg__ExtremeSensorAlert__Sequence__destroy(robot_msg__msg__ExtremeSensorAlert__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_msg__msg__ExtremeSensorAlert__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_msg__msg__ExtremeSensorAlert__Sequence__are_equal(const robot_msg__msg__ExtremeSensorAlert__Sequence * lhs, const robot_msg__msg__ExtremeSensorAlert__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_msg__msg__ExtremeSensorAlert__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_msg__msg__ExtremeSensorAlert__Sequence__copy(
  const robot_msg__msg__ExtremeSensorAlert__Sequence * input,
  robot_msg__msg__ExtremeSensorAlert__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_msg__msg__ExtremeSensorAlert);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_msg__msg__ExtremeSensorAlert * data =
      (robot_msg__msg__ExtremeSensorAlert *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_msg__msg__ExtremeSensorAlert__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_msg__msg__ExtremeSensorAlert__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_msg__msg__ExtremeSensorAlert__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
