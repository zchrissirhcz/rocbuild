# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2025-03-09 15:08:06

# This cmake plugin let you run clang-tidy on specified target
# Each time you run "make", it report warnings if potential bug found
#
# Usage:
# include(clang-tidy.cmake)
# rocbuild_apply_clang_tidy(clang-tidy-executable target)
#
# e.g.
# # VS2022
# rocbuild_apply_clang_tidy("C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/Llvm/x64/bin/clang-tidy.exe" main)
# 
# # ubuntu 22.04
# rocbuild_apply_clang_tidy(clang-tidy-18 main)
#

cmake_minimum_required(VERSION 3.15)
include_guard()


# Apply clang-tidy on source files of given target
# CLANG_TIDY_EXECUTABLE: clang-tidy executable file path
#   - Ubuntu: https://apt.llvm.org/
#   - Windows: "https://github.com/llvm/llvm-project/releases/"
#   - Windows with VS2022: "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/Llvm/x64/bin/clang-tidy.exe"
#   - Android NDK on Windows: don't use NDK's clang-tidy.exe. Use "clang-tidy" instead.
# TARGET: target name
function(rocbuild_apply_clang_tidy CLANG_TIDY_EXECUTABLE TARGET)
  # collecting absolute paths for each source file in the given target
  get_target_property(target_sources ${TARGET} SOURCES)
  get_target_property(target_source_dir ${TARGET} SOURCE_DIR)
  # message(STATUS "target_source_dir: ${target_source_dir}")
  # message(STATUS "target_sources:")
  set(src_path_lst "")
  foreach(target_source ${target_sources})
    # message(STATUS "   ${target_source}")
    if(IS_ABSOLUTE ${target_source})
      set(target_source_absolute_path ${target_source})
    else()
      set(target_source_absolute_path ${target_source_dir}/${target_source})
    endif()
    list(APPEND src_path_lst ${target_source_absolute_path})
  endforeach()

  # prepare clang-tidy command with arguments
  set(clang_tidy_full_command "${CLANG_TIDY_EXECUTABLE}")
  list(APPEND clang_tidy_full_command "-p")
  list(APPEND clang_tidy_full_command "${CMAKE_BINARY_DIR}")
  list(APPEND clang_tidy_full_command "${src_path_lst}")

  add_custom_target(
    ${TARGET}_clang-tidy
    COMMAND ${clang_tidy_full_command}
  )
  add_dependencies(${TARGET} ${TARGET}_clang-tidy)
endfunction()
