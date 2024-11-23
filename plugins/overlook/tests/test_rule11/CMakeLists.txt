cmake_minimum_required(VERSION 3.20)
project(test_rule11)
include("../../overlook.cmake")
add_executable(test_rule11
  ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp
)

