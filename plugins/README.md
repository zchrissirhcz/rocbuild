## asan.cmake

Enable Address Sanitizer globally in your CMake-based project, by download [asan.cmake](asan.cmake) and only add one line in CMakeLists.txt
```cmake
include(asan.cmake)
```

Support many compiler platforms:
- GCC/Linux/Android NDK
- VS2019
- VS2022

## tsan.cmake

Enable ThreadSanitizer globally in your CMake-based project, by download [tsan.cmake](tsan.cmake) and only add one line in CMakeLists.txt
```cmake
include(tsan.cmake)
```

## summary.cmake

Get a summary message for your current build, including global stuffs and list each target, by download [summary.cmake](summary.cmake) and only add one line in CMakeLists.txt
```cmake
include(summary.cmake)
```

## msvc_utf8_encoding.cmake

When you write unicode chars (e.g. Chinese characters) in utf-8 encoding source files (.c/.cpp/.h/.hpp), and your command prompt use encodings like `/cp936` (due to OS language), it prints garbage. You may avoid that by specify encoding for source files and execution, separately. 

Here is the tool you can use, just download [msvc_utf8_encoding.cmake](msvc_utf8_encoding.cmake) (and also [QueryCodePage.py](QueryCodePage.py) if your cmake < 3.24), and only add one line in CMakeLists.txt

```cmake
include(msvc_utf8_encoding.cmake)
```
