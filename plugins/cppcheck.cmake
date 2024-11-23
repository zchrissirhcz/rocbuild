# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2024-06-12 00:00:00
cmake_minimum_required(VERSION 3.15)
include_guard()

# Usage:
# add_executable(hello hello.cpp)
# apply_cppcheck(hello)
function(apply_cppcheck TARGET)
  find_program(CMAKE_CXX_CPPCHECK NAMES cppcheck)

  # collecting absolute paths for each source file in the given target
  get_target_property(target_sources ${TARGET} SOURCES)
  get_target_property(target_source_dir ${TARGET} SOURCE_DIR)
  set(src_path_lst "")
  foreach(target_source ${target_sources})
    if(IS_ABSOLUTE ${target_source})
      set(target_source_absolute_path ${target_source})
    else()
      set(target_source_absolute_path ${target_source_dir}/${target_source})
    endif()
    list(APPEND src_path_lst ${target_source_absolute_path})
  endforeach()

  set(cppcheck_raw_command "cppcheck --enable=warning --inconclusive --force --inline-suppr ${src_path_lst}")
  string(REPLACE " " ";" cppcheck_converted_command "${cppcheck_raw_command}")
  add_custom_target(
    cppcheck
    COMMAND ${cppcheck_converted_command}
  )
  add_dependencies(${TARGET} cppcheck)
endfunction()