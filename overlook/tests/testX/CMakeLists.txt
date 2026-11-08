cmake_minimum_required(VERSION 3.20)
project(testcaseX)
include("../../overlook.cmake")
add_executable(testcaseX
  ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp
)