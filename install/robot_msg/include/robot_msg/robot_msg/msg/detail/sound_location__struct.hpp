// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_msg:msg/SoundLocation.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__STRUCT_HPP_
#define ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__STRUCT_HPP_

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
# define DEPRECATED__robot_msg__msg__SoundLocation __attribute__((deprecated))
#else
# define DEPRECATED__robot_msg__msg__SoundLocation __declspec(deprecated)
#endif

namespace robot_msg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct SoundLocation_
{
  using Type = SoundLocation_<ContainerAllocator>;

  explicit SoundLocation_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : timestamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->azimuth = 0.0;
      this->elevation = 0.0;
      this->distance = 0.0;
      this->confidence = 0.0;
    }
  }

  explicit SoundLocation_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : timestamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->azimuth = 0.0;
      this->elevation = 0.0;
      this->distance = 0.0;
      this->confidence = 0.0;
    }
  }

  // field types and members
  using _azimuth_type =
    double;
  _azimuth_type azimuth;
  using _elevation_type =
    double;
  _elevation_type elevation;
  using _distance_type =
    double;
  _distance_type distance;
  using _confidence_type =
    double;
  _confidence_type confidence;
  using _timestamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _timestamp_type timestamp;

  // setters for named parameter idiom
  Type & set__azimuth(
    const double & _arg)
  {
    this->azimuth = _arg;
    return *this;
  }
  Type & set__elevation(
    const double & _arg)
  {
    this->elevation = _arg;
    return *this;
  }
  Type & set__distance(
    const double & _arg)
  {
    this->distance = _arg;
    return *this;
  }
  Type & set__confidence(
    const double & _arg)
  {
    this->confidence = _arg;
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
    robot_msg::msg::SoundLocation_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_msg::msg::SoundLocation_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_msg::msg::SoundLocation_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_msg::msg::SoundLocation_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::SoundLocation_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::SoundLocation_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::SoundLocation_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::SoundLocation_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_msg::msg::SoundLocation_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_msg::msg::SoundLocation_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_msg__msg__SoundLocation
    std::shared_ptr<robot_msg::msg::SoundLocation_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_msg__msg__SoundLocation
    std::shared_ptr<robot_msg::msg::SoundLocation_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SoundLocation_ & other) const
  {
    if (this->azimuth != other.azimuth) {
      return false;
    }
    if (this->elevation != other.elevation) {
      return false;
    }
    if (this->distance != other.distance) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->timestamp != other.timestamp) {
      return false;
    }
    return true;
  }
  bool operator!=(const SoundLocation_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SoundLocation_

// alias to use template instance with default allocator
using SoundLocation =
  robot_msg::msg::SoundLocation_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__STRUCT_HPP_
