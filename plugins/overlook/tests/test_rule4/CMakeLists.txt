cmake_minimum_required(VERSION 3.20)
project(test_rule4)
#include("../../overlook.cmake")
add_executable(test_rule4
  ${CMAKE_CURRENT_SOURCE_DIR}/main.c
)

