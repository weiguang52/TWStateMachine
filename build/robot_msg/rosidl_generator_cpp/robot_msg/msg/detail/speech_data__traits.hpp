// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_msg:msg/SpeechData.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__TRAITS_HPP_
#define ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_msg/msg/detail/speech_data__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace robot_msg
{

namespace msg
{

inline void to_flow_style_yaml(
  const SpeechData & msg,
  std::ostream & out)
{
  out << "{";
  // member: audio_data
  {
    if (msg.audio_data.size() == 0) {
      out << "audio_data: []";
    } else {
      out << "audio_data: [";
      size_t pending_items = msg.audio_data.size();
      for (auto item : msg.audio_data) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: sample_rate
  {
    out << "sample_rate: ";
    rosidl_generator_traits::value_to_yaml(msg.sample_rate, out);
    out << ", ";
  }

  // member: channels
  {
    out << "channels: ";
    rosidl_generator_traits::value_to_yaml(msg.channels, out);
    out << ", ";
  }

  // member: duration
  {
    out << "duration: ";
    rosidl_generator_traits::value_to_yaml(msg.duration, out);
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
  const SpeechData & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: audio_data
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.audio_data.size() == 0) {
      out << "audio_data: []\n";
    } else {
      out << "audio_data:\n";
      for (auto item : msg.audio_data) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: sample_rate
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "sample_rate: ";
    rosidl_generator_traits::value_to_yaml(msg.sample_rate, out);
    out << "\n";
  }

  // member: channels
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "channels: ";
    rosidl_generator_traits::value_to_yaml(msg.channels, out);
    out << "\n";
  }

  // member: duration
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "duration: ";
    rosidl_generator_traits::value_to_yaml(msg.duration, out);
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

inline std::string to_yaml(const SpeechData & msg, bool use_flow_style = false)
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
  const robot_msg::msg::SpeechData & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_msg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_msg::msg::to_yaml() instead")]]
inline std::string to_yaml(const robot_msg::msg::SpeechData & msg)
{
  return robot_msg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<robot_msg::msg::SpeechData>()
{
  return "robot_msg::msg::SpeechData";
}

template<>
inline const char * name<robot_msg::msg::SpeechData>()
{
  return "robot_msg/msg/SpeechData";
}

template<>
struct has_fixed_size<robot_msg::msg::SpeechData>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_msg::msg::SpeechData>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_msg::msg::SpeechData>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__TRAITS_HPP_
