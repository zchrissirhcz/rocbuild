set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(ZZBUILD_ROOT /opt/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu)
set(CMAKE_C_COMPILER ${ZZBUILD_ROOT}/bin/aarch64-none-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER ${ZZBUILD_ROOT}/bin/aarch64-none-linux-gnu-g++)

set(CMAKE_FIND_ROOT_PATH ${ZZBUILD_ROOT})
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM ONLY)

include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)
