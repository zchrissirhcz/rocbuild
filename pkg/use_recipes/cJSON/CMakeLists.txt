cmake_minimum_required(VERSION 3.15)
project(use_cJSON)

set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(cJSON_PKG_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../recipes/cJSON/build/install")

add_library(cJSON STATIC IMPORTED)
set_target_properties(cJSON PROPERTIES
  IMPORTED_LOCATION "${cJSON_PKG_DIR}/lib/libcjson.a"
  INTERFACE_INCLUDE_DIRECTORIES "${cJSON_PKG_DIR}/include"
)

add_executable(use_cjson main.cpp)
target_link_libraries(use_cjson cJSON)
