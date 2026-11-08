cmake_minimum_required(VERSION 3.15)
project(build_eigen)

include(../../basic.cmake)

include(FetchContent)
FetchContent_Declare(
  eigen
  #GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
  GIT_REPOSITORY /Users/zz/gitlab/eigen
  GIT_TAG 3.4.0
)
FetchContent_MakeAvailable(eigen)