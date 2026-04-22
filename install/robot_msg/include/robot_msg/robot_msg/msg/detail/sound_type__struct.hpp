// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_msg:msg/SoundType.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__STRUCT_HPP_
#define ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__STRUCT_HPP_

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
# define DEPRECATED__robot_msg__msg__SoundType __attribute__((deprecated))
#else
# define DEPRECATED__robot_msg__msg__SoundType __declspec(deprecated)
#endif

namespace robot_msg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct SoundType_
{
  using Type = SoundType_<ContainerAllocator>;

  explicit SoundType_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : timestamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sound_category = "";
    }
  }

  explicit SoundType_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : sound_category(_alloc),
    timestamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sound_category = "";
    }
  }

  // field types and members
  using _sound_category_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _sound_category_type sound_category;
  using _detected_sounds_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _detected_sounds_type detected_sounds;
  using _confidence_scores_type =
    std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>>;
  _confidence_scores_type confidence_scores;
  using _timestamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _timestamp_type timestamp;

  // setters for named parameter idiom
  Type & set__sound_category(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->sound_category = _arg;
    return *this;
  }
  Type & set__detected_sounds(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->detected_sounds = _arg;
    return *this;
  }
  Type & set__confidence_scores(
    const std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>> & _arg)
  {
    this->confidence_scores = _arg;
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
    robot_msg::msg::SoundType_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_msg::msg::SoundType_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_msg::msg::SoundType_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_msg::msg::SoundType_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::SoundType_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::SoundType_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::SoundType_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::SoundType_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_msg::msg::SoundType_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_msg::msg::SoundType_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_msg__msg__SoundType
    std::shared_ptr<robot_msg::msg::SoundType_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_msg__msg__SoundType
    std::shared_ptr<robot_msg::msg::SoundType_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SoundType_ & other) const
  {
    if (this->sound_category != other.sound_category) {
      return false;
    }
    if (this->detected_sounds != other.detected_sounds) {
      return false;
    }
    if (this->confidence_scores != other.confidence_scores) {
      return false;
    }
    if (this->timestamp != other.timestamp) {
      return false;
    }
    return true;
  }
  bool operator!=(const SoundType_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SoundType_

// alias to use template instance with default allocator
using SoundType =
  robot_msg::msg::SoundType_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__STRUCT_HPP_
