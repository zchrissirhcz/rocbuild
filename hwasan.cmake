# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2024-11-14 22:50:00
cmake_minimum_required(VERSION 3.15)
include_guard()

# https://developer.android.google.cn/ndk/guides/hwasan#ndk-build
if(ANDROID)
  # Note: `-g` is explicitly required here for debug symbol information such line number and file name
  # There is NDK's android.toolchain.cmake's `-g`, in case user removed it, explicitly add `-g` here.
  set(HWASAN_OPTIONS -fsanitize=hwaddress -fno-omit-frame-pointer -g)
else()
  message(FATAL_ERROR "HWASan is only supported by Android")
endif()

# 1. NDK 21
if((CMAKE_CXX_COMPILER_ID STREQUAL "Clang") AND (CMAKE_CXX_COMPILER_VERSION GREATER_EQUAL 9.0))
  message(STATUS "HWASan check: NDK version OK")
else()
  message(FATAL_ERROR "HWSAsan check failed: requires NDK >= r21")
endif()

# 2. API
if(ANDROID_NATIVE_API_LEVEL LESS 29)
  message(FATAL_ERROR "HWASan check failed: requires ANDROID_NATIVE_API_LEVEL >= 29")
else()
  message(STATUS "HWASan check: ANDROID_NATIVE_API_LEVEL OK")
endif()

# 3. arm64
if(ANDROID_ABI STREQUAL "arm64-v8a")
  message(STATUS "HWASan check: ANDROID_ABI OK")
else()
  message(FATAL_ERROR "HWASan only works for ANDROID_ABI=armv8-a")
endif()

message(STATUS "Using HWASAN: YES")
add_compile_options(${HWASAN_OPTIONS})
add_link_options(${HWASAN_OPTIONS})
