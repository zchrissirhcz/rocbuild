# author: Zhuo Zhang <imzhuo@foxmail.com>

# Download toolchain from https://developer.arm.com/downloads/-/gnu-a/9-2-2019-12

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

if(WIN32)
    set(TOOLCHAIN_ROOT "D:/soft/toolchains/arm-bare-metal/gcc-arm-9.2-2019.12-mingw-w64-i686-arm-none-eabi")
else()
    set(TOOLCHAIN_ROOT "/home/zz/soft/toolchains/arm-bare-metal/gcc-arm-9.2-2019.12-x86_64-arm-none-eabi")
endif()

find_program(CMAKE_C_COMPILER   arm-none-eabi-gcc PATHS "${TOOLCHAIN_ROOT}/bin" NO_DEFAULT_PATH)
find_program(CMAKE_CXX_COMPILER arm-none-eabi-g++ PATHS "${TOOLCHAIN_ROOT}/bin" NO_DEFAULT_PATH)

set(CMAKE_EXE_LINKER_FLAGS "--specs=nosys.specs")

include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)