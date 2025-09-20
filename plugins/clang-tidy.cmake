# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Create: 2025-03-09 15:08:06
# Modify: 2025-09-20 12:36:00

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
# # macOS
# rocbuild_apply_clang_tidy("/Users/zz/soft/LLVM-20.1.1-macOS-ARM64/bin/clang-tidy" main)
#

cmake_minimum_required(VERSION 3.15)
include_guard()


# Apply clang-tidy on source files of given target with support for ignoring specific files
# CLANG_TIDY_EXECUTABLE: clang-tidy executable file path
#   - Ubuntu: https://apt.llvm.org/
#   - Windows: "https://github.com/llvm/llvm-project/releases/"
#   - Windows with VS2022: "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/Llvm/x64/bin/clang-tidy.exe"
#   - Android NDK on Windows: don't use NDK's clang-tidy.exe. Use "clang-tidy" instead.
# TARGET: target name
# IGNORED_FILES: list of files to ignore (optional, default is empty)
function(rocbuild_apply_clang_tidy CLANG_TIDY_EXECUTABLE TARGET)
  # Parse optional ignored files argument
  set(options "")
  set(oneValueArgs "")
  set(multiValueArgs IGNORED_FILES)
  cmake_parse_arguments(ARG "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

  # Collecting absolute paths for each source file in the given target
  get_target_property(target_sources ${TARGET} SOURCES)
  get_target_property(target_source_dir ${TARGET} SOURCE_DIR)

  set(src_path_lst "")
  foreach(target_source ${target_sources})
    # Get absolute path for the source file
    if(IS_ABSOLUTE ${target_source})
      set(target_source_absolute_path ${target_source})
    else()
      set(target_source_absolute_path ${target_source_dir}/${target_source})
    endif()

    # Check if this file should be ignored
    set(should_ignore FALSE)
    foreach(ignored_file ${ARG_IGNORED_FILES})
      # Check both absolute and relative paths for matching
      if(IS_ABSOLUTE ${ignored_file})
        if("${target_source_absolute_path}" STREQUAL "${ignored_absolute}")
          set(should_ignore TRUE)
          break()
        endif()
      else()
        if("${target_source}" MATCHES "${ignored_file}")
          set(should_ignore TRUE)
          break()
        endif()
      endif()
    endforeach()

    # Only add the file if it's not in the ignored list
    if(NOT should_ignore)
      list(APPEND src_path_lst ${target_source_absolute_path})
    else()
      message(STATUS "clang-tidy: Ignoring file ${target_source_absolute_path}")
    endif()
  endforeach()

  # Prepare clang-tidy command with arguments
  set(clang_tidy_full_command "${CLANG_TIDY_EXECUTABLE}")
  list(APPEND clang_tidy_full_command "-p")
  list(APPEND clang_tidy_full_command "${CMAKE_BINARY_DIR}")
  list(APPEND clang_tidy_full_command "${src_path_lst}")

  list(APPEND clang_tidy_full_command "--use-color")

  add_custom_target(
    clang-tidy_${TARGET}
    COMMAND ${clang_tidy_full_command}
    COMMENT "Running clang-tidy on target ${TARGET}"
  )
  add_dependencies(${TARGET} clang-tidy_${TARGET})
endfunction()