# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2024-06-12 00:00:00
cmake_minimum_required(VERSION 3.15)
include_guard()

# Enables use of dynamically linked CRT
# i.e. use MD / MDd

# 设置策略CMP0091为NEW，新策略
if (POLICY CMP0091)
  cmake_policy(SET CMP0091 NEW)
endif (POLICY CMP0091)

if(MSVC AND NOT CMAKE_VERSION VERSION_LESS "3.15")
  # cmake before version 3.15 not work
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreadedDLL$<$<CONFIG:Debug>:Debug>")
endif()