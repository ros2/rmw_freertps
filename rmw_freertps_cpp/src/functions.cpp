// Copyright 2015 Open Source Robotics Foundation, Inc.
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

#include <cassert>
#include <cstring>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "rmw/allocators.h"
#include "rmw/impl/cpp/macros.hpp"
#include "rmw/rmw.h"

#include "rosidl_generator_c/message_type_support.h"
#include "rosidl_generator_c/service_type_support.h"
#include "rosidl_typesupport_freertps_cpp/identifier.hpp"
#include "rosidl_typesupport_freertps_cpp/message_type_support.h"
#include "rosidl_typesupport_freertps_cpp/service_type_support.h"


extern "C"
{
#include "freertps/freertps.h"
}

inline std::string
_create_type_name(
  const message_type_support_callbacks_t * callbacks,
  const std::string & sep)
{
  return std::string(callbacks->package_name) +
         "::" + sep + "::dds_::" + callbacks->message_name + "_";
}


// The extern "C" here enforces that overloading is not used.
extern "C"
{
using rosidl_typesupport_freertps_cpp::typesupport_freertps_identifier;
const char * freertps_cpp_identifier = "freertps_static";

struct PublisherInfo
{
  frudp_pub_t * pub;
  const message_type_support_callbacks_t * callbacks;
};


const char *
rmw_get_implementation_identifier()
{
  return freertps_cpp_identifier;
}

rmw_ret_t
rmw_init()
{
  printf("rmw_init()\n");
  freertps_system_init();
  return RMW_RET_OK;
}

rmw_node_t *
rmw_create_node(const char * name, size_t domain_id)
{
  (void)name;  // need to stash this somewhere

  // TODO(jacquelinekay): domain ID is not yet implemented in freertps (?)
  if (!frudp_part_create()) {
    RMW_SET_ERROR_MSG("failed to create freertps participant");
    return nullptr;
  }

  rmw_node_t * node = rmw_node_allocate();
  if (!node) {
    RMW_SET_ERROR_MSG("failed to allocate rmw_node_t");
    return nullptr;
    // goto fail;
  }
  node->implementation_identifier = freertps_cpp_identifier;
  node->data = nullptr;

  frudp_disco_tick();
  return node;
}

rmw_ret_t
rmw_destroy_node(rmw_node_t * node)
{
  if (!node) {
    RMW_SET_ERROR_MSG("received null pointer");
    return RMW_RET_ERROR;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    node handle,
    node->implementation_identifier, freertps_cpp_identifier,
    return RMW_RET_ERROR)

  auto result = RMW_RET_OK;

  rmw_node_free(node);
  return result;
}

rmw_publisher_t *
rmw_create_publisher(
  const rmw_node_t * node,
  const rosidl_message_type_support_t * type_support,
  const char * topic_name,
  const rmw_qos_profile_t * qos_profile)
{
  if (!node) {
    RMW_SET_ERROR_MSG("node handle is null");
    return nullptr;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    node handle,
    node->implementation_identifier, freertps_cpp_identifier,
    return nullptr)

  if (!type_support) {
    RMW_SET_ERROR_MSG("type support handle is null");
    return nullptr;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    type support,
    type_support->typesupport_identifier, typesupport_freertps_identifier,
    return nullptr)
    (void) qos_profile;  // todo: figure out what to do with this. maybe
                         // return an error if anything complicated is requested?

  const message_type_support_callbacks_t * callbacks =
    static_cast<const message_type_support_callbacks_t *>(type_support->data);
  // todo: deal with dynamic memory created here
  std::string type_name = _create_type_name(callbacks, "msg");
  printf("rmw_create_publisher(%s, %s)\n",
    topic_name,
    type_name.c_str());

  rmw_publisher_t * publisher = rmw_publisher_allocate();
  if (!publisher) {
    RMW_SET_ERROR_MSG("failed to allocate rmw_publisher_t");
    return nullptr;
  }

  frudp_pub_t * freertps_pub = nullptr;
  if (strcmp(topic_name, "parameter_events")) {
    freertps_pub = freertps_create_pub(topic_name, type_name.c_str());
  } else {
    printf("refusing to create parameter_events topic\n");
  }

  PublisherInfo * pub_info = static_cast<PublisherInfo *>(
    rmw_allocate(sizeof(PublisherInfo)));
  pub_info->pub = freertps_pub;
  pub_info->callbacks = callbacks;

  publisher->implementation_identifier = freertps_cpp_identifier;
  publisher->data = pub_info;

  return publisher;
}

rmw_ret_t
rmw_destroy_publisher(rmw_node_t * node, rmw_publisher_t * publisher)
{
  if (!node) {
    RMW_SET_ERROR_MSG("node handle is null");
    return RMW_RET_ERROR;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    node handle,
    node->implementation_identifier, freertps_cpp_identifier,
    return RMW_RET_ERROR)

  if (!publisher) {
    RMW_SET_ERROR_MSG("pointer handle is null");
    return RMW_RET_ERROR;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    publisher handle,
    publisher->implementation_identifier, freertps_cpp_identifier,
    return RMW_RET_ERROR)

  auto result = RMW_RET_ERROR;
  RMW_SET_ERROR_MSG("rmw_destroy_publisher() not yet implemented");
  return result;
}

rmw_ret_t
rmw_publish(const rmw_publisher_t * publisher, const void * ros_message)
{
  if (!publisher) {
    RMW_SET_ERROR_MSG("publisher handle is null");
    return RMW_RET_ERROR;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    publisher handle,
    publisher->implementation_identifier, freertps_cpp_identifier,
    return RMW_RET_ERROR)
  if (!ros_message) {
    RMW_SET_ERROR_MSG("ros message handle is null");
    return RMW_RET_ERROR;
  }
  const PublisherInfo * pub_info =
    static_cast<const PublisherInfo *>(publisher->data);
  if (!pub_info) {
    RMW_SET_ERROR_MSG("publisher info handle is null");
    return RMW_RET_ERROR;
  }
  const message_type_support_callbacks_t * callbacks = pub_info->callbacks;
  if (!callbacks) {
    RMW_SET_ERROR_MSG("callbacks handle is null");
    return RMW_RET_ERROR;
  }
  frudp_pub_t * fr_pub = pub_info->pub;
  if (!fr_pub) {
    RMW_SET_ERROR_MSG("hey, fr_pub is empty. uh oh...\n");
    return RMW_RET_ERROR;
  }
  const char * error_string = callbacks->publish(fr_pub, ros_message);
  if (error_string) {
    RMW_SET_ERROR_MSG((std::string("failed to publish:") + error_string).c_str());
    return RMW_RET_ERROR;
  }
  return RMW_RET_OK;
}

rmw_subscription_t *
rmw_create_subscription(
  const rmw_node_t * node,
  const rosidl_message_type_support_t * type_support,
  const char * topic_name,
  const rmw_qos_profile_t * qos_profile,
  bool ignore_local_publications)
{
  if (!node) {
    RMW_SET_ERROR_MSG("node handle is null");
    return nullptr;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    node handle,
    node->implementation_identifier, freertps_cpp_identifier,
    return NULL)

  if (!type_support) {
    RMW_SET_ERROR_MSG("type support handle is null");
    return nullptr;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    type support,
    type_support->typesupport_identifier, typesupport_freertps_identifier,
    return nullptr)

  RMW_SET_ERROR_MSG("rmw_create_subscription() not yet implemented");
  (void)topic_name;
  (void)qos_profile;
  (void)ignore_local_publications;
  return nullptr;
}

rmw_ret_t
rmw_destroy_subscription(rmw_node_t * node, rmw_subscription_t * subscription)
{
  if (!node) {
    RMW_SET_ERROR_MSG("node handle is null");
    return RMW_RET_ERROR;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    node handle,
    node->implementation_identifier, freertps_cpp_identifier,
    return RMW_RET_ERROR)

  if (!subscription) {
    RMW_SET_ERROR_MSG("subscription handle is null");
    return RMW_RET_ERROR;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    subscription handle,
    subscription->implementation_identifier, freertps_cpp_identifier,
    return RMW_RET_ERROR)
  RMW_SET_ERROR_MSG("rmw_destroy_subscription() not yet implemented");
  return RMW_RET_ERROR;  // todo: not this
}

rmw_ret_t
rmw_take(const rmw_subscription_t * subscription, void * ros_message, bool * taken)
{
  if (!subscription) {
    RMW_SET_ERROR_MSG("subscription handle is null");
    return RMW_RET_ERROR;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    subscription handle,
    subscription->implementation_identifier, freertps_cpp_identifier,
    return RMW_RET_ERROR)

  if (ros_message == nullptr) {
    RMW_SET_ERROR_MSG("ros_message argument cannot be null");
    return RMW_RET_ERROR;
  }

  if (taken == nullptr) {
    RMW_SET_ERROR_MSG("taken argument cannot be null");
    return RMW_RET_ERROR;
  }
  RMW_SET_ERROR_MSG("rmw_take() not yet implemented");
  return RMW_RET_ERROR;  // todo: not this
}

rmw_ret_t
rmw_take_with_info(
  const rmw_subscription_t * subscription,
  void * ros_message,
  bool * taken,
  rmw_message_info_t * message_info)
{
  RMW_SET_ERROR_MSG("rmw_take_with_info() not yet implemented");
  return RMW_RET_ERROR;
}


rmw_guard_condition_t *
rmw_create_guard_condition()
{
  printf("rmw_guard_condition alloc\r\n");
  rmw_guard_condition_t * guard_condition = rmw_guard_condition_allocate();
  if (!guard_condition) {
    RMW_SET_ERROR_MSG("failed to allocate guard condition");
    return nullptr;
  }
  guard_condition->implementation_identifier = freertps_cpp_identifier;
  guard_condition->data = nullptr;
  return guard_condition;
}

rmw_ret_t
rmw_destroy_guard_condition(rmw_guard_condition_t * guard_condition)
{
  if (!guard_condition) {
    RMW_SET_ERROR_MSG("guard condition handle is null");
    return RMW_RET_ERROR;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    guard condition handle,
    guard_condition->implementation_identifier, freertps_cpp_identifier,
    return RMW_RET_ERROR)

  RMW_SET_ERROR_MSG("rmw_trigger_guard_condition() not yet implemented");
  return RMW_RET_ERROR;
}

rmw_ret_t
rmw_trigger_guard_condition(const rmw_guard_condition_t * guard_condition)
{
  if (!guard_condition) {
    RMW_SET_ERROR_MSG("guard condition handle is null");
    return RMW_RET_ERROR;
  }
  RMW_CHECK_TYPE_IDENTIFIERS_MATCH(
    guard condition handle,
    guard_condition->implementation_identifier, freertps_cpp_identifier,
    return RMW_RET_ERROR)

  RMW_SET_ERROR_MSG("rmw_trigger_guard_condition() not yet implemented");
  return RMW_RET_ERROR;
}

rmw_waitset_t *
rmw_create_waitset(rmw_guard_conditions_t * fixed_guard_conditions, size_t max_conditions)
{
  RMW_SET_ERROR_MSG("rmw_create_waitset() not yet implemented");
  return nullptr;
}

rmw_ret_t
rmw_destroy_waitset(rmw_waitset_t * waitset)
{
  RMW_SET_ERROR_MSG("rmw_destroy_waitset() not yet implemented");
  return RMW_RET_ERROR;
}

rmw_ret_t
rmw_wait(
  rmw_subscriptions_t * subscriptions,
  rmw_guard_conditions_t * guard_conditions,
  rmw_services_t * services,
  rmw_clients_t * clients,
  rmw_waitset_t * waitset,
  const rmw_time_t * wait_timeout)
{
  (void)subscriptions;
  (void)services;
  (void)clients;
  (void)wait_timeout;
  (void)guard_conditions;
  (void)waitset;
  const uint32_t max_usecs = wait_timeout->nsec / 1000 +
    wait_timeout->sec * 1000000;
  printf("rmw_wait(%d)\n", static_cast<int>(max_usecs));
  frudp_listen(max_usecs);

  static double t_prev_disco = 0;  // stayin alive
  const double t_now = fr_time_now_double();
  if (t_now - t_prev_disco > 1.0) {  // disco every second. stayin alive.
    t_prev_disco = t_now;
    frudp_disco_tick();
  }
  return RMW_RET_OK;
}

rmw_client_t *
rmw_create_client(
  const rmw_node_t * node,
  const rosidl_service_type_support_t * type_support,
  const char * service_name,
  const rmw_qos_profile_t * qos_policies)
{
  RMW_SET_ERROR_MSG("rmw_create_client() not yet implemented");
  (void)node;
  (void)type_support;
  (void)service_name;
  return nullptr;
}

rmw_ret_t
rmw_destroy_client(rmw_client_t * client)
{
  RMW_SET_ERROR_MSG("rmw_destroy_client() not yet implemented");
  (void)client;
  return RMW_RET_ERROR;
}

rmw_ret_t
rmw_send_request(
  const rmw_client_t * client, const void * ros_request,
  int64_t * sequence_id)
{
  RMW_SET_ERROR_MSG("rmw_send_request() not yet implemented");
  (void)client;
  (void)ros_request;
  (void)sequence_id;
  return RMW_RET_ERROR;
}

rmw_ret_t
rmw_take_response(const rmw_client_t * client, void * ros_request_header,
  void * ros_response, bool * taken)
{
  RMW_SET_ERROR_MSG("rmw_take_response() not yet implemented");
  (void)client;
  (void)ros_request_header;
  (void)ros_response;
  (void)taken;
  return RMW_RET_ERROR;
}

rmw_service_t *
rmw_create_service(
  const rmw_node_t * node,
  const rosidl_service_type_support_t * type_support,
  const char * service_name,
  const rmw_qos_profile_t * qos_policies)
{
  RMW_SET_ERROR_MSG("rmw_create_service() not yet implemented");
  (void)node;
  (void)type_support;
  (void)service_name;
  return nullptr;
}

rmw_ret_t
rmw_destroy_service(rmw_service_t * service)
{
  RMW_SET_ERROR_MSG("rmw_destroy_service() not yet implemented");
  (void)service;
  return RMW_RET_ERROR;
}

rmw_ret_t
rmw_take_request(
  const rmw_service_t * service,
  void * ros_request_header, void * ros_request, bool * taken)
{
  RMW_SET_ERROR_MSG("rmw_take_request() not yet implemented");
  (void)service;
  (void)ros_request_header;
  (void)ros_request;
  (void)taken;
  return RMW_RET_ERROR;
}

rmw_ret_t
rmw_send_response(
  const rmw_service_t * service,
  void * ros_request_header, void * ros_response)
{
  RMW_SET_ERROR_MSG("rmw_send_response() not yet implemented");
  (void)service;
  (void)ros_request_header;
  (void)ros_response;
  return RMW_RET_ERROR;
}

void
destroy_topic_names_and_types(
  rmw_topic_names_and_types_t * topic_names_and_types)
{
  (void)topic_names_and_types;
  printf("rmw_destroy_topic_names_and_types() not yet implemented\n");
  // not yet implemented
  /*
  if (topic_names_and_types->topic_count) {
    for (size_t i = 0; i < topic_names_and_types->topic_count; ++i) {
      delete topic_names_and_types->topic_names[i];
      delete topic_names_and_types->type_names[i];
      topic_names_and_types->topic_names[i] = nullptr;
      topic_names_and_types->type_names[i] = nullptr;
    }
    if (topic_names_and_types->topic_names) {
      rmw_free(topic_names_and_types->topic_names);
      topic_names_and_types->topic_names = nullptr;
    }
    if (topic_names_and_types->type_names) {
      rmw_free(topic_names_and_types->type_names);
      topic_names_and_types->type_names = nullptr;
    }
    topic_names_and_types->topic_count = 0;
  }
  */
}

rmw_ret_t
rmw_get_topic_names_and_types(
  const rmw_node_t * node,
  rmw_topic_names_and_types_t * topic_names_and_types)
{
  RMW_SET_ERROR_MSG("rmw_get_topic_names_and_types() not yet implemented");
  (void)node;
  (void)topic_names_and_types;
  return RMW_RET_ERROR;
  /*
  if (!node) {
    RMW_SET_ERROR_MSG("node handle is null");
    return RMW_RET_ERROR;
  }
  if (node->implementation_identifier != opensplice_cpp_identifier) {
    RMW_SET_ERROR_MSG("node handle is not from this rmw implementation");
    return RMW_RET_ERROR;
  }
  if (!topic_names_and_types) {
    RMW_SET_ERROR_MSG("topics handle is null");
    return RMW_RET_ERROR;
  }
  if (topic_names_and_types->topic_count) {
    RMW_SET_ERROR_MSG("topic count is not zero");
    return RMW_RET_ERROR;
  }
  if (topic_names_and_types->topic_names) {
    RMW_SET_ERROR_MSG("topic names is not null");
    return RMW_RET_ERROR;
  }
  if (topic_names_and_types->type_names) {
    RMW_SET_ERROR_MSG("type names is not null");
    return RMW_RET_ERROR;
  }

  auto node_info = static_cast<OpenSpliceStaticNodeInfo *>(node->data);
  if (!node_info) {
    RMW_SET_ERROR_MSG("node info handle is null");
    return RMW_RET_ERROR;
  }
  if (!node_info->publisher_listener) {
    RMW_SET_ERROR_MSG("publisher listener handle is null");
    return RMW_RET_ERROR;
  }
  if (!node_info->subscriber_listener) {
    RMW_SET_ERROR_MSG("subscriber listener handle is null");
    return RMW_RET_ERROR;
  }

  // combine publisher and subscriber information
  std::map<std::string, std::set<std::string>> topics_with_multiple_types;
  for (auto it : node_info->publisher_listener->topic_names_and_types) {
    for (auto & jt : it.second) {
      topics_with_multiple_types[it.first].insert(jt);
    }
  }
  for (auto it : node_info->subscriber_listener->topic_names_and_types) {
    for (auto & jt : it.second) {
      topics_with_multiple_types[it.first].insert(jt);
    }
  }

  // ignore inconsistent types
  std::map<std::string, std::string> topics;
  for (auto & it : topics_with_multiple_types) {
    if (it.second.size() != 1) {
      fprintf(stderr, "topic type mismatch - ignoring topic '%s'\n", it.first.c_str());
      continue;
    }
    topics[it.first] = *it.second.begin();
  }

  // reformat type name
  std::string substr = "::msg::dds_::";
  for (auto & it : topics) {
    size_t substr_pos = it.second.find(substr);
    if (it.second[it.second.size() - 1] == '_' && substr_pos != std::string::npos) {
      it.second = it.second.substr(0, substr_pos) + "/" + it.second.substr(
        substr_pos + substr.size(), it.second.size() - substr_pos - substr.size() - 1);
    }
  }

  // copy data into result handle
  if (topics.size() > 0) {
    topic_names_and_types->topic_names = static_cast<char **>(
      rmw_allocate(sizeof(char *) * topics.size()));
    if (!topic_names_and_types->topic_names) {
      RMW_SET_ERROR_MSG("failed to allocate memory for topic names")
      return RMW_RET_ERROR;
    }
    topic_names_and_types->type_names = static_cast<char **>(
      rmw_allocate(sizeof(char *) * topics.size()));
    if (!topic_names_and_types->type_names) {
      rmw_free(topic_names_and_types->topic_names);
      RMW_SET_ERROR_MSG("failed to allocate memory for type names")
      return RMW_RET_ERROR;
    }
    for (auto it : topics) {
      char * topic_name = strdup(it.first.c_str());
      if (!topic_name) {
        RMW_SET_ERROR_MSG("failed to allocate memory for topic name")
        goto fail;
      }
      char * type_name = strdup(it.second.c_str());
      if (!type_name) {
        rmw_free(topic_name);
        RMW_SET_ERROR_MSG("failed to allocate memory for type name")
        goto fail;
      }
      size_t i = topic_names_and_types->topic_count;
      topic_names_and_types->topic_names[i] = topic_name;
      topic_names_and_types->type_names[i] = type_name;
      ++topic_names_and_types->topic_count;
    }
  }

  return RMW_RET_OK;
fail:
  destroy_topic_names_and_types(topic_names_and_types);
  return RMW_RET_ERROR;
  */
}

rmw_ret_t
rmw_destroy_topic_names_and_types(
  rmw_topic_names_and_types_t * topic_names_and_types)
{
  RMW_SET_ERROR_MSG("rmw_destroy_topic_names_and_types() not yet implemented");
  (void)topic_names_and_types;
  return RMW_RET_ERROR;
  /*
  if (!topic_names_and_types) {
    RMW_SET_ERROR_MSG("topics handle is null");
    return RMW_RET_ERROR;
  }
  destroy_topic_names_and_types(topic_names_and_types);
  return RMW_RET_OK;
  */
}

rmw_ret_t
rmw_count_publishers(
  const rmw_node_t * node,
  const char * topic_name,
  size_t * count)
{
  if (!node) {
    RMW_SET_ERROR_MSG("node handle is null");
    return RMW_RET_ERROR;
  }
  if (node->implementation_identifier != freertps_cpp_identifier) {
    RMW_SET_ERROR_MSG("node handle is not from this rmw implementation");
    return RMW_RET_ERROR;
  }
  if (!topic_name) {
    RMW_SET_ERROR_MSG("topic name is null");
    return RMW_RET_ERROR;
  }
  if (!count) {
    RMW_SET_ERROR_MSG("count handle is null");
    return RMW_RET_ERROR;
  }
  RMW_SET_ERROR_MSG("rmw_count_publishers() not yet implemented");
  return RMW_RET_ERROR;
  /*
  auto node_info = static_cast<OpenSpliceStaticNodeInfo *>(node->data);
  if (!node_info) {
    RMW_SET_ERROR_MSG("node info handle is null");
    return RMW_RET_ERROR;
  }
  if (!node_info->publisher_listener) {
    RMW_SET_ERROR_MSG("publisher listener handle is null");
    return RMW_RET_ERROR;
  }

  const auto & topic_names_and_types = node_info->publisher_listener->topic_names_and_types;
  auto it = topic_names_and_types.find(topic_name);
  if (it == topic_names_and_types.end()) {
    *count = 0;
  } else {
    *count = it->second.size();
  }
  return RMW_RET_OK;
  */
}

rmw_ret_t
rmw_get_gid_for_publisher(const rmw_publisher_t * publisher, rmw_gid_t * gid)
{
  RMW_SET_ERROR_MSG("rmw_get_gid_for_publisher() not yet implemented");
  return RMW_RET_ERROR;
}
rmw_ret_t
rmw_compare_gids_equal(const rmw_gid_t * gid1, const rmw_gid_t * gid2, bool * result)
{
  RMW_SET_ERROR_MSG("rmw_compare_gids_equal() not yet implemented");
  return RMW_RET_ERROR;
}

rmw_ret_t
rmw_count_subscribers(
  const rmw_node_t * node,
  const char * topic_name,
  size_t * count)
{
  if (!node) {
    RMW_SET_ERROR_MSG("node handle is null");
    return RMW_RET_ERROR;
  }
  if (node->implementation_identifier != freertps_cpp_identifier) {
    RMW_SET_ERROR_MSG("node handle is not from this rmw implementation");
    return RMW_RET_ERROR;
  }
  if (!topic_name) {
    RMW_SET_ERROR_MSG("topic name is null");
    return RMW_RET_ERROR;
  }
  if (!count) {
    RMW_SET_ERROR_MSG("count handle is null");
    return RMW_RET_ERROR;
  }
  RMW_SET_ERROR_MSG("rmw_count_subscribers() not yet implemented");
  return RMW_RET_ERROR;
  /*
  auto node_info = static_cast<OpenSpliceStaticNodeInfo *>(node->data);
  if (!node_info) {
    RMW_SET_ERROR_MSG("node info handle is null");
    return RMW_RET_ERROR;
  }
  if (!node_info->subscriber_listener) {
    RMW_SET_ERROR_MSG("subscriber listener handle is null");
    return RMW_RET_ERROR;
  }

  const auto & topic_names_and_types = node_info->subscriber_listener->topic_names_and_types;
  auto it = topic_names_and_types.find(topic_name);
  if (it == topic_names_and_types.end()) {
    *count = 0;
  } else {
    *count = it->second.size();
  }
  return RMW_RET_OK;
  */
}
}  // extern "C"
