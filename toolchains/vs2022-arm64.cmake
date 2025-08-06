# author: Zhuo Zhang <imzhuo@foxmail.com>

# for Ninja, Ninja Multi-Config

set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

set(VS2022_PATH "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.44.35207/bin")
set(WINDOWS_SDK_VERSION "10.0.26100.0")
set(CMAKE_C_COMPILER "${VS2022_PATH}/Hostarm64/arm64/cl.exe")
set(CMAKE_CXX_COMPILER "${VS2022_PATH}/Hostarm64/arm64/cl.exe")
set(CMAKE_RC_COMPILER "C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/arm64/rc.exe")
set(CMAKE_MT "C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/arm64/mt.exe")

include_directories(
  "C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/ucrt/stdio.h" # stdio.h, stdlib.h, etc.
  "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.44.35207/include" # algorithm, vector, etc.
  "C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/um"  # Windows.h, winbase.h, etc.
  "C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared" # winapifamily.h, windef.h, winnt.h, etc.
)
link_directories(
  "C:/Program Files (x86)/Windows Kits/10/Lib/10.0.26100.0/ucrt/arm64" # ucrt.lib
  "C:/Program Files (x86)/Windows Kits/10/Lib/10.0.26100.0/um/arm64" # kernel32.lib, user32.lib, etc. # ok
  "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.44.35207/lib/arm64" # msvcprtd.lib, libcmt.lib, etc.
)

# set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
# set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
# set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
# set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

set(CMAKE_CROSSCOMPILING FALSE)

include(${CMAKE_CURRENT_LIST_DIR}/toolchain-checker.cmake)
