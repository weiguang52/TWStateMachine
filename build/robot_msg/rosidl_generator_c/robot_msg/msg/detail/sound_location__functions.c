// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_msg:msg/SoundLocation.idl
// generated code does not contain a copyright notice
#include "robot_msg/msg/detail/sound_location__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `timestamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
robot_msg__msg__SoundLocation__init(robot_msg__msg__SoundLocation * msg)
{
  if (!msg) {
    return false;
  }
  // azimuth
  // elevation
  // distance
  // confidence
  // timestamp
  if (!builtin_interfaces__msg__Time__init(&msg->timestamp)) {
    robot_msg__msg__SoundLocation__fini(msg);
    return false;
  }
  return true;
}

void
robot_msg__msg__SoundLocation__fini(robot_msg__msg__SoundLocation * msg)
{
  if (!msg) {
    return;
  }
  // azimuth
  // elevation
  // distance
  // confidence
  // timestamp
  builtin_interfaces__msg__Time__fini(&msg->timestamp);
}

bool
robot_msg__msg__SoundLocation__are_equal(const robot_msg__msg__SoundLocation * lhs, const robot_msg__msg__SoundLocation * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // azimuth
  if (lhs->azimuth != rhs->azimuth) {
    return false;
  }
  // elevation
  if (lhs->elevation != rhs->elevation) {
    return false;
  }
  // distance
  if (lhs->distance != rhs->distance) {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
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
robot_msg__msg__SoundLocation__copy(
  const robot_msg__msg__SoundLocation * input,
  robot_msg__msg__SoundLocation * output)
{
  if (!input || !output) {
    return false;
  }
  // azimuth
  output->azimuth = input->azimuth;
  // elevation
  output->elevation = input->elevation;
  // distance
  output->distance = input->distance;
  // confidence
  output->confidence = input->confidence;
  // timestamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->timestamp), &(output->timestamp)))
  {
    return false;
  }
  return true;
}

robot_msg__msg__SoundLocation *
robot_msg__msg__SoundLocation__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__SoundLocation * msg = (robot_msg__msg__SoundLocation *)allocator.allocate(sizeof(robot_msg__msg__SoundLocation), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_msg__msg__SoundLocation));
  bool success = robot_msg__msg__SoundLocation__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_msg__msg__SoundLocation__destroy(robot_msg__msg__SoundLocation * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_msg__msg__SoundLocation__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_msg__msg__SoundLocation__Sequence__init(robot_msg__msg__SoundLocation__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__SoundLocation * data = NULL;

  if (size) {
    data = (robot_msg__msg__SoundLocation *)allocator.zero_allocate(size, sizeof(robot_msg__msg__SoundLocation), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_msg__msg__SoundLocation__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_msg__msg__SoundLocation__fini(&data[i - 1]);
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
robot_msg__msg__SoundLocation__Sequence__fini(robot_msg__msg__SoundLocation__Sequence * array)
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
      robot_msg__msg__SoundLocation__fini(&array->data[i]);
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

robot_msg__msg__SoundLocation__Sequence *
robot_msg__msg__SoundLocation__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__SoundLocation__Sequence * array = (robot_msg__msg__SoundLocation__Sequence *)allocator.allocate(sizeof(robot_msg__msg__SoundLocation__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_msg__msg__SoundLocation__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_msg__msg__SoundLocation__Sequence__destroy(robot_msg__msg__SoundLocation__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_msg__msg__SoundLocation__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_msg__msg__SoundLocation__Sequence__are_equal(const robot_msg__msg__SoundLocation__Sequence * lhs, const robot_msg__msg__SoundLocation__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_msg__msg__SoundLocation__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_msg__msg__SoundLocation__Sequence__copy(
  const robot_msg__msg__SoundLocation__Sequence * input,
  robot_msg__msg__SoundLocation__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_msg__msg__SoundLocation);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_msg__msg__SoundLocation * data =
      (robot_msg__msg__SoundLocation *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_msg__msg__SoundLocation__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_msg__msg__SoundLocation__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_msg__msg__SoundLocation__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
