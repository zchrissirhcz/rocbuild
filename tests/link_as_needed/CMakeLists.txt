cmake_minimum_required(VERSION 3.10)
project(test_link_as_needed)

include(../../rocbuild.cmake)

# For test purpose, we explicitly enable `--no-as-needed` for GNU and Clang as the default behavior.
if(CMAKE_C_COMPILER_ID MATCHES "^(GNU|Clang)$")
  add_link_options("LINKER:--no-as-needed")
endif()

add_library(foo_math SHARED
  foo_math.h
  foo_math.c
)
target_include_directories(foo_math PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(foo_math PRIVATE FOO_MATH_EXPORTS)

add_library(foo SHARED ../src/foo.c)
target_include_directories(foo PRIVATE ../src)

target_link_libraries(foo_math PRIVATE foo)

if(LINK_AS_NEEDED)
  rocbuild_link_as_needed(foo_math)
endif()
