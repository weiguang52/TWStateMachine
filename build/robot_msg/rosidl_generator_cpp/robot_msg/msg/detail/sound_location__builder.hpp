// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_msg:msg/SoundLocation.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__BUILDER_HPP_
#define ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_msg/msg/detail/sound_location__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_msg
{

namespace msg
{

namespace builder
{

class Init_SoundLocation_timestamp
{
public:
  explicit Init_SoundLocation_timestamp(::robot_msg::msg::SoundLocation & msg)
  : msg_(msg)
  {}
  ::robot_msg::msg::SoundLocation timestamp(::robot_msg::msg::SoundLocation::_timestamp_type arg)
  {
    msg_.timestamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_msg::msg::SoundLocation msg_;
};

class Init_SoundLocation_confidence
{
public:
  explicit Init_SoundLocation_confidence(::robot_msg::msg::SoundLocation & msg)
  : msg_(msg)
  {}
  Init_SoundLocation_timestamp confidence(::robot_msg::msg::SoundLocation::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_SoundLocation_timestamp(msg_);
  }

private:
  ::robot_msg::msg::SoundLocation msg_;
};

class Init_SoundLocation_distance
{
public:
  explicit Init_SoundLocation_distance(::robot_msg::msg::SoundLocation & msg)
  : msg_(msg)
  {}
  Init_SoundLocation_confidence distance(::robot_msg::msg::SoundLocation::_distance_type arg)
  {
    msg_.distance = std::move(arg);
    return Init_SoundLocation_confidence(msg_);
  }

private:
  ::robot_msg::msg::SoundLocation msg_;
};

class Init_SoundLocation_elevation
{
public:
  explicit Init_SoundLocation_elevation(::robot_msg::msg::SoundLocation & msg)
  : msg_(msg)
  {}
  Init_SoundLocation_distance elevation(::robot_msg::msg::SoundLocation::_elevation_type arg)
  {
    msg_.elevation = std::move(arg);
    return Init_SoundLocation_distance(msg_);
  }

private:
  ::robot_msg::msg::SoundLocation msg_;
};

class Init_SoundLocation_azimuth
{
public:
  Init_SoundLocation_azimuth()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SoundLocation_elevation azimuth(::robot_msg::msg::SoundLocation::_azimuth_type arg)
  {
    msg_.azimuth = std::move(arg);
    return Init_SoundLocation_elevation(msg_);
  }

private:
  ::robot_msg::msg::SoundLocation msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_msg::msg::SoundLocation>()
{
  return robot_msg::msg::builder::Init_SoundLocation_azimuth();
}

}  // namespace robot_msg

#endif  // ROBOT_MSG__MSG__DETAIL__SOUND_LOCATION__BUILDER_HPP_
