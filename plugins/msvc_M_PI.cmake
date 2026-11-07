# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2026-11-07 23:42:00
cmake_minimum_required(VERSION 3.15)
include_guard()

if(MSVC)
  add_definitions(-D_USE_MATH_DEFINES)
endif()