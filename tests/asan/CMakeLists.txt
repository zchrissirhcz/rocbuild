cmake_minimum_required(VERSION 3.10)
project(test_asan)

include(../../rocbuild.cmake)

add_executable(basic-global-overflow basic-global-overflow.cpp)
rocbuild_enable_asan(basic-global-overflow)

add_library(matrix INTERFACE matrix.hpp)
add_executable(test_matrix test_matrix.cpp)
target_link_libraries(test_matrix PRIVATE matrix)
rocbuild_enable_asan(matrix)

set(OpenCV_DIR "C:/pkgs/opencv/4.10.0/x64/vc16/lib")
find_package(OpenCV REQUIRED)
add_executable(use_opencv use_opencv.cpp)
target_link_libraries(use_opencv PRIVATE opencv_core)
rocbuild_copy_dlls(use_opencv)
rocbuild_enable_asan(use_opencv)