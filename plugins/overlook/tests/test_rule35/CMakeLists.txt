cmake_minimum_required(VERSION 3.20)
project(test_rule35)
include("../../overlook.cmake")
set(CMAKE_BUILD_TYPE Debug)
add_executable(test_rule35
  ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp
)
