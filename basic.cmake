cmake_minimum_required(VERSION 3.10)

include_guard()

# Set default installation directory
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
  set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}/install" CACHE PATH "" FORCE)
endif()

# Generate libfoo_d.lib when CMAKE_BUILD_TYPE is Debug
set(CMAKE_DEBUG_POSTFIX "_d")

# Enable fPIC
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

################################################################################
# Generate lib(.a/.lib/.so/.dll/...) and executable files in the same directory
################################################################################
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

################################################################################
# Source files with utf-8 encoding. Solves Visual Studio warning C4819
################################################################################
add_compile_options(
  "$<$<COMPILE_LANG_AND_ID:C,MSVC>:/source-charset:utf-8>"
  "$<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/source-charset:utf-8>"
)

# RPATH
if(NOT CMAKE_INSTALL_RPATH)
  set(CMAKE_INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib")
endif()
if(CMAKE_CROSSCOMPILING)
  set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)
endif()

function(rocbuild_set_install_runtime_path target)
  if(NOT TARGET ${target})
    message(FATAL_ERROR "Target ${target} does not exist.")
  endif()

  # skip windows
  if(WIN32)
    message(WARNING "Windows does not use rpath, skipping setting runtime path for target ${target}.")
    return()
  endif()

  # skip imported targets
  get_target_property(is_imported ${target} IMPORTED)
  if(is_imported)
    message(WARNING "Target ${target} is imported, cannot set runtime path.")
    return()
  endif()

  # get target type
  get_target_property(target_type ${target} TYPE)
  if(NOT (target_type MATCHES "^(SHARED_LIBRARY|EXECUTABLE)$"))
    message(WARNING "Target ${target} is not a shared library or executable, cannot set runtime path.")
    return()
  endif()

  if(APPLE)
    if(target_type STREQUAL "SHARED_LIBRARY")
      set_target_properties(${target} PROPERTIES
        INSTALL_RPATH "@loader_path"
      )
    elseif(target_type STREQUAL "EXECUTABLE")
      set_target_properties(${target} PROPERTIES
        INSTALL_RPATH "@executable_path/../Frameworks;@loader_path/../lib"
      )
    endif()
  elseif(ANDROID)
    # https://gitlab.kitware.com/cmake/cmake/-/issues/23670
    # cmake assumes android-ndk does not support RPATH, but it actually does, so we set it manually here
    target_link_options(${target} PRIVATE
      "-Wl,-rpath,\$ORIGIN:\$ORIGIN/../lib"
    )
  elseif(UNIX) # Linux
    if(target_type STREQUAL "SHARED_LIBRARY")
      target_link_options(${target} PRIVATE
        "-Wl,--enable-new-dtags"     # generate DT_RUNPATH
        # "-Wl,--disable-new-dtags"  # generate DT_RPATH (not recommended)
        "-Wl,-rpath,$ORIGIN"
      )
    elseif(target_type STREQUAL "EXECUTABLE")
      target_link_options(${target} PRIVATE
        "-Wl,--enable-new-dtags"     # generate DT_RUNPATH
        # "-Wl,--disable-new-dtags"  # generate DT_RPATH (not recommended)
        "-Wl,-rpath,$ORIGIN/../lib"
      )
    endif()
  endif()

endfunction()
