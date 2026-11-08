# 04 · OpenCL：在 `[*]` 里硬编码路径变量

这个示例不依赖环境变量。SDK 路径直接写在 `[*]` 的变量里：

```ini
[*]
var.SDK_INC = C:\path\to\OpenCL\include
var.SDK_LIB = C:\path\to\OpenCL\lib

[opencl-info]
include_dirs = ${SDK_INC}
lib_dirs = ${SDK_LIB}
libs = OpenCL
```

## Windows

1. 打开 `arche.ini`，把 `var.SDK_INC` / `var.SDK_LIB` 改成你的 SDK 路径；
2. 构建并运行：

```bat
python ..\..\arche.py
build\opencl-info\opencl-info.exe
```

如果使用的是 OpenCL-Headers + OpenCL-ICD-Loader 这套独立 SDK，把变量指向其中的
`inc` 和 `lib` 目录。

如果 `OpenCL.dll` 不在 `System32`，在 `[*]` 里加：

```ini
var.SDK_BIN = C:\path\to\OpenCL-ICD-Loader\bin
```

并取消目标里的注释：

```ini
copy_dlls = ${SDK_BIN}
```

arche 会把该目录下的 DLL 复制到 exe 旁边。

## Linux

把 `arche.ini` 里的 Windows 两行注释掉，改用：

```ini
var.SDK_INC = /usr/include
var.SDK_LIB = /usr/lib/x86_64-linux-gnu
```

安装头文件和 ICD loader 开发包：

```bash
sudo apt install opencl-headers ocl-icd-opencl-dev
python3 ../../arche.py
./build/opencl-info/opencl-info
```

有些发行版只安装了运行库 `libOpenCL.so.1`，没有 `libOpenCL.so` 开发符号链接。
这时把 `libs` 改成：

```ini
libs = ${SDK_LIB}/libOpenCL.so.1
```

## 预期输出

```text
OpenCL platforms: 2
[0] NVIDIA CUDA | OpenCL 3.0 CUDA 12.6.65 | devices: 1
[1] AMD Accelerated Parallel Processing | OpenCL 2.1 AMD-APP (3570.0) | devices: 1
```

平台数量、名称和版本取决于机器上安装的 OpenCL 驱动。

## 变量规则

- `${NAME}` 只查 `[*]` 里的 `var.NAME`，**不会**回退到环境变量；
- 环境变量必须显式写成 `$ENV{NAME}`；
- 两边同名也不会互相覆盖；
- 需要环境变量版本时见 `../08-env-vars`。

完整语法见 [`docs/arche-ini.md`](../../docs/arche-ini.md)。
