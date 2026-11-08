# 工具链

工具链统一写在 `arche.ini` 的 `[*]`：

```ini
[*]
toolchain = auto
```

| 值 | 平台 | 说明 |
| --- | --- | --- |
| `auto` | 全部 | Windows 用 MSVC，Linux 用 GCC |
| `msvc` | Windows | Visual Studio C++ 工具集 |
| `gcc` | Linux | GCC |
| `clang` | Linux | Clang |
| `android-ndk` | 任意主机 | Android NDK 交叉编译 |

`auto` 只按平台选默认值，不会在多个本机工具链之间猜。想用 Clang 就显式写 `toolchain = clang`。

## Windows / MSVC

```ini
[*]
toolchain = msvc
vs = 2022
arch = x64
```

### 自动发现

arche 直接用 Visual Studio Setup Configuration COM 接口枚举安装，不调用 `vswhere.exe`，也不假定 VS 装在 C 盘。

- 能发现 VS 和 Build Tools；
- 不扫描固定磁盘，不写死 `Program Files`；
- COM 不可用时直接报错，不猜路径。

### `vs`

只接受年份：

```ini
vs = 2019
vs = 2022
vs = 2026
```

- 不接受 `17` 这类短版本号；
- `2022` 会匹配所有 17.x，包括 VS2022 Preview；
- 不写 `vs` 时选最高可用版本。

`arche --list-vs` 查看检测结果：

```text
版本                    状态        安装路径
18.11.12328.437        可用        C:\Program Files\Microsoft Visual Studio\18\Community
17.14.37827.9          可用        C:\Program Files\Microsoft Visual Studio\2022\Community
```

### `arch`

| 值 | 说明 |
| --- | --- |
| `x64` | 默认 |
| `x86` | 32 位 |
| `arm64` | ARM64 |
| `arm` | ARM |

### 要求

- 安装“使用 C++ 的桌面开发”工作负载；
- 通过 `vcvarsall.bat` 加载环境；
- arche 使用 `cl.exe`、`link.exe`、`lib.exe` 的绝对路径。

## Linux / GCC / Clang

```ini
[*]
toolchain = gcc
# 或 toolchain = clang
```

默认查找：

- C++：`g++` 或 `clang++`；
- C：`gcc` 或 `clang`；
- 归档：`ar`。

可以用 `[*] cxx`、`[*] cc` 或环境变量 `CXX`/`CC` 覆盖具体编译器。环境变量只作为默认值，INI 优先。

## Android NDK

```ini
[*]
toolchain = android-ndk
ndk = C:\soft\toolchains\android-ndk\r27c
api = 21
abi = arm64-v8a
stl = c++_static
std = c++17
```

| 键 | 默认值 | 说明 |
| --- | --- | --- |
| `ndk` | 无 | NDK 根目录，必须存在 |
| `api` | `21` | API level |
| `abi` | `arm64-v8a` | `arm64-v8a`/`armeabi-v7a`/`x86`/`x86_64` |
| `stl` | `c++_static` | `c++_static`/`c++_shared`/`none` |

### STL

| 值 | 行为 |
| --- | --- |
| `c++_static` | 加 `-static-libstdc++`，STL 静态进产物 |
| `c++_shared` | 依赖 `libc++_shared.so`，运行时需部署 |
| `none` | 加 `-nostdlib++`，C++ 代码不能使用标准库 |

`c++_shared` 时，从 NDK 取对应 ABI 的库并随产物部署：

```text
<ndk>/toolchains/llvm/prebuilt/<host>/sysroot/usr/lib/<triple>/libc++_shared.so
```

### 产物与运行

- 产物是 Android ELF，不能在主机直接运行；
- 用 `adb push` 推到设备；
- 选择 `c++_shared` 时，`libc++_shared.so` 要和可执行文件/`.so` 一起推送；
- Android 不写 rpath，运行时需要把库放到设备可搜索路径。

示例：[examples/05-android](../examples/05-android/README.md)。

## 支持矩阵

| 平台 | 工具链值 | 状态 |
| --- | --- | --- |
| Windows MSVC | `auto`/`msvc` | 支持 |
| Linux GCC | `auto`/`gcc` | 支持 |
| Linux Clang | `clang` | 支持 |
| Android NDK | `android-ndk` | 支持 |
| Windows MinGW | `gcc`/`clang` | 不支持，明确报错 |
| macOS native | — | 不支持 |

详细 INI 字段见 [arche-ini.md](arche-ini.md)。
