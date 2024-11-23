# RocBuild

<img alt="GitHub" src="https://img.shields.io/github/license/zchrissirhcz/RocBuild"> ![Ubuntu](https://img.shields.io/badge/Ubuntu-333333?style=flat&logo=ubuntu) ![Windows](https://img.shields.io/badge/Windows-333333?style=flat&logo=windows&logoColor=blue) ![macOS](https://img.shields.io/badge/-macOS-333333?style=flat&logo=apple) ![android](https://img.shields.io/badge/-Android-333333?style=flat&logo=Android) ![Build Status](https://github.com/zchrissirhcz/rocbuild/actions/workflows/build.yml/badge.svg)

A set of cmake plugins for C/C++ building.

## rocsetup.cmake

Ease your cmake configure setup. e.g.

```pwsh
cmake -P rocsetup.cmake -p vs2022 -a x64
```

Will parse and then run:
```pwsh
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
```

## rocbuild.cmake

Ease your cmake build experience, by add one line in your `CMakeLists.txt`:
```cmake
include(rocbuild.cmake)
```
