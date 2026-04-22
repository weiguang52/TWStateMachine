// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_msg:msg/SoundLocation.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__TRAITS_HPP_
#define ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_msg/msg/detail/sound_location__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace robot_msg
{

namespace msg
{

inline void to_flow_style_yaml(
  const SoundLocation & msg,
  std::ostream & out)
{
  out << "{";
  // member: azimuth
  {
    out << "azimuth: ";
    rosidl_generator_traits::value_to_yaml(msg.azimuth, out);
    out << ", ";
  }

  // member: elevation
  {
    out << "elevation: ";
    rosidl_generator_traits::value_to_yaml(msg.elevation, out);
    out << ", ";
  }

  // member: distance
  {
    out << "distance: ";
    rosidl_generator_traits::value_to_yaml(msg.distance, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << ", ";
  }

  // member: timestamp
  {
    out << "timestamp: ";
    to_flow_style_yaml(msg.timestamp, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const SoundLocation & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: azimuth
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "azimuth: ";
    rosidl_generator_traits::value_to_yaml(msg.azimuth, out);
    out << "\n";
  }

  // member: elevation
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "elevation: ";
    rosidl_generator_traits::value_to_yaml(msg.elevation, out);
    out << "\n";
  }

  // member: distance
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "distance: ";
    rosidl_generator_traits::value_to_yaml(msg.distance, out);
    out << "\n";
  }

  // member: confidence
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
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
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const SoundLocation & msg, bool use_flow_style = false)
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
  const robot_msg::msg::SoundLocation & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_msg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_msg::msg::to_yaml() instead")]]
inline std::string to_yaml(const robot_msg::msg::SoundLocation & msg)
{
  return robot_msg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<robot_msg::msg::SoundLocation>()
{
  return "robot_msg::msg::SoundLocation";
}

template<>
inline const char * name<robot_msg::msg::SoundLocation>()
{
  return "robot_msg/msg/SoundLocation";
}

template<>
struct has_fixed_size<robot_msg::msg::SoundLocation>
  : std::integral_constant<bool, has_fixed_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct has_bounded_size<robot_msg::msg::SoundLocation>
  : std::integral_constant<bool, has_bounded_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct is_message<robot_msg::msg::SoundLocation>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__TRAITS_HPP_
