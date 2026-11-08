cmake_minimum_required(VERSION 3.15)
project(build_cJSON)

include(../../basic.cmake)

set(ENABLE_CJSON_TEST OFF)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build cJSON as a shared library" FORCE)
include(FetchContent)
FetchContent_Declare(
  cJSON
  #GIT_REPOSITORY https://github.com/DaveGamble/cJSON.git
  GIT_REPOSITORY /Users/zz/github/cJSON
  GIT_TAG v1.7.18
)
FetchContent_MakeAvailable(cJSON)