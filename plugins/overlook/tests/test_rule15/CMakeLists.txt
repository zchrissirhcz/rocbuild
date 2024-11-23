cmake_minimum_required(VERSION 3.20)
project(test_rule15)
include("../../overlook.cmake")
add_executable(test_rule15
  ${CMAKE_CURRENT_SOURCE_DIR}/a.c
  ${CMAKE_CURRENT_SOURCE_DIR}/b.c
)

