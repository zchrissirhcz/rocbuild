cmake_minimum_required(VERSION 3.10)
project(test_artifacts_path)
include(../../rocbuild.cmake)
add_library(foo_static STATIC ../src/foo.c)
add_library(foo_shared SHARED ../src/foo.c)
add_executable(hello ../src/hello.c)

add_subdirectory(sub)