// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_msg:msg/SpeechData.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__BUILDER_HPP_
#define ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_msg/msg/detail/speech_data__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_msg
{

namespace msg
{

namespace builder
{

class Init_SpeechData_timestamp
{
public:
  explicit Init_SpeechData_timestamp(::robot_msg::msg::SpeechData & msg)
  : msg_(msg)
  {}
  ::robot_msg::msg::SpeechData timestamp(::robot_msg::msg::SpeechData::_timestamp_type arg)
  {
    msg_.timestamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_msg::msg::SpeechData msg_;
};

class Init_SpeechData_duration
{
public:
  explicit Init_SpeechData_duration(::robot_msg::msg::SpeechData & msg)
  : msg_(msg)
  {}
  Init_SpeechData_timestamp duration(::robot_msg::msg::SpeechData::_duration_type arg)
  {
    msg_.duration = std::move(arg);
    return Init_SpeechData_timestamp(msg_);
  }

private:
  ::robot_msg::msg::SpeechData msg_;
};

class Init_SpeechData_channels
{
public:
  explicit Init_SpeechData_channels(::robot_msg::msg::SpeechData & msg)
  : msg_(msg)
  {}
  Init_SpeechData_duration channels(::robot_msg::msg::SpeechData::_channels_type arg)
  {
    msg_.channels = std::move(arg);
    return Init_SpeechData_duration(msg_);
  }

private:
  ::robot_msg::msg::SpeechData msg_;
};

class Init_SpeechData_sample_rate
{
public:
  explicit Init_SpeechData_sample_rate(::robot_msg::msg::SpeechData & msg)
  : msg_(msg)
  {}
  Init_SpeechData_channels sample_rate(::robot_msg::msg::SpeechData::_sample_rate_type arg)
  {
    msg_.sample_rate = std::move(arg);
    return Init_SpeechData_channels(msg_);
  }

private:
  ::robot_msg::msg::SpeechData msg_;
};

class Init_SpeechData_audio_data
{
public:
  Init_SpeechData_audio_data()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SpeechData_sample_rate audio_data(::robot_msg::msg::SpeechData::_audio_data_type arg)
  {
    msg_.audio_data = std::move(arg);
    return Init_SpeechData_sample_rate(msg_);
  }

private:
  ::robot_msg::msg::SpeechData msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::msg::SpeechData>()
{
  return robot_msg::msg::builder::Init_SpeechData_audio_data();
}

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__SPEECH_DATA__BUILDER_HPP_
