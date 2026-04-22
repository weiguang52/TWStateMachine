// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_msg:srv/GetTemperatureAndHumidity.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__SRV__DETAIL__GET_TEMPERATURE_AND_HUMIDITY__BUILDER_HPP_
#define ROBOT_MSG__SRV__DETAIL__GET_TEMPERATURE_AND_HUMIDITY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_msg/srv/detail/get_temperature_and_humidity__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_msg
{

namespace srv
{


}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::srv::GetTemperatureAndHumidity_Request>()
{
  return ::robot_msg::srv::GetTemperatureAndHumidity_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace robot_msg


namespace robot_msg
{

namespace srv
{

namespace builder
{

class Init_GetTemperatureAndHumidity_Response_message
{
public:
  explicit Init_GetTemperatureAndHumidity_Response_message(::robot_msg::srv::GetTemperatureAndHumidity_Response & msg)
  : msg_(msg)
  {}
  ::robot_msg::srv::GetTemperatureAndHumidity_Response message(::robot_msg::srv::GetTemperatureAndHumidity_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_msg::srv::GetTemperatureAndHumidity_Response msg_;
};

class Init_GetTemperatureAndHumidity_Response_success
{
public:
  explicit Init_GetTemperatureAndHumidity_Response_success(::robot_msg::srv::GetTemperatureAndHumidity_Response & msg)
  : msg_(msg)
  {}
  Init_GetTemperatureAndHumidity_Response_message success(::robot_msg::srv::GetTemperatureAndHumidity_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_GetTemperatureAndHumidity_Response_message(msg_);
  }

private:
  ::robot_msg::srv::GetTemperatureAndHumidity_Response msg_;
};

class Init_GetTemperatureAndHumidity_Response_humidity
{
public:
  explicit Init_GetTemperatureAndHumidity_Response_humidity(::robot_msg::srv::GetTemperatureAndHumidity_Response & msg)
  : msg_(msg)
  {}
  Init_GetTemperatureAndHumidity_Response_success humidity(::robot_msg::srv::GetTemperatureAndHumidity_Response::_humidity_type arg)
  {
    msg_.humidity = std::move(arg);
    return Init_GetTemperatureAndHumidity_Response_success(msg_);
  }

private:
  ::robot_msg::srv::GetTemperatureAndHumidity_Response msg_;
};

class Init_GetTemperatureAndHumidity_Response_temperature
{
public:
  Init_GetTemperatureAndHumidity_Response_temperature()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GetTemperatureAndHumidity_Response_humidity temperature(::robot_msg::srv::GetTemperatureAndHumidity_Response::_temperature_type arg)
  {
    msg_.temperature = std::move(arg);
    return Init_GetTemperatureAndHumidity_Response_humidity(msg_);
  }

private:
  ::robot_msg::srv::GetTemperatureAndHumidity_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::srv::GetTemperatureAndHumidity_Response>()
{
  return robot_msg::srv::builder::Init_GetTemperatureAndHumidity_Response_temperature();
}

}  // namespace robot_msg

#endif  // ROBOT_MSG__SRV__DETAIL__GET_TEMPERATURE_AND_HUMIDITY__BUILDER_HPP_
