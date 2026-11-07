
# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Create: 2026-11-07 12:30

# This script copy dependent dlls to directory where the executable lives.
#
# Usage:
# include(copy_dll.cmake)
# rocbuild_copy_dlls(<target>)

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