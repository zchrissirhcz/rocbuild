# arche.ini 参考

`arche.ini` 是 `arche.py` 的构建描述文件。本文是完整规范：新增配置、修改实现或让 AI 按需求扩展时，以本文为准。

## 1. 文件位置与编码

- 默认读取当前目录的 `arche.ini`，可用 `-f` 指定其他文件；
- 一个工程一个 INI，不支持 `subdirs`/`add_subdirectory`；
- UTF-8，可带 BOM；支持中文路径和中文注释；
- `[DEFAULT]` 节不支持，全局设置写在 `[*]`。

## 2. 语法基础

```ini
# 注释
[*]
std = c++17

[app]
type = exe
sources =
    src/main.cpp
    src/util.cpp
include_dirs = include, third_party/include
libs = foo bar
```

- 节名就是目标名；`[*]` 是唯一的全局节；
- 键和值用 `=` 或 `:` 分隔；
- 列表值支持逗号、空白、换行；
- 路径相对**当前 INI 文件所在目录**；
- 值里的空格不需要引号；路径含 `#`/`;` 等 INI 特殊字符时需按 INI 规则处理；
- 未知键会报错，并给出最接近的合法键名；
- 同一个键重复出现会报错。

## 3. 变量

### 3.1 两种变量

```ini
[*]
var.SDK_ROOT = C:\SDK
var.SDK_INC = ${SDK_ROOT}\include
var.HOME_SDK = $ENV{USERPROFILE}\sdk
```

| 写法 | 来源 |
| --- | --- |
| `var.NAME = value` + `${NAME}` | INI 变量 |
| `$ENV{NAME}` | 环境变量 |

- 只有这两种，不存在 `${env:NAME}`、`%NAME%`、`$NAME`；
- 两边命名空间独立：INI 变量不会覆盖同名环境变量，也不会回退；
- 变量名不区分大小写；
- 环境变量不存在时直接报错，不会当成普通路径。

### 3.2 引用规则

- 变量可以互相引用，支持嵌套；
- 循环引用报错；
- `var.NAME` 只能写在 `[*]`；
- 变量只在路径/字符串类字段展开：`sources`、`include_dirs`、`lib_dirs`、`libs`、`ndk`、`build_dir`、`copy_dlls`；
- `flags`、`cflags`、`cxxflags`、`ldflags`、`defines` 不做变量展开。

## 4. `[*]` 全局设置

| 键 | 默认值 | 说明 |
| --- | --- | --- |
| `toolchain` | `auto` | `auto`/`msvc`/`gcc`/`clang`/`android-ndk` |
| `cxx` | 平台默认 | C++ 编译器路径 |
| `cc` | 平台默认 | C 编译器路径 |
| `vs` | 最高可用 | MSVC 的 VS 年份：`2019`/`2022`/`2026` |
| `arch` | `x64` | MSVC 架构：`x64`/`x86`/`arm64`/`arm` |
| `ndk` | 无 | Android NDK 根目录 |
| `api` | `21` | Android API level |
| `abi` | `arm64-v8a` | Android ABI |
| `stl` | `c++_static` | Android STL：`c++_static`/`c++_shared`/`none` |
| `std` | `c++17` | C++ 标准；`none` 表示不传 |
| `config` | `none` | `none`/`debug`/`release` |
| `build_dir` | `build` | 构建产物目录，相对 INI 文件 |
| `jobs` | `0` | 并行任务数；`0` 自动，CLI `-j` 覆盖 |
| `flags` | 空 | C/C++ 共用编译参数 |
| `cflags` | 空 | 仅 C |
| `cxxflags` | 空 | 仅 C++ |
| `ldflags` | 空 | 链接参数 |
| `include_dirs` | 空 | 全局头文件目录 |
| `lib_dirs` | 空 | 全局库目录 |
| `libs` | 空 | 全局链接库 |
| `defines` | 空 | 全局宏 |
| `header_conflict_check` | `error` | `error`/`warn`/`off` |
| `var.NAME` | 无 | INI 变量 |
| `option.NAME` | `off` | 布尔开关 |
| `choice.NAME` | 无 | N 选 1 当前值 |
| `choice.NAME.values` | 无 | 合法值列表 |

### 4.1 `toolchain`

- `auto`：Windows 用 MSVC，Linux 用 GCC；只按平台选默认值，不会猜其他工具链；
- `msvc`：仅 Windows；
- `gcc` / `clang`：仅 Linux；Windows 上的 MinGW 暂不支持；
- `android-ndk`：Android NDK 交叉编译。

### 4.2 `vs` / `arch`

- `vs` 只接受年份：`2019`、`2022`、`2026`；
- 不接受 `17` 这类短版本号；
- `2022` 会匹配所有 17.x，包括 VS2022 Preview；
- 不写 `vs` 时选最高可用版本；
- `arch` 只影响 MSVC。

### 4.3 `std` / `config`

- `std` 默认 `c++17`；`none` 表示不传标准参数；
- `config` 影响优化/调试宏和 MSVC 运行库：
  - `none`：不额外加配置参数；
  - `debug`：调试符号、调试运行库；
  - `release`：优化。

### 4.4 `jobs`

- `0` 表示自动，取 CPU 数量的合理上限；
- `-j N` 优先于 INI 的 `jobs`；
- `-j 0` 也自动；
- 并行粒度是**源文件**：不同的 `.c`/`.cpp` 同时编译，不是按 target 并行；链接/归档串行。

### 4.5 `build_dir`

```ini
[*]
build_dir = out
```

- 默认 `build`，相对 INI 文件；
- 可以用 `${VAR}`；
- 所有对象、库、exe、`compile_commands.json`、`copy_dlls` 目标都在此目录下；
- `--clean` 清理这个目录；
- 命令行 `-B out2` 只覆盖本次构建。

## 5. option / choice

### 5.1 `option`

```ini
[*]
option.WITH_OPENCL = off
option.WITH_ASAN = off
```

- 只能是 `on/off/true/false/1/0/yes/no`；
- 默认 `off`；
- 条件段写法：`[app:WITH_OPENCL]`、`[app:!WITH_OPENCL]`。

### 5.2 `choice`

```ini
[*]
choice.NPU = npu_a
choice.NPU.values = npu_a, npu_b, npu_c
```

- `choice.NAME` 是当前值，必须在 `.values` 列表里；
- `.values` 必须显式声明，逗号/空白分隔；
- 条件段写法：`[app:NPU=npu_a]`、`[app:NPU!=npu_a]`；
- `choice` 名称不区分大小写，值区分大小写；
- 同一名字不能同时定义成 `option` 和 `choice`。

### 5.3 `--set`

```bash
arche --set NPU=npu_b
arche --set WITH_OPENCL=on
arche --set SDK_DIR=D:\sdk
```

- 可重复；
- 可覆盖 `option`、`choice`、`var`；
- `option` 只接受布尔值；
- `choice` 必须是合法值；
- 只影响当前构建，不写持久 cache；
- `--set` 需要 `arche.ini`；
- 切换 option/choice 会改变宏或链接库，建议同时加 `--force`。

## 6. 目标

```ini
[app]
type = exe
sources = src/main.cpp
include_dirs = include
libs = foo
```

### 6.1 目标名

- 节名就是目标名；
- 不能包含 `/ \ : * ? " < > |`；
- `:` 保留给条件补丁段；
- 没有保留字：`build`、`clean`、`list`、`arche`、`all` 都可以作为目标名；
- 目标名不区分大小写地查重；
- `arche` 不带目标参数时构建全部；没有特殊的 `all` 目标。

### 6.2 `type`

| 值 | 说明 |
| --- | --- |
| `exe` | 可执行文件（默认） |
| `static` | 静态库 |
| `shared` | 动态库 |
| `interface` | header-only/元数据目标；不编译、无产物 |

别名：

- `crate_type`、`kind` → `type`；
- `header`、`header_only` → `interface`；
- `executable`/`app`/`binary` → `exe`；
- `staticlib`/`lib` → `static`；
- `sharedlib`/`dll` → `shared`。

`interface` 的 `sources` 可省略；其他类型必须有 `sources`。

`deps` 是 `requires` 的旧别名；`crate_type`/`kind` 是 `type` 的旧别名。

### 6.3 `sources`

```ini
sources = src/a.cpp, src/b.cpp
sources =
    src/a.cpp
    src/b.cpp
sources = src/*.cpp
sources = src/**/*.cpp
```

- 相对 INI 所在目录；
- 支持 `*`、`?`、`[]`、`**`；
- 通配符无匹配时报错；
- 结果去重。

### 6.4 头文件与库

| 键 | 说明 |
| --- | --- |
| `include_dirs` | 当前目标编译用；通过 `requires` 向下游传递 |
| `lib_dirs` | 链接库目录；沿链接闭包传递 |
| `libs` | 链接库名；沿链接闭包传递 |
| `defines` | 宏，仅当前目标 |
| `flags` | C/C++ 共用编译参数 |
| `cflags` | 仅 C |
| `cxxflags` | 仅 C++ |
| `ldflags` | 仅当前目标链接 |
| `copy_dlls` | 外部 DLL 复制（Windows） |

`defines`、`flags`、`cflags`、`cxxflags`、`ldflags` 不向下游传递。

### 6.5 `copy_dlls`

```ini
[app]
copy_dlls = C:\SDK\bin, C:\SDK\bin\*.dll
```

- 目录：复制其中所有 `.dll`；
- 文件：复制该文件；
- 通配符：按 glob 匹配；
- 仅 Windows 生效；
- 复制到目标产物目录；
- 目标已是最新时也会补齐缺失 DLL；
- arche 自己构建的动态库依赖会自动复制，不需要重复写；
- MSVC ASan 的 `clang_rt.asan_dynamic*.dll` 自动复制。

## 7. 依赖

### 7.1 三种依赖

```ini
[app]
requires = sdk
private_requires = impl
links = vendor
```

| 写法 | 当前目标编译 | 下游编译 | 下游链接 |
| --- | --- | --- | --- |
| `requires = x` | 看得到 `x.include_dirs` | 看得到 | 是 |
| `private_requires = x` | 看得到 | 看不到 | 是 |
| `links = x` | 看不到 | 看不到 | 是 |

- `requires`：公开依赖；头文件和链接都向下游传递；
- `private_requires`：当前目标的实现细节；下游只链接，不继承头文件；
- `links`：下游主动选择“只链接”，适合只需要库产物、不需要头文件的场景。

同一个目标不能同时出现在 `requires`、`private_requires`、`links` 中。

### 7.2 传递规则

- `requires` 的 `include_dirs` 逐层传递；
- `private_requires` 的 `include_dirs` 只给当前目标；
- `links` 不贡献 `include_dirs`；
- `lib_dirs`/`libs` 沿整个链接闭包汇总；
- `defines`/`flags`/`ldflags` 不传递；
- 构建顺序由依赖图决定，依赖先构建；
- 循环依赖、缺失目标会报错。

### 7.3 私有依赖示例

```ini
[cici]
type = interface
include_dirs = cici/include

[foo]
type = static
sources = foo/src/foo.cpp
include_dirs = foo/include
private_requires = cici

[app]
type = exe
sources = app/main.cpp
requires = foo
```

- `foo` 编译时能看到 `cici/include`；
- `app` 编译时只能看到 `foo/include`；
- `app` 链接时仍链接 `foo` 及其私有静态依赖。

### 7.4 同名头文件检查

```ini
[*]
header_conflict_check = error
```

编译前扫描源文件里的 `#include`：

- `#include "x.h"`：先看源文件所在目录，再看 `include_dirs`；
- `#include <x.h>`：只看 `include_dirs`；
- 同一个头文件有多个候选时，按配置处理：

| 值 | 行为 |
| --- | --- |
| `error` | 报错并列出所有候选路径（默认） |
| `warn` | 打印警告，继续编译 |
| `off` | 不检查 |

检查是文本级扫描：只针对实际出现的 `#include`，不扫描整个目录，不展开预处理宏和条件编译，也不解析注释；动态生成或宏拼接的 include 不保证能识别。同名冲突通常用下游 `links` 或库的 `private_requires` 解决。

## 8. 条件补丁段

### 8.1 语法

```ini
[app]
type = exe
sources = main.cpp

[app:WITH_OPENCL]
defines = WITH_OPENCL=1
libs = OpenCL

[app:NPU=npu_a]
requires = npu_a
```

- 节名 `[目标:条件]`；目标名本身不允许 `:`，所以没有歧义；
- 条件只支持一个：
  - `NAME`：`option.NAME` 为 on；
  - `!NAME`：`option.NAME` 为 off；
  - `NAME=value`：`choice.NAME` 等于 value；
  - `NAME!=value`：`choice.NAME` 不等于 value；
- 不支持 `&&`、`||`、括号、嵌套；
- 条件为假时整段跳过。

### 8.2 可追加的键

补丁可以追加：

`sources`、`include_dirs`、`lib_dirs`、`libs`、`defines`、`flags`、`cflags`、`cxxflags`、`ldflags`、`requires`、`private_requires`、`links`、`copy_dlls`。

不能修改 `type`。列表字段追加并去重；多个补丁按 INI 中出现的顺序应用。补丁引用的目标、option 或 choice 未声明时会报错。

### 8.3 写法 A：适配器是库目标

```ini
[*]
choice.NPU = npu_a
choice.NPU.values = npu_a, npu_b

[npu_a]
type = static
sources = npu_a/adapter.cpp
include_dirs = npu_a/include
lib_dirs = npu_a/lib
libs = npu_a_runtime

[app]
type = exe
sources = app/main.cpp

[app:NPU=npu_a]
defines = USE_NPU_A=1
private_requires = npu_a
```

适用：适配器有自己的源码，要产出 `.lib`/`.a`/`.so`/`.dll`。

### 8.4 写法 B：直接写路径和库

```ini
[app:NPU=npu_a]
defines = USE_NPU_A=1
include_dirs = npu_a/include
lib_dirs = npu_a/lib
libs = npu_a_runtime
```

适用：外部预编译 SDK，没有 arche 能构建的适配器源码。

## 9. 产物布局

| 类型 | MSVC | Linux / Android |
| --- | --- | --- |
| `exe` | `<build_dir>/<name>/<name>.exe` | `<build_dir>/<name>/<name>` |
| `static` | `<build_dir>/<name>/<name>.lib` | `<build_dir>/<name>/lib<name>.a` |
| `shared` | `<build_dir>/<name>/<name>.dll` + `<name>.lib` | `<build_dir>/<name>/lib<name>.so` |
| `interface` | 无 | 无 |

- 对象文件：`<build_dir>/.arche/obj/<target>/...`；
- MSVC debug 构建额外生成 `.pdb`；
- Windows 动态库依赖自动复制 DLL 到使用方目录；
- Linux 动态库依赖加 rpath；
- Android 不写 rpath，运行时需把 `.so` 放到设备可搜索路径。

## 10. 编译/链接参数

### 10.1 顺序

编译参数顺序：

1. 全局 `flags`；
2. 目标 `flags`；
3. 全局 `cflags` 或 `cxxflags`；
4. 目标 `cflags` 或 `cxxflags`。

链接参数顺序：

1. 全局 `ldflags`；
2. 目标 `ldflags`；
3. 依赖库产物、`lib_dirs`、`libs`。

越靠后的参数越优先，因此目标里的 `cxxflags` 可以覆盖全局标准等设置。

### 10.2 ASan

GCC/Clang：

```ini
[*]
config = debug
flags = -fsanitize=address -fno-omit-frame-pointer
ldflags = -fsanitize=address
```

MSVC：

```ini
[*]
config = debug
flags = /fsanitize=address
ldflags = /ignore:4300
defines = _DISABLE_VECTOR_ANNOTATION _DISABLE_STRING_ANNOTATION
```

MSVC 的 ASan 运行库 DLL 会自动复制到 exe 旁。

## 11. 增量构建

- 每个源文件单独生成对象文件；
- 对象文件比源文件旧时重编；
- 编译器生成头文件依赖：
  - MSVC：`/sourceDependencies` JSON；
  - GCC/Clang：`-MMD -MF`；
- 依赖头文件变化时，相关源文件全部重编；
- 链接/归档只在对象变化或产物缺失时执行；
- `--force` 强制重编指定目标，不强制依赖。

以下变化不会自动触发重编，需要 `--force` 或 `--clean`：

- `flags`/`cflags`/`cxxflags`/`defines`/`std`；
- `include_dirs`/`libs`/`ldflags`；
- 工具链或 `config`。

## 12. 编译数据库

- 每次非 `--dry-run` 的规则构建写 `<build_dir>/compile_commands.json`；
- 包含每条编译命令的 `directory`、`file`、`output`、`arguments`；
- clangd 默认在 `build/` 下查找，无需额外配置；
- 命令行模式不生成编译数据库。

## 13. Android

```ini
[*]
toolchain = android-ndk
ndk = C:\soft\toolchains\android-ndk\r27c
api = 21
abi = arm64-v8a
stl = c++_static
std = c++17
```

- `api` 默认 21；
- `abi` 默认 `arm64-v8a`，支持 `armeabi-v7a`/`x86`/`x86_64`；
- `stl` 默认 `c++_static`：
  - `c++_static`：加 `-static-libstdc++`，STL 静态进产物；
  - `c++_shared`：依赖 `libc++_shared.so`，需随产物部署；
  - `none`：加 `-nostdlib++`，C++ 代码不能使用标准库；
- 产物不能在主机直接运行；用 `adb push` 到设备；
- 选择 `c++_shared` 时从 NDK 取对应 ABI 的 `libc++_shared.so`。

详细工具链说明：[toolchains.md](toolchains.md)。

## 14. 限制

- 不支持 `subdirs`/`add_subdirectory`，一个项目一个 INI；
- 不支持自定义命令、代码生成、安装、打包；
- 不支持通用 `if/else`、`&&`/`||`、函数、循环；
- 不支持持久 cache；`--set` 只影响当前构建；
- 不支持 MinGW、macOS native、clang-cl；
- 大工程或复杂生成逻辑请用 CMake。

## 15. 完整示例

```ini
[*]
std = c++17
option.WITH_EXTRA = off
choice.NPU = npu_a
choice.NPU.values = npu_a, npu_b

var.SDK_ROOT = C:\SDK

[npu_a]
type = static
sources = npu_a/src/npu_a.cpp
include_dirs = npu_a/include

[npu_b]
type = static
sources = npu_b/src/npu_b.cpp
include_dirs = npu_b/include

[app]
type = exe
sources = src/main.cpp
include_dirs = ${SDK_ROOT}\include

[app:NPU=npu_a]
defines = USE_NPU_A=1
requires = npu_a

[app:NPU=npu_b]
defines = USE_NPU_B=1
requires = npu_b

[app:WITH_EXTRA]
defines = WITH_EXTRA=1
libs = extra
```

构建：

```bash
arche --set NPU=npu_b --set WITH_EXTRA=on --force
```
