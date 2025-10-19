cmake_minimum_required(VERSION 3.20)
project(thread)

add_executable(demo demo.cpp)

find_package(Threads REQUIRED)
target_link_libraries(demo PRIVATE Threads::Threads)
