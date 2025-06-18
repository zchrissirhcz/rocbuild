cmake_minimum_required(VERSION 3.15)
project(build_clinfo)

include(../../basic.cmake)

include(FetchContent)
FetchContent_Declare(
  clinfo
  #GIT_REPOSITORY https://github.com/Oblomov/clinfo.git
  GIT_REPOSITORY /Users/zz/work/github/clinfo
  GIT_TAG 3.0.25.02.14
)
FetchContent_MakeAvailable(clinfo)

message(STATUS "clinfo_SOURCE_DIR: ${clinfo_SOURCE_DIR}")

# build/_deps/clinfo-src
execute_process(
    COMMAND "make"
    WORKING_DIRECTORY ${clinfo_SOURCE_DIR}
    RESULT_VARIABLE result
    OUTPUT_VARIABLE output
)

message(STATUS "clinfo build result: ${result}")
message(STATUS "clinfo build output: ${output}")