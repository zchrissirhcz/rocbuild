cmake_minimum_required(VERSION 3.20)
project(test_rule24)
include("../../overlook.cmake")
add_executable(test_rule24
  ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp
)

