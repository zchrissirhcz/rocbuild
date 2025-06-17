cmake_minimum_required(VERSION 3.13)
project(RocBuildExamples)

include(../rocbuild.cmake)

add_subdirectory(use_opencv)
add_subdirectory(clang-tidy)