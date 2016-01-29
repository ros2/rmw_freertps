cmake_minimum_required(VERSION 2.8.3)

project(rosidl_typesupport_freertps_cpp)

if(NOT WIN32)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -Wall -Wextra")
endif()

find_package(ament_cmake REQUIRED)

find_package(freertps REQUIRED)
if(NOT freertps_FOUND)
  message(FATAL_ERROR "Could not find freertps - skipping '${PROJECT_NAME}'")
endif()

find_package(ament_cmake_python REQUIRED)

ament_export_dependencies(rmw)
ament_export_dependencies(rosidl_cmake)
ament_export_dependencies(rosidl_generator_c)
ament_export_dependencies(rosidl_generator_cpp)
# The reason the impl folder is exported is that it contains the implementation
# for the get_*_type_support_handle functions and defines the freertps
# specific version of these functions.
ament_export_include_directories(include include/${PROJECT_NAME}/impl)

ament_python_install_package(${PROJECT_NAME})

add_library(${PROJECT_NAME} SHARED src/identifier.cpp)
if(WIN32)
  target_compile_definitions(${PROJECT_NAME}
    PRIVATE "ROSIDL_TYPESUPPORT_FREERTPS_CPP_BUILDING_DLL")
endif()
target_include_directories(${PROJECT_NAME}
  PUBLIC
  include
)
ament_export_libraries(${PROJECT_NAME})

if(AMENT_ENABLE_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  set(message_files
    "msg/BoundedArrayBounded.msg"
    "msg/BoundedArrayStatic.msg"
    "msg/BoundedArrayUnbounded.msg"

    "msg/Empty.msg"
    "msg/LargeArray.msg"

    "msg/PrimitiveStaticArrays.msg"

    "msg/PrimitivesBounded.msg"
    "msg/PrimitivesStatic.msg"
    "msg/PrimitivesUnbounded.msg"

    "msg/StaticArrayBounded.msg"
    "msg/StaticArrayStatic.msg"
    "msg/StaticArrayUnbounded.msg"

    "msg/UnboundedArrayBounded.msg"
    "msg/UnboundedArrayStatic.msg"
    "msg/UnboundedArrayUnbounded.msg"
  )

  include(cmake/register_cpp.cmake)
  set(rosidl_typesupport_freertps_cpp_DIR "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

  rosidl_typesupport_freertps_cpp_extras(
    "${CMAKE_CURRENT_SOURCE_DIR}/bin/rosidl_typesupport_freertps_cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/rosidl_typesupport_freertps_cpp/__init__.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/resource"
  )

  rosidl_generate_interfaces(${PROJECT_NAME}_msgs ${message_files}
    SKIP_INSTALL
  )

  ament_add_gtest(test_serialization_cpp test/test_serialization.cpp)
  if(TARGET test_serialization_cpp)
    target_link_libraries(test_serialization_cpp
      ${PROJECT_NAME}_msgs__rosidl_typesupport_freertps_cpp
      ${_AMENT_EXPORT_ABSOLUTE_LIBRARIES}
      ${_AMENT_EXPORT_LIBRARY_TARGETS})
    # include the built files directly, instead of their install location
    target_include_directories(test_serialization_cpp
      PUBLIC
      "${CMAKE_CURRENT_BINARY_DIR}/rosidl_typesupport_freertps_cpp"
      "${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_cpp"
    )
    add_dependencies(test_serialization_cpp ${PROJECT_NAME} rosidl_generator_cpp)
  endif()
endif()

ament_package(
  CONFIG_EXTRAS "rosidl_typesupport_freertps_cpp-extras.cmake.in"
)

install(
  PROGRAMS bin/rosidl_typesupport_freertps_cpp
  DESTINATION lib/rosidl_typesupport_freertps_cpp
)
install(
  DIRECTORY cmake resource
  DESTINATION share/${PROJECT_NAME}
)
install(
  DIRECTORY include/
  DESTINATION include
)
install(
  TARGETS ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
