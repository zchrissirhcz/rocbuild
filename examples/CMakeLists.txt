cmake_minimum_required(VERSION 3.13)
project(RocBuildExamples)

include(../rocbuild.cmake)
include(../plugins/copy_dll.cmake)
include(../plugins/no_rtti.cmake)
include(../plugins/no_exception.cmake)

#add_subdirectory(use_opencv)
add_subdirectory(clang-tidy)
add_subdirectory(exception)
add_subdirectory(rtti)