cmake_minimum_required(VERSION 3.10)
project(test_postfix)

include(../../rocbuild.cmake)

add_library(foo STATIC ../src/foo.c)
rocbuild_define_package(foo)