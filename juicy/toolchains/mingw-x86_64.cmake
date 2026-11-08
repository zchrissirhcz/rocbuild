# author: Zhuo Zhang <imzhuo@foxmail.com>

# for Ninja, Ninja Multi-Config

# Compiler downloaded from https://nuwen.net/mingw.html
# (Stephan T. Lavavej's "MinGW Distro"; STL is the author of MSVC's STL)
#
# Also usable for cross compiling on Linux: set JUICY_TOOLCHAIN_ROOT (or the
# JUICY_TOOLCHAIN_ROOT environment variable) to the MinGW prefix, e.g. /usr.

set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

if(NOT JUICY_TOOLCHAIN_ROOT)
  set(JUICY_TOOLCHAIN_ROOT "$ENV{JUICY_TOOLCHAIN_ROOT}")
endif()
if(NOT JUICY_TOOLCHAIN_ROOT)
  if(CMAKE_HOST_WIN32)
    set(JUICY_TOOLCHAIN_ROOT "C:/soft/toolchains/MinGW")
  else()
    message(FATAL_ERROR "Please set JUICY_TOOLCHAIN_ROOT or ENV{JUICY_TOOLCHAIN_ROOT} to the MinGW root directory")
  endif()
endif()
set(JUICY_TOOLCHAIN_ROOT "${JUICY_TOOLCHAIN_ROOT}" CACHE INTERNAL "Toolchain root")

# find_program adds the host executable suffix (.exe on Windows) itself, and
# tries the cross-prefixed name first so the same file works on Linux.
find_program(CMAKE_C_COMPILER NAMES x86_64-w64-mingw32-gcc gcc PATHS "${JUICY_TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)
find_program(CMAKE_CXX_COMPILER NAMES x86_64-w64-mingw32-g++ g++ PATHS "${JUICY_TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)
find_program(CMAKE_RC_COMPILER NAMES x86_64-w64-mingw32-windres windres PATHS "${JUICY_TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)
find_program(CMAKE_AR NAMES x86_64-w64-mingw32-ar ar PATHS "${JUICY_TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)
find_program(CMAKE_RANLIB NAMES x86_64-w64-mingw32-ranlib ranlib PATHS "${JUICY_TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)
find_program(CMAKE_STRIP NAMES x86_64-w64-mingw32-strip strip PATHS "${JUICY_TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)

set(CMAKE_FIND_ROOT_PATH "${JUICY_TOOLCHAIN_ROOT}/x86_64-w64-mingw32")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)
