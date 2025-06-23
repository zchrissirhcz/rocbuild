# vs2015-x64.toolchain.cmake
# for Ninja, Ninja Multi-Config

set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

set(VS2015_PATH "C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/bin")
set(WINDOWS_SDK_VERSION "10.0.14393.0")
set(CMAKE_C_COMPILER ${VS2015_PATH}/amd64/cl.exe)
set(CMAKE_CXX_COMPILER ${VS2015_PATH}/amd64/cl.exe)
set(CMAKE_RC_COMPILER "C:/Program Files (x86)/Windows Kits/10/bin/x64/rc.exe")
set(CMAKE_MT "C:/Program Files (x86)/Windows Kits/10/bin/x64/mt.exe")

include_directories(
  "C:/Program Files (x86)/Windows Kits/10/Include/10.0.14393.0/ucrt" # stdio.h, stdlib.h, etc.
  "C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/include" # algorithm, vector, etc.
  "C:/Program Files (x86)/Windows Kits/10/Include/10.0.14393.0/um" # Windows.h, winbase.h, etc.
  "C:/Program Files (x86)/Windows Kits/10/Include/10.0.14393.0/shared" # winapifamily.h, windef.h, winnt.h, etc.
)
link_directories(
  "C:/Program Files (x86)/Windows Kits/10/Lib/10.0.14393.0/ucrt/x64" # ucrt.lib
  "C:/Program Files (x86)/Windows Kits/10/Lib/10.0.14393.0/um/x64" # kernel32.lib, user32.lib, etc.
  "C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/lib/amd64" # msvcprtd.lib, libcmt.lib, etc.
)

# set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
# set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
# set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
# set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

set(CMAKE_CROSSCOMPILING 0)
