# 07 · header-only 库

`type = interface` 表示一个只提供头文件目录的 interface 目标：

```ini
[geo]
type = interface
include_dirs = include

[app]
type = exe
sources = main.cpp
requires = geo
```

- `geo` 不编译源文件，也不产出 `.lib`/`.a`；
- `app` 通过 `requires = geo` 继承 `include_dirs`；
- 适合 `stb`、`nlohmann/json`、Eigen 这类 header-only 库；
- `arche --list` 中 `geo` 的 OUTPUT 显示为 `-`。

## 构建

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
twice(21) = 42
square(9) = 81
```

## 和静态库目标的区别

| | `type = interface` | `type = static` |
| --- | --- | --- |
| 编译源文件 | 不编译 | 编译 |
| 产物 | 无 | `.lib`/`lib*.a` |
| `include_dirs` 传递 | 是 | 是 |
| 适合 | header-only 库 | 有 `.cpp` 实现的库 |
