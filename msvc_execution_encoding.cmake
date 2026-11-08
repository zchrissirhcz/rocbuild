# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2025-06-18 00:00:00
cmake_minimum_required(VERSION 3.15)
include_guard()

# Set executable run with gbk encoding for CP936 (GBK) locale
if(WIN32)
  if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.24)
    cmake_host_system_information(
      RESULT CodePage
      QUERY WINDOWS_REGISTRY "HKLM/SYSTEM/CurrentControlSet/Control/Nls/CodePage"
      VALUE "ACP"
    )
  else()
    include(FindPythonInterp)
    execute_process(
      COMMAND ${PYTHON_EXECUTABLE} "${CMAKE_SOURCE_DIR}/cmake/QueryCodePage.py"
      WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
      RESULT_VARIABLE ReturnCode
      OUTPUT_VARIABLE CodePage
    )
  endif()
  if("${CodePage}" STREQUAL "936")
    add_compile_options(
      "$<$<COMPILE_LANG_AND_ID:C,MSVC>:/execution-charset:gbk>"
      "$<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/execution-charset:gbk>"
    )
  endif()
endif()
