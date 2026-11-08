cmake_minimum_required(VERSION 3.15)
project(build_gtest)

include(../../basic.cmake)

include(FetchContent)
FetchContent_Declare(
  googletest
  #GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_REPOSITORY /Users/zz/github/googletest
  GIT_TAG v1.17.0
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)