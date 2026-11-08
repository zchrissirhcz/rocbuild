# 06 · ASan：分别设置编译参数和链接参数

这个示例演示 `[*]` 中的两个不同字段：

- `flags`：编译参数，传给每个 `.cpp`/`.c`；
- `ldflags`：链接参数，只在链接产物时使用。

ASan 通常两边都需要：编译时要插桩，链接时要链接 ASan 运行时。

```ini
[*]
config = debug
flags = -fsanitize=address -fno-omit-frame-pointer
ldflags = -fsanitize=address

[app]
type = exe
sources = main.cpp
```

## Linux / GCC / Clang

```bash
python3 ../../arche.py
./build/app/app
```

程序会故意越界，输出类似：

```text
=================================================================
==12345==ERROR: AddressSanitizer: heap-buffer-overflow ...
WRITE of size 4 ...
```

## Windows / MSVC

使用单独的配置：

```bat
python ..\..\arche.py -f arche.msvc.ini
build\app\app.exe
```

`arche.msvc.ini`：

```ini
[*]
config = debug
flags = /fsanitize=address
ldflags = /ignore:4300
defines = _DISABLE_VECTOR_ANNOTATION _DISABLE_STRING_ANNOTATION

[app]
type = exe
sources = main.cpp
```

- `config = debug` 自动补 `/Od /Z7 /MDd` 和链接 `/DEBUG /PDB`；
- `/ignore:4300` 避免链接器对 `/INCREMENTAL:NO` 的警告；
- `_DISABLE_VECTOR_ANNOTATION` / `_DISABLE_STRING_ANNOTATION` 规避 VS2022
  容器注解的误报（参考仓库的 `asan.cmake`）；
- arche 检测到 `/fsanitize=address` 时，会把 `cl.exe` 同目录下的
  `clang_rt.asan_dynamic*.dll` 自动复制到 exe 旁边，所以不需要手动改 `PATH`。

如果 ASan 报告里的调用栈没有文件名/行号，可以在运行前设置符号化工具路径：

```bat
set ASAN_SYMBOLIZER_PATH=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64
build\app\app.exe
```

实际路径以你的 VS 安装为准。

## 按目标设置 flags

`flags`/`ldflags` 也可以写在目标里，只影响该目标：

```ini
[app]
type = exe
sources = main.cpp
flags = -fsanitize=address -fno-omit-frame-pointer
ldflags = -fsanitize=address
```

`[*]` 里的值会排在目标值之前，因此目标里的参数可以覆盖全局默认值。

## 说明

- `flags` 只用于编译，`ldflags` 只用于链接；
- MSVC 的 ASan 需要 VS2019 16.7+，并安装 C++ AddressSanitizer 组件；
- 修改 `flags`/`ldflags` 后请加 `--force`，arche 的增量判断基于时间戳。
