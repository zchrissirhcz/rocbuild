cmake_minimum_required(VERSION 3.20)
project(test_rule14)
include("../../overlook.cmake")
add_executable(test_rule14
  ${CMAKE_CURRENT_SOURCE_DIR}/main.c
)

