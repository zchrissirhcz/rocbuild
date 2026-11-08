cmake_minimum_required(VERSION 3.20)
project(build_cereal)

include(../../basic.cmake)

include(FetchContent)
FetchContent_Declare(
  cereal
  # GIT_REPOSITORY https://github.com/USCiLab/cereal.git
  GIT_REPOSITORY /Users/zz/github/cereal
  GIT_TAG v1.3.2
)

set(WITH_WERROR OFF)
set(BUILD_SANDBOX ON)
set(SKIP_PERFORMANCE_COMPARISON ON)
FetchContent_MakeAvailable(cereal)