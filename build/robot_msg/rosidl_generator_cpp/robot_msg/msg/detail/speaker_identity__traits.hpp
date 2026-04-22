// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_msg:msg/SpeakerIdentity.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__TRAITS_HPP_
#define ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_msg/msg/detail/speaker_identity__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace robot_msg
{

namespace msg
{

inline void to_flow_style_yaml(
  const SpeakerIdentity & msg,
  std::ostream & out)
{
  out << "{";
  // member: speaker_id
  {
    out << "speaker_id: ";
    rosidl_generator_traits::value_to_yaml(msg.speaker_id, out);
    out << ", ";
  }

  // member: speaker_name
  {
    out << "speaker_name: ";
    rosidl_generator_traits::value_to_yaml(msg.speaker_name, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << ", ";
  }

  // member: is_registered
  {
    out << "is_registered: ";
    rosidl_generator_traits::value_to_yaml(msg.is_registered, out);
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
  const SpeakerIdentity & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: speaker_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "speaker_id: ";
    rosidl_generator_traits::value_to_yaml(msg.speaker_id, out);
    out << "\n";
  }

  // member: speaker_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "speaker_name: ";
    rosidl_generator_traits::value_to_yaml(msg.speaker_name, out);
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

  // member: is_registered
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "is_registered: ";
    rosidl_generator_traits::value_to_yaml(msg.is_registered, out);
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

inline std::string to_yaml(const SpeakerIdentity & msg, bool use_flow_style = false)
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
  const robot_msg::msg::SpeakerIdentity & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_msg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_msg::msg::to_yaml() instead")]]
inline std::string to_yaml(const robot_msg::msg::SpeakerIdentity & msg)
{
  return robot_msg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<robot_msg::msg::SpeakerIdentity>()
{
  return "robot_msg::msg::SpeakerIdentity";
}

template<>
inline const char * name<robot_msg::msg::SpeakerIdentity>()
{
  return "robot_msg/msg/SpeakerIdentity";
}

template<>
struct has_fixed_size<robot_msg::msg::SpeakerIdentity>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_msg::msg::SpeakerIdentity>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_msg::msg::SpeakerIdentity>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__TRAITS_HPP_
