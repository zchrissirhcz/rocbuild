# 编译相关小工具

## overlook/overlook.cmake

视30+编译warning为error，让C/C++编译器报错更准确些。
CMakeLists.txt 中一句话启用 overlook 插件，include(overlook.cmake)

## asan.cmake

CMakeLists.txt 中一句话启用 asan (address sanitizer) 编译支持: include(asan.cmake)

## tsan.cmake

CMakeLists.txt 中一句话启用 tsan (thread sanitizer) 编译支持: include(tsan.cmake)

## vs.env.ps1

拷贝到 ~/.vs.env.ps1 位置。
powershell 中一句话启用 Visual Studio 编译环境:
```
. ~/.vs.env.ps1
cl hello.c
```

需要先安装 vswhere 和 visual studio。 解决了“不知道 vcvarsall.bat 在哪、 有太多的 vs 版本容易选错” 的问题。

## vslocate.c

来自 https://github.com/mjansson/vslocate 的工具, 极简定位 Visual Studio 安装路径。

```cmd
cl /O1 /Os /Gm- /GF- /sdl /MT /GS /D COMPILE_TOOL=1 vslocate.c /link /out:vslocate.exe
```

## vslocator（独立仓库）

https://github.com/zchrissirhcz/vslocator

和微软官方 vswhere.exe 完全一致输出的 Python 实现。

## dll_deps.py（原 dll_checker.py）

列出 .dll 文件的依赖文件，格式类似 Linux 下的 ldd 命令。

```
PS C:\work\rocbuild\plugins> python .\dll_deps.py c:\windows\system32\opencl.dll                                        
        ADVAPI32.dll => c:\windows\system32\ADVAPI32.dll
        CFGMGR32.dll => c:\windows\system32\CFGMGR32.dll
        ole32.dll => c:\windows\system32\ole32.dll
        KERNEL32.dll => c:\windows\system32\KERNEL32.dll
```

## dll_info.py

检查 DLL 的版本号、Visual Studio 版本、Debug/Release 和导出符号。单文件，内置测试；依赖 `pefile`：

```
python -m pip install pefile
python .\dll_info.py C:\Windows\System32\kernel32.dll
python .\dll_info.py --limit 20 C:\Windows\System32\user32.dll
python .\dll_info.py --json C:\Windows\System32\msvcp140.dll
```

输出示例：

```
File: C:\Windows\System32\kernel32.dll
  File version: 10.0.26100.9711 (WinBuild.160101.0800)
  Product version: 10.0.26100.9711
  Visual Studio: Visual Studio 2022 (MSVC 14.38, v143)
  Build mode: Release (no debug markers; a PDB alone is not proof of Debug)
  Exports: 1698
         1  AcquireSRWLockExclusive -> NTDLL.RtlAcquireSRWLockExclusive
```

说明：VS 大版本由 linker version 推断；Debug/Release 由 Debug CRT、RTC 字符串和
PDB 路径启发式判断；没有版本资源时显示 `(none)`；“符号”指 PE 导出表。

测试：

```
python .\dll_info.py --test
```


## copy_dll.cmake

遍历 target 的所有依赖，找到对应的 DLL 文件， 拷贝到可执行文件所在目录。

对于在命令行运行可执行程序，很有帮助。

## stack-usage.cmake

GCC/Clang编译器下，为每个 .c/.cpp 文件生成 .su 文件， 列出各函数、变量的栈内存开销。 在排查栈溢出(stack-overflow)问题时非常有用。

CMakeLists.txt 中一句话启用 stack-usage 插件，include(stack-usage.cmake)

```bash
$ gcc get_stack_size.c -fstack-usage
$ cat get_stack_size.su
get_stack_size.c:6:f	1104	static
get_stack_size.c:13:main	32	static
```

## check_glibc_version.cmake

检查系统上安装的 glibc 版本。

CMakeLists.txt 中一句话启用 check_glibc_version 插件，include(check_glibc_version.cmake)

## msvc_enlarge_stack_size.cmake

Visual Studio 编译器默认用 1MB 内存作为线程栈大小，相比Linux默认8MB更容易触发栈溢出(stack-overflow)问题。

msvc_enlarge_stack_size.cmake 给出了设置线程栈大小的示例。

## msvc_static_crt.cmake

Visual Studio 创建的 C/C++ 工程， 或基于 CMake 生成的 visual studio solution, 默认用 MD / MDd 作为运行时库 (C Runtime Library 动态链接)。

有时要编译 MT / MTd (C Runtime Library 静态链接)， 用法见 msvc_static_crt.cmake。

## msvc_ignore_fopen_warning.cmake

Visual Studio 编译器在使用 fopen 时产生警告:

> warning C4996: 'fopen': This function or variable may be unsafe. Consider using fopen_s instead

msvc_ignore_fopen_warning.cmake 提供了忽略该警告的方式。

## msvc_M_PI.cmake

Visual Studio 编译器下，使用数学常量 M_PI 需要定义 _USE_MATH_DEFINES 宏。

蹩脚的做法:
```c
#define _USE_MATH_DEFINES
#include <cmath>
```

更好方式，是在 CMakeLists.txt 中全局启用:

```cmake
include(msvc_M_PI.cmake)
```

## rename_eigen_symbol_example.cmake

描述如何重命名 Eigen 的符号，避免潜在的符号冲突。 例如多个库都依赖 Eigen、 Eigen 版本或编译选项不同， 造成同一符号出现多次， 链接器可能链接到非预期的那一份。

通过编译期宏定义，将 Eigen 相关符号重命名为其他名称，从而避免符号冲突。 namespace 也算符号的一部分。

## no_exception.cmake, no_rtti.cmake

关闭 C++ 异常和 RTTI 支持。

