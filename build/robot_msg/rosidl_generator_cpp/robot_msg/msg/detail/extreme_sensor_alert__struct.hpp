// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_msg:msg/ExtremeSensorAlert.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__STRUCT_HPP_
#define ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__STRUCT_HPP_

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
# define DEPRECATED__robot_msg__msg__ExtremeSensorAlert __attribute__((deprecated))
#else
# define DEPRECATED__robot_msg__msg__ExtremeSensorAlert __declspec(deprecated)
#endif

namespace robot_msg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct ExtremeSensorAlert_
{
  using Type = ExtremeSensorAlert_<ContainerAllocator>;

  explicit ExtremeSensorAlert_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : timestamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sensor_type = "";
      this->alert_level = "";
      this->alert_type = "";
      this->current_value = 0.0;
      this->threshold_value = 0.0;
      this->description = "";
      this->is_active = false;
      this->alert_id = 0ul;
    }
  }

  explicit ExtremeSensorAlert_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : sensor_type(_alloc),
    alert_level(_alloc),
    alert_type(_alloc),
    description(_alloc),
    timestamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sensor_type = "";
      this->alert_level = "";
      this->alert_type = "";
      this->current_value = 0.0;
      this->threshold_value = 0.0;
      this->description = "";
      this->is_active = false;
      this->alert_id = 0ul;
    }
  }

  // field types and members
  using _sensor_type_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _sensor_type_type sensor_type;
  using _alert_level_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _alert_level_type alert_level;
  using _alert_type_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _alert_type_type alert_type;
  using _current_value_type =
    double;
  _current_value_type current_value;
  using _threshold_value_type =
    double;
  _threshold_value_type threshold_value;
  using _description_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _description_type description;
  using _timestamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _timestamp_type timestamp;
  using _is_active_type =
    bool;
  _is_active_type is_active;
  using _alert_id_type =
    uint32_t;
  _alert_id_type alert_id;

  // setters for named parameter idiom
  Type & set__sensor_type(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->sensor_type = _arg;
    return *this;
  }
  Type & set__alert_level(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->alert_level = _arg;
    return *this;
  }
  Type & set__alert_type(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->alert_type = _arg;
    return *this;
  }
  Type & set__current_value(
    const double & _arg)
  {
    this->current_value = _arg;
    return *this;
  }
  Type & set__threshold_value(
    const double & _arg)
  {
    this->threshold_value = _arg;
    return *this;
  }
  Type & set__description(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->description = _arg;
    return *this;
  }
  Type & set__timestamp(
    const builtin_interfaces::msg::Time_<ContainerAllocator> & _arg)
  {
    this->timestamp = _arg;
    return *this;
  }
  Type & set__is_active(
    const bool & _arg)
  {
    this->is_active = _arg;
    return *this;
  }
  Type & set__alert_id(
    const uint32_t & _arg)
  {
    this->alert_id = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_msg__msg__ExtremeSensorAlert
    std::shared_ptr<robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_msg__msg__ExtremeSensorAlert
    std::shared_ptr<robot_msg::msg::ExtremeSensorAlert_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExtremeSensorAlert_ & other) const
  {
    if (this->sensor_type != other.sensor_type) {
      return false;
    }
    if (this->alert_level != other.alert_level) {
      return false;
    }
    if (this->alert_type != other.alert_type) {
      return false;
    }
    if (this->current_value != other.current_value) {
      return false;
    }
    if (this->threshold_value != other.threshold_value) {
      return false;
    }
    if (this->description != other.description) {
      return false;
    }
    if (this->timestamp != other.timestamp) {
      return false;
    }
    if (this->is_active != other.is_active) {
      return false;
    }
    if (this->alert_id != other.alert_id) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExtremeSensorAlert_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExtremeSensorAlert_

// alias to use template instance with default allocator
using ExtremeSensorAlert =
  robot_msg::msg::ExtremeSensorAlert_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__STRUCT_HPP_
