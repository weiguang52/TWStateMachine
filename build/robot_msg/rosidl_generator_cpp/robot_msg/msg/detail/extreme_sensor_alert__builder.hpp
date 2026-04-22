// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_msg:msg/ExtremeSensorAlert.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__BUILDER_HPP_
#define ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_msg/msg/detail/extreme_sensor_alert__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_msg
{

namespace msg
{

namespace builder
{

class Init_ExtremeSensorAlert_alert_id
{
public:
  explicit Init_ExtremeSensorAlert_alert_id(::robot_msg::msg::ExtremeSensorAlert & msg)
  : msg_(msg)
  {}
  ::robot_msg::msg::ExtremeSensorAlert alert_id(::robot_msg::msg::ExtremeSensorAlert::_alert_id_type arg)
  {
    msg_.alert_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_msg::msg::ExtremeSensorAlert msg_;
};

class Init_ExtremeSensorAlert_is_active
{
public:
  explicit Init_ExtremeSensorAlert_is_active(::robot_msg::msg::ExtremeSensorAlert & msg)
  : msg_(msg)
  {}
  Init_ExtremeSensorAlert_alert_id is_active(::robot_msg::msg::ExtremeSensorAlert::_is_active_type arg)
  {
    msg_.is_active = std::move(arg);
    return Init_ExtremeSensorAlert_alert_id(msg_);
  }

private:
  ::robot_msg::msg::ExtremeSensorAlert msg_;
};

class Init_ExtremeSensorAlert_timestamp
{
public:
  explicit Init_ExtremeSensorAlert_timestamp(::robot_msg::msg::ExtremeSensorAlert & msg)
  : msg_(msg)
  {}
  Init_ExtremeSensorAlert_is_active timestamp(::robot_msg::msg::ExtremeSensorAlert::_timestamp_type arg)
  {
    msg_.timestamp = std::move(arg);
    return Init_ExtremeSensorAlert_is_active(msg_);
  }

private:
  ::robot_msg::msg::ExtremeSensorAlert msg_;
};

class Init_ExtremeSensorAlert_description
{
public:
  explicit Init_ExtremeSensorAlert_description(::robot_msg::msg::ExtremeSensorAlert & msg)
  : msg_(msg)
  {}
  Init_ExtremeSensorAlert_timestamp description(::robot_msg::msg::ExtremeSensorAlert::_description_type arg)
  {
    msg_.description = std::move(arg);
    return Init_ExtremeSensorAlert_timestamp(msg_);
  }

private:
  ::robot_msg::msg::ExtremeSensorAlert msg_;
};

class Init_ExtremeSensorAlert_threshold_value
{
public:
  explicit Init_ExtremeSensorAlert_threshold_value(::robot_msg::msg::ExtremeSensorAlert & msg)
  : msg_(msg)
  {}
  Init_ExtremeSensorAlert_description threshold_value(::robot_msg::msg::ExtremeSensorAlert::_threshold_value_type arg)
  {
    msg_.threshold_value = std::move(arg);
    return Init_ExtremeSensorAlert_description(msg_);
  }

private:
  ::robot_msg::msg::ExtremeSensorAlert msg_;
};

class Init_ExtremeSensorAlert_current_value
{
public:
  explicit Init_ExtremeSensorAlert_current_value(::robot_msg::msg::ExtremeSensorAlert & msg)
  : msg_(msg)
  {}
  Init_ExtremeSensorAlert_threshold_value current_value(::robot_msg::msg::ExtremeSensorAlert::_current_value_type arg)
  {
    msg_.current_value = std::move(arg);
    return Init_ExtremeSensorAlert_threshold_value(msg_);
  }

private:
  ::robot_msg::msg::ExtremeSensorAlert msg_;
};

class Init_ExtremeSensorAlert_alert_type
{
public:
  explicit Init_ExtremeSensorAlert_alert_type(::robot_msg::msg::ExtremeSensorAlert & msg)
  : msg_(msg)
  {}
  Init_ExtremeSensorAlert_current_value alert_type(::robot_msg::msg::ExtremeSensorAlert::_alert_type_type arg)
  {
    msg_.alert_type = std::move(arg);
    return Init_ExtremeSensorAlert_current_value(msg_);
  }

private:
  ::robot_msg::msg::ExtremeSensorAlert msg_;
};

class Init_ExtremeSensorAlert_alert_level
{
public:
  explicit Init_ExtremeSensorAlert_alert_level(::robot_msg::msg::ExtremeSensorAlert & msg)
  : msg_(msg)
  {}
  Init_ExtremeSensorAlert_alert_type alert_level(::robot_msg::msg::ExtremeSensorAlert::_alert_level_type arg)
  {
    msg_.alert_level = std::move(arg);
    return Init_ExtremeSensorAlert_alert_type(msg_);
  }

private:
  ::robot_msg::msg::ExtremeSensorAlert msg_;
};

class Init_ExtremeSensorAlert_sensor_type
{
public:
  Init_ExtremeSensorAlert_sensor_type()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ExtremeSensorAlert_alert_level sensor_type(::robot_msg::msg::ExtremeSensorAlert::_sensor_type_type arg)
  {
    msg_.sensor_type = std::move(arg);
    return Init_ExtremeSensorAlert_alert_level(msg_);
  }

private:
  ::robot_msg::msg::ExtremeSensorAlert msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::msg::ExtremeSensorAlert>()
{
  return robot_msg::msg::builder::Init_ExtremeSensorAlert_sensor_type();
}

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__BUILDER_HPP_
