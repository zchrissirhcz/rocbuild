# 12 · option / choice / 条件补丁段

这个示例有两个 NPU 适配器，用 `choice.NPU` 多选一。

## OOP 写法：适配器是 static 库

`arche.ini`：

```ini
[*]
choice.NPU = npu_a
choice.NPU.values = npu_a, npu_b

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
sources = app/main.cpp

[app:NPU=npu_a]
defines = USE_NPU_A=1
requires = npu_a

[app:NPU=npu_b]
defines = USE_NPU_B=1
requires = npu_b
```

- `npu_a` / `npu_b` 是真正的 `static` 适配库；
- 条件补丁只负责“选哪个库 + 定义哪个宏”；
- `requires` 让 `app` 继承适配器的头文件目录并链接库。

构建：

```bash
python3 ../../arche.py
./build/app/app
```

Windows：

```bat
python ..\..\arche.py
build\app\app.exe
```

输出：

```text
npu_value() = 1
```

切换到 `npu_b`：

```bash
python3 ../../arche.py --set NPU=npu_b --force
./build/app/app
```

输出：

```text
npu_value() = 2
```

## 直接写法：补丁里写 sources/include_dirs

`arche.flat.ini`：

```ini
[app:NPU=npu_a]
defines = USE_NPU_A=1
sources = npu_a/src/npu_a.cpp
include_dirs = npu_a/include
```

```bash
python3 ../../arche.py -f arche.flat.ini
python3 ../../arche.py -f arche.flat.ini --set NPU=npu_b --force
```

这种方式不需要单独的适配器 target，适合外部预编译 SDK 或一次性包装。两种写法二选一，不要同时使用。

## 规则

- `choice.NPU.values` 必须显式列出合法值；
- `--set NPU=...` 只影响本次构建；
- 条件段只支持单条件：`[app:NPU=npu_a]`、`[app:NPU!=npu_a]`；
- 布尔开关用 `option.NAME = off`，条件段写 `[app:WITH_X]` / `[app:!WITH_X]`；
- 补丁不能改 `type`。
