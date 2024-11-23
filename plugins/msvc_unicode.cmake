# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2024-05-26 23:30:00
cmake_minimum_required(VERSION 3.15)
include_guard()

# CMake generated Visual Studio Solution is multi-byte character on default
# VS2022 generated console application is unicode on default
# https://github.com/Jebbs/DSFML-C/issues/8
if (MSVC)
  add_compile_definitions(UNICODE _UNICODE)
endif()

