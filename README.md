# 编译相关小工具

本仓库收集编译、链接、诊断相关的小工具，包括 CMake 插件、Python 脚本、C 小工具和
PowerShell 环境脚本。除特别说明外，CMake 插件都可以单文件拷贝到项目里，通过
`include(...)` 使用。

## 工具索引

### CMake 基础与工程配置

| 工具 | 作用 |
| --- | --- |
| [basic.cmake](basic.cmake) | 安装目录、Debug 后缀、PIC、产物目录、RPATH 等基础默认值 |
| [rocbuild.cmake](rocbuild.cmake) | 常用 CMake 功能入口，自动包含 `basic.cmake` |
| [summary.cmake](summary.cmake) | 在 configure 结束时打印编译器、编译选项、target 等摘要 |
| [properties.cmake](properties.cmake) | 打印 target、directory、global 的 CMake 属性 |
| [source_group.cmake](source_group.cmake) | 在 Visual Studio / Xcode 中按目录显示源文件 |
| [debug_symbols.cmake](debug_symbols.cmake) | 为 MSVC / GCC / Clang 统一开启调试符号 |

### 编译检查与 Sanitizer

| 工具 | 作用 |
| --- | --- |
| [overlook/overlook.cmake](overlook/overlook.cmake) | 把 30+ 个严重编译警告当作错误 |
| [asan.cmake](asan.cmake) | AddressSanitizer |
| [tsan.cmake](tsan.cmake) | ThreadSanitizer |
| [hwasan.cmake](hwasan.cmake) | Android HWAddressSanitizer |
| [stack-usage.cmake](stack-usage.cmake) | GCC / Clang 生成 `.su` 栈使用报告 |
| [clang-tidy.cmake](clang-tidy.cmake) | 对指定 target 运行 clang-tidy |
| [cppcheck.cmake](cppcheck.cmake) | 对指定 target 运行 cppcheck |

### MSVC / Windows 兼容

| 工具 | 作用 |
| --- | --- |
| [msvc_static_crt.cmake](msvc_static_crt.cmake) | 静态链接 CRT（`/MT`、`/MTd`） |
| [msvc_dynamic_crt.cmake](msvc_dynamic_crt.cmake) | 动态链接 CRT（`/MD`、`/MDd`） |
| [msvc_EHsc.cmake](msvc_EHsc.cmake) | 添加 `/EHsc` 异常处理选项 |
| [msvc_exception_fh3.cmake](msvc_exception_fh3.cmake) | 使用 FH3 异常帧，兼容旧版 VS 链接 |
| [msvc_disable_constexpr_mutex_constructor.cmake](msvc_disable_constexpr_mutex_constructor.cmake) | 规避 `std::mutex` 相关运行时崩溃 |
| [msvc_parallel_build.cmake](msvc_parallel_build.cmake) | 用 `/MP` 并行编译 |
| [msvc_unicode.cmake](msvc_unicode.cmake) | 定义 `UNICODE` / `_UNICODE` |
| [msvc_M_PI.cmake](msvc_M_PI.cmake) | 定义 `_USE_MATH_DEFINES`，使用 `M_PI` |
| [msvc_enlarge_stack_size.cmake](msvc_enlarge_stack_size.cmake) | 设置 MSVC 线程栈大小的示例 |
| [msvc_ignore_fopen_warning.cmake](msvc_ignore_fopen_warning.cmake) | 屏蔽 `fopen` 的 C4996 警告 |
| [msvc_ignore_no_pdb_warning.cmake](msvc_ignore_no_pdb_warning.cmake) | 屏蔽链接警告 LNK4099 |
| [msvc_ignore_stdext_arr_iters_warning.cmake](msvc_ignore_stdext_arr_iters_warning.cmake) | 屏蔽 STL4043 / C4996 警告 |
| [msvc_execution_encoding.cmake](msvc_execution_encoding.cmake) | 在 CP936 系统上设置 `/execution-charset:gbk` |
| [windows_source_encoding.cmake](windows_source_encoding.cmake) | 在 CP936 系统上统一 MSVC / MinGW 源码和执行字符集 |

### 链接、产物与兼容性

| 工具 | 作用 |
| --- | --- |
| [copy_dll.cmake](copy_dll.cmake) | 把 target 依赖的 DLL 拷贝到可执行文件目录 |
| [no_exception.cmake](no_exception.cmake) | 关闭 C++ 异常 |
| [no_rtti.cmake](no_rtti.cmake) | 关闭 C++ RTTI |
| [rename_eigen_symbol_example.cmake](rename_eigen_symbol_example.cmake) | 重命名 Eigen 符号，避免符号冲突的示例 |
| [check_glibc_version.cmake](check_glibc_version.cmake) | 检查系统 glibc 版本 |

### Python 工具

| 工具 | 作用 |
| --- | --- |
| [juicy/juicy.py](juicy/juicy.py) | 简化 CMake configure / build，支持 VS、Linux、Android、QNX、MinGW |
| [dll_deps.py](dll_deps.py) | 类似 `ldd`，列出 PE 文件依赖的 DLL 及路径 |
| [dll_info.py](dll_info.py) | 查看 DLL 版本、VS 版本、Debug/Release 和导出符号 |
| [QueryCodePage.py](QueryCodePage.py) | 查询 Windows 当前 ANSI 代码页（ACP） |
| [test.py](test.py) | 运行 `tests/` 下的 CMake 集成测试 |

### C 与 PowerShell 工具

| 工具 | 作用 |
| --- | --- |
| [vslocate.c](vslocate.c) | 极简定位 Visual Studio 安装路径 |
| [pdbdump.c](pdbdump.c) | 从 `.pdb` / `.exe` 导出符号 |
| [vs.env.ps1](vs.env.ps1) | 在 PowerShell 中加载 Visual Studio 编译环境 |
| [vslocator](https://github.com/zchrissirhcz/vslocator)（独立仓库） | 和 `vswhere.exe` 输出一致的 Python 实现 |

## CMake 基础配置

### basic.cmake

为工程设置一组常用默认值：

- 默认安装目录为 `${CMAKE_BINARY_DIR}/install`
- Debug 产物加 `_d` 后缀
- 打开 `CMAKE_POSITION_INDEPENDENT_CODE`
- 可执行文件、静态库、动态库都输出到构建目录根部
- MSVC 下使用 `/source-charset:utf-8`
- 设置 Linux / macOS / Android 的 RPATH

```cmake
include(basic.cmake)
```

需要为单个 target 设置安装后的运行路径时，使用：

```cmake
rocbuild_set_install_runtime_path(hello)
```

该函数会根据平台设置 `INSTALL_RPATH`，或在 Android 下手动传入 `-Wl,-rpath`。

### rocbuild.cmake

`rocbuild.cmake` 是常用功能的统一入口，会自动包含 `basic.cmake`，并默认打开 Ninja
彩色输出：

```cmake
include(rocbuild.cmake)
```

提供的函数：

| 函数 | 作用 |
| --- | --- |
| `rocbuild_enable_ninja_colorful_output()` | 让 Ninja 下的 GCC / Clang 诊断信息带颜色 |
| `rocbuild_hide_symbols(<target>)` | 对共享库设置 `-fvisibility=hidden` |
| `rocbuild_link_as_needed(<target>)` | Linux 使用 `--as-needed`，macOS 使用 `-dead_strip_dylibs` |
| `rocbuild_remove_unused_data_and_function(<target>)` | Release 下用 section + gc 去掉未使用代码和数据 |
| `rocbuild_enable_asan(<target>)` | 对 target 及其依赖递归开启 ASan |
| `rocbuild_set_vs_debugger_environment(<target>)` | 配置 VS 调试器的 `PATH` / ASan 符号化路径 |

### summary.cmake

在根 `CMakeLists.txt` 最后一行包含，configure 结束时会打印 CMake、编译器、编译选项、
链接选项、target 列表等摘要：

```cmake
include(summary.cmake)
```

### properties.cmake

用于排查 CMake 属性：

```cmake
include(properties.cmake)

print_target_properties(opencv_core)
print_directory_properties(.)
print_global_properties()
```

### source_group.cmake

按源文件相对路径在 Visual Studio / Xcode 中建立目录结构：

```cmake
include(source_group.cmake)
assign_source_group(${SOURCES})
```

同时提供 `overlook_add_executable()`、`overlook_add_library()` 等包装函数，在创建
target 时自动调用 `assign_source_group()`。

### debug_symbols.cmake

为 MSVC 添加 `/Zi`，为 GCC / Clang 添加 `-g`，Clang 还会添加
`-fstandalone-debug`：

```cmake
include(debug_symbols.cmake)
```

## 编译检查与 Sanitizer

### overlook

[overlook.cmake](overlook/overlook.cmake) 把 30+ 个严重编译 warning 当作 error，
让 C/C++ 编译器更早报错。全局启用：

```cmake
include(overlook.cmake)
```

也可以只在 target 或文件级别启用，具体见 [overlook/README.md](overlook/README.md)。

### asan.cmake

在 `CMakeLists.txt` 中一句话启用 AddressSanitizer：

```cmake
include(asan.cmake)
```

MSVC 下要求 VS2019 16.7 及以上，并安装 “C++ AddressSanitizer” 组件。可选变量：

- `VS2022_ASAN_DISABLE_VECTOR_ANNOTATION`（默认 `ON`）
- `VS2022_ASAN_DISABLE_STRING_ANNOTATION`（默认 `ON`）
- `COPY_ASAN_DLLS`（默认 `OFF`）

### tsan.cmake

在 `CMakeLists.txt` 中一句话启用 ThreadSanitizer：

```cmake
include(tsan.cmake)
```

目前对 GCC / Clang / AppleClang 生效。

### hwasan.cmake

Android HWAddressSanitizer，要求：

- Android NDK r21 及以上
- `ANDROID_NATIVE_API_LEVEL >= 29`
- `ANDROID_ABI=arm64-v8a`

```cmake
include(hwasan.cmake)
```

### stack-usage.cmake

GCC / Clang 下为每个 `.c` / `.cpp` 文件生成 `.su` 文件，列出函数和变量的栈内存开销，
排查栈溢出时很有用：

```cmake
include(stack-usage.cmake)
```

```bash
$ gcc get_stack_size.c -fstack-usage
$ cat get_stack_size.su
get_stack_size.c:6:f	1104	static
get_stack_size.c:13:main	32	static
```

### clang-tidy.cmake

对指定 target 的源文件运行 clang-tidy，并支持忽略部分文件：

```cmake
include(clang-tidy.cmake)

# VS2022 自带 clang-tidy
rocbuild_apply_clang_tidy("C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/Llvm/x64/bin/clang-tidy.exe" main)

# Ubuntu
rocbuild_apply_clang_tidy(clang-tidy-18 main)

# 忽略第三方目录
rocbuild_apply_clang_tidy(clang-tidy-18 main IGNORED_FILES third_party/.*)
```

### cppcheck.cmake

对指定 target 运行 cppcheck（需要 `cppcheck` 在 `PATH` 中）：

```cmake
include(cppcheck.cmake)
apply_cppcheck(hello)
```

## MSVC / Windows 兼容

这些插件一般直接 include 即可：

```cmake
include(msvc_static_crt.cmake) # 或 msvc_dynamic_crt.cmake，二者选其一
include(msvc_EHsc.cmake)
include(msvc_unicode.cmake)
include(msvc_M_PI.cmake)
include(msvc_parallel_build.cmake)
```

各文件说明：

- `msvc_static_crt.cmake` / `msvc_dynamic_crt.cmake`：分别使用 `/MT`、`/MTd` 和
  `/MD`、`/MDd`。两者不要同时包含。
- `msvc_EHsc.cmake`：添加 `/EHsc`。
- `msvc_exception_fh3.cmake`：当使用 VS2019 16.3+ / VS2022 编译的库需要被
  VS2017/VS2015 链接时，用 `/d2FH4-` 关闭 FH4，避免 `__CxxFrameHandler4` 链接错误。
  由 `USE_COMPATIBLE_FRAME_HANDLER_FOR_VS` 控制，默认 `ON`。
- `msvc_disable_constexpr_mutex_constructor.cmake`：检测 `msvcp140.dll` 版本并定义
  `_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR`，规避 VS2022 17.10+ 下 `std::mutex`
  相关的启动崩溃。
- `msvc_parallel_build.cmake`：给 MSVC 添加 `/Gm-` 和 `/MP<逻辑核心数/2>`，让
  MSBuild 也能并行编译。
- `msvc_unicode.cmake`：定义 `UNICODE` 和 `_UNICODE`。
- `msvc_M_PI.cmake`：定义 `_USE_MATH_DEFINES`，避免每个源文件手写。
- `msvc_enlarge_stack_size.cmake`：示例文件，把里面的 `your_target` 替换为实际 target
  后 include；当前示例设置为 10 MB 栈。
- `msvc_ignore_fopen_warning.cmake`：定义 `_CRT_SECURE_NO_WARNINGS`。
- `msvc_ignore_no_pdb_warning.cmake`：给链接器添加 `/ignore:4099`。
- `msvc_ignore_stdext_arr_iters_warning.cmake`：定义
  `_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING`。
- `msvc_execution_encoding.cmake`：当 Windows ACP 为 936 时，给 MSVC 添加
  `/execution-charset:gbk`。
- `windows_source_encoding.cmake`：当 Windows ACP 为 936 时，MSVC 使用
  `/source-charset:utf-8`，MinGW 使用 `-finput-charset=UTF-8 -fexec-charset=GBK`。
  适合源码为 UTF-8、控制台/执行字符集为 GBK 的项目。

## 链接、产物与兼容性

### copy_dll.cmake

遍历 target 的所有依赖，把对应的 DLL 拷贝到可执行文件所在目录，方便命令行运行：

```cmake
include(copy_dll.cmake)
rocbuild_copy_dlls(hello)
```

只在 Windows 非交叉编译时生效；需要在所有依赖 target 都定义之后调用。

### no_exception.cmake / no_rtti.cmake

分别关闭 C++ 异常和 RTTI：

```cmake
include(no_exception.cmake)
include(no_rtti.cmake)
```

### rename_eigen_symbol_example.cmake

演示如何通过编译期宏定义重命名 Eigen 符号，避免多个库依赖不同版本/不同编译选项的
Eigen 时发生符号冲突：

```cmake
target_compile_definitions(foo PRIVATE Eigen=fooEigen)
```

完整示例见 [rename_eigen_symbol_example.cmake](rename_eigen_symbol_example.cmake)。

### check_glibc_version.cmake

检查系统上安装的 glibc 版本：

```cmake
include(check_glibc_version.cmake)

CHECK_GLIBC_VERSION(FOUND_GLIBC GLIBC_VERSION)
if(FOUND_GLIBC)
  message(STATUS "glibc version: ${GLIBC_VERSION}")
endif()
```

## Python 工具

### juicy.py

[juicy.py](juicy/juicy.py) 让 CMake 的 configure 和 build 更简单：不用记完整的 VS
generator 名，不用为交叉编译手写 toolchain，也不用手动进入 VS 开发者环境。

```powershell
# Windows：自动选择最新 Visual Studio
python juicy.py -S . -B build

# Linux/WSL native
python juicy.py -p linux -a x64 -S . -B build

# Visual Studio + Ninja
python juicy.py -p vs2022 -G Ninja -S . -B build

# 交叉编译
python juicy.py -p android -a armv8-a -r C:\soft\toolchains\android-ndk\r27c -S . -B build
python juicy.py -p qnx -a aarch64 -r C:\soft\toolchains\qnx800 -S . -B build-qnx
python juicy.py -p mingw -a x86_64 -r C:\soft\toolchains\MinGW -S . -B build-mingw

# 构建
python juicy.py build -B build
python juicy.py build -B build -j 8 --target hello
```

支持的平台、参数和测试方式见 [juicy/README.md](juicy/README.md)。需要 Python 3 和
CMake；使用 Ninja 时还需要 `ninja` 在 `PATH` 中。`juicy/` 目录还包含示例
`hello.c`、`build.cmd`、测试 `test_juicy.py` 和 juicy 自用的 `toolchains/`。

### dll_deps.py

列出 `.dll` / `.exe` 文件的依赖文件，格式类似 Linux 下的 `ldd`。依赖 `pefile`：

```powershell
python -m pip install pefile
python .\dll_deps.py C:\Windows\System32\opencl.dll
```

输出示例：

```
        ADVAPI32.dll => c:\windows\system32\ADVAPI32.dll
        CFGMGR32.dll => c:\windows\system32\CFGMGR32.dll
        ole32.dll => c:\windows\system32\ole32.dll
        KERNEL32.dll => c:\windows\system32\KERNEL32.dll
```

### dll_info.py

检查 DLL 的版本号、Visual Studio 版本、Debug/Release 和导出符号。单文件，内置测试；
依赖 `pefile`：

```powershell
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

```powershell
python .\dll_info.py --test
```

### QueryCodePage.py

查询 Windows 当前 ANSI 代码页（ACP），主要用于 CMake 3.24 以下的编码配置场景：

```powershell
python .\QueryCodePage.py
```

### test.py

运行 `tests/` 下的 CMake 集成测试，会在 `build/` 下生成临时工程并在测试结束后清理：

```powershell
python .\test.py
```

## C 与 PowerShell 工具

### vslocate.c

来自 https://github.com/mjansson/vslocate 的工具，极简定位 Visual Studio 安装路径。
编译：

```cmd
cl /O1 /Os /Gm- /GF- /sdl /MT /GS /D COMPILE_TOOL=1 vslocate.c /link /out:vslocate.exe
```

运行后输出已安装 Visual Studio 的版本号和安装路径。

### pdbdump.c

从 `.pdb` 和可执行文件中导出符号（public domain，来源见文件头）。编译：

```cmd
cl /Ox /Zi pdbdump.c
```

常用示例：

```cmd
pdbdump.exe a.pdb b.dll
pdbdump.exe -csv a.pdb | findstr SymTagFunction
pdbdump.exe -wis_enab* a.pdb
echo 0x401000 is_enabled | pdbdump.exe -r a.pdb
```

需要 Windows SDK 和 `dbghelp.lib`。

### vs.env.ps1

拷贝到 `~/.vs.env.ps1` 位置。PowerShell 中一句话启用 Visual Studio 编译环境：

```powershell
. ~/.vs.env.ps1
cl hello.c
```

需要先安装 vswhere 和 Visual Studio。解决了“不知道 `vcvarsall.bat` 在哪、有太多 VS
版本容易选错”的问题。

### vslocator（独立仓库）

https://github.com/zchrissirhcz/vslocator

和微软官方 `vswhere.exe` 输出完全一致的 Python 实现。

## 目录与示例

### pkg 目录

`pkg/recipes` 在 `CMakeLists.txt` 中使用 `FetchContent_Declare` 引入开源依赖，便于执行
和安装，目前包含：

- `cereal`（v1.3.2）
- `cJSON`（v1.7.18）
- `eigen`（3.4.0）
- `googletest`（v1.17.0）

注意：recipe 里的 `GIT_REPOSITORY` 目前指向作者本地路径，使用前改成远端地址或自己的
本地路径。

`pkg/use_recipes` 是使用上述 recipes 的示例，目前包含 `cJSON` 和 `gtest`。

### toolchains 目录

存放 CMake 工具链（适配）文件，用于交叉编译或自定义编译环境：

- `gcc-aarch64-none-linux-gnu.cmake`
- `gcc-arm-none-eabi.cmake`
- `qnx-aarch64.cmake`
- `vs2015-x64.cmake`
- `vs2022-arm64.cmake`
- `vs2022-x64.cmake`
- `toolchain-checker.cmake`：检查 `CMAKE_SYSTEM_NAME`、`CMAKE_SYSTEM_PROCESSOR`、
  编译器和 `CMAKE_SYSROOT`，并打印工具链摘要。

### examples 目录

一组可直接用 CMake 构建的示例工程，覆盖 `atomic`、`clang-tidy`、`exception`、
`gen_asm`、`hello`、`imported_no_soname`、`program`、`rtti`、`runtime_path`、
`thread`、`use_opencv` 等场景。

### tests 目录

配合 `test.py` 使用的集成测试工程，覆盖 `artifacts_path`、`asan`、`copy_dlls`、
`hide_symbols`、`link_as_needed`、`lldb_string`、`msvc_utf8_encoding`、
`unused_data_and_function` 等场景，公共源码放在 `src/`。
