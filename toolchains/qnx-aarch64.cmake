# Request license and download SDP from QNX Software Center: https://www.qnx.com/products/everywhere/
# reference: 
# - https://github.com/conan-io/conan/issues/15752
# - https://www.qnx.com/developers/docs/7.1/index.html#com.qnx.doc.security.system/topic/manual/stack_protection.html
# - https://www.qnx.com/developers/docs/8.0/com.qnx.doc.security.system/topic/manual/stack_protection.html

set(CMAKE_SYSTEM_NAME QNX)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

if((NOT DEFINED ENV{QNX_HOST}) OR (NOT DEFINED ENV{QNX_TARGET}))
  message(FATAL_ERROR "Please do: source /path/to/qnxsdp-env.sh (Linux) or call /path/to/qnxsdp-env.bat (Windows)")
endif()
set(QNX_HOST "$ENV{QNX_HOST}")
set(QNX_TARGET "$ENV{QNX_TARGET}")

# this requires license
# set(CMAKE_C_FLAGS_INIT "-Vgcc_ntoaarch64le")
# set(CMAKE_CXX_FLAGS_INIT "-lang-c++ -Vgcc_ntoaarch64le")
# find_program(CMAKE_C_COMPILER   qcc    PATHS "${QNX_HOST}/usr/bin" NO_DEFAULT_PATH)
# find_program(CMAKE_CXX_COMPILER q++    PATHS "${QNX_HOST}/usr/bin" NO_DEFAULT_PATH)

# this does not require license
find_program(CMAKE_C_COMPILER   ntoaarch64-gcc    PATHS "${QNX_HOST}/usr/bin" NO_DEFAULT_PATH)
find_program(CMAKE_CXX_COMPILER ntoaarch64-g++    PATHS "${QNX_HOST}/usr/bin" NO_DEFAULT_PATH)

find_program(CMAKE_AR           ntoaarch64-ar     PATHS "${QNX_HOST}/usr/bin" NO_DEFAULT_PATH)
find_program(CMAKE_STRIP        ntoaarch64-strip  PATHS "${QNX_HOST}/usr/bin" NO_DEFAULT_PATH)
find_program(CMAKE_RANLIB       ntoaarch64-ranlib PATHS "${QNX_HOST}/usr/bin" NO_DEFAULT_PATH)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)
