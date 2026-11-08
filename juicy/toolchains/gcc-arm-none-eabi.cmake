# author: Zhuo Zhang <imzhuo@foxmail.com>

# Download toolchain from https://developer.arm.com/downloads/-/gnu-a/9-2-2019-12

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

if(NOT TOOLCHAIN_ROOT)
  message(WARNING "Please set TOOLCHAIN_ROOT or ENV{TOOLCHAIN_ROOT} to toolchain root directory")
  message(WARNING "Windows: D:/soft/toolchains/arm-bare-metal/gcc-arm-9.2-2019.12-mingw-w64-i686-arm-none-eabi")
  message(WARNING "Linux: /home/zz/soft/toolchains/arm-bare-metal/gcc-arm-9.2-2019.12-x86_64-arm-none-eabi")
  message(FATAL_ERROR "")
endif()

# Make variables visible in try_compile() command
set(CMAKE_TRY_COMPILE_PLATFORM_VARIABLES TOOLCHAIN_ROOT)

set(CMAKE_SYSROOT "${TOOLCHAIN_ROOT}")

find_program(CMAKE_C_COMPILER   arm-none-eabi-gcc PATHS "${TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)
find_program(CMAKE_CXX_COMPILER arm-none-eabi-g++ PATHS "${TOOLCHAIN_ROOT}/bin" REQUIRED NO_DEFAULT_PATH)

set(CMAKE_EXE_LINKER_FLAGS "--specs=nosys.specs")

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)

include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)
