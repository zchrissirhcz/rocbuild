cmake_minimum_required(VERSION 3.15)
project(test_artifacts_path)
include(../../rocbuild.cmake)

add_executable(test test.c)
if(REMOVE_UNUSED_DATA_AND_FUNCTION)
  rocbuild_remove_unused_data_and_function(test)
endif()
