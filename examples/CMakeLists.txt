cmake_minimum_required(VERSION 3.13)
project(RocBuildExamples)

include(../rocbuild.cmake)
include(../plugins/copy_dll.cmake)

add_subdirectory(use_opencv)
add_subdirectory(clang-tidy)