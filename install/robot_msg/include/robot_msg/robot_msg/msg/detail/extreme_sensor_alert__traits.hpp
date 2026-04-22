// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_msg:msg/ExtremeSensorAlert.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__TRAITS_HPP_
#define ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_msg/msg/detail/extreme_sensor_alert__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace robot_msg
{

namespace msg
{

inline void to_flow_style_yaml(
  const ExtremeSensorAlert & msg,
  std::ostream & out)
{
  out << "{";
  // member: sensor_type
  {
    out << "sensor_type: ";
    rosidl_generator_traits::value_to_yaml(msg.sensor_type, out);
    out << ", ";
  }

  // member: alert_level
  {
    out << "alert_level: ";
    rosidl_generator_traits::value_to_yaml(msg.alert_level, out);
    out << ", ";
  }

  // member: alert_type
  {
    out << "alert_type: ";
    rosidl_generator_traits::value_to_yaml(msg.alert_type, out);
    out << ", ";
  }

  // member: current_value
  {
    out << "current_value: ";
    rosidl_generator_traits::value_to_yaml(msg.current_value, out);
    out << ", ";
  }

  // member: threshold_value
  {
    out << "threshold_value: ";
    rosidl_generator_traits::value_to_yaml(msg.threshold_value, out);
    out << ", ";
  }

  // member: description
  {
    out << "description: ";
    rosidl_generator_traits::value_to_yaml(msg.description, out);
    out << ", ";
  }

  // member: timestamp
  {
    out << "timestamp: ";
    to_flow_style_yaml(msg.timestamp, out);
    out << ", ";
  }

  // member: is_active
  {
    out << "is_active: ";
    rosidl_generator_traits::value_to_yaml(msg.is_active, out);
    out << ", ";
  }

  // member: alert_id
  {
    out << "alert_id: ";
    rosidl_generator_traits::value_to_yaml(msg.alert_id, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ExtremeSensorAlert & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: sensor_type
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "sensor_type: ";
    rosidl_generator_traits::value_to_yaml(msg.sensor_type, out);
    out << "\n";
  }

  // member: alert_level
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "alert_level: ";
    rosidl_generator_traits::value_to_yaml(msg.alert_level, out);
    out << "\n";
  }

  // member: alert_type
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "alert_type: ";
    rosidl_generator_traits::value_to_yaml(msg.alert_type, out);
    out << "\n";
  }

  // member: current_value
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "current_value: ";
    rosidl_generator_traits::value_to_yaml(msg.current_value, out);
    out << "\n";
  }

  // member: threshold_value
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "threshold_value: ";
    rosidl_generator_traits::value_to_yaml(msg.threshold_value, out);
    out << "\n";
  }

  // member: description
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "description: ";
    rosidl_generator_traits::value_to_yaml(msg.description, out);
    out << "\n";
  }

  // member: timestamp
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "timestamp:\n";
    to_block_style_yaml(msg.timestamp, out, indentation + 2);
  }

  // member: is_active
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "is_active: ";
    rosidl_generator_traits::value_to_yaml(msg.is_active, out);
    out << "\n";
  }

  // member: alert_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "alert_id: ";
    rosidl_generator_traits::value_to_yaml(msg.alert_id, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ExtremeSensorAlert & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace robot_msg

namespace rosidl_generator_traits
{

[[deprecated("use robot_msg::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const robot_msg::msg::ExtremeSensorAlert & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_msg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_msg::msg::to_yaml() instead")]]
inline std::string to_yaml(const robot_msg::msg::ExtremeSensorAlert & msg)
{
  return robot_msg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<robot_msg::msg::ExtremeSensorAlert>()
{
  return "robot_msg::msg::ExtremeSensorAlert";
}

template<>
inline const char * name<robot_msg::msg::ExtremeSensorAlert>()
{
  return "robot_msg/msg/ExtremeSensorAlert";
}

template<>
struct has_fixed_size<robot_msg::msg::ExtremeSensorAlert>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_msg::msg::ExtremeSensorAlert>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_msg::msg::ExtremeSensorAlert>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_MSG__MSG__DETAIL__EXTREME_SENSOR_ALERT__TRAITS_HPP_
