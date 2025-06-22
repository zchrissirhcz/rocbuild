set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(TCDIR /opt/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu)
set(CMAKE_C_COMPILER ${TCDIR}/bin/aarch64-none-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER ${TCDIR}/bin/aarch64-none-linux-gnu-g++)

set(CMAKE_FIND_ROOT_PATH /opt/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM ONLY)

include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)
