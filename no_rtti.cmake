# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2026-11-07 21:43:00
cmake_minimum_required(VERSION 3.15)
include_guard()

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:-fno-rtti>")
elseif(MSVC)
    # 精确地从 CMAKE_CXX_FLAGS 中移除 /GR 这一项(不会误伤 /GR-)
    separate_arguments(_cxx_flags NATIVE_COMMAND "${CMAKE_CXX_FLAGS}")
    list(REMOVE_ITEM _cxx_flags "/GR")
    string(JOIN " " CMAKE_CXX_FLAGS ${_cxx_flags})

    add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:/GR->")
endif()