cmake_minimum_required(VERSION 3.10)
project(test_hide_symbols)

include(../../rocbuild.cmake)

add_library(bar SHARED 
  ../src/bar.h
  ../src/bar.c
  ../src/bar_internal.h
  ../src/bar_internal.c
)
target_include_directories(bar PRIVATE ../src)
target_compile_definitions(bar PRIVATE BAR_EXPORTS)

if(HIDDEN)
  rocbuild_hide_symbols(bar)
endif()
