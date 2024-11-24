# RocBuild

![Build Status](https://github.com/zchrissirhcz/rocbuild/actions/workflows/build.yml/badge.svg)

## rocsetup.cmake

[rocsetup.cmake](rocsetup.cmake) is a starter program for CMake configure step.

Usage:
```pwsh
cmake -P rocsetup.cmake -p vs2022 -a x64 -S . -B build
```

Will parse and then run:
```pwsh
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
```

## rocbuild.cmake

[rocbuild.cmake](rocbuild.cmake) is a set of functions/macros for daily building opeorations: 
- use `CMAKE_BINARY_DIR` as output location for artifacts: `.a/.lib/.dll/.so/.exe/...`
- copy dlls for recursive shared dependencies
- copy OpenCV's videoio plugin dlls
- enable Ninja colorful output by default
- set debug postfix for artifacts under Debug build type for multi-config generator
- hide symbols for shared library for gcc/clang/appleclang
- remove unused data/function for gcc/clang/appleclang
- more fuctionalities to be added...

Usage: add one line in your `CMakeLists.txt`:
```cmake
include(rocbuild.cmake)
```

## plugins

[plugins directory](plugins/README.md) provides a collection of standalone cmake plugins. 