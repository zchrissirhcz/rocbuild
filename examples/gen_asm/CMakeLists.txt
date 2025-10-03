cmake_minimum_required(VERSION 3.20)
project(demo)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-save-temps=obj -fverbose-asm)
elseif(MSVC)
  add_compile_options(/FA)
endif()

add_executable(demo main.cpp)