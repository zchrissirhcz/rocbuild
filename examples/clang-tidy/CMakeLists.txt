add_executable(point point.cpp)

include(${CMAKE_SOURCE_DIR}/../plugins/clang-tidy.cmake)
rocbuild_apply_clang_tidy("C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/Llvm/x64/bin/clang-tidy.exe" point)