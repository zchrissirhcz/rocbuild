# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2024-06-13 22:14:00
cmake_minimum_required(VERSION 3.15)
include_guard()

add_compile_options(
  "$<$<COMPILE_LANG_AND_ID:C,GNU,Clang,AppleClang>:-fsanitize=thread;-fno-omit-frame-pointer;-g>"
  "$<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-fsanitize=thread;-fno-omit-frame-pointer;-g>"
)
add_link_options(
  "$<$<COMPILE_LANG_AND_ID:C,GNU,Clang,AppleClang>:-fsanitize=thread>"
  "$<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-fsanitize=thread>"
)
