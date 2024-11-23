cmake_minimum_required(VERSION 3.20)
project(hello)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_BUILD_TYPE Debug)
find_package(OpenCV REQUIRED)
include(../../debug_symbols.cmake)
add_executable(testbed main.cpp)
target_link_libraries(testbed ${OpenCV_LIBS})

