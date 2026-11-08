cmake_minimum_required(VERSION 3.15)
project(use_gtest)

# GoogleTest requires at least C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(GTest_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../recipes/gtest/build/install/lib/cmake/GTest")
find_package(GTest REQUIRED)

enable_testing()

add_executable(
  hello_test
  hello_test.cc
)
target_link_libraries(
  hello_test
  GTest::gtest_main
)

include(GoogleTest)
gtest_discover_tests(hello_test)