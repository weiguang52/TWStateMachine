// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_msg:srv/CloudCommand.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__TRAITS_HPP_
#define ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_msg/srv/detail/cloud_command__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace robot_msg
{

namespace srv
{

inline void to_flow_style_yaml(
  const CloudCommand_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: target_service
  {
    out << "target_service: ";
    rosidl_generator_traits::value_to_yaml(msg.target_service, out);
    out << ", ";
  }

  // member: payload_json
  {
    out << "payload_json: ";
    rosidl_generator_traits::value_to_yaml(msg.payload_json, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const CloudCommand_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: target_service
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "target_service: ";
    rosidl_generator_traits::value_to_yaml(msg.target_service, out);
    out << "\n";
  }

  // member: payload_json
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "payload_json: ";
    rosidl_generator_traits::value_to_yaml(msg.payload_json, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const CloudCommand_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace robot_msg

namespace rosidl_generator_traits
{

[[deprecated("use robot_msg::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const robot_msg::srv::CloudCommand_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_msg::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_msg::srv::to_yaml() instead")]]
inline std::string to_yaml(const robot_msg::srv::CloudCommand_Request & msg)
{
  return robot_msg::srv::to_yaml(msg);
}

template<>
inline const char * data_type<robot_msg::srv::CloudCommand_Request>()
{
  return "robot_msg::srv::CloudCommand_Request";
}

template<>
inline const char * name<robot_msg::srv::CloudCommand_Request>()
{
  return "robot_msg/srv/CloudCommand_Request";
}

template<>
struct has_fixed_size<robot_msg::srv::CloudCommand_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_msg::srv::CloudCommand_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_msg::srv::CloudCommand_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace robot_msg
{

namespace srv
{

inline void to_flow_style_yaml(
  const CloudCommand_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: response_json
  {
    out << "response_json: ";
    rosidl_generator_traits::value_to_yaml(msg.response_json, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const CloudCommand_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: response_json
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "response_json: ";
    rosidl_generator_traits::value_to_yaml(msg.response_json, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const CloudCommand_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace robot_msg

namespace rosidl_generator_traits
{

[[deprecated("use robot_msg::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const robot_msg::srv::CloudCommand_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_msg::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_msg::srv::to_yaml() instead")]]
inline std::string to_yaml(const robot_msg::srv::CloudCommand_Response & msg)
{
  return robot_msg::srv::to_yaml(msg);
}

template<>
inline const char * data_type<robot_msg::srv::CloudCommand_Response>()
{
  return "robot_msg::srv::CloudCommand_Response";
}

template<>
inline const char * name<robot_msg::srv::CloudCommand_Response>()
{
  return "robot_msg/srv/CloudCommand_Response";
}

template<>
struct has_fixed_size<robot_msg::srv::CloudCommand_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_msg::srv::CloudCommand_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_msg::srv::CloudCommand_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<robot_msg::srv::CloudCommand>()
{
  return "robot_msg::srv::CloudCommand";
}

template<>
inline const char * name<robot_msg::srv::CloudCommand>()
{
  return "robot_msg/srv/CloudCommand";
}

template<>
struct has_fixed_size<robot_msg::srv::CloudCommand>
  : std::integral_constant<
    bool,
    has_fixed_size<robot_msg::srv::CloudCommand_Request>::value &&
    has_fixed_size<robot_msg::srv::CloudCommand_Response>::value
  >
{
};

template<>
struct has_bounded_size<robot_msg::srv::CloudCommand>
  : std::integral_constant<
    bool,
    has_bounded_size<robot_msg::srv::CloudCommand_Request>::value &&
    has_bounded_size<robot_msg::srv::CloudCommand_Response>::value
  >
{
};

template<>
struct is_service<robot_msg::srv::CloudCommand>
  : std::true_type
{
};

template<>
struct is_service_request<robot_msg::srv::CloudCommand_Request>
  : std::true_type
{
};

template<>
struct is_service_response<robot_msg::srv::CloudCommand_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_MSG__SRV__DETAIL__CLOUD_COMMAND__TRAITS_HPP_
