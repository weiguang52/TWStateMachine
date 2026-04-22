// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_msg:msg/SoundType.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__BUILDER_HPP_
#define ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_msg/msg/detail/sound_type__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_msg
{

namespace msg
{

namespace builder
{

class Init_SoundType_timestamp
{
public:
  explicit Init_SoundType_timestamp(::robot_msg::msg::SoundType & msg)
  : msg_(msg)
  {}
  ::robot_msg::msg::SoundType timestamp(::robot_msg::msg::SoundType::_timestamp_type arg)
  {
    msg_.timestamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_msg::msg::SoundType msg_;
};

class Init_SoundType_confidence_scores
{
public:
  explicit Init_SoundType_confidence_scores(::robot_msg::msg::SoundType & msg)
  : msg_(msg)
  {}
  Init_SoundType_timestamp confidence_scores(::robot_msg::msg::SoundType::_confidence_scores_type arg)
  {
    msg_.confidence_scores = std::move(arg);
    return Init_SoundType_timestamp(msg_);
  }

private:
  ::robot_msg::msg::SoundType msg_;
};

class Init_SoundType_detected_sounds
{
public:
  explicit Init_SoundType_detected_sounds(::robot_msg::msg::SoundType & msg)
  : msg_(msg)
  {}
  Init_SoundType_confidence_scores detected_sounds(::robot_msg::msg::SoundType::_detected_sounds_type arg)
  {
    msg_.detected_sounds = std::move(arg);
    return Init_SoundType_confidence_scores(msg_);
  }

private:
  ::robot_msg::msg::SoundType msg_;
};

class Init_SoundType_sound_category
{
public:
  Init_SoundType_sound_category()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SoundType_detected_sounds sound_category(::robot_msg::msg::SoundType::_sound_category_type arg)
  {
    msg_.sound_category = std::move(arg);
    return Init_SoundType_detected_sounds(msg_);
  }

private:
  ::robot_msg::msg::SoundType msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::msg::SoundType>()
{
  return robot_msg::msg::builder::Init_SoundType_sound_category();
}

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__SOUND_TYPE__BUILDER_HPP_
