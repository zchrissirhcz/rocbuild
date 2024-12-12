cmake_minimum_required(VERSION 3.10)
project(test_asan)

include(../../rocbuild.cmake)

add_executable(basic-global-overflow basic-global-overflow.cpp)
rocbuild_enable_asan(basic-global-overflow)

add_library(matrix INTERFACE matrix.hpp)
add_executable(test_matrix test_matrix.cpp)
target_link_libraries(test_matrix PRIVATE matrix)
rocbuild_enable_asan(matrix)