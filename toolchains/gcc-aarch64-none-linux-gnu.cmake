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

set(CMAKE_SYSROOT "${TOOLCHAIN_ROOT}/aarch64-none-linux-gnu/libc")

find_program(CMAKE_C_COMPILER   aarch64-none-linux-gnu-gcc PATHS "${TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)
find_program(CMAKE_CXX_COMPILER aarch64-none-linux-gnu-g++ PATHS "${TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)

set(CMAKE_FIND_ROOT_PATH ${TOOLCHAIN_ROOT})
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)

include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)
