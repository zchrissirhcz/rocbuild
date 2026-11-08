# arche

`arche` 是一个轻量级 C/C++ 构建工具：一个 `arche.py` + 一个 `arche.ini`，不生成工程、不依赖第三方库。

- Windows：MSVC，自动发现 Visual Studio，不依赖 `vswhere.exe`；
- Linux：GCC / Clang；
- Android：NDK 交叉编译，支持 ABI、API 和 STL 选择；
- 支持可执行文件、静态库、动态库、header-only interface，以及目标间依赖。

## 为什么不用 CMake / Make

| | CMake | Make | arche |
| --- | --- | --- | --- |
| 构建描述 | CMakeLists + 一门 DSL | Makefile + tab/ shell | 简单 INI |
| 生成步骤 | configure + generator + cache | 无 | 无，直接构建 |
| 依赖传递 | `PUBLIC`/`PRIVATE`/`INTERFACE` | 手写变量和链接顺序 | `requires` / `private_requires` / `links` |
| Windows MSVC | 需要生成器/VS 工程 | 通常配 MinGW | 内置 COM 发现 + `vcvarsall` |
| Android | toolchain 文件 | 手写 NDK 参数 | `toolchain = android-ndk` |
| 增量构建 | 编译器 depfile | 手写规则 | 源文件 + 头文件依赖 |
| IDE | `compile_commands.json` | 常靠 `bear` 等外部工具 | 自动生成 `<build_dir>/compile_commands.json` |
| 扩展方式 | 函数、生成器、脚本 | shell | 有意保持小而受限 |

arche 的优势是“短路径”：改一行 INI 或直接 `arche main.cpp`，没有 configure、没有生成器、没有隐藏 cache；Windows 和 Linux 用同一套描述。

arche 不试图替代 CMake 的全部能力。它没有通用 `if/else` 表达式、函数、代码生成、安装/打包和 `subdirs`；这些场景请继续用 CMake。

## 快速开始

### 1. 命令行模式

不写 `arche.ini`，直接编译：

```bash
python arche.py hello.cpp
python arche.py main.cpp util.cpp -o app -Iinclude -DDEBUG
python arche.py main.cpp -Llib -lfoo -- -Wall -O2
```

- 支持 `-o`、`-I`、`-D`、`-L`、`-l`；
- `--` 之后的参数原样交给编译器；
- 不做增量构建；
- 如果当前目录有 `arche.ini`，会复用 `[*]` 里的工具链和全局参数。

### 2. 规则模式

`arche.ini`：

```ini
[*]
std = c++17

[mathx]
type = static
sources = src/mathx.cpp, src/stats.cpp
include_dirs = include

[app]
type = exe
sources = src/main.cpp
requires = mathx
```

构建：

```bash
python arche.py            # 全部目标
python arche.py app        # 只构建 app，自动先构建 mathx
python arche.py --list     # 查看目标
python arche.py --clean    # 清理 build/
python arche.py -B out     # 产物放到 out/
python arche.py -S proj -B out  # 指定源码目录和构建目录
```

`app` 不需要重复写 `include_dirs = include`：通过 `requires = mathx`，头文件目录和静态库产物都会自动传递。

### 3. 直接体验示例

```bash
cd examples/02-static-lib
python ../../arche.py
./build/app/app
```

## 核心概念

### 目标类型

| `type` | 产物 |
| --- | --- |
| `exe` | 可执行文件 |
| `static` | `.lib` / `lib*.a` |
| `shared` | `.dll` + `.lib` / `lib*.so` |
| `interface` | 无产物；只传递 `include_dirs` 等配置 |

`crate_type`/`kind` 是 `type` 的别名；`header`/`header_only` 是 `interface` 的别名。

### 三种依赖

```ini
[app]
requires = sdk          # 公开：头文件 + 链接，继续向下游传递
private_requires = impl # 私有：当前目标能用头文件，下游只链接
links = vendor          # 只链接：当前目标和下游都不继承头文件
```

- `requires`：目标自己的 `include_dirs` 和库产物都会传给下游；
- `private_requires`：只有当前目标能看到依赖的 `include_dirs`，下游不继承，但链接闭包保留；
- `links`：不继承对方 `include_dirs`，只参与构建顺序和链接。

这可以覆盖：

```text
cici (interface)
  ↑ private_requires
foo (static)
  ↑ requires
app (exe)
```

`foo` 能看到 `cici` 头文件，`app` 只能看到 `foo` 头文件。

### option / choice / 条件补丁

布尔开关：

```ini
[*]
option.WITH_OPENCL = off

[app:WITH_OPENCL]
defines = WITH_OPENCL=1
libs = OpenCL
```

多选一：

```ini
[*]
choice.NPU = npu_a
choice.NPU.values = npu_a, npu_b

[npu_a]
type = static
sources = npu_a.cpp
include_dirs = npu_a/include

[app:NPU=npu_a]
defines = USE_NPU_A=1
requires = npu_a
```

命令行覆盖，仅本次有效：

```bash
python arche.py --set NPU=npu_b --force
python arche.py --set WITH_OPENCL=on --force
```

切换 option/choice 会改变宏或链接库，但这些不属于时间戳增量判断，所以需要 `--force`。

条件段只支持单个条件：`NAME`、`!NAME`、`NAME=value`、`NAME!=value`；不支持 `&&`/`||`。

### 变量

```ini
[*]
var.SDK_ROOT = C:\SDK
var.SDK_INC = ${SDK_ROOT}\include
var.HOME = $ENV{USERPROFILE}\sdk

[app]
include_dirs = ${SDK_INC}
```

只有两种：

- `var.NAME` + `${NAME}`：INI 变量；
- `$ENV{NAME}`：环境变量。

两者互不覆盖；同名也不会串。

### 构建目录

```ini
[*]
build_dir = out
```

- 默认 `build`，相对 INI 文件；
- 对象、库、exe、`compile_commands.json` 都在这个目录；
- 命令行 `python arche.py -B out2` 只覆盖本次构建；
- `--clean` 清理当前构建目录。

## 工具链

```ini
[*]
toolchain = auto        # auto/msvc/gcc/clang/android-ndk
```

- `auto`：Windows → MSVC，Linux → GCC；
- Windows 上的 `gcc`/`clang`（MinGW）暂不支持；
- MSVC 用 Setup Configuration COM 发现 VS，`vs = 2022` 会匹配所有 17.x（含 Preview）；
- Android 见下一节。

详细说明：[docs/toolchains.md](docs/toolchains.md)。

## Android

```ini
[*]
toolchain = android-ndk
ndk = C:\soft\toolchains\android-ndk\r27c
api = 21
abi = arm64-v8a
stl = c++_static
std = c++17
```

- `abi`：`arm64-v8a` / `armeabi-v7a` / `x86` / `x86_64`；
- `stl`：`c++_static`（默认）/ `c++_shared` / `none`；
- 产物是 Android ELF，不能直接在主机运行；用 `adb push` 到设备；
- 选择 `c++_shared` 时需要同时部署 `libc++_shared.so`。

示例：[examples/05-android](examples/05-android/README.md)。

## 增量构建

- 每个源文件单独生成 `.obj`/`.o`，只重编变化的源文件；
- 编译器生成头文件依赖：MSVC `/sourceDependencies`，GCC/Clang `-MMD`；
- 头文件变化时，所有包含它的源文件重编；
- 链接/归档只在有对象变化或产物缺失时执行；
- `--force` 强制重编指定目标，但不强制其依赖。

注意：修改 `flags`/`defines`/`std`/`include_dirs` 等配置不会自动触发重编；用 `--force` 或 `--clean`。

## 编译数据库与 DLL

- 每次非 dry-run 的规则构建都会写 `<build_dir>/compile_commands.json`，clangd/IDE 可直接使用；
- Windows 上自动复制 arche 构建的动态库依赖；
- 外部 SDK 的 DLL 用 `copy_dlls` 声明，支持目录、文件、通配符；
- MSVC ASan 的 `clang_rt.asan_dynamic*.dll` 自动复制。

## 命令行速查

| 选项 | 说明 |
| --- | --- |
| `-S DIR` | 源码/工程目录（等价于先进入该目录） |
| `-B DIR` | 覆盖构建产物目录 |
| `-f FILE` | 指定 INI 文件 |
| `-j N` | 并行任务数；按源文件并行，`0` 自动 |
| `-v` / `-q` | 详细输出 / 只输出错误 |
| `-n` / `--dry-run` | 打印命令但不执行 |
| `--force` | 强制重建指定目标 |
| `--set NAME=VALUE` | 覆盖 var/option/choice，仅本次有效 |
| `--clean [目标]` | 清理全部或指定目标 |
| `--list` | 列出目标 |
| `--list-vs` | 列出检测到的 Visual Studio |
| `--version` | 版本 |
| `-o` / `-I` / `-D` / `-L` / `-l` | 命令行模式的输出/头文件/宏/库 |

位置参数是目标名或源文件：

```bash
arche              # 构建全部目标
arche app          # 只构建 app，自动先构建依赖
arche app libfoo   # 构建多个目标
```

没有特殊的 `all` 目标；`arche` 不带参数就是全部。`[all]` 仍然是合法的普通目标名。

详细说明：[docs/cli.md](docs/cli.md)。

## 示例

| 目录 | 演示内容 |
| --- | --- |
| [01-hello-cli](examples/01-hello-cli) | 命令行模式：单/多源文件、`-I`、`-D`、`--` |
| [02-static-lib](examples/02-static-lib) | 静态库 + `requires` + 多源文件 + 增量构建 |
| [03-shared-lib](examples/03-shared-lib) | 动态库 + Windows DLL 复制 + Linux rpath |
| [04-opencl](examples/04-opencl) | INI 变量硬编码 SDK 路径 + 第三方库 |
| [05-android](examples/05-android) | Android NDK 交叉编译 + STL |
| [06-asan](examples/06-asan) | `flags`/`ldflags` 分离 + ASan |
| [07-header-only](examples/07-header-only) | `type = interface` |
| [08-env-vars](examples/08-env-vars) | `$ENV{NAME}` |
| [09-copy-dlls](examples/09-copy-dlls) | `copy_dlls` 复制外部 DLL |
| [10-links](examples/10-links) | 下游 `links` + 同名头文件检查 |
| [11-private-requires](examples/11-private-requires) | `private_requires` 隔离私有头文件 |
| [12-options](examples/12-options) | `option`/`choice`/条件补丁段 |

## 详细文档

- [docs/arche-ini.md](docs/arche-ini.md)：`arche.ini` 完整规范，写新配置优先看这个；
- [docs/cli.md](docs/cli.md)：命令行参考；
- [docs/toolchains.md](docs/toolchains.md)：MSVC/GCC/Clang/Android；
- [docs/requirements.md](docs/requirements.md)：需求覆盖表、暂缓项。

## 边界

arche 有意保持小：

- 没有 `subdirs`/`add_subdirectory`，一个项目使用一个 `arche.ini`；
- 没有自定义命令、代码生成、安装、打包；
- 没有通用 `if/else`、函数、循环；
- 没有持久 cache，`--set` 只影响当前构建；
- 不支持 macOS native、MinGW、clang-cl；
- 大工程、复杂生成逻辑请用 CMake。

## 测试

```bash
# Windows
python -m unittest discover -s tests

# Linux
python3 -m unittest discover -s tests
```

## License

MIT
