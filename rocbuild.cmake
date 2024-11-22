# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild

cmake_minimum_required(VERSION 3.10)

# CMake 3.10: include_guard()

include_guard()


macro(rocbuild_set_artifacts_path)
  if(NOT CMAKE_RUNTIME_OUTPUT_DIRECTORY)
    # Where add_executable() generates executable file
    # Where add_library(SHARED) generates .dll file on Windowos
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}" CACHE INTERNAL "")
  endif()

  if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
    # Where add_library(MODULE) generates loadable module file (.dll or .so)
    # Where add_library(SHARED) generates shared library (.so, .dylib)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}" CACHE INTERNAL "")
  endif()

  if(NOT CMAKE_ARCHIVE_OUTPUT_DIRECTORY)
    # Where add_library(STATIC) generates static library file
    # Where add_library(SHARED) generates the import library file (.lib) of the shared library (.dll) if exports at least one symbol
    # Where add_executable() generates the import library file (.lib) of the executable target if ENABLE_EXPORTS target property is set
    # Where add_executable() generates the linker import file (.imp on AIX) of the executable target if ENABLE_EXPORTS target property is set
    # Where add_library(SHARED) generates the linker import file (.tbd) of the shared library target if ENABLE_EXPORTS target property is set
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}" CACHE INTERNAL "")
  endif()
endmacro()


macro(rocbuild_enable_ninja_colorful_output)  
  # When building a CMake-based project, Ninja may speedup the building speed, comparing to Make.
  # However, with `-GNinja` specified, compile errors are with no obvious colors.
  # This cmake plugin just solve this mentioned problem, giving colorful output for Ninja.
  ## References: https://medium.com/@alasher/colored-c-compiler-output-with-ninja-clang-gcc-10bfe7f2b949
  add_compile_options(
    "$<$<COMPILE_LANG_AND_ID:CXX,GNU>:-fdiagnostics-color=always>"
    "$<$<COMPILE_LANG_AND_ID:CXX,Clang,AppleClang>:-fcolor-diagnostics>"
    "$<$<COMPILE_LANG_AND_ID:C,GNU>:-fdiagnostics-color=always>"
    "$<$<COMPILE_LANG_AND_ID:C,Clang,AppleClang>:-fcolor-diagnostics>"
  )
endmacro()


macro(rocbuild_enable_sanitizer_options)
  if(ASAN)
    include(plugins/asan.cmake)
  endif()

  if(HWASAN)
    include(plugins/hwasan.cmake)
  endif()

  if(TSAN)
    include(plugins/tsan.cmake)
  endif()
endmacro()


rocbuild_set_artifacts_path()
rocbuild_enable_ninja_colorful_output()
rocbuild_enable_sanitizer_options()