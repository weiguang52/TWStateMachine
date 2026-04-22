// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_msg:msg/SpeechData.idl
// generated code does not contain a copyright notice
#include "robot_msg/msg/detail/speech_data__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `audio_data`
#include "rosidl_runtime_c/primitives_sequence_functions.h"
// Member `timestamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
robot_msg__msg__SpeechData__init(robot_msg__msg__SpeechData * msg)
{
  if (!msg) {
    return false;
  }
  // audio_data
  if (!rosidl_runtime_c__uint8__Sequence__init(&msg->audio_data, 0)) {
    robot_msg__msg__SpeechData__fini(msg);
    return false;
  }
  // sample_rate
  // channels
  // duration
  // timestamp
  if (!builtin_interfaces__msg__Time__init(&msg->timestamp)) {
    robot_msg__msg__SpeechData__fini(msg);
    return false;
  }
  return true;
}

void
robot_msg__msg__SpeechData__fini(robot_msg__msg__SpeechData * msg)
{
  if (!msg) {
    return;
  }
  // audio_data
  rosidl_runtime_c__uint8__Sequence__fini(&msg->audio_data);
  // sample_rate
  // channels
  // duration
  // timestamp
  builtin_interfaces__msg__Time__fini(&msg->timestamp);
}

bool
robot_msg__msg__SpeechData__are_equal(const robot_msg__msg__SpeechData * lhs, const robot_msg__msg__SpeechData * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // audio_data
  if (!rosidl_runtime_c__uint8__Sequence__are_equal(
      &(lhs->audio_data), &(rhs->audio_data)))
  {
    return false;
  }
  // sample_rate
  if (lhs->sample_rate != rhs->sample_rate) {
    return false;
  }
  // channels
  if (lhs->channels != rhs->channels) {
    return false;
  }
  // duration
  if (lhs->duration != rhs->duration) {
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
robot_msg__msg__SpeechData__copy(
  const robot_msg__msg__SpeechData * input,
  robot_msg__msg__SpeechData * output)
{
  if (!input || !output) {
    return false;
  }
  // audio_data
  if (!rosidl_runtime_c__uint8__Sequence__copy(
      &(input->audio_data), &(output->audio_data)))
  {
    return false;
  }
  // sample_rate
  output->sample_rate = input->sample_rate;
  // channels
  output->channels = input->channels;
  // duration
  output->duration = input->duration;
  // timestamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->timestamp), &(output->timestamp)))
  {
    return false;
  }
  return true;
}

robot_msg__msg__SpeechData *
robot_msg__msg__SpeechData__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__SpeechData * msg = (robot_msg__msg__SpeechData *)allocator.allocate(sizeof(robot_msg__msg__SpeechData), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_msg__msg__SpeechData));
  bool success = robot_msg__msg__SpeechData__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_msg__msg__SpeechData__destroy(robot_msg__msg__SpeechData * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_msg__msg__SpeechData__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_msg__msg__SpeechData__Sequence__init(robot_msg__msg__SpeechData__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__SpeechData * data = NULL;

  if (size) {
    data = (robot_msg__msg__SpeechData *)allocator.zero_allocate(size, sizeof(robot_msg__msg__SpeechData), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_msg__msg__SpeechData__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_msg__msg__SpeechData__fini(&data[i - 1]);
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
robot_msg__msg__SpeechData__Sequence__fini(robot_msg__msg__SpeechData__Sequence * array)
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
      robot_msg__msg__SpeechData__fini(&array->data[i]);
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

robot_msg__msg__SpeechData__Sequence *
robot_msg__msg__SpeechData__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_msg__msg__SpeechData__Sequence * array = (robot_msg__msg__SpeechData__Sequence *)allocator.allocate(sizeof(robot_msg__msg__SpeechData__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_msg__msg__SpeechData__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_msg__msg__SpeechData__Sequence__destroy(robot_msg__msg__SpeechData__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_msg__msg__SpeechData__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_msg__msg__SpeechData__Sequence__are_equal(const robot_msg__msg__SpeechData__Sequence * lhs, const robot_msg__msg__SpeechData__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_msg__msg__SpeechData__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_msg__msg__SpeechData__Sequence__copy(
  const robot_msg__msg__SpeechData__Sequence * input,
  robot_msg__msg__SpeechData__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_msg__msg__SpeechData);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_msg__msg__SpeechData * data =
      (robot_msg__msg__SpeechData *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_msg__msg__SpeechData__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_msg__msg__SpeechData__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_msg__msg__SpeechData__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
