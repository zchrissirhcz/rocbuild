# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2024-06-11 23:48:00
cmake_minimum_required(VERSION 3.15)
include_guard()

# When using VS2022 >= 17.10.0, and C:/Windows/System32/msvcp140.dll version < 14.40.0
# people meet crash in Release or RelWithDebInfo configuration, with error message:
# > 0xC0000005: Access violation reading location 0x0000000000000000.
#
# this runtime error can be reproduces with simple code that using `std::mutex`:
# // https://github.com/microsoft/STL/issues/4730
# #include <iostream>
# #include <mutex>
# std::mutex mtx;
#
# void testmethod() {
#         std::scoped_lock lock{ mtx };
#         std::cout << "lock worked!\n";
# }
# int main()
# {
#     std::cout << "Start!\n";
#     testmethod();
#     std::cout << "End!\n";
#     return 0;
# }
#
# Or, people are using spdlog, even don't know what `std::mutex` is, also suffer same crash with minimal code:
# // https://github.com/gabime/spdlog/issues/2902
# #include <spdlog/spdlog.h>
# int main()
# {
#     SPDLOG_INFO("x");
#     return 0;
# }
#
# The short solution is define `_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR` macro.
# The long term solution is update both "Visual Studio 2022" and "Microsoft Visual C++ 2015-2022 Redistributable package" to the latest
# And when `C:\Windows\System32\msvcp140.dll` is silently downgraded to < 14.40, people may:
# - Repair it in control panel, even it shows a misleading new version
# - Determine version in PowerShell by: `echo ((Get-Command C:\Windows\System32\msvcp140.dll).Version)`
# - Detect it first (in CMakeLists.txt), then define `_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR`
#
# https://github.com/gabime/spdlog/issues/2902
# https://github.com/microsoft/STL/issues/2285
# https://github.com/microsoft/STL/wiki/Changelog#vs-2022-1710
# https://stackoverflow.com/questions/78598141/first-stdmutexlock-crashes-in-application-built-with-latest-visual-studio/78599923#78599923
# https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170
# https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute?view=msvc-170
if((CMAKE_CXX_COMPILER_ID STREQUAL "MSVC") AND (CMAKE_CXX_COMPILER_VERSION STRGREATER_EQUAL 17.10))
  set(DLL_PATH "C:/Windows/System32/msvcp140.dll")

  # PowerShell command to get the version of the DLL and format it
  set(PS_COMMAND "[System.String]::Join('.', ((Get-Command ${DLL_PATH}).Version.Major, (Get-Command ${DLL_PATH}).Version.Minor, (Get-Command ${DLL_PATH}).Version.Build, (Get-Command ${DLL_PATH}).Version.Revision))")

  execute_process(
    COMMAND powershell -NoProfile -ExecutionPolicy Bypass -Command ${PS_COMMAND}
    OUTPUT_VARIABLE MSVCP140_DLL_VERSION
    ERROR_VARIABLE ERROR_OUTPUT
    RESULT_VARIABLE RESULT
  )

  if(RESULT EQUAL 0)
    string(STRIP "${MSVCP140_DLL_VERSION}" MSVCP140_DLL_VERSION)  # Remove any trailing newlines or spaces
    message(STATUS "${DLL_PATH} version: ${MSVCP140_DLL_VERSION}")
    if(MSVCP140_DLL_VERSION STRGREATER_EQUAL 14.40)
      add_compile_definitions(_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR)
    endif()
  else()
    message(FATAL_ERROR "Failed to get DLL version: ${ERROR_OUTPUT}")
  endif()

  unset(PS_COMMAND)
  unset(DLL_PATH)
endif()
