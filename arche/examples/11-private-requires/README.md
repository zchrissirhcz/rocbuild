# 11 · 私有依赖：foo 能看 cici，app 看不到 cici

依赖关系：

```text
cici (interface)
  ↑ private_requires
foo (static)
  ↑ requires
app (exe)
```

```ini
[cici]
type = interface
include_dirs = cici/include

[foo]
type = static
sources = foo/src/foo.cpp
include_dirs = foo/include
private_requires = cici

[app]
type = exe
sources = app/main.cpp
requires = foo
```

- `foo` 编译时能看到 `cici/include` 和 `foo/include`；
- `app` 编译时只看到 `foo/include`，看不到 `cici/include`；
- `app` 链接时仍会链接 `foo`（以及 `foo` 的私有静态依赖，如果需要）。

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
foo_value() = 2
```

## 反例：app 直接包含 cici.h

```bash
python3 ../../arche.py -f arche.bad.ini
```

`app_bad.cpp` 里写了 `#include "cici.h"`，但 `cici` 是 `foo` 的私有依赖，不进入
`app` 的 include 路径，所以会编译失败：

```text
fatal error: cici.h: No such file or directory
```

## `requires`、`private_requires`、`links`

| 写法 | 当前目标编译时看得到 | 下游看得到 | 下游链接 |
| --- | --- | --- | --- |
| `requires = cici` | 是 | 是 | 是 |
| `private_requires = cici` | 是 | 否 | 是 |
| `links = cici`（下游写） | 否 | 否 | 是 |

- `private_requires` 由**库的作者**声明：这是实现细节；
- `links` 由**下游**声明：我不想看你的头文件，只想链接；
- 两者可以组合使用。
