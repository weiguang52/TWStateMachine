// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_msg:msg/SpeechData.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__STRUCT_HPP_
#define ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__robot_msg__msg__SpeechData __attribute__((deprecated))
#else
# define DEPRECATED__robot_msg__msg__SpeechData __declspec(deprecated)
#endif

namespace robot_msg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct SpeechData_
{
  using Type = SpeechData_<ContainerAllocator>;

  explicit SpeechData_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : timestamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sample_rate = 0ul;
      this->channels = 0ul;
      this->duration = 0.0f;
    }
  }

  explicit SpeechData_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : timestamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sample_rate = 0ul;
      this->channels = 0ul;
      this->duration = 0.0f;
    }
  }

  // field types and members
  using _audio_data_type =
    std::vector<uint8_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint8_t>>;
  _audio_data_type audio_data;
  using _sample_rate_type =
    uint32_t;
  _sample_rate_type sample_rate;
  using _channels_type =
    uint32_t;
  _channels_type channels;
  using _duration_type =
    float;
  _duration_type duration;
  using _timestamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _timestamp_type timestamp;

  // setters for named parameter idiom
  Type & set__audio_data(
    const std::vector<uint8_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint8_t>> & _arg)
  {
    this->audio_data = _arg;
    return *this;
  }
  Type & set__sample_rate(
    const uint32_t & _arg)
  {
    this->sample_rate = _arg;
    return *this;
  }
  Type & set__channels(
    const uint32_t & _arg)
  {
    this->channels = _arg;
    return *this;
  }
  Type & set__duration(
    const float & _arg)
  {
    this->duration = _arg;
    return *this;
  }
  Type & set__timestamp(
    const builtin_interfaces::msg::Time_<ContainerAllocator> & _arg)
  {
    this->timestamp = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    robot_msg::msg::SpeechData_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_msg::msg::SpeechData_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_msg::msg::SpeechData_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_msg::msg::SpeechData_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::SpeechData_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::SpeechData_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::SpeechData_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::SpeechData_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_msg::msg::SpeechData_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_msg::msg::SpeechData_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_msg__msg__SpeechData
    std::shared_ptr<robot_msg::msg::SpeechData_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_msg__msg__SpeechData
    std::shared_ptr<robot_msg::msg::SpeechData_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SpeechData_ & other) const
  {
    if (this->audio_data != other.audio_data) {
      return false;
    }
    if (this->sample_rate != other.sample_rate) {
      return false;
    }
    if (this->channels != other.channels) {
      return false;
    }
    if (this->duration != other.duration) {
      return false;
    }
    if (this->timestamp != other.timestamp) {
      return false;
    }
    return true;
  }
  bool operator!=(const SpeechData_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SpeechData_

// alias to use template instance with default allocator
using SpeechData =
  robot_msg::msg::SpeechData_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__STRUCT_HPP_
