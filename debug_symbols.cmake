# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2024-06-13 23:00:00
cmake_minimum_required(VERSION 3.15)
include_guard()

add_compile_options(
  "$<$<COMPILE_LANG_AND_ID:C,MSVC>:/Zi>"
  "$<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/Zi>"

  "$<$<COMPILE_LANG_AND_ID:C,GNU,Clang,AppleClang>:-g>"
  "$<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-g>"

  "$<$<COMPILE_LANG_AND_ID:C,Clang,AppleClang>:-fstandalone-debug>"
  "$<$<COMPILE_LANG_AND_ID:CXX,Clang,AppleClang>:-fstandalone-debug>"
)
