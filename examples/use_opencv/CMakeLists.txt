set(OpenCV_DIR "C:/pkgs/opencv/4.10.0/x64/vc16/lib")
find_package(OpenCV REQUIRED)

add_executable(use_opencv use_opencv.cpp)
target_link_libraries(use_opencv PRIVATE opencv_videoio opencv_highgui opencv_imgcodecs opencv_core)

rocbuild_copy_dlls(use_opencv)
rocbuild_copy_opencv_videoio_plugin_dlls(use_opencv)