# 02 · 规则模式：多源文件 + 静态库 + 可执行文件

这个示例比“一个 `.cpp` 编一个 exe”多走一步，演示真实一点的工程结构：

- `mathx` 静态库由 **两个** 源文件组成：`src/mathx.cpp`、`src/stats.cpp`；
- `app` 可执行文件也由 **两个** 源文件组成：`src/main.cpp`、`src/report.cpp`；
- `app` 通过 `requires = mathx` 依赖静态库；
- `mathx` 的 `include_dirs` 自动传递给 `app`。

## 构建

Windows：

```bat
python ..\..\arche.py
build\app\app.exe
```

Linux：

```bash
python3 ../../arche.py
./build/app/app
```

输出：

```text
2 + 3    = 5
2 * 3    = 6
max      = 3
```

也可以只构建 `app`（依赖会自动构建）：

```bash
python3 ../../arche.py app
```

## 多源文件：逗号、换行、空白、通配符

`arche.ini` 里 `mathx` 用的是**逗号分隔**：

```ini
[mathx]
type = static
sources = src/mathx.cpp, src/stats.cpp
```

`app` 用的是**换行分隔**，两者完全等价：

```ini
[app]
type = exe
sources =
    src/main.cpp
    src/report.cpp
requires = mathx
```

四种写法都支持：

```ini
# 1. 逗号分隔
sources = src/main.cpp, src/report.cpp

# 2. 换行分隔
sources =
    src/main.cpp
    src/report.cpp

# 3. 空白分隔
sources = src/main.cpp src/report.cpp

# 4. 通配符
sources = src/*.cpp
```

`requires`、`include_dirs`、`lib_dirs`、`libs` 同样支持逗号或空白分隔，例如：

```ini
requires = mathx, platform
include_dirs = include, third_party/include
libs = user32, gdi32
```

注意：

- `flags`、`cflags`、`cxxflags`、`ldflags`、`defines` **只按空白分隔**，不按逗号分隔，
  以免拆坏 `-Wl,-rpath,/some/path` 这类参数；
- 路径含空格时用双引号：`include_dirs = "C:\Program Files\SDK\include"`；
- 相对路径都相对于 `arche.ini` 所在目录；
- 通配符没有匹配到文件时会直接报错，不会静默漏编译。

## 每个源文件都有自己的对象文件

```text
build/
  .arche/
    obj/
      mathx/src/mathx.cpp.obj     # Windows 为 .obj，Linux 为 .o
      mathx/src/stats.cpp.obj
      app/src/main.cpp.obj
      app/src/report.cpp.obj
  mathx/
    mathx.lib                     # Linux: libmathx.a
  app/
    app.exe                       # Linux: app
```

默认会并行编译这些对象文件。修改 `include/mathx.h` 后，`mathx.cpp` 和 `stats.cpp`
都会重新编译；`main.cpp` 也包含该头文件，所以也会重新编译。

## 查看目标、增量构建与清理

```bash
python3 ../../arche.py --list       # 查看目标、产物、requires
python3 ../../arche.py               # 第二次执行会提示“已是最新”
python3 ../../arche.py --force app   # 只强制重建 app（mathx 不强制）
python3 ../../arche.py --clean app   # 只清理 app，保留 mathx 的产物
python3 ../../arche.py --clean       # 清理整个 build/
```

`--list` 输出：

```text
NAME   TYPE    OUTPUT                 REQUIRES/LINKS
mathx  static  build/mathx/libmathx.a  -
app    exe     build/app/app           mathx
```
