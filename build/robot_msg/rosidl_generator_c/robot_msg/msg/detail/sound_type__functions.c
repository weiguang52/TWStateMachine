// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_msg:msg/SoundType.idl
// generated code does not contain a copyright notice
#include "robot_msg/msg/detail/sound_type__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `sound_category`
// Member `detected_sounds`
#include "rosidl_runtime_c/string_functions.h"
// Member `confidence_scores`
#include "rosidl_runtime_c/primitives_sequence_functions.h"
// Member `timestamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
robot_msg__msg__SoundType__init(robot_msg__msg__SoundType * msg)
{
  if (!msg) {
    return false;
  }
  // sound_category
  if (!rosidl_runtime_c__String__init(&msg->sound_category)) {
    robot_msg__msg__SoundType__fini(msg);
    return false;
  }
  // detected_sounds
  if (!rosidl_runtime_c__String__Sequence__init(&msg->detected_sounds, 0)) {
    robot_msg__msg__SoundType__fini(msg);
    return false;
  }
  // confidence_scores
  if (!rosidl_runtime_c__float__Sequence__init(&msg->confidence_scores, 0)) {
    robot_msg__msg__SoundType__fini(msg);
    return false;
  }
  // timestamp
  if (!builtin_interfaces__msg__Time__init(&msg->timestamp)) {
    robot_msg__msg__SoundType__fini(msg);
    return false;
  }
  return true;
}

void
robot_msg__msg__SoundType__fini(robot_msg__msg__SoundType * msg)
{
  if (!msg) {
    return;
  }
  // sound_category
  rosidl_runtime_c__String__fini(&msg->sound_category);
  // detected_sounds
  rosidl_runtime_c__String__Sequence__fini(&msg->detected_sounds);
  // confidence_scores
  rosidl_runtime_c__float__Sequence__fini(&msg->confidence_scores);
  // timestamp
  builtin_interfaces__msg__Time__fini(&msg->timestamp);
}

bool
robot_msg__msg__SoundType__are_equal(const robot_msg__msg__SoundType * lhs, const robot_msg__msg__SoundType * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // sound_category
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->sound_category), &(rhs->sound_category)))
  {
    return false;
  }
  // detected_sounds
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->detected_sounds), &(rhs->detected_sounds)))
  {
    return false;
  }
  // confidence_scores
  if (!rosidl_runtime_c__float__Sequence__are_equal(
      &(lhs->confidence_scores), &(rhs->confidence_scores)))
  {
    return false;
  }
  // timestamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->timestamp), &(rhs->timestamp)))
  {
    return false;
  }
  return true;
}

bool
robot_msg__msg__SoundType__copy(
  const robot_msg__msg__SoundType * input,
  robot_msg__msg__SoundType * output)
{
  if (!input || !output) {
    return false;
  }
  // sound_category
  if (!rosidl_runtime_c__String__copy(
      &(input->sound_category), &(output->sound_category)))
  {
    return false;
  }
  // detected_sounds
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->detected_sounds), &(output->detected_sounds)))
  {
    return false;
  }
  // confidence_scores
  if (!rosidl_runtime_c__float__Sequence__copy(
      &(input->confidence_scores), &(output->confidence_scores)))
  {
    return false;
  }
  // timestamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->timestamp), &(output->timestamp)))
  {
    return false;
  }
  return true;
}

robot_msg__msg__SoundType *
robot_msg__msg__SoundType__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__SoundType * msg = (robot_msg__msg__SoundType *)allocator.allocate(sizeof(robot_msg__msg__SoundType), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_msg__msg__SoundType));
  bool success = robot_msg__msg__SoundType__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_msg__msg__SoundType__destroy(robot_msg__msg__SoundType * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_msg__msg__SoundType__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_msg__msg__SoundType__Sequence__init(robot_msg__msg__SoundType__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__SoundType * data = NULL;

  if (size) {
    data = (robot_msg__msg__SoundType *)allocator.zero_allocate(size, sizeof(robot_msg__msg__SoundType), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_msg__msg__SoundType__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_msg__msg__SoundType__fini(&data[i - 1]);
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
robot_msg__msg__SoundType__Sequence__fini(robot_msg__msg__SoundType__Sequence * array)
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
      robot_msg__msg__SoundType__fini(&array->data[i]);
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

robot_msg__msg__SoundType__Sequence *
robot_msg__msg__SoundType__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__SoundType__Sequence * array = (robot_msg__msg__SoundType__Sequence *)allocator.allocate(sizeof(robot_msg__msg__SoundType__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_msg__msg__SoundType__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_msg__msg__SoundType__Sequence__destroy(robot_msg__msg__SoundType__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_msg__msg__SoundType__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_msg__msg__SoundType__Sequence__are_equal(const robot_msg__msg__SoundType__Sequence * lhs, const robot_msg__msg__SoundType__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_msg__msg__SoundType__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_msg__msg__SoundType__Sequence__copy(
  const robot_msg__msg__SoundType__Sequence * input,
  robot_msg__msg__SoundType__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_msg__msg__SoundType);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_msg__msg__SoundType * data =
      (robot_msg__msg__SoundType *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_msg__msg__SoundType__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_msg__msg__SoundType__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_msg__msg__SoundType__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
