# Android NDK toolchain wrapper.
#
# `juicy.py -p android` passes JUICY_TOOLCHAIN_ROOT (the NDK root) and this file
# includes the NDK's own toolchain, so all platforms use the same root variable.

if(NOT JUICY_TOOLCHAIN_ROOT)
  message(FATAL_ERROR "Please set JUICY_TOOLCHAIN_ROOT to the Android NDK root")
endif()

set(_android_toolchain "${JUICY_TOOLCHAIN_ROOT}/build/cmake/android.toolchain.cmake")
if(NOT EXISTS "${_android_toolchain}")
  message(FATAL_ERROR "Android NDK toolchain not found: ${_android_toolchain}")
endif()

set(JUICY_TOOLCHAIN_ROOT "${JUICY_TOOLCHAIN_ROOT}" CACHE INTERNAL "Toolchain root")
include("${_android_toolchain}")
list(APPEND CMAKE_TRY_COMPILE_PLATFORM_VARIABLES JUICY_TOOLCHAIN_ROOT)
unset(_android_toolchain)
