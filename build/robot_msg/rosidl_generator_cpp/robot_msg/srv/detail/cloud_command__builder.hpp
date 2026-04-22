// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_msg:srv/CloudCommand.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__BUILDER_HPP_
#define ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_msg/srv/detail/cloud_command__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_msg
{

namespace srv
{

namespace builder
{

class Init_CloudCommand_Request_payload_json
{
public:
  explicit Init_CloudCommand_Request_payload_json(::robot_msg::srv::CloudCommand_Request & msg)
  : msg_(msg)
  {}
  ::robot_msg::srv::CloudCommand_Request payload_json(::robot_msg::srv::CloudCommand_Request::_payload_json_type arg)
  {
    msg_.payload_json = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_msg::srv::CloudCommand_Request msg_;
};

class Init_CloudCommand_Request_target_service
{
public:
  Init_CloudCommand_Request_target_service()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_CloudCommand_Request_payload_json target_service(::robot_msg::srv::CloudCommand_Request::_target_service_type arg)
  {
    msg_.target_service = std::move(arg);
    return Init_CloudCommand_Request_payload_json(msg_);
  }

private:
  ::robot_msg::srv::CloudCommand_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::srv::CloudCommand_Request>()
{
  return robot_msg::srv::builder::Init_CloudCommand_Request_target_service();
}

}  // namespace robot_msg


namespace robot_msg
{

namespace srv
{

namespace builder
{

class Init_CloudCommand_Response_response_json
{
public:
  Init_CloudCommand_Response_response_json()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::robot_msg::srv::CloudCommand_Response response_json(::robot_msg::srv::CloudCommand_Response::_response_json_type arg)
  {
    msg_.response_json = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_msg::srv::CloudCommand_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::srv::CloudCommand_Response>()
{
  return robot_msg::srv::builder::Init_CloudCommand_Response_response_json();
}

}  // namespace robot_msg

#endif  // ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__BUILDER_HPP_
