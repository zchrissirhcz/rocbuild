# 命令行参考

```text
arche [选项] [目标|源文件 ...] [-- 编译器参数 ...]
```

`-S` 指定源码/工程目录，`-B` 指定构建目录；工具链只写在 `arche.ini` 的 `[*]`，命令行不提供 `--toolchain`、`--vs`、`--arch`、`--cxx`、`--cc`。

## 1. 两种模式

### 规则模式

当前目录有 `arche.ini`：

```bash
arche                 # 构建全部目标
arche app             # 构建 app 及其依赖
arche app libfoo      # 多个目标
arche main.cpp        # 若 main.cpp 属于某个目标，构建该目标
```

位置参数永远是目标名或源文件，没有 `clean`/`list` 这类位置命令。

### 命令行模式

没有 `arche.ini`，或源文件不属于任何目标：

```bash
arche hello.cpp
arche main.cpp util.cpp -o app
arche main.cpp -Iinclude -DDEBUG -Llib -lfoo
```

同一次调用不能混合目标名和临时源文件。

### 位置参数

位置参数是目标名或源文件：

```bash
arche              # 全部目标
arche app          # app 及其依赖
arche app libfoo   # 多个目标
arche main.cpp     # main.cpp 所属目标
```

没有特殊的 `all` 目标；`arche` 不带参数就是全部。`[all]` 是合法的普通目标名。

`-j N` 按**源文件**调度编译任务，不是按 target 或 project；链接/归档在编译阶段结束后串行执行。

## 2. 通用选项

| 选项 | 说明 |
| --- | --- |
| `-S DIR` | 源码/工程目录 |
| `-B DIR` | 覆盖构建产物目录 |
| `-f FILE` | 指定 INI |
| `-j N` | 并行任务数；按源文件并行，`0` 自动 |
| `-v` / `--verbose` | 打印命令 |
| `-q` / `--quiet` | 只输出错误 |
| `-n` / `--dry-run` | 打印命令但不执行 |
| `--force` | 强制重建指定目标（不强制依赖） |
| `--set NAME=VALUE` | 覆盖 var/option/choice，仅本次有效 |
| `--clean [目标]` | 清理全部或指定目标 |
| `--list` | 列出目标 |
| `--list-vs` | 列出检测到的 Visual Studio |
| `--version` | 版本 |

`-v` 和 `-q` 不能同时使用。

### `-S` / `--source-dir`

```bash
arche -S proj
arche -S proj -B out
```

- 指定源码/工程目录，相当于先进入该目录；
- 默认读取该目录下的 `arche.ini`；
- `-f` 的相对路径也相对该目录；
- `-B` 仍相对调用时的当前目录解析。

### `-B` / `--build-dir`

```bash
arche -B out
arche -B out --clean
```

- 覆盖 INI 的 `build_dir`，只影响本次调用；
- 相对路径按当前工作目录解析；
- 对象、产物、`compile_commands.json` 都放到该目录；
- 需要 `arche.ini`。

### `--force`

```bash
arche --force app
```

只强制重建 `app` 的源文件；`app` 的依赖仍按增量规则处理。不带目标名时强制全部。

### `--set`

```bash
arche --set NPU=npu_b
arche --set WITH_OPENCL=on
arche --set SDK_DIR=D:\sdk
```

- `option` 只接受 `on/off/true/false/1/0/yes/no`；
- `choice` 必须是 `choice.NAME.values` 中的值；
- `var` 覆盖字符串/路径；
- 名称不区分大小写，choice 值区分大小写；
- 需要 `arche.ini`，只影响本次构建，不写 cache；
- 切换 option/choice 会改变宏或链接库，建议同时加 `--force`。

### `--clean`

```bash
arche --clean              # 清理整个 build/
arche --clean app          # 只清理 app
```

`--clean app` 不清理依赖目标的产物。

### `--list`

```bash
arche --list
```

不接受目标参数；输出：

```text
NAME   TYPE    OUTPUT                 REQUIRES/LINKS
app    exe     build/app/app.exe      mathx
mathx  static  build/mathx/mathx.lib  -
```

如果目标名恰好是 `clean`/`list`，用 `--clean clean` 清理它，用 `--list` 查看全部。

`REQUIRES/LINKS` 列包含 `requires`、`private_requires`、`links` 三种依赖。

## 3. 命令行模式选项

| 选项 | 说明 |
| --- | --- |
| `-o FILE` | 输出文件；默认源文件旁 |
| `-I DIR` | 头文件目录，可重复 |
| `-D NAME[=VALUE]` | 宏，可重复 |
| `-L DIR` | 库目录，可重复 |
| `-l LIB` | 链接库，可重复 |

命令行模式不做增量构建，适合临时验证。如果当前目录有 `arche.ini`，会复用 `[*]` 的工具链和全局参数。

## 4. `--` 之后的参数

```bash
arche main.cpp -- -Wall -O2
arche --force app -- -DEXTRA=1
```

- 命令行模式：原样追加到编译器命令；
- 规则模式：追加到该目标的编译参数，也会写入 `compile_commands.json`；
- 链接参数请写在 `arche.ini` 的 `ldflags`。

## 5. 编译数据库

规则模式每次非 dry-run 构建写 `build/compile_commands.json`：

- `directory`、`file`、`output`、`arguments`；
- 包含全部目标的源文件，包括依赖目标；
- clangd 默认查找 `build/compile_commands.json`；
- 命令行模式不生成。

## 6. 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 成功 |
| `1` | 编译/链接失败 |
| `2` | 配置/参数/依赖图错误 |
| `130` | Ctrl+C 中断 |

## 7. 环境变量

| 变量 | 作用 |
| --- | --- |
| `CC` | 本机 C 编译器默认值；`[*] cc` 优先 |
| `CXX` | 本机 C++ 编译器默认值；`[*] cxx` 优先 |
| `AR` | 归档工具默认值 |
| `PATH` | 编译器、运行时 DLL/so 搜索 |

INI 里的变量用 `${NAME}`，环境变量用 `$ENV{NAME}`，两者互不覆盖。

## 8. 示例

```bash
# 构建全部
arche

# 只构建 app
arche app

# 强制重建 app
arche --force app

# 切换 NPU 适配器
arche --set NPU=npu_b --force

# 清理
arche --clean

# 查看目标
arche --list

# 直接编译
arche hello.cpp -o hello -Iinclude
```
