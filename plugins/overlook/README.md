# Overlook

Overlook: a cmake plugin for safer c/c++ programming.

## Introduction

[overlook.cmake](overlook.cmake) collects 30+ warnings, mark them as errors, help you found bugs when compile C/C++ code.

## Usage

Download [overlook.cmake](https://github.com/zchrissirhcz/rocbuild/blob/main/overlook/overlook.cmake) and included it in `CMakeLists.txt`, enable its compile options at your required level:

### Case1: enable overlook globally

```cmake
include("overlook.cmake")
```

### Case2: enable overlook on target level

```cmake
set(OVERLOOK_GLOBAL OFF)
include("overlook.cmake")
add_library(hello STATIC hello.c)
target_link_libraries(hello PRIVATE overlook)
```

or:
```cmake
set(OVERLOOK_GLOBAL OFF)
include("overlook.cmake")
add_library(world STATIC world.cpp)
target_compile_options(world PRIVATE
  ${OVERLOOK_CXX_COMPILE_OPTIONS} # C++
  # ${OVERLOOK_C_COMPILE_OPTIONS} # C
)
```

### Case3: enable overlook on file level

```cmake
set(OVERLOOK_GLOBAL OFF)
include("overlook.cmake")
add_library(hello foo.c bar.cpp)
set_source_files_properties(foo.c PROPERTIES COMPILE_OPTIONS
  ${OVERLOOK_C_COMPILE_OPTIONS}
)
```

Then compile your projec as usual, it will report bugs more seriously thanks to overlook.

## Purpose

Good programmers should not ignore warnings. Treating all warnings as errors, however, is not practical due to reasons:
- time cost
- not own scratch project, too much to modify
- not affect result

Moreover, on the GCC/Clang common flags:
- `-Wall` does not mean `turn on all warnings`, missing flags like `-Wnon-virtual-dtor`
- `-Wpedantic` check more flags that `-Wall`, but still missing flags like `-Wnon-virtual-dtor`
- `-Weffc++` may cover more flags

Here comes the contradiction: which warnings should be considered carefully?

In [overlook.cmake](overlook.cmake), there are **36 serious compilation warnings' checking, treat corresponding C/C++ flags as error**, with corresponding unit tests (See [tests](tests)). Most are extracted from practical cross-platform projects, and does resolve severe bugs such as:
- Segmentation Faults(caused by address truncation)
- Memory leaks(caused by missing including header file)
- Trap(caused by missing return value)

These severe bugs can not be inspected by famous tools like AddressSanitizer, Valgrind, VLD, but [overlook.cmake](overlook.cmake) can. People may also use [clang-tidy](https://clang.llvm.org/extra/clang-tidy/), which will report more compile warnings (instead of compile errors).


## Advanced Usage

### Disable a specific warning

Compile your code with overlook.cmake applyed, see that error nessage's type/number, search it in overlook.cmake and comment it out via inserting `#`, such as:
```cmake
#if(OVERLOOK_ENABLE_RULE32)
#  if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
#    if(CMAKE_CXX_COMPILER_VERSION GREATER 7.5)
#      list(APPEND OVERLOOK_CXX_COMPILE_OPTIONS -Werror=class-memaccess)
#    endif()
#  endif()
#endif()
```

### Debugging

If you're using Overlook, but it seems not work, possible cases:

1. The overlook.cmake you are using is not the latest.
2. Overlook's rules are suppressed due to your `add_definitions(-w)`, which ignore all warnings thus overlook won't work.
3. Your compiler is not covered by Overlook. If so, feel free to create a Pull Request or open an issue.

## References

- https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
- https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html
