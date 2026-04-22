// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_msg:msg/SpeakerIdentity.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__STRUCT_HPP_
#define ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__STRUCT_HPP_

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
# define DEPRECATED__robot_msg__msg__SpeakerIdentity __attribute__((deprecated))
#else
# define DEPRECATED__robot_msg__msg__SpeakerIdentity __declspec(deprecated)
#endif

namespace robot_msg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct SpeakerIdentity_
{
  using Type = SpeakerIdentity_<ContainerAllocator>;

  explicit SpeakerIdentity_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : timestamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->speaker_id = "";
      this->speaker_name = "";
      this->confidence = 0.0f;
      this->is_registered = false;
    }
  }

  explicit SpeakerIdentity_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : speaker_id(_alloc),
    speaker_name(_alloc),
    timestamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->speaker_id = "";
      this->speaker_name = "";
      this->confidence = 0.0f;
      this->is_registered = false;
    }
  }

  // field types and members
  using _speaker_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _speaker_id_type speaker_id;
  using _speaker_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _speaker_name_type speaker_name;
  using _confidence_type =
    float;
  _confidence_type confidence;
  using _is_registered_type =
    bool;
  _is_registered_type is_registered;
  using _timestamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _timestamp_type timestamp;

  // setters for named parameter idiom
  Type & set__speaker_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->speaker_id = _arg;
    return *this;
  }
  Type & set__speaker_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->speaker_name = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }
  Type & set__is_registered(
    const bool & _arg)
  {
    this->is_registered = _arg;
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
    robot_msg::msg::SpeakerIdentity_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_msg::msg::SpeakerIdentity_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_msg::msg::SpeakerIdentity_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_msg::msg::SpeakerIdentity_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::SpeakerIdentity_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::SpeakerIdentity_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::SpeakerIdentity_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::SpeakerIdentity_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_msg::msg::SpeakerIdentity_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_msg::msg::SpeakerIdentity_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_msg__msg__SpeakerIdentity
    std::shared_ptr<robot_msg::msg::SpeakerIdentity_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_msg__msg__SpeakerIdentity
    std::shared_ptr<robot_msg::msg::SpeakerIdentity_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SpeakerIdentity_ & other) const
  {
    if (this->speaker_id != other.speaker_id) {
      return false;
    }
    if (this->speaker_name != other.speaker_name) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->is_registered != other.is_registered) {
      return false;
    }
    if (this->timestamp != other.timestamp) {
      return false;
    }
    return true;
  }
  bool operator!=(const SpeakerIdentity_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SpeakerIdentity_

// alias to use template instance with default allocator
using SpeakerIdentity =
  robot_msg::msg::SpeakerIdentity_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__STRUCT_HPP_
