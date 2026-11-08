# 10 · links：下游只链接，不继承头文件目录

这个示例演示两个头文件同名 `config.h` 的冲突，以及下游如何用 `links` 只链接：

```text
foo/include/config.h    # FOO_VALUE = 2
app/config.h            # APP_VALUE = 1
```

`app` 和 `foo` 都需要自己的 `config.h`，但 `app` 只调用 `foo` 的 C 函数，不需要
`foo` 的头文件。

## 先看冲突

```bash
python3 ../../arche.py -f arche.conflict.ini
```

`app` 用 `requires = foo`，会继承 `foo/include`。arche 的 `header_conflict_check` 会报错：

```text
发现同名头文件冲突:
目标 [app] 的 .../app/main.cpp 中 #include "config.h" 有多个候选:
  - .../app/config.h
  - .../foo/include/config.h
可以用下游目标的 links = <库> 只链接、不继承头文件目录，
或设置 header_conflict_check = warn/off。
```

## 修复：下游使用 `links`

`arche.ini` 中把 `app` 的依赖改成：

```ini
[foo]
type = static
sources = foo/src/foo.cpp
include_dirs = foo/include

[app]
type = exe
sources = app/main.cpp
links = foo          # 只链接 foo，不继承 foo/include
```

构建并运行：

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
APP_VALUE + foo_value() = 3
```

## 说明

- `requires = foo`：构建顺序 + `foo.include_dirs` + 链接 `foo`；
- `links = foo`：构建顺序 + 链接 `foo`，**不继承** `foo.include_dirs`；
- 选择权在下游：`app1` 可以 `requires = foo` 使用 foo 的头文件，`app2` 可以
  `links = foo` 只链接；
- `header_conflict_check = error`（默认）会主动发现同名头文件；也可设为 `warn`/`off`。

`app` 这里用 `extern "C" int foo_value();` 手写声明，是因为它不包含 `foo` 的公共
头文件。如果 `app` 需要 `foo` 的公共头文件，就用 `requires = foo`，并把私有头文件
（如 `config.h`）放到另一个目录，避免传播。
