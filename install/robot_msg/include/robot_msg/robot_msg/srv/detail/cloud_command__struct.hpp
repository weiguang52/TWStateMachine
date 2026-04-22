// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_msg:srv/CloudCommand.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__STRUCT_HPP_
#define ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__robot_msg__srv__CloudCommand_Request __attribute__((deprecated))
#else
# define DEPRECATED__robot_msg__srv__CloudCommand_Request __declspec(deprecated)
#endif

namespace robot_msg
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct CloudCommand_Request_
{
  using Type = CloudCommand_Request_<ContainerAllocator>;

  explicit CloudCommand_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->target_service = "";
      this->payload_json = "";
    }
  }

  explicit CloudCommand_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : target_service(_alloc),
    payload_json(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->target_service = "";
      this->payload_json = "";
    }
  }

  // field types and members
  using _target_service_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _target_service_type target_service;
  using _payload_json_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _payload_json_type payload_json;

  // setters for named parameter idiom
  Type & set__target_service(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->target_service = _arg;
    return *this;
  }
  Type & set__payload_json(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->payload_json = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    robot_msg::srv::CloudCommand_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_msg::srv::CloudCommand_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_msg::srv::CloudCommand_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_msg::srv::CloudCommand_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_msg::srv::CloudCommand_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_msg::srv::CloudCommand_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_msg::srv::CloudCommand_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_msg::srv::CloudCommand_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_msg::srv::CloudCommand_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_msg::srv::CloudCommand_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_msg__srv__CloudCommand_Request
    std::shared_ptr<robot_msg::srv::CloudCommand_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_msg__srv__CloudCommand_Request
    std::shared_ptr<robot_msg::srv::CloudCommand_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const CloudCommand_Request_ & other) const
  {
    if (this->target_service != other.target_service) {
      return false;
    }
    if (this->payload_json != other.payload_json) {
      return false;
    }
    return true;
  }
  bool operator!=(const CloudCommand_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct CloudCommand_Request_

// alias to use template instance with default allocator
using CloudCommand_Request =
  robot_msg::srv::CloudCommand_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace robot_msg


#ifndef _WIN32
# define DEPRECATED__robot_msg__srv__CloudCommand_Response __attribute__((deprecated))
#else
# define DEPRECATED__robot_msg__srv__CloudCommand_Response __declspec(deprecated)
#endif

namespace robot_msg
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct CloudCommand_Response_
{
  using Type = CloudCommand_Response_<ContainerAllocator>;

  explicit CloudCommand_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->response_json = "";
    }
  }

  explicit CloudCommand_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : response_json(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->response_json = "";
    }
  }

  // field types and members
  using _response_json_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _response_json_type response_json;

  // setters for named parameter idiom
  Type & set__response_json(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->response_json = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    robot_msg::srv::CloudCommand_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_msg::srv::CloudCommand_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_msg::srv::CloudCommand_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_msg::srv::CloudCommand_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_msg::srv::CloudCommand_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_msg::srv::CloudCommand_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_msg::srv::CloudCommand_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_msg::srv::CloudCommand_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_msg::srv::CloudCommand_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_msg::srv::CloudCommand_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_msg__srv__CloudCommand_Response
    std::shared_ptr<robot_msg::srv::CloudCommand_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_msg__srv__CloudCommand_Response
    std::shared_ptr<robot_msg::srv::CloudCommand_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const CloudCommand_Response_ & other) const
  {
    if (this->response_json != other.response_json) {
      return false;
    }
    return true;
  }
  bool operator!=(const CloudCommand_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct CloudCommand_Response_

// alias to use template instance with default allocator
using CloudCommand_Response =
  robot_msg::srv::CloudCommand_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace robot_msg

namespace robot_msg
{

namespace srv
{

struct CloudCommand
{
  using Request = robot_msg::srv::CloudCommand_Request;
  using Response = robot_msg::srv::CloudCommand_Response;
};

}  // namespace srv

}  // namespace robot_msg

#endif  // ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__STRUCT_HPP_
