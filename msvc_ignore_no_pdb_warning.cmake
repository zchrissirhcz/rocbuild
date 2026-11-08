# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2024-06-12 00:00:00
cmake_minimum_required(VERSION 3.15)
include_guard()

#set_target_properties(${PROJECT_NAME} PROPERTIES LINK_FLAGS "/ignore:4099")
add_link_options(
  "$<$<COMPILE_LANG_AND_ID:C,MSVC>:/ignore:4099>"
  "$<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/ignore:4099>"
)
