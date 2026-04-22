// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_msg:msg/SoundType.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__TRAITS_HPP_
#define ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_msg/msg/detail/sound_type__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'timestamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace robot_msg
{

namespace msg
{

inline void to_flow_style_yaml(
  const SoundType & msg,
  std::ostream & out)
{
  out << "{";
  // member: sound_category
  {
    out << "sound_category: ";
    rosidl_generator_traits::value_to_yaml(msg.sound_category, out);
    out << ", ";
  }

  // member: detected_sounds
  {
    if (msg.detected_sounds.size() == 0) {
      out << "detected_sounds: []";
    } else {
      out << "detected_sounds: [";
      size_t pending_items = msg.detected_sounds.size();
      for (auto item : msg.detected_sounds) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: confidence_scores
  {
    if (msg.confidence_scores.size() == 0) {
      out << "confidence_scores: []";
    } else {
      out << "confidence_scores: [";
      size_t pending_items = msg.confidence_scores.size();
      for (auto item : msg.confidence_scores) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
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
  const SoundType & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: sound_category
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "sound_category: ";
    rosidl_generator_traits::value_to_yaml(msg.sound_category, out);
    out << "\n";
  }

  // member: detected_sounds
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.detected_sounds.size() == 0) {
      out << "detected_sounds: []\n";
    } else {
      out << "detected_sounds:\n";
      for (auto item : msg.detected_sounds) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: confidence_scores
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.confidence_scores.size() == 0) {
      out << "confidence_scores: []\n";
    } else {
      out << "confidence_scores:\n";
      for (auto item : msg.confidence_scores) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
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

inline std::string to_yaml(const SoundType & msg, bool use_flow_style = false)
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
  const robot_msg::msg::SoundType & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_msg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_msg::msg::to_yaml() instead")]]
inline std::string to_yaml(const robot_msg::msg::SoundType & msg)
{
  return robot_msg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<robot_msg::msg::SoundType>()
{
  return "robot_msg::msg::SoundType";
}

template<>
inline const char * name<robot_msg::msg::SoundType>()
{
  return "robot_msg/msg/SoundType";
}

template<>
struct has_fixed_size<robot_msg::msg::SoundType>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_msg::msg::SoundType>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_msg::msg::SoundType>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__TRAITS_HPP_
