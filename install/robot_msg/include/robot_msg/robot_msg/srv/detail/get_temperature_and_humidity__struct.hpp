// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_msg:srv/GetTemperatureAndHumidity.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__SRV__DETAIL__GET_TEMPERATURE_AND_HUMIDITY__STRUCT_HPP_
#define ROBOT_MSG__SRV__DETAIL__GET_TEMPERATURE_AND_HUMIDITY__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__robot_msg__srv__GetTemperatureAndHumidity_Request __attribute__((deprecated))
#else
# define DEPRECATED__robot_msg__srv__GetTemperatureAndHumidity_Request __declspec(deprecated)
#endif

namespace robot_msg
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetTemperatureAndHumidity_Request_
{
  using Type = GetTemperatureAndHumidity_Request_<ContainerAllocator>;

  explicit GetTemperatureAndHumidity_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit GetTemperatureAndHumidity_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  // field types and members
  using _structure_needs_at_least_one_member_type =
    uint8_t;
  _structure_needs_at_least_one_member_type structure_needs_at_least_one_member;


  // constant declarations

  // pointer types
  using RawPtr =
    robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_msg__srv__GetTemperatureAndHumidity_Request
    std::shared_ptr<robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_msg__srv__GetTemperatureAndHumidity_Request
    std::shared_ptr<robot_msg::srv::GetTemperatureAndHumidity_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetTemperatureAndHumidity_Request_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetTemperatureAndHumidity_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetTemperatureAndHumidity_Request_

// alias to use template instance with default allocator
using GetTemperatureAndHumidity_Request =
  robot_msg::srv::GetTemperatureAndHumidity_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace robot_msg


#ifndef _WIN32
# define DEPRECATED__robot_msg__srv__GetTemperatureAndHumidity_Response __attribute__((deprecated))
#else
# define DEPRECATED__robot_msg__srv__GetTemperatureAndHumidity_Response __declspec(deprecated)
#endif

namespace robot_msg
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetTemperatureAndHumidity_Response_
{
  using Type = GetTemperatureAndHumidity_Response_<ContainerAllocator>;

  explicit GetTemperatureAndHumidity_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->temperature = 0.0;
      this->humidity = 0.0;
      this->success = false;
      this->message = "";
    }
  }

  explicit GetTemperatureAndHumidity_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->temperature = 0.0;
      this->humidity = 0.0;
      this->success = false;
      this->message = "";
    }
  }

  // field types and members
  using _temperature_type =
    double;
  _temperature_type temperature;
  using _humidity_type =
    double;
  _humidity_type humidity;
  using _success_type =
    bool;
  _success_type success;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__temperature(
    const double & _arg)
  {
    this->temperature = _arg;
    return *this;
  }
  Type & set__humidity(
    const double & _arg)
  {
    this->humidity = _arg;
    return *this;
  }
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_msg__srv__GetTemperatureAndHumidity_Response
    std::shared_ptr<robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_msg__srv__GetTemperatureAndHumidity_Response
    std::shared_ptr<robot_msg::srv::GetTemperatureAndHumidity_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetTemperatureAndHumidity_Response_ & other) const
  {
    if (this->temperature != other.temperature) {
      return false;
    }
    if (this->humidity != other.humidity) {
      return false;
    }
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetTemperatureAndHumidity_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetTemperatureAndHumidity_Response_

// alias to use template instance with default allocator
using GetTemperatureAndHumidity_Response =
  robot_msg::srv::GetTemperatureAndHumidity_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace robot_msg

namespace robot_msg
{

namespace srv
{

struct GetTemperatureAndHumidity
{
  using Request = robot_msg::srv::GetTemperatureAndHumidity_Request;
  using Response = robot_msg::srv::GetTemperatureAndHumidity_Response;
};

}  // namespace srv

}  // namespace robot_msg

#endif  // ROBOT_MSG__SRV__DETAIL__GET_TEMPERATURE_AND_HUMIDITY__STRUCT_HPP_
