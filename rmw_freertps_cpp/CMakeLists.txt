cmake_minimum_required(VERSION 2.8.3)

project(rmw_freertps_cpp)

if(NOT WIN32)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -Wall -Wextra")
endif()

find_package(ament_cmake REQUIRED)

find_package(freertps REQUIRED)
if(NOT freertps_FOUND)
  message(FATAL_ERROR "Could not find freertps - not going to configure any more stuff in '${PROJECT_NAME}'")
endif()

find_package(rmw REQUIRED)
find_package(rosidl_generator_cpp REQUIRED)
find_package(rosidl_typesupport_freertps_cpp REQUIRED)

ament_export_definitions(${freertps_DEFINITIONS})
ament_export_dependencies(rmw rosidl_generator_cpp rosidl_typesupport_freertps_cpp)
ament_export_include_directories(${freertps_INCLUDE_DIRS})

link_directories(${freertps_LIBRARY_DIRS})
add_library(rmw_freertps_cpp SHARED src/functions.cpp)
ament_target_dependencies(rmw_freertps_cpp
  "rmw"
  "rosidl_generator_cpp"
  "rosidl_typesupport_freertps_cpp"
  "freertps")
# On Windows this adds the RMW_BUILDING_DLL definition.
# On Unix (GCC or Clang) it hides the symbols with -fvisibility=hidden.
configure_rmw_library(rmw_freertps_cpp)
# Additionally, on Windows, add the ROSIDL_TYPESUPPORT_OPENSPLICE_CPP_BUILDING_DLL definition.
if(WIN32)
  target_compile_definitions(rmw_freertps_cpp
      PRIVATE "ROSIDL_TYPESUPPORT_FREERTPS_CPP_BUILDING_DLL")
endif()

ament_export_libraries(rmw_freertps_cpp ${freertps_LIBRARIES})

register_rmw_implementation("rosidl_typesupport_freertps_cpp")

if(AMENT_ENABLE_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

install(
  TARGETS rmw_freertps_cpp
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
