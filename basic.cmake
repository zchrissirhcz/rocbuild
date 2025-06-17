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