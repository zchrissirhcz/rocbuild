cmake_minimum_required(VERSION 3.10)
project(test_copy_dlls)

include(../../rocbuild.cmake)

add_library(foo SHARED ../src/foo.c)
target_compile_definitions(foo PRIVATE FOO_EXPORTS)
target_include_directories(foo PUBLIC ../src)
set_target_properties(foo PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/foo)

add_library(bar SHARED ../src/bar.c ../src/bar_internal.c)
target_compile_definitions(bar PRIVATE BAR_EXPORTS)
target_include_directories(bar PUBLIC ../src)
set_target_properties(bar PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bar)

add_library(baz SHARED ../src/baz.c)
target_compile_definitions(baz PRIVATE BAZ_EXPORTS)
target_include_directories(baz PUBLIC ../src)
set_target_properties(baz PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/baz)
target_link_libraries(baz PRIVATE foo)

add_executable(test test.c)
target_link_libraries(test PRIVATE bar baz)
set_target_properties(test PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/test)

if(COPY_DLLS)
  rocbuild_copy_dlls(test)
endif()