cmake_minimum_required(VERSION 3.20)
project(test_rule6)
include("../../overlook.cmake")
add_executable(test_rule6
  ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp
)

