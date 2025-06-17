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