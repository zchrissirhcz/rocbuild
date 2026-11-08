# author: Zhuo Zhang <imzhuo@foxmail.com>

# Download toolchain from https://developer.arm.com/downloads/-/gnu-a/9-2-2019-12

set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

if(NOT TOOLCHAIN_ROOT)
  set(TOOLCHAIN_ROOT $ENV{TOOLCHAIN_ROOT})
endif()
if(NOT TOOLCHAIN_ROOT)
  message(WARNING "Please set TOOLCHAIN_ROOT or ENV{TOOLCHAIN_ROOT} to toolchain root directory")
  message(WARNING "Windows: D:/soft/toolchains/aarch64-linux-gnu/gcc-arm-9.2-2019.12-mingw-w64-i686-aarch64-none-linux-gnu")
  message(WARNING "Linux: /opt/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu")
  message(FATAL_ERROR "")
endif()

# Make variables visible in try_compile() command
set(CMAKE_TRY_COMPILE_PLATFORM_VARIABLES TOOLCHAIN_ROOT)

# ROCBUILD_TARGET_TRIPLET
set(ROCBUILD_TARGET_TRIPLET aarch64-none-linux-gnu)

# CMAKE_FIND_ROOT_PATH_MODE_XXX
set(CMAKE_FIND_ROOT_PATH ${TOOLCHAIN_ROOT})
if(NOT CMAKE_FIND_ROOT_PATH_MODE_PROGRAM)
  set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
endif()
if(NOT CMAKE_FIND_ROOT_PATH_MODE_INCLUDE)
  set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
endif()

# Programs
find_program(CMAKE_C_COMPILER   ${ROCBUILD_TARGET_TRIPLET}-gcc PATHS "${TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)
find_program(CMAKE_CXX_COMPILER ${ROCBUILD_TARGET_TRIPLET}-g++ PATHS "${TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)

# CMAKE_SYSROOT
execute_process(
  COMMAND ${CMAKE_C_COMPILER} -print-sysroot
  OUTPUT_VARIABLE COMPILER_SYSROOT
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_QUIET
  RESULT_VARIABLE CMD_RESULT
)
if(CMD_RESULT EQUAL 0 AND NOT "${COMPILER_SYSROOT}" STREQUAL "")
  set(CMAKE_SYSROOT "${COMPILER_SYSROOT}" CACHE PATH "System root from compiler" FORCE)
else()
  message(FATAL_ERROR "No CMAKE_SYSROOT found from c compiler")
  # set(CMAKE_SYSROOT "${TOOLCHAIN_ROOT}/aarch64-none-linux-gnu/libc")
endif()
file(REAL_PATH ${CMAKE_SYSROOT} CMAKE_SYSROOT)
unset(COMPILER_SYSROOT)
unset(CMD_RESULT)

# C include directories
set(CMAKE_C_STANDARD_INCLUDE_DIRECTORIES "${CMAKE_SYSROOT}/libc/usr/include")

# C++ include directories
file(GLOB_RECURSE IOSTREAM_FILE "${TOOLCHAIN_ROOT}/*/iostream")
if(IOSTREAM_FILE)
  get_filename_component(CMAKE_CXX_STANDARD_INCLUDE_DIRECTORIES ${IOSTREAM_FILE} DIRECTORY)
else()
  message(FATAL_ERROR "C++ headers not found")
endif()
unset(IOSTREAM_FILE)

# Check
include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)
