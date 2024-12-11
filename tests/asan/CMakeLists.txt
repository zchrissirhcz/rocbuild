cmake_minimum_required(VERSION 3.10)
project(asan)

include(../../rocbuild.cmake)

add_executable(test basic-global-overflow.cpp)

rocbuild_enable_asan(test)
