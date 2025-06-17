# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild

cmake_minimum_required(VERSION 3.13)

# CMake 3.10: include_guard()
# CMake 3.21: $<TARGET_RUNTIME_DLLS:tgt>
# CMake 3.13: target_link_options() use "LINKER:" as a portable way for different compiler + linker combo

include_guard()

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


# Transitively list all link libraries of a target (recursive call)
# Modified from https://github.com/libigl/libigl/blob/main/cmake/igl/igl_copy_dll.cmake, GPL-3.0 / MPL-2.0
function(rocbuild_get_target_dependencies_impl OUTPUT_VARIABLE TARGET)
  get_target_property(_aliased ${TARGET} ALIASED_TARGET)
  if(_aliased)
    set(TARGET ${_aliased})
  endif()

  get_target_property(_IMPORTED ${TARGET} IMPORTED)
  get_target_property(_TYPE ${TARGET} TYPE)
  if(_IMPORTED OR (${_TYPE} STREQUAL "INTERFACE_LIBRARY"))
    get_target_property(TARGET_DEPENDENCIES ${TARGET} INTERFACE_LINK_LIBRARIES)
  else()
    get_target_property(TARGET_DEPENDENCIES ${TARGET} LINK_LIBRARIES)
  endif()

  set(VISITED_TARGETS ${${OUTPUT_VARIABLE}})
  foreach(DEPENDENCY IN ITEMS ${TARGET_DEPENDENCIES})
    if(TARGET ${DEPENDENCY})
      get_target_property(_aliased ${DEPENDENCY} ALIASED_TARGET)
      if(_aliased)
        set(DEPENDENCY ${_aliased})
      endif()

      if(NOT (DEPENDENCY IN_LIST VISITED_TARGETS))
        list(APPEND VISITED_TARGETS ${DEPENDENCY})
        rocbuild_get_target_dependencies_impl(VISITED_TARGETS ${DEPENDENCY})
      endif()
    endif()
  endforeach()
  set(${OUTPUT_VARIABLE} ${VISITED_TARGETS} PARENT_SCOPE)
endfunction()

# Transitively list all link libraries of a target
function(rocbuild_get_target_dependencies OUTPUT_VARIABLE TARGET)
  set(DISCOVERED_TARGETS "")
  rocbuild_get_target_dependencies_impl(DISCOVERED_TARGETS ${TARGET})
  set(${OUTPUT_VARIABLE} ${DISCOVERED_TARGETS} PARENT_SCOPE)
endfunction()

# Copy .dll dependencies to a target executable's folder. This function must be called *after* all the CMake
# dependencies of the executable target have been defined, otherwise some .dlls might not be copied to the target
# folder.
function(rocbuild_copy_dlls target)
  # Sanity checks
  if(CMAKE_CROSSCOMPILING OR (NOT WIN32))
    return()
  endif()

  if(NOT TARGET ${target})
    message(STATUS "rocbuild_copy_dlls() was called with a non-target: ${target}")
    return()
  endif()

  # Sanity checks
  get_target_property(TYPE ${target} TYPE)
  if(NOT ${TYPE} STREQUAL "EXECUTABLE")
    message(FATAL_ERROR "rocbuild_copy_dlls() was called on a non-executable target: ${target}")
  endif()

  if(CMAKE_VERSION VERSION_GREATER_EQUAL "3.21")
    add_custom_command(TARGET ${target} POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_RUNTIME_DLLS:${target}> $<TARGET_FILE_DIR:${target}>
      COMMAND_EXPAND_LISTS
    )
    return()
  endif()

  # set the name of file to be written
  if(DEFINED CMAKE_CONFIGURATION_TYPES)
    set(COPY_SCRIPT "${CMAKE_BINARY_DIR}/rocbuild_copy_dlls_${target}_$<CONFIG>.cmake")
  else()
    set(COPY_SCRIPT "${CMAKE_BINARY_DIR}/rocbuild_copy_dlls_${target}.cmake")
  endif()

  add_custom_command(
    TARGET ${target}
    PRE_LINK
    COMMAND ${CMAKE_COMMAND} -E touch "${COPY_SCRIPT}"
    COMMAND ${CMAKE_COMMAND} -P "${COPY_SCRIPT}"
    COMMENT "Copying dlls for target ${target}"
  )

  # Retrieve all target dependencies
  rocbuild_get_target_dependencies(TARGET_DEPENDENCIES ${target})

  set(DEPENDENCY_FILES "")
  foreach(DEPENDENCY IN LISTS TARGET_DEPENDENCIES)
    get_target_property(TYPE ${DEPENDENCY} TYPE)
    if(NOT (${TYPE} STREQUAL "SHARED_LIBRARY" OR ${TYPE} STREQUAL "MODULE_LIBRARY"))
      continue()
    endif()
    string(APPEND DEPENDENCY_FILES "  $<TARGET_FILE:${DEPENDENCY}> # ${DEPENDENCY}\n")
  endforeach()

  set(COPY_SCRIPT_CONTENT "")
  string(APPEND COPY_SCRIPT_CONTENT
    "set(dependency_files \n${DEPENDENCY_FILES})\n\n"
    "list(REMOVE_DUPLICATES dependency_files)\n\n"
    "foreach(file IN ITEMS \${dependency_files})\n"
    "  if(EXISTS \"\${file}\")\n    "
        "execute_process(COMMAND \${CMAKE_COMMAND} -E copy_if_different "
        "\"\${file}\" \"$<TARGET_FILE_DIR:${target}>/\")\n"
    "  endif()\n"
  )
  string(APPEND COPY_SCRIPT_CONTENT "endforeach()\n")

  # Finally generate one script for each configuration supported by this generator
  message(STATUS "Populating copy rules for target: ${target}")
  file(GENERATE
    OUTPUT "${COPY_SCRIPT}"
    CONTENT "${COPY_SCRIPT_CONTENT}"
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
    set(COPY_SCRIPT "${CMAKE_BINARY_DIR}/rocbuild_copy_opencv_videoio_plugin_dlls_${target}_$<CONFIG>.cmake")
  else()
    set(COPY_SCRIPT "${CMAKE_BINARY_DIR}/rocbuild_copy_opencv_videoio_plugin_dlls_${target}.cmake")
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


function(rocbuild_hide_symbols TARGET)
  get_target_property(TARGET_TYPE ${TARGET} TYPE)
  if(TARGET_TYPE STREQUAL "SHARED_LIBRARY")  
    if((CMAKE_C_COMPILER_ID MATCHES "GNU|Clang") OR
       (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang"))
      target_compile_options(${TARGET} PRIVATE "-fvisibility=hidden")
    endif()
  endif()
endfunction()


function(rocbuild_link_as_needed TARGET)
  get_target_property(TARGET_TYPE ${TARGET} TYPE)
  if(TARGET_TYPE STREQUAL "SHARED_LIBRARY")  
    if((CMAKE_C_COMPILER_ID MATCHES "^(GNU|Clang)$") OR
       (CMAKE_CXX_COMPILER_ID MATCHES "^(GNU|Clang)$"))
      target_link_options(${TARGET} PRIVATE "LINKER:-as-needed")
    elseif((CMAKE_C_COMPILER_ID STREQUAL "AppleClang") OR
           (CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang"))
      target_link_options(${TARGET} PRIVATE "LINKER:-dead_strip_dylibs")
    endif()
  endif()
endfunction()


function(rocbuild_remove_unused_data_and_function TARGET)
  if(CMAKE_BUILD_TYPE STREQUAL "Release" OR "$<CONFIG:Release>")
    if((CMAKE_C_COMPILER_ID MATCHES "^(GNU|Clang)$") OR
       (CMAKE_CXX_COMPILER_ID MATCHES "^(GNU|Clang)$"))
      target_compile_options(${TARGET} PRIVATE "-fdata-sections" "-ffunction-sections")
      target_link_options(${TARGET} PRIVATE "LINKER:--gc-sections")
    elseif((CMAKE_C_COMPILER_ID STREQUAL "AppleClang") OR
           (CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang"))
      target_compile_options(${TARGET} PRIVATE "-fdata-sections" "-ffunction-sections")
      target_link_options(${TARGET} PRIVATE "LINKER:-dead_strip")
    endif()
  endif()
endfunction()


function(rocbuild_print_args)
  message(STATUS "ROCBUILD/I: CMake version: ${CMAKE_VERSION}")
  message(STATUS "ROCBUILD/I: ROCBUILD_PLATFORM: ${ROCBUILD_PLATFORM}")
  message(STATUS "ROCBUILD/I: ROCBUILD_ARCH: ${ROCBUILD_ARCH}")
endfunction()


function(rocbuild_is_asan_available OUTPUT_VARIABLE)
  if((CMAKE_C_COMPILER_ID MATCHES "GNU|Clang") OR (CMAKE_CXX_COMPILER_ID STREQUAL "GNU|Clang"))
    set(${OUTPUT_VARIABLE} TRUE PARENT_SCOPE)
  elseif(MSVC)
    if(CMAKE_C_COMPILER_VERSION STRLESS 16.7 OR CMAKE_CXX_COMPILER_VERSION STRLESS 16.7)
      set(${OUTPUT_VARIABLE} FALSE PARENT_SCOPE)
      message(WARNING "ASAN is available since VS2019 16.7, but you are using ${CMAKE_C_COMPILER_VERSION}")
    else()
      set(${OUTPUT_VARIABLE} TRUE PARENT_SCOPE)
    endif()
  else()
    set(${OUTPUT_VARIABLE} FALSE PARENT_SCOPE)
  endif()
endfunction()


function(rocbuild_enable_asan TARGET)
  rocbuild_is_asan_available(ASAN_AVAILABLE)
  if(NOT ASAN_AVAILABLE)
    message(WARNING "ASAN is not available for the current compiler")
    return()
  endif()

  # Retrieve all target dependencies
  rocbuild_get_target_dependencies(TARGETS_TO_PROCESS ${TARGET})

  if(MSVC)
    set(ASAN_COMPILE_OPTIONS /fsanitize=address)
    set(ASAN_LINK_OPTIONS /ignore:4300) # /INCREMENTAL
  else()
    set(ASAN_COMPILE_OPTIONS -fsanitize=address -fno-omit-frame-pointer -g)
    set(ASAN_LINK_OPTIONS -fsanitize=address)
  endif()  

  # Add TARGET itself to the list of targets to process
  list(APPEND TARGETS_TO_PROCESS ${TARGET})

  foreach(DEPENDENCY IN LISTS TARGETS_TO_PROCESS)
    # Skip imported targets
    get_target_property(IMPORTED ${DEPENDENCY} IMPORTED)
    if(IMPORTED)
      continue()
    endif()

    get_target_property(TYPE ${DEPENDENCY} TYPE)
    if(TYPE STREQUAL "INTERFACE_LIBRARY")
      target_compile_options(${DEPENDENCY} INTERFACE ${ASAN_COMPILE_OPTIONS})
      target_link_options(${DEPENDENCY} INTERFACE ${ASAN_LINK_OPTIONS})
    else()
      target_compile_options(${DEPENDENCY} PUBLIC ${ASAN_COMPILE_OPTIONS})
      target_link_options(${DEPENDENCY} PUBLIC ${ASAN_LINK_OPTIONS})
    endif()
  endforeach()
endfunction()


# Should be called after rocbuild_enable_asan()
function(rocbuild_set_vs_debugger_environment TARGET)
  # Skip non-Visual Studio generators
  if(NOT CMAKE_GENERATOR MATCHES "Visual Studio")
    return()
  endif()

  # Skip non-executable targets
  get_target_property(TARGET_TYPE ${TARGET} TYPE)
  if(NOT TARGET_TYPE STREQUAL "EXECUTABLE")
    return()
  endif()
  
  set(EXTRA_PATHS)
  set(EXTRA_VARS) 
  if(CMAKE_C_COMPILER_ID STREQUAL "MSVC" OR CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    # Check if TARGET is with ASAN enabled
    get_target_property(TARGET_COMPILE_OPTIONS ${TARGET} COMPILE_OPTIONS)
    if(TARGET_COMPILE_OPTIONS MATCHES "/fsanitize=address")
      # https://devblogs.microsoft.com/cppblog/msvc-address-sanitizer-one-dll-for-all-runtime-configurations/
      if((CMAKE_C_COMPILER_VERSION STRGREATER_EQUAL 17.7) OR (CMAKE_CXX_COMPILER_ID STRGREATER_EQUAL 17.7))
        if(CMAKE_GENERATOR_PLATFORM MATCHES "x64")
          list(APPEND EXTRA_PATHS "$(VC_ExecutablePath_x64)")
          list(APPEND EXTRA_VARS "ASAN_SYMBOLIZER_PATH=$(VC_ExecutablePath_x64)")
        elseif(CMAKE_GENERATOR_PLATFORM MATCHES "Win32")
          list(APPEND EXTRA_PATHS "$(VC_ExecutablePath_x86)")
          list(APPEND EXTRA_VARS "ASAN_SYMBOLIZER_PATH=$(VC_ExecutablePath_x86)")
        endif()
      endif()
    endif()
  endif()

  # Retrieve all target dependencies
  rocbuild_get_target_dependencies(TARGET_DEPENDENCIES ${TARGET})
  foreach(DEPENDENCY IN LISTS TARGET_DEPENDENCIES)
    get_target_property(TYPE ${DEPENDENCY} TYPE)
    if(TYPE STREQUAL "SHARED_LIBRARY")
      set(DLL_DIRECTORY $<TARGET_FILE_DIR:${DEPENDENCY}>)
      list(APPEND EXTRA_PATHS ${DLL_DIRECTORY})
    endif()
  endforeach()

  set(VS_DEBUGGER_ENVIRONMENT "PATH=${EXTRA_PATHS};%PATH%")
  if(EXTRA_VARS)
    string(APPEND VS_DEBUGGER_ENVIRONMENT "\n")
    string(APPEND VS_DEBUGGER_ENVIRONMENT "${EXTRA_VARS}")
  endif()
  
  set_target_properties(${TARGET} PROPERTIES VS_DEBUGGER_ENVIRONMENT "${VS_DEBUGGER_ENVIRONMENT}")
endfunction()


macro(rocbuild_import_package RECIPE)
  # Parse attributes from recipe
  string(REGEX MATCH "^([^/]+)/(.+)$" _ "${RECIPE}")
  set(pkg_name ${CMAKE_MATCH_1})
  set(pkg_version ${CMAKE_MATCH_2})

  message(STATUS "[debug] package name: ${pkg_name}")
  message(STATUS "[debug] package version: ${pkg_version}")

  set(pkg_dir ".rocpkg/${pkg_name}-${pkg_version}")
  if(NOT EXISTS ${pkg_dir})
    message(FATAL_ERROR "${pkg_dir} not exist. \nPlease run: python rocpkg.py install ${RECIPE}")
  endif()

  add_library(${pkg_name} INTERFACE)
  target_include_directories(${pkg_name}
    INTERFACE
      ${pkg_dir}
  )
  set_target_properties(${pkg_name} PROPERTIES
    VERSION ${pkg_version}
    INTERFACE_${pkg_name}_VERSION "${pkg_version}"
  )

  # cleanup
  unset(pkg_name)
  unset(pkg_version)
  unset(pkg_dir)
endmacro()


rocbuild_print_args()
include(${CMAKE_CURRENT_LIST_DIR}/basic.cmake)
rocbuild_enable_ninja_colorful_output()