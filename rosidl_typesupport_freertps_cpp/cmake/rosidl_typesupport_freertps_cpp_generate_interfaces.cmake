# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set(_target_suffix "__rosidl_typesupport_freertps_cpp")

set(_output_path "${CMAKE_CURRENT_BINARY_DIR}/rosidl_typesupport_freertps_cpp/${PROJECT_NAME}")
set(_generated_msg_files "")
set(_generated_srv_files "")
foreach(_idl_file ${rosidl_generate_interfaces_IDL_FILES})
  get_filename_component(_extension "${_idl_file}" EXT)
  get_filename_component(_msg_name "${_idl_file}" NAME_WE)
  string_camel_case_to_lower_case_underscore("${_msg_name}" _header_name)
  if("${_extension} " STREQUAL ".msg ")
    get_filename_component(_parent_folder "${_idl_file}" DIRECTORY)
    get_filename_component(_parent_folder "${_parent_folder}" NAME)
    list(APPEND _generated_msg_files
      "${_output_path}/${_parent_folder}/dds_freertps/${_header_name}__type_support.hpp"
      "${_output_path}/${_parent_folder}/dds_freertps/${_header_name}__type_support.cpp")
  elseif("${_extension} " STREQUAL ".srv ")
    list(APPEND _generated_srv_files "${_output_path}/srv/dds_freertps/${_header_name}__type_support.cpp")
  else()
    message(FATAL_ERROR "Interface file with unknown extension: ${_idl_file}")
  endif()
endforeach()

# If not on Windows, disable some warnings with freertps's generated code
if(NOT WIN32)
  set(_freertps_compile_flags)
  if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
    set(_freertps_compile_flags
      "-Wno-unused-but-set-variable"
    )
  endif()
  if(NOT "${_freertps_compile_flags} " STREQUAL " ")
    string(REPLACE ";" " " _freertps_compile_flags "${_freertps_compile_flags}")
  endif()
endif()

set(_dependencies "")

foreach(_pkg_name ${rosidl_generate_interfaces_DEPENDENCY_PACKAGE_NAMES})
  foreach(_idl_file ${${_pkg_name}_INTERFACE_FILES})
    get_filename_component(_extension "${_idl_file}" EXT)
    if("${_extension} " STREQUAL ".msg ")
      get_filename_component(_parent_folder "${_idl_file}" DIRECTORY)
      get_filename_component(_parent_folder "${_parent_folder}" NAME)
      # ignore builtin_interfaces since it does not have any idl files
      set(_abs_idl_file "${${_pkg_name}_DIR}/../${_idl_file}")
      normalize_path(_abs_idl_file "${_abs_idl_file}")
      list(APPEND _dependencies "${_pkg_name}:${_abs_idl_file}")
    elseif("${_extension} " STREQUAL ".srv ")
      get_filename_component(_name "${_idl_file}" NAME_WE)

      list(APPEND _dependencies "${_pkg_name}:${_idl_file}")
    endif()
  endforeach()
endforeach()

set(target_dependencies
  "${rosidl_typesupport_freertps_cpp_BIN}"
  ${rosidl_typesupport_freertps_cpp_GENERATOR_FILES}
  "${rosidl_typesupport_freertps_cpp_TEMPLATE_DIR}/msg__type_support.hpp.template"
  "${rosidl_typesupport_freertps_cpp_TEMPLATE_DIR}/msg__type_support.cpp.template"
  "${rosidl_typesupport_freertps_cpp_TEMPLATE_DIR}/srv__type_support.cpp.template")
foreach(dep ${target_dependencies})
  if(NOT EXISTS "${dep}")
    message(FATAL_ERROR "Target dependency '${dep}' does not exist")
  endif()
endforeach()

set(generator_arguments_file "${CMAKE_BINARY_DIR}/rosidl_typesupport_freertps_cpp__arguments.json")
rosidl_write_generator_arguments(
  "${generator_arguments_file}"
  PACKAGE_NAME "${PROJECT_NAME}"
  ROS_INTERFACE_FILES "${rosidl_generate_interfaces_IDL_FILES}"
  ROS_INTERFACE_DEPENDENCIES "${_dependencies}"
  OUTPUT_DIR "${_output_path}"
  TEMPLATE_DIR "${rosidl_typesupport_freertps_cpp_TEMPLATE_DIR}"
  TARGET_DEPENDENCIES ${target_dependencies}
)

add_custom_command(
  OUTPUT
  ${_generated_msg_files}
  ${_generated_srv_files}
  COMMAND ${PYTHON_EXECUTABLE} ${rosidl_typesupport_freertps_cpp_BIN}
  --generator-arguments-file "${generator_arguments_file}"
  DEPENDS ${target_dependencies}
  COMMENT "Generating C++ type support for freertps"
  VERBATIM
)

# generate header to switch between export and import for a specific package on Windows
set(_visibility_control_file
  "${_output_path}/msg/dds_freertps/visibility_control.h")
configure_file(
  "${rosidl_typesupport_freertps_cpp_TEMPLATE_DIR}/visibility_control.h.in"
  "${_visibility_control_file}"
  @ONLY
)
list(APPEND _generated_msg_files "${_visibility_control_file}")

if(NOT rosidl_generate_interfaces_SKIP_INSTALL)
  install(
    FILES ${_generated_msg_files}
    DESTINATION "include/${PROJECT_NAME}/msg/dds_freertps"
  )
  install(
    FILES ${_generated_srv_files}
    DESTINATION "include/${PROJECT_NAME}/srv/dds_freertps"
  )
endif()

link_directories(${freertps_LIBRARY_DIRS})
add_library(${rosidl_generate_interfaces_TARGET}${_target_suffix} SHARED
  ${_generated_msg_files}
  ${_generated_srv_files})
if(WIN32)
  target_compile_definitions(${rosidl_generate_interfaces_TARGET}${_target_suffix}
    PRIVATE "ROSIDL_BUILDING_DLL")
  target_compile_definitions(${rosidl_generate_interfaces_TARGET}${_target_suffix}
    PRIVATE "ROSIDL_TYPESUPPORT_FREERTPS_CPP_BUILDING_DLL")
endif()
target_compile_definitions(${rosidl_generate_interfaces_TARGET}${_target_suffix}
  PRIVATE "ROSIDL_TYPESUPPORT_FREERTPS_CPP_BUILDING_DLL_${PROJECT_NAME}")
target_include_directories(${rosidl_generate_interfaces_TARGET}${_target_suffix}
  PUBLIC
  ${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_cpp
  ${CMAKE_CURRENT_BINARY_DIR}/rosidl_typesupport_freertps_cpp
  "${_output_path}/msg/dds_freertps"
  "${_output_path}/srv/dds_freertps"
)
ament_target_dependencies(${rosidl_generate_interfaces_TARGET}${_target_suffix} "rmw")
foreach(_pkg_name ${rosidl_generate_interfaces_DEPENDENCY_PACKAGE_NAMES})
  set(_msg_include_dir "${${_pkg_name}_DIR}/../../../include/${_pkg_name}/msg/dds_freertps")
  set(_srv_include_dir "${${_pkg_name}_DIR}/../../../include/${_pkg_name}/srv/dds_freertps")
  normalize_path(_msg_include_dir "${_msg_include_dir}")
  normalize_path(_srv_include_dir "${_srv_include_dir}")
  target_include_directories(${rosidl_generate_interfaces_TARGET}${_target_suffix}
    PUBLIC
    "${_msg_include_dir}"
    "${_srv_include_dir}"
  )
  ament_target_dependencies(
    ${rosidl_generate_interfaces_TARGET}${_target_suffix}
    ${_pkg_name})
endforeach()
ament_target_dependencies(
  ${rosidl_generate_interfaces_TARGET}${_target_suffix}
  "freertps"
  "rosidl_typesupport_freertps_cpp")

add_dependencies(
  ${rosidl_generate_interfaces_TARGET}
  ${rosidl_generate_interfaces_TARGET}${_target_suffix}
)
add_dependencies(
  ${rosidl_generate_interfaces_TARGET}${_target_suffix}
  ${rosidl_generate_interfaces_TARGET}__cpp
)

if(NOT rosidl_generate_interfaces_SKIP_INSTALL)
  install(
    TARGETS ${rosidl_generate_interfaces_TARGET}${_target_suffix}
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
  )
endif()

ament_export_libraries(${rosidl_generate_interfaces_TARGET}${_target_suffix} ${freertps_LIBRARIES})

ament_export_include_directories(include)
