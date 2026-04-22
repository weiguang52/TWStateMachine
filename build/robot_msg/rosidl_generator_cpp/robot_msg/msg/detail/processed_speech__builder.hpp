// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_msg:msg/ProcessedSpeech.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__PROCESSED_SPEECH__BUILDER_HPP_
#define ROBOT_MSG__MSG__DETAIL__PROCESSED_SPEECH__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_msg/msg/detail/processed_speech__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_msg
{

namespace msg
{

namespace builder
{

class Init_ProcessedSpeech_timestamp
{
public:
  explicit Init_ProcessedSpeech_timestamp(::robot_msg::msg::ProcessedSpeech & msg)
  : msg_(msg)
  {}
  ::robot_msg::msg::ProcessedSpeech timestamp(::robot_msg::msg::ProcessedSpeech::_timestamp_type arg)
  {
    msg_.timestamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_msg::msg::ProcessedSpeech msg_;
};

class Init_ProcessedSpeech_noise_level_after
{
public:
  explicit Init_ProcessedSpeech_noise_level_after(::robot_msg::msg::ProcessedSpeech & msg)
  : msg_(msg)
  {}
  Init_ProcessedSpeech_timestamp noise_level_after(::robot_msg::msg::ProcessedSpeech::_noise_level_after_type arg)
  {
    msg_.noise_level_after = std::move(arg);
    return Init_ProcessedSpeech_timestamp(msg_);
  }

private:
  ::robot_msg::msg::ProcessedSpeech msg_;
};

class Init_ProcessedSpeech_noise_level_before
{
public:
  explicit Init_ProcessedSpeech_noise_level_before(::robot_msg::msg::ProcessedSpeech & msg)
  : msg_(msg)
  {}
  Init_ProcessedSpeech_noise_level_after noise_level_before(::robot_msg::msg::ProcessedSpeech::_noise_level_before_type arg)
  {
    msg_.noise_level_before = std::move(arg);
    return Init_ProcessedSpeech_noise_level_after(msg_);
  }

private:
  ::robot_msg::msg::ProcessedSpeech msg_;
};

class Init_ProcessedSpeech_duration
{
public:
  explicit Init_ProcessedSpeech_duration(::robot_msg::msg::ProcessedSpeech & msg)
  : msg_(msg)
  {}
  Init_ProcessedSpeech_noise_level_before duration(::robot_msg::msg::ProcessedSpeech::_duration_type arg)
  {
    msg_.duration = std::move(arg);
    return Init_ProcessedSpeech_noise_level_before(msg_);
  }

private:
  ::robot_msg::msg::ProcessedSpeech msg_;
};

class Init_ProcessedSpeech_channels
{
public:
  explicit Init_ProcessedSpeech_channels(::robot_msg::msg::ProcessedSpeech & msg)
  : msg_(msg)
  {}
  Init_ProcessedSpeech_duration channels(::robot_msg::msg::ProcessedSpeech::_channels_type arg)
  {
    msg_.channels = std::move(arg);
    return Init_ProcessedSpeech_duration(msg_);
  }

private:
  ::robot_msg::msg::ProcessedSpeech msg_;
};

class Init_ProcessedSpeech_sample_rate
{
public:
  explicit Init_ProcessedSpeech_sample_rate(::robot_msg::msg::ProcessedSpeech & msg)
  : msg_(msg)
  {}
  Init_ProcessedSpeech_channels sample_rate(::robot_msg::msg::ProcessedSpeech::_sample_rate_type arg)
  {
    msg_.sample_rate = std::move(arg);
    return Init_ProcessedSpeech_channels(msg_);
  }

private:
  ::robot_msg::msg::ProcessedSpeech msg_;
};

class Init_ProcessedSpeech_audio_data
{
public:
  Init_ProcessedSpeech_audio_data()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ProcessedSpeech_sample_rate audio_data(::robot_msg::msg::ProcessedSpeech::_audio_data_type arg)
  {
    msg_.audio_data = std::move(arg);
    return Init_ProcessedSpeech_sample_rate(msg_);
  }

private:
  ::robot_msg::msg::ProcessedSpeech msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::msg::ProcessedSpeech>()
{
  return robot_msg::msg::builder::Init_ProcessedSpeech_audio_data();
}

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__PROCESSED_SPEECH__BUILDER_HPP_
