# 08 · 环境变量

这个示例演示环境变量的**显式**写法 `$ENV{NAME}`：

```ini
[*]
var.SDK_INC = $ENV{ARCHE_DEMO_INC}

[app]
type = exe
sources = main.cpp
include_dirs = ${SDK_INC}
```

- `${NAME}` 只查 `[*]` 的 `var.NAME`；
- `$ENV{NAME}` 只查环境变量；
- 两边同名也不会互相覆盖。

## Windows

```bat
set ARCHE_DEMO_INC=%CD%\include
python ..\..\arche.py
build\app\app.exe
```

PowerShell：

```powershell
$env:ARCHE_DEMO_INC = "$PWD\include"
python ..\..\arche.py
.\build\app\app.exe
```

## Linux

```bash
export ARCHE_DEMO_INC=$PWD/include
python3 ../../arche.py
./build/app/app
```

输出：

```text
ENV_VALUE = 123
```

如果 `ARCHE_DEMO_INC` 没有设置，arche 会报错并指出 `$ENV{ARCHE_DEMO_INC}`，
不会把它当成相对路径。

## 和 04-opencl 的区别

- `04-opencl`：路径硬编码在 `var.NAME` 里，工程自包含；
- 本示例：路径由环境变量提供，适合 CI 或机器相关的 SDK 路径。
