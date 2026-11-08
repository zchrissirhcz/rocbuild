# 05 · Android NDK 交叉编译

这个示例用 `[*]` 里的工具链配置交叉编译一个动态库和一个可执行文件：

```ini
[*]
toolchain = android-ndk
ndk = C:\soft\toolchains\android-ndk\r27c
api = 21
abi = arm64-v8a
stl = c++_static
std = c++17
config = release

[greet]
type = shared
sources = src/greet.cpp
include_dirs = include

[app]
type = exe
sources = src/main.cpp
requires = greet
```

## 构建

把 `ndk` 改成你的 NDK 根目录，然后：

```bat
python ..\..\arche.py
```

产物：

```text
build/
  greet/
    libgreet.so
  app/
    app
```

`app` 是 AArch64 Android ELF，不是 Windows/Linux 可执行文件，不能直接在主机运行。

## 选择 ABI / API

```ini
abi = arm64-v8a     # aarch64-linux-android
# abi = armeabi-v7a # armv7a-linux-androideabi
# abi = x86         # i686-linux-android
# abi = x86_64      # x86_64-linux-android

api = 21
```

`stl` 可选 `c++_static`（默认，STL 静态进产物）、`c++_shared`（运行时部署
`libc++_shared.so`）、`none`（不使用 STL）。

## 验证架构

```powershell
& "C:\soft\toolchains\android-ndk\r27c\toolchains\llvm\prebuilt\windows-x86_64\bin\llvm-readelf.exe" -h build\app\app
```

输出中应包含：

```text
Class:   ELF64
Machine: AArch64
```

## 推送到设备运行

```bash
adb push build/app/app /data/local/tmp/
adb push build/greet/libgreet.so /data/local/tmp/
adb shell chmod +x /data/local/tmp/app
adb shell "cd /data/local/tmp && LD_LIBRARY_PATH=. ./app"
```

如果选择 `c++_shared`，C++ 程序通常还依赖 `libc++_shared.so`。从 NDK 中取对应 ABI 的库一起推送：

```text
<ndk>/toolchains/llvm/prebuilt/<host>/sysroot/usr/lib/<triple>/libc++_shared.so
```

例如 `aarch64-linux-android/libc++_shared.so`。

## 说明

- `toolchain`、`ndk`、`api`、`abi` 都在 `arche.ini` 的 `[*]` 里，命令行不需要再传；
- 头文件依赖、静态库/动态库链接、增量构建与 本机编译模式一致；
- Android 模式不添加 rpath，运行时用 `LD_LIBRARY_PATH` 或把 `.so` 放到 APK 的
  `lib/<abi>/` 目录。
