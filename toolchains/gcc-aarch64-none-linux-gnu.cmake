# author: Zhuo Zhang <imzhuo@foxmail.com>

# Download toolchain from https://developer.arm.com/downloads/-/gnu-a/9-2-2019-12

set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

if(WIN32)
    set(TOOLCHAIN_ROOT "D:/soft/toolchains/aarch64-linux-gnu/gcc-arm-9.2-2019.12-mingw-w64-i686-aarch64-none-linux-gnu")
else()
    set(TOOLCHAIN_ROOT "/opt/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu")
endif()

find_program(CMAKE_C_COMPILER   aarch64-none-linux-gnu-gcc PATHS "${TOOLCHAIN_ROOT}/bin" NO_DEFAULT_PATH)
find_program(CMAKE_CXX_COMPILER aarch64-none-linux-gnu-g++ PATHS "${TOOLCHAIN_ROOT}/bin" NO_DEFAULT_PATH)

set(CMAKE_FIND_ROOT_PATH ${TOOLCHAIN_ROOT})
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM ONLY)

include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)
