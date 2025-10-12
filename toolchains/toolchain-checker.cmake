# author: Zhuo Zhang <imzhuo@foxmail.com>

cmake_minimum_required(VERSION 3.10)
include_guard()

if(NOT CMAKE_SYSTEM_NAME)
  message(FATAL_ERROR "Please set(CMAKE_SYSTEM_NAME <some_value>) in CMAKE_TOOLCHAIN_FILE: ${CMAKE_TOOLCHAIN_FILE}")
  # https://cmake.org/cmake/help/latest/variable/CMAKE_SYSTEM_NAME.html#variable:CMAKE_SYSTEM_NAME
  # Linux, Windows, Generic (embedded system without an OS)
endif()

if(NOT CMAKE_SYSTEM_PROCESSOR)
  message(FATAL_ERROR "Please set(CMAKE_SYSTEM_PROCESSOR <some_value>) in CMAKE_TOOLCHAIN_FILE: ${CMAKE_TOOLCHAIN_FILE}")
endif()

if(NOT CMAKE_C_COMPILER)
  message(FATAL_ERROR "Please set(CMAKE_C_COMPILER <some_value>) in CMAKE_TOOLCHAIN_FILE: ${CMAKE_TOOLCHAIN_FILE}")
endif()

if(NOT CMAKE_CXX_COMPILER)
  message(FATAL_ERROR "Please set(CMAKE_CXX_COMPILER <some_value>) in CMAKE_TOOLCHAIN_FILE: ${CMAKE_TOOLCHAIN_FILE}")
endif()

if(NOT CMAKE_SYSROOT)
  message(WARNING "CMAKE_SYSROOT is not set, IDE may not be able to find system headers like stdio.h")
  if(CMAKE_C_COMPILER)
    execute_process(
      COMMAND ${CMAKE_C_COMPILER} -print-sysroot
      OUTPUT_VARIABLE COMPILER_SYSROOT
      OUTPUT_STRIP_TRAILING_WHITESPACE
      RESULT_VARIABLE CMD_RESULT
    )

    if(CMD_RESULT EQUAL 0)
      if(COMPILER_SYSROOT)
        # convert to absolute path
        get_filename_component(COMPILER_SYSROOT "${COMPILER_SYSROOT}" REALPATH)
        file(RELATIVE_PATH SYSROOT_RELATIVE_TO_TOOLCHAIN "${TOOLCHAIN_ROOT}" "${COMPILER_SYSROOT}")
        set(CANDIDATE_CMAKE_SYSROOT "\${TOOLCHAIN_ROOT}/${SYSROOT_RELATIVE_TO_TOOLCHAIN}")
        string(STRIP "${CANDIDATE_CMAKE_SYSROOT}" CANDIDATE_CMAKE_SYSROOT)
        message(STATUS "Candidate CMAKE_SYSROOT: ${CANDIDATE_CMAKE_SYSROOT}")
      else()
        message(STATUS "no candidate CMAKE_SYSROOT found by -print-sysroot")
      endif()
    else()
      message(WARNING "Error when invoke ${CMAKE_C_COMPILER} -print-sysroot, msg: ${CMD_RESULT}")
    endif()
    unset(COMPILER_SYSROOT)
    unset(CMD_RESULT)
    unset(SYSROOT_RELATIVE_TO_TOOLCHAIN)
    unset(CANDIDATE_CMAKE_SYSROOT)
  endif()
elseif(NOT EXISTS "${CMAKE_SYSROOT}")
  message(WARNING "Not existent path of CMAKE_SYSROOT: ${CMAKE_SYSROOT}")
endif()

# if(NOT WIN32)
  # if(NOT (${CMAKE_CXX_FLAGS_INIT} MATCHES "-isystem"))
    # message(WARNING "CMAKE_CXX_FLAGS_INIT does not contain -isystem, IDE may not be able to find C++ headers like iostream")
  # endif()
# endif()

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
message(STATUS "  CMAKE_TRY_COMPILE_PLATFORM_VARIABLES: ${CMAKE_TRY_COMPILE_PLATFORM_VARIABLES}")
message(STATUS "")
