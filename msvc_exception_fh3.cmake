# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2024-06-30 13:08 :00
cmake_minimum_required(VERSION 3.15)
include_guard()

# Scenario:
# - build an library `hello` with VS2019 >= 16.3 (or VS2022), which uses Frame Handler 4 on default (`__CxxFrameHandler4`)
# - link this library `hello` in VS2017/VS2015, or VS2019 < 16.3, which uses Frame Handler 3 on default (`__CxxFrameHandler3`)
# - then comes link error: unresolved external symbol __CxxFrameHandler4
# For a full example, see https://github.com/zchrissirhcz/min-repros/tree/master/test_GS_EHsc_link_error
#

option(USE_COMPATIBLE_FRAME_HANDLER_FOR_VS "Switch off FH4 feature(then use FH3) for compatibility?" ON)

if(USE_COMPATIBLE_FRAME_HANDLER_FOR_VS)
  if((CMAKE_CXX_COMPILER_ID STREQUAL "MSVC") AND (CMAKE_CXX_COMPILER_VERSION STRGREATER_EQUAL 16.3))
    # https://devblogs.microsoft.com/cppblog/making-cpp-exception-handling-smaller-x64
    # https://devblogs.microsoft.com/cppblog/msvc-backend-updates-in-visual-studio-2019-version-16-2/
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /d2FH4-") # Disable FH4, means use FH3
    # You may also manually turn this on by:
    # VS2019->Properties->C/C++->Command Line add '-d2FH4-'

    # TODO: is link options also required?
    # VS2019->Properties->Linker->Command Line add '-d2:-FH4-'
  endif()
  message(STATUS ">>> USE_COMPATIBLE_FRAME_HANDLER_FOR_VS: YES")
else()
  message(STATUS ">>> USE_COMPATIBLE_FRAME_HANDLER_FOR_VS: NO")
endif()