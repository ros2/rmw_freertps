// Copyright 2016 Open Source Robotics Foundation, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <gtest/gtest.h>
#include <string>
#include <type_traits>

#include "rosidl_typesupport_freertps_cpp/msg/freertps/bounded_array_bounded__type_support.hpp"
#include "rosidl_typesupport_freertps_cpp/msg/freertps/bounded_array_static__type_support.hpp"
#include "rosidl_typesupport_freertps_cpp/msg/freertps/bounded_array_unbounded__type_support.hpp"

#include "rosidl_typesupport_freertps_cpp/msg/freertps/empty__type_support.hpp"
#include "rosidl_typesupport_freertps_cpp/msg/freertps/large_array__type_support.hpp"

#include "rosidl_typesupport_freertps_cpp/msg/freertps/primitive_static_arrays__type_support.hpp"

#include "rosidl_typesupport_freertps_cpp/msg/freertps/primitives_bounded__type_support.hpp"
#include "rosidl_typesupport_freertps_cpp/msg/freertps/primitives_static__type_support.hpp"
#include "rosidl_typesupport_freertps_cpp/msg/freertps/primitives_unbounded__type_support.hpp"

#include "rosidl_typesupport_freertps_cpp/msg/freertps/static_array_bounded__type_support.hpp"
#include "rosidl_typesupport_freertps_cpp/msg/freertps/static_array_static__type_support.hpp"
#include "rosidl_typesupport_freertps_cpp/msg/freertps/static_array_unbounded__type_support.hpp"

#include "rosidl_typesupport_freertps_cpp/msg/freertps/unbounded_array_bounded__type_support.hpp"
#include "rosidl_typesupport_freertps_cpp/msg/freertps/unbounded_array_static__type_support.hpp"
#include "rosidl_typesupport_freertps_cpp/msg/freertps/unbounded_array_unbounded__type_support.hpp"


void message_factory(rosidl_typesupport_freertps_cpp::msg::Empty & msg)
{
  (void)msg;
}

void message_factory(rosidl_typesupport_freertps_cpp::msg::LargeArray & msg)
{
  for (uint32_t i = 0; i < 256; ++i) {
    msg.static_values[i] = i;
    msg.unbounded_values.push_back(i);
  }
}

template<std::size_t ArraySize, typename MsgType>
void primitives_message_factory(MsgType & msg)
{
  for (uint32_t i = 0; i < ArraySize; ++i) {
    msg.bool_value[i] = i % 2 == 0;
    msg.byte_value[i] = i + 1;
    msg.char_value[i] = i + 2;
    msg.float32_value[i] = i + 3 + 0.01;
    msg.float64_value[i] = i + 4 + 0.001;
    msg.int8_value[i] = -i + 5;
    msg.uint8_value[i] = i + 6;
    msg.int16_value[i] = -i + 7;
    msg.uint16_value[i] = i + 8;
    msg.int32_value[i] = -i + 9;
    msg.uint32_value[i] = i + 10;
    msg.int64_value[i] = -i + 11;
    msg.uint64_value[i] = i + 12;
  }
}

void message_factory(rosidl_typesupport_freertps_cpp::msg::PrimitivesBounded & msg)
{
  primitives_message_factory<10>(msg);
  for (uint32_t i = 0; i < 10; ++i) {
    msg.string_array[i] = std::string("hello #") + std::to_string(i);
  }
  msg.string_value = "world";
}

void message_factory(rosidl_typesupport_freertps_cpp::msg::PrimitivesStatic & msg)
{
  msg.bool_value = true;
  msg.byte_value = 42;
  msg.char_value = 'r';
  msg.float32_value = 12.34;
  msg.float64_value = 567.89;
  msg.int8_value = -42;
  msg.uint8_value = 42;
  msg.int16_value = -43;
  msg.uint16_value = 43;
  msg.int32_value = -44;
  msg.uint32_value = 44;
  msg.int64_value = -45;
  msg.uint64_value = 45;
}

void message_factory(rosidl_typesupport_freertps_cpp::msg::PrimitiveStaticArrays & msg)
{
  primitives_message_factory<3>(msg);
}

void message_factory(rosidl_typesupport_freertps_cpp::msg::PrimitivesUnbounded & msg)
{
  msg.bool_value.resize(10);
  msg.byte_value.resize(10);
  msg.char_value.resize(10);
  msg.float32_value.resize(10);
  msg.float64_value.resize(10);
  msg.int8_value.resize(10);
  msg.uint8_value.resize(10);
  msg.int16_value.resize(10);
  msg.uint16_value.resize(10);
  msg.int32_value.resize(10);
  msg.uint32_value.resize(10);
  msg.int64_value.resize(10);
  msg.uint64_value.resize(10);

  primitives_message_factory<10>(msg);
  for (uint32_t i = 0; i < 10; ++i) {
    msg.string_array.push_back(std::string("hello #") + std::to_string(i));
  }
  msg.string_value = "world";
}

void validate_factory_message(const rosidl_typesupport_freertps_cpp::msg::Empty & msg)
{
  (void)msg;
}

template<std::size_t ArraySize, typename MsgType>
void primitive_array_validation(const MsgType & msg)
{
  for (size_t i = 0; i < ArraySize; ++i) {
    EXPECT_EQ(msg.bool_value[i], i % 2 == 0);
    EXPECT_EQ(msg.byte_value[i], i + 1);
    EXPECT_EQ(msg.char_value[i], i + 2);
    EXPECT_FLOAT_EQ(msg.float32_value[i], i + 3 + 0.01);
    EXPECT_DOUBLE_EQ(msg.float64_value[i], i + 4 + 0.001);
    EXPECT_EQ(msg.int8_value[i], -i + 5);
    EXPECT_EQ(msg.uint8_value[i], i + 6);
    EXPECT_EQ(msg.int16_value[i], -i + 7);
    EXPECT_EQ(msg.uint16_value[i], i + 8);
    EXPECT_EQ(msg.int32_value[i], -i + 9);
    EXPECT_EQ(msg.uint32_value[i], i + 10);
    EXPECT_EQ(msg.int64_value[i], -i + 11);
    EXPECT_EQ(msg.uint64_value[i], i + 12);
  }
}

void validate_factory_message(const rosidl_typesupport_freertps_cpp::msg::PrimitivesStatic & msg)
{
  EXPECT_TRUE(msg.bool_value);
  EXPECT_EQ(msg.byte_value, 42);
  EXPECT_EQ(msg.char_value, 'r');
  EXPECT_FLOAT_EQ(msg.float32_value, 12.34);
  EXPECT_DOUBLE_EQ(msg.float64_value, 567.89);
  EXPECT_EQ(msg.int8_value, -42);
  EXPECT_EQ(msg.uint8_value, 42);
  EXPECT_EQ(msg.int16_value, -43);
  EXPECT_EQ(msg.uint16_value, 43);
  EXPECT_EQ(msg.int32_value, -44);
  EXPECT_EQ(msg.uint32_value, 44);
  EXPECT_EQ(msg.int64_value, -45);
  EXPECT_EQ(msg.uint64_value, 45);
}

void validate_factory_message(const rosidl_typesupport_freertps_cpp::msg::PrimitivesBounded & msg)
{
  primitive_array_validation<10>(msg);
  for (uint32_t i = 0; i < 10; ++i) {
    EXPECT_EQ(msg.string_array[i], std::string("hello #") + std::to_string(i));
  }
  EXPECT_EQ(msg.string_value, "world");
}

void validate_factory_message(const rosidl_typesupport_freertps_cpp::msg::PrimitivesUnbounded & msg)
{
  primitive_array_validation<10>(msg);
  for (uint32_t i = 0; i < 10; ++i) {
    EXPECT_EQ(msg.string_array[i], std::string("hello #") + std::to_string(i));
  }
  EXPECT_EQ(msg.string_value, "world");
}

void validate_factory_message(
  const rosidl_typesupport_freertps_cpp::msg::PrimitiveStaticArrays & msg)
{
  primitive_array_validation<3>(msg);
}

void validate_factory_message(const rosidl_typesupport_freertps_cpp::msg::LargeArray & msg)
{
  for (uint32_t i = 0; i < 256; ++i) {
    EXPECT_EQ(msg.static_values[i], i);
    EXPECT_EQ(msg.unbounded_values[i], i);
  }
}

template<typename MsgType,
std::size_t ArraySize,
bool unbounded,
typename std::enable_if<ArraySize != 0>::type * = nullptr>
void test_case()
{
  uint8_t * buf = nullptr;
  uint32_t max_size = 0;
  {
    MsgType msg;

    msg.primitive_values.resize(ArraySize);
    for (uint32_t i = 0; i < ArraySize; ++i) {
      message_factory(msg.primitive_values[i]);
    }
    max_size =
      rosidl_typesupport_freertps_cpp::msg::typesupport_freertps_cpp::allocate_buffer_for_ros_msg(
      &msg, buf);
    ASSERT_TRUE(buf);
    ASSERT_NE(max_size, 0);
    uint32_t result =
      rosidl_typesupport_freertps_cpp::msg::typesupport_freertps_cpp::serialize_ros_msg(
      &msg, buf, max_size);
    EXPECT_GE(max_size, result);
  }
  {
    uint32_t length = max_size;
    uint8_t * tmp_buf = buf;
    MsgType msg;
    ASSERT_TRUE(
      rosidl_typesupport_freertps_cpp::msg::typesupport_freertps_cpp::deserialize_ros_msg(
        &tmp_buf, &msg, &length));
    for (uint32_t i = 0; i < ArraySize; ++i) {
      validate_factory_message(msg.primitive_values[i]);
    }
  }

  free(buf);
}

template<typename MsgType,
std::size_t ArraySize,
typename std::enable_if<ArraySize != 0>::type * = nullptr>
void test_case()
{
  uint8_t * buf = nullptr;
  uint32_t max_size = 0;
  {
    MsgType msg;

    for (uint32_t i = 0; i < ArraySize; ++i) {
      message_factory(msg.primitive_values[i]);
    }
    max_size =
      rosidl_typesupport_freertps_cpp::msg::typesupport_freertps_cpp::allocate_buffer_for_ros_msg(
      &msg, buf);
    ASSERT_TRUE(buf);
    ASSERT_NE(max_size, 0);
    uint32_t result =
      rosidl_typesupport_freertps_cpp::msg::typesupport_freertps_cpp::serialize_ros_msg(
      &msg, buf, max_size);
    EXPECT_GE(max_size, result);
  }
  {
    uint32_t length = max_size;
    uint8_t * tmp_buf = buf;
    MsgType msg;
    ASSERT_TRUE(
      rosidl_typesupport_freertps_cpp::msg::typesupport_freertps_cpp::deserialize_ros_msg(
        &tmp_buf, &msg, &length));
    for (uint32_t i = 0; i < ArraySize; ++i) {
      validate_factory_message(msg.primitive_values[i]);
    }
  }

  free(buf);
}

template<typename MsgType>
void test_case()
{
  uint8_t * buf = nullptr;
  uint32_t max_size = 0;
  {
    MsgType msg;
    message_factory(msg);

    max_size =
      rosidl_typesupport_freertps_cpp::msg::typesupport_freertps_cpp::allocate_buffer_for_ros_msg(
      &msg, buf);
    uint32_t result =
      rosidl_typesupport_freertps_cpp::msg::typesupport_freertps_cpp::serialize_ros_msg(
      &msg, buf, max_size);
    EXPECT_GE(max_size, result);
  }
  {
    uint32_t length = max_size;
    uint8_t * tmp_buf = buf;
    MsgType msg;
    ASSERT_TRUE(
      rosidl_typesupport_freertps_cpp::msg::typesupport_freertps_cpp::deserialize_ros_msg(
        &tmp_buf, &msg, &length));
    validate_factory_message(msg);
  }

  free(buf);
}

TEST(test_serialization, serialize_empty) {
  test_case<rosidl_typesupport_freertps_cpp::msg::Empty>();
}

TEST(test_serialization, serialize_bounded_array_bounded) {
  test_case<rosidl_typesupport_freertps_cpp::msg::BoundedArrayBounded, 3>();
}

TEST(test_serialization, serialize_bounded_array_static) {
  test_case<rosidl_typesupport_freertps_cpp::msg::BoundedArrayStatic, 3>();
}

TEST(test_serialization, serialize_bounded_array_unbounded) {
  test_case<rosidl_typesupport_freertps_cpp::msg::BoundedArrayUnbounded, 3>();
}

TEST(test_serialization, serialize_primitives_bounded) {
  test_case<rosidl_typesupport_freertps_cpp::msg::PrimitivesBounded>();
}

TEST(test_serialization, serialize_primitives_static) {
  test_case<rosidl_typesupport_freertps_cpp::msg::PrimitivesStatic>();
}

TEST(test_serialization, serialize_primitives_unbounded) {
  test_case<rosidl_typesupport_freertps_cpp::msg::PrimitivesUnbounded>();
}

TEST(test_serialization, serialize_primitive_static_arrays) {
  test_case<rosidl_typesupport_freertps_cpp::msg::PrimitiveStaticArrays>();
}

TEST(test_serialization, serialize_static_array_bounded) {
  test_case<rosidl_typesupport_freertps_cpp::msg::StaticArrayBounded, 3>();
}

TEST(test_serialization, serialize_static_array_static) {
  test_case<rosidl_typesupport_freertps_cpp::msg::StaticArrayStatic, 3>();
}

TEST(test_serialization, serialize_static_array_unbounded) {
  test_case<rosidl_typesupport_freertps_cpp::msg::StaticArrayUnbounded, 3>();
}

TEST(test_serialization, serialize_unbounded_array_bounded) {
  test_case<rosidl_typesupport_freertps_cpp::msg::UnboundedArrayBounded, 3, true>();
}

TEST(test_serialization, serialize_unbounded_array_static) {
  test_case<rosidl_typesupport_freertps_cpp::msg::UnboundedArrayStatic, 3, true>();
}

TEST(test_serialization, serialize_unbounded_array_unbounded) {
  test_case<rosidl_typesupport_freertps_cpp::msg::UnboundedArrayUnbounded, 3, true>();
}

TEST(test_serialization, serialize_large_array) {
  test_case<rosidl_typesupport_freertps_cpp::msg::LargeArray>();
}
