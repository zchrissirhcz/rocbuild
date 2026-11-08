# juicy.py

`juicy.py` 让 cmake 的 configure 和 build 都更简单.

- 不用记 `Visual Studio 17 2022` 这种又长又容易写错的 generator 名字, 只需传 -p vs2022 或省略, juicy 会自动选择最新的 Visual Studio
- 不用为交叉编译平台手写 `toolchain.cmake`
- 不用为了 MSVC + Ninja 的配置和构建进入 VS 开发者环境

只需要传平台和架构, juicy 会补齐 generator 和编译环境.
native 构建 (VS / Linux) 直接使用本机编译器, 不需要 `toolchain.cmake`;
交叉编译 (Android / QNX / MinGW) 才使用 `toolchain.cmake`.
`juicy.py build` 会沿用配置时的环境.

需要 Python 3 和 CMake; 使用 Ninja 生成器时还需要 ninja 在 PATH 中.

## Configure

```powershell
# Windows: 不传 -p 时自动选最新 Visual Studio
# Linux/WSL: 不传 -p 时使用 native 构建
python juicy.py -S . -B build

# Linux/WSL native
python juicy.py -p linux -a x64 -S . -B build

# VS + Ninja
python juicy.py -p vs2022 -G Ninja -S . -B build

# Android NDK
python juicy.py -p android -a armv8-a -r C:\soft\toolchains\android-ndk\r27c -S . -B build

# QNX SDP
python juicy.py -p qnx -a aarch64 -r C:\soft\toolchains\qnx800 -S . -B build-qnx

# MinGW
python juicy.py -p mingw -a x86_64 -r C:\soft\toolchains\MinGW -S . -B build-mingw

# 透传参数给 cmake
python juicy.py -p vs2022 -G Ninja -S . -B build -DCMAKE_BUILD_TYPE=Release

# 平台帮助
python juicy.py -p android --help
```

## Build

`juicy.py build -B <dir>` 对所有平台都可用:

- MSVC + Ninja: 从 CMakeCache 恢复 VS 环境, 不需要手动进 VS 开发者环境
- QNX: 从 CMakeCache 恢复 SDP 环境, 不需要手动 call qnxsdp-env
- Linux native: 不需要额外环境, juicy 会直接执行 `cmake --build`

无论 native 还是 cross, 构建入口都是 `python juicy.py build -B <dir>`.

```powershell
python juicy.py build -B build
python juicy.py build -B build-qnx
python juicy.py build -B build -j 8 --target hello
```

## Tests

```powershell
python -m unittest -v test_juicy
```

Windows/Linux native 和本地 Android/QNX/MinGW 都会实际执行 configure + build.
本地工具链目录在 `test_juicy.py` 开头, 可用 `JUICY_TEST_ANDROID_NDK`,
`JUICY_TEST_QNX_SDP`, `JUICY_TEST_MINGW` 覆盖.
测试 build 目录在 `build-tests/` 下, 每个 case 一个子目录, 已忽略; 失败后可直接进去看.

## 平台

| `-p` | 类型 | `-r` | 默认生成器 |
| --- | --- | --- | --- |
| `vs2026` / `vs2022` / `vs2019` | native | 不用 | 对应 VS 生成器 |
| `linux` | native | 不用 | Ninja |
| `android` | cross | NDK 根目录, 必填 | Ninja |
| `qnx` | cross | QNX SDP 根目录, 必填 | Ninja |
| `mingw` | cross | MinGW 根目录, 可选 | Ninja |

- `-r` 的根目录会存为 `JUICY_TOOLCHAIN_ROOT`.
- 未指定 `-p` 时, Windows (非 WSL) 自动选最新 Visual Studio; Linux/WSL 使用 native 构建.
- `vs20xx` 只能在 Windows 上使用; `linux` 只能在 Linux/WSL 上使用.
- `toolchains/` 存放 Android/QNX/MinGW 等平台使用的 toolchain 文件; juicy 的 VS/Linux native 构建不使用 toolchain 文件.
