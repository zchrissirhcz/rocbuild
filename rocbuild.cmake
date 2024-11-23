# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild

cmake_minimum_required(VERSION 3.21)

# CMake 3.10: include_guard()
# CMake 3.21: $<TARGET_RUNTIME_DLLS:tgt>

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


function(rocbuild_copy_dll target)
  add_custom_command(TARGET ${target} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_RUNTIME_DLLS:${target}> $<TARGET_FILE_DIR:${target}>
    COMMAND_EXPAND_LISTS
  )
endfunction()


# Scan opencv_videoio dlls and copy them to the target executable's folder
function(rocbuild_copy_opencv_videoio_plugin_dlls target)
  # Sanity checks
  if(CMAKE_CROSSCOMPILING OR (NOT WIN32))
    return()
  endif()

  if(NOT TARGET ${target})
    message(WARNING "rocbuild_copy_opencv_videoio_plugin_dlls() was called with a non-target: ${target}")
    return()
  endif()

  get_target_property(TYPE ${target} TYPE)
  if(NOT ${TYPE} STREQUAL "EXECUTABLE")
    message(WARNING "rocbuild_copy_opencv_videoio_plugin_dlls() was called on a non-executable target: ${target}")
    return()
  endif()

  # If OpenCV_DIR is not set, we can't copy the opencv_videoio dlls
  if(NOT DEFINED OpenCV_DIR)
    message(WARNING "OpenCV_DIR is not defined, can't copy opencv_videoio dlls")
    return()
  endif()
  
  if(DEFINED CMAKE_CONFIGURATION_TYPES)
    set(COPY_SCRIPT "${CMAKE_BINARY_DIR}/rocbuild_copy_opencv_videoio_plugin_dlls_for_${target}_$<CONFIG>.cmake")
  else()
    set(COPY_SCRIPT "${CMAKE_BINARY_DIR}/rocbuild_copy_opencv_videoio_plugin_dlls_for_${target}.cmake")
  endif()
  set(COPY_SCRIPT_CONTENT "")

  if(EXISTS "${OpenCV_DIR}/bin")
    set(opencv_videoio_plugin_dll_dir "${OpenCV_DIR}/bin")
  elseif(EXISTS "${OpenCV_DIR}/../bin")
    set(opencv_videoio_plugin_dll_dir "${OpenCV_DIR}/../bin")
  else()
    message(WARNING "Could not find opencv videoio plugin dlls in ${OpenCV_DIR}/bin or ${OpenCV_DIR}/../bin")
    return()
  endif()

  file(REAL_PATH "${opencv_videoio_plugin_dll_dir}" opencv_videoio_plugin_dll_dir)
  file(GLOB opencv_videoio_plugin_dlls "${opencv_videoio_plugin_dll_dir}/opencv_videoio_*.dll")

  # convert opencv_videoio_dlls to a string
  string(REPLACE ";" "\n" opencv_videoio_plugin_dlls "${opencv_videoio_plugin_dlls}")

  string(APPEND COPY_SCRIPT_CONTENT
    "set(opencv_videoio_plugin_dlls\n${opencv_videoio_plugin_dlls}\n)\n"
    "foreach(file IN ITEMS \${opencv_videoio_plugin_dlls})\n"
    "  if(EXISTS \"\${file}\")\n"
    "    execute_process(COMMAND \${CMAKE_COMMAND} -E copy_if_different \"\${file}\" \"$<TARGET_FILE_DIR:${target}>\")\n"
    "  endif()\n"
    "endforeach()\n"
  )

  file(GENERATE
    OUTPUT "${COPY_SCRIPT}"
    CONTENT "${COPY_SCRIPT_CONTENT}"
  )

  add_custom_command(
    TARGET ${target}
    PRE_LINK
    COMMAND ${CMAKE_COMMAND} -E touch "${COPY_SCRIPT}"
    COMMAND ${CMAKE_COMMAND} -P "${COPY_SCRIPT}"
    COMMENT "Copying opencv_videoio plugin dlls for target ${target}"
  )
endfunction()


function(rocbuild_set_debug_postfix TARGET)
  # determine TARGET type
  get_target_property(TYPE ${TARGET} TYPE)
  if(NOT TYPE)
    message(FATAL_ERROR "rocbuild_define_package() called with non-existent target: ${TARGET}")
  endif()

  # determine if TARGET is imported
  get_target_property(IMPORTED ${TARGET} IMPORTED)
  if(IMPORTED)
    return()
  endif()

  # Don't treat for single config generators
  if(NOT CMAKE_CONFIGURATION_TYPES)
    return()
  endif()

  if(TYPE MATCHES "^(STATIC_LIBRARY|SHARED_LIBRARY|EXECUTABLE)$")
    set_target_properties(${TARGET} PROPERTIES DEBUG_POSTFIX "_d")
  endif()
endfunction()


function(rocbuild_hide_symbols TARGET)
  get_target_property(TARGET_TYPE ${TARGET} TYPE)
  if(TARGET_TYPE STREQUAL "SHARED_LIBRARY")  
    if((CMAKE_C_COMPILER_ID MATCHES "GNU|Clang") OR
       (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang"))
      target_compile_options(${TARGET} PRIVATE "-fvisibility=hidden")
    endif()
  endif()
endfunction()


rocbuild_set_artifacts_path()
rocbuild_enable_ninja_colorful_output()