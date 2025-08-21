# author: Zhuo Zhang <imzhuo@foxmail.com>

cmake_minimum_required(VERSION 3.10)
include_guard()

if(NOT CMAKE_SYSTEM_NAME)
  message(FATAL_ERROR "Please set(CMAKE_SYSTEM_NAME <some_value>) in <CMAKE_TOOLCHAIN_FILE>")
  # https://cmake.org/cmake/help/latest/variable/CMAKE_SYSTEM_NAME.html#variable:CMAKE_SYSTEM_NAME
  # Linux, Windows, Generic (embedded system without an OS)
endif()

if(NOT CMAKE_SYSTEM_PROCESSOR)
  message(FATAL_ERROR "Please set(CMAKE_SYSTEM_PROCESSOR <some_value>) in <CMAKE_TOOLCHAIN_FILE>")
endif()

if(NOT CMAKE_C_COMPILER)
  message(FATAL_ERROR "Please set(CMAKE_C_COMPILER <some_value>) in <CMAKE_TOOLCHAIN_FILE>")
endif()

if(NOT CMAKE_CXX_COMPILER)
  message(FATAL_ERROR "Please set(CMAKE_CXX_COMPILER <some_value>) in <CMAKE_TOOLCHAIN_FILE>")
endif()

if(NOT CMAKE_SYSROOT)
  message(WARNING "CMAKE_SYSROOT is not set, IDE may not be able to find system headers like stdio.h")
endif()

if(NOT WIN32)
  if(NOT (${CMAKE_CXX_FLAGS_INIT} MATCHES "-isystem"))
    message(WARNING "CMAKE_CXX_FLAGS_INIT does not contain -isystem, IDE may not be able to find C++ headers like iostream")
  endif()
endif()

message(STATUS "CMAKE_TOOLCHAIN_FILE summary:")
message(STATUS "  CMAKE_SYSTEM_NAME : ${CMAKE_SYSTEM_NAME}")
message(STATUS "  CMAKE_SYSTEM_PROCESSOR : ${CMAKE_SYSTEM_PROCESSOR}")
message(STATUS "  CMAKE_C_COMPILER : ${CMAKE_C_COMPILER}")
message(STATUS "  CMAKE_CXX_COMPILER : ${CMAKE_CXX_COMPILER}")
message(STATUS "")
message(STATUS "  CMAKE_FIND_ROOT_PATH_MODE_PROGRAM : ${CMAKE_FIND_ROOT_PATH_MODE_PROGRAM}")
message(STATUS "  CMAKE_FIND_ROOT_PATH_MODE_LIBRARY : ${CMAKE_FIND_ROOT_PATH_MODE_LIBRARY}")
message(STATUS "  CMAKE_FIND_ROOT_PATH_MODE_INCLUDE : ${CMAKE_FIND_ROOT_PATH_MODE_INCLUDE}")
message(STATUS "  CMAKE_FIND_ROOT_PATH_MODE_PACKAGE : ${CMAKE_FIND_ROOT_PATH_MODE_PACKAGE}")
message(STATUS "")
message(STATUS "  CMAKE_SYSROOT : ${CMAKE_SYSROOT}")
message(STATUS "  CMAKE_C_FLAGS_INIT : ${CMAKE_C_FLAGS_INIT}")
message(STATUS "  CMAKE_CXX_FLAGS_INIT : ${CMAKE_CXX_FLAGS_INIT}")
message(STATUS "")