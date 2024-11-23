cmake_minimum_required(VERSION 3.10)
project(test_postfix)

include(../../rocbuild.cmake)

add_library(foo STATIC ../src/foo.c)
rocbuild_set_debug_postfix(foo)

add_executable(hello ../src/hello.c)
rocbuild_set_debug_postfix(hello)