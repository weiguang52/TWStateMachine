// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_msg:msg/SpeakerIdentity.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__BUILDER_HPP_
#define ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_msg/msg/detail/speaker_identity__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_msg
{

namespace msg
{

namespace builder
{

class Init_SpeakerIdentity_timestamp
{
public:
  explicit Init_SpeakerIdentity_timestamp(::robot_msg::msg::SpeakerIdentity & msg)
  : msg_(msg)
  {}
  ::robot_msg::msg::SpeakerIdentity timestamp(::robot_msg::msg::SpeakerIdentity::_timestamp_type arg)
  {
    msg_.timestamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_msg::msg::SpeakerIdentity msg_;
};

class Init_SpeakerIdentity_is_registered
{
public:
  explicit Init_SpeakerIdentity_is_registered(::robot_msg::msg::SpeakerIdentity & msg)
  : msg_(msg)
  {}
  Init_SpeakerIdentity_timestamp is_registered(::robot_msg::msg::SpeakerIdentity::_is_registered_type arg)
  {
    msg_.is_registered = std::move(arg);
    return Init_SpeakerIdentity_timestamp(msg_);
  }

private:
  ::robot_msg::msg::SpeakerIdentity msg_;
};

class Init_SpeakerIdentity_confidence
{
public:
  explicit Init_SpeakerIdentity_confidence(::robot_msg::msg::SpeakerIdentity & msg)
  : msg_(msg)
  {}
  Init_SpeakerIdentity_is_registered confidence(::robot_msg::msg::SpeakerIdentity::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_SpeakerIdentity_is_registered(msg_);
  }

private:
  ::robot_msg::msg::SpeakerIdentity msg_;
};

class Init_SpeakerIdentity_speaker_name
{
public:
  explicit Init_SpeakerIdentity_speaker_name(::robot_msg::msg::SpeakerIdentity & msg)
  : msg_(msg)
  {}
  Init_SpeakerIdentity_confidence speaker_name(::robot_msg::msg::SpeakerIdentity::_speaker_name_type arg)
  {
    msg_.speaker_name = std::move(arg);
    return Init_SpeakerIdentity_confidence(msg_);
  }

private:
  ::robot_msg::msg::SpeakerIdentity msg_;
};

class Init_SpeakerIdentity_speaker_id
{
public:
  Init_SpeakerIdentity_speaker_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SpeakerIdentity_speaker_name speaker_id(::robot_msg::msg::SpeakerIdentity::_speaker_id_type arg)
  {
    msg_.speaker_id = std::move(arg);
    return Init_SpeakerIdentity_speaker_name(msg_);
  }

private:
  ::robot_msg::msg::SpeakerIdentity msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::msg::SpeakerIdentity>()
{
  return robot_msg::msg::builder::Init_SpeakerIdentity_speaker_id();
}

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__SPEAKER_IDENTITY__BUILDER_HPP_
