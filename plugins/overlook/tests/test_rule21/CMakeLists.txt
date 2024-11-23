cmake_minimum_required(VERSION 3.20)
project(test_rule21)
include("../../overlook.cmake")
add_executable(test_rule21
  ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp
)

