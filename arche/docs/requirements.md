# arche 需求覆盖表

这份文档把会话中提出的需求逐条列出，并标注当前实现状态，方便其他人判断 arche
是否覆盖自己的场景。它不是用户手册；语法细节见
[`arche-ini.md`](arche-ini.md)、[`cli.md`](cli.md)、[`toolchains.md`](toolchains.md)。

状态说明：

| 状态 | 含义 |
| --- | --- |
| ✅ | 已实现并有测试/示例 |
| ⚠️ | 已实现但有限制，或未达到目标 |
| ❌ | 尚未实现 |
| ➖ | 明确不做/暂不支持 |

## 1. 总体定位

| # | 需求 | 状态 | 说明 |
| --- | --- | --- | --- |
| R1 | 轻量级替代 make + Makefile，用简单构建描述文件 | ✅ | 单文件 `arche.py` + `arche.ini` |
| R2 | 不像 CMake 那样必须 configure/生成工程 | ✅ | 直接读取 INI 构建 |
| R3 | 对简单工程直观，保留 `.pro` 那种“写路径就能编译”的感觉 | ✅ | `src`/`include_dirs`/`lib_dirs`/`libs` |
| R4 | 单文件工具，尽量少依赖 | ✅ | 只依赖 Python 3.9+ 标准库 |
| R5 | 代码规模控制（曾提出 1000 行目标） | ⚠️ | 当前约 1700 行；见第 9 节 |

## 2. 两种使用模式

| # | 需求 | 状态 | 说明 |
| --- | --- | --- | --- |
| R6 | 命令行直接编译单个源文件 | ✅ | `arche hello.cpp` |
| R7 | 命令行编译多个源文件、指定输出 | ✅ | `-o`，示例 `01-hello-cli` |
| R8 | 命令行支持头文件/宏/库目录/库 | ✅ | `-I`/`-D`/`-L`/`-l` |
| R9 | 通过 INI 定义目标并构建 | ✅ | 全部示例 |
| R10 | 无参数构建全部目标，或指定目标 | ✅ | `arche` / `arche app` |

## 3. 目标与依赖

| # | 需求 | 状态 | 说明 |
| --- | --- | --- | --- |
| R11 | 可执行文件目标 | ✅ | `type = exe` |
| R12 | 静态库目标 | ✅ | `type = static` |
| R13 | 动态库目标 | ✅ | `type = shared` |
| R14 | 目标间依赖，自动先构建依赖 | ✅ | `requires`，示例 `02-static-lib` |
| R15 | 静态库被可执行文件依赖并自动链接 | ✅ | 传递闭包，依赖者在前 |
| R16 | `requires` 跨目录/跨文件（中等工程） | ❌ | 需要 `subdirs`，见 R84 |
| R17 | 依赖的头文件目录自动传递 | ✅ | `include_dirs` 沿 requires 传递 |
| R18 | `lib_dirs`/`libs` 沿依赖传递 | ✅ | 传递闭包 |
| R19 | 检测循环依赖/缺失目标 | ✅ | 报错并给出链路 |
| R20 | 关键字 `requires`（旧名 `deps` 兼容） | ✅ | `deps` 为别名 |
| R21 | 用 `type` 指定目标类型，`crate_type` 兼容 | ✅ | `crate_type`/`kind` 别名 |
| R22 | header-only 库 | ✅ | `type = interface`；`header`/`header_only` 别名；示例 `07-header-only` |
| R23 | 目标名为 `build`/`arche`/`clean`/`list` 等不被保留 | ✅ | 无目标保留字；命令冲突用 `--clean`/`--list` |
| R23a | 下游可以只链接库、不继承其头文件目录 | ✅ | 下游写 `links = foo`；示例 `10-links` |
| R23b | 同名头文件冲突检测 | ✅ | 编译前扫描 `#include`；`header_conflict_check = error/warn/off`；示例 `10-links` |
| R23c | 库可以声明私有依赖，不把私有依赖头文件传给下游 | ✅ | 库写 `private_requires = cici`；示例 `11-private-requires` |

## 4. 源文件与配置语法

| # | 需求 | 状态 | 说明 |
| --- | --- | --- | --- |
| R24 | 多源文件 | ✅ | 示例 `02-static-lib` 每个目标两个源文件 |
| R25 | `sources` 支持逗号分隔 | ✅ | 示例和测试覆盖 |
| R26 | `sources` 支持空白/换行/通配符 | ✅ | `src/*.cpp`、`**` |
| R27 | 全局节用 `[*]`（EditorConfig 约定） | ✅ | `[*]` 不与目标名冲突 |
| R28 | `[build]` 不再占用目标名 | ✅ | 已改为 `[*]` |
| R29 | 路径相对各 INI 文件 | ✅ | 目标路径相对所在 INI |
| R30 | 路径含空格 | ✅ | 引号或变量值（变量值无需引号） |
| R31 | UTF-8/中文路径/中文注释 | ✅ | `utf-8-sig` 读取 |
| R32 | INI 内定义变量 | ✅ | `[*] var.NAME = ...` |
| R33 | 变量可引用变量/环境变量 | ✅ | 循环引用报错 |
| R34 | INI 变量不覆盖同名环境变量 | ✅ | `${NAME}` 只查 INI；`$ENV{NAME}` 只查环境 |
| R35 | 环境变量显式语法 | ✅ | `$ENV{NAME}`；示例 `08-env-vars` |
| R36 | 未定义变量报错并指出名字 | ✅ | 不把 `${X}` 当相对路径 |
| R36a | 布尔开关 option | ✅ | `option.NAME = off`；条件段 `[app:NAME]` |
| R36b | N 选 1 的 choice | ✅ | `choice.NAME` + `choice.NAME.values`；`[app:NAME=value]` |
| R36c | 条件补丁段 | ✅ | `[target:条件]` 追加 sources/defines/libs/requires 等；示例 `12-options` |
| R36d | 命令行覆盖 option/choice/var | ✅ | `--set NAME=VALUE`，不持久化 |

## 5. 工具链

| # | 需求 | 状态 | 说明 |
| --- | --- | --- | --- |
| R37 | 工具链在 `[*]` 配置，而不是命令行 | ✅ | `toolchain = auto/msvc/gcc/clang/android-ndk` |
| R38 | `auto` 有明确默认值 | ✅ | Windows→MSVC，Linux→GCC |
| R39 | Windows MSVC 自动发现 | ✅ | Setup Configuration COM，参考 `vslocate.py` |
| R40 | 不依赖 `vswhere.exe` | ✅ | 不调用 |
| R41 | 不假定 VS 装在 C 盘 | ✅ | COM 返回真实安装路径 |
| R42 | 选择 VS 版本/架构 | ✅ | `vs` 只接受 `2019`/`2022`/`2026`；`2022` 匹配 17.x（含 Preview）；`arch` 在 `[*]` |
| R43 | 列出 VS 安装 | ✅ | `arche --list-vs` |
| R44 | Linux g++/clang++ | ✅ | `toolchain = gcc`/`clang` |
| R45 | 显式本机工具链名，不用模糊的 `native` | ✅ | `auto`/`msvc`/`gcc`/`clang` |
| R46 | MinGW（Windows gcc） | ➖ | 暂不支持，会明确报错；配置名已预留 |
| R47 | macOS native | ➖ | 不支持 |
| R48 | Android NDK 交叉编译 | ✅ | `toolchain = android-ndk` + `ndk`/`api`/`abi`；示例 `05-android` |
| R49 | Android STL 选择 | ✅ | `stl = c++_static`（默认）/`c++_shared`/`none` |
| R50 | Android ABI 选择 | ✅ | `arm64-v8a`/`armeabi-v7a`/`x86`/`x86_64` |

## 6. 编译/链接参数

| # | 需求 | 状态 | 说明 |
| --- | --- | --- | --- |
| R51 | 编译参数与链接参数分开 | ✅ | `flags`/`cflags`/`cxxflags` vs `ldflags` |
| R52 | C 与 C++ 编译参数分开 | ✅ | `cflags` / `cxxflags`，`flags` 共用 |
| R53 | 目标级 flags 覆盖全局 flags | ✅ | 全局在前，目标在后 |
| R54 | ASan Windows/Linux 示例 | ✅ | 示例 `06-asan`；MSVC ASan DLL 自动复制 |
| R55 | `--` 透传编译器参数 | ✅ | 规则模式追加到编译；命令行模式原样传递 |
| R56 | debug/release 配置 | ✅ | `config = none/debug/release` |
| R57 | 指定 C++ 标准 | ✅ | `std = c++17` 等 |

## 7. 构建体验

| # | 需求 | 状态 | 说明 |
| --- | --- | --- | --- |
| R58 | 增量构建 | ✅ | 源文件/头文件时间戳；对象文件+头依赖 |
| R59 | 头文件变更触发重编 | ✅ | MSVC `/sourceDependencies`；GCC/Clang `-MMD` |
| R60 | 并行编译 | ✅ | `-j` / `jobs` |
| R61 | `--force` 强制重建 | ✅ | 只强制指定目标，不强制依赖 |
| R62 | `clean` 清理 | ✅ | 可只清理指定目标 |
| R63 | `list` 列出目标 | ✅ | 显示类型/产物/requires |
| R64 | `--dry-run` 只打印命令 | ✅ | 不写编译数据库 |
| R65 | `compile_commands.json` | ✅ | 自动生成到 `<build_dir>/`，供 clangd/IDE |
| R65a | 自定义构建目录 | ✅ | `[*] build_dir` / `-B DIR` |
| R65b | 指定源码目录 | ✅ | `-S DIR` |
| R66 | 复制 arche 构建的 DLL 依赖 | ✅ | Windows 自动复制 |
| R67 | 复制外部 SDK 的 DLL | ✅ | `copy_dlls`；示例 `09-copy-dlls` |
| R68 | 任意 post-build 脚本 | ➖ | 不做，避免 INI 变成脚本宿主；用声明式 `copy_dlls` |

## 8. 文档与示例

| # | 需求 | 状态 | 说明 |
| --- | --- | --- | --- |
| R69 | 专门的 INI 文档 | ✅ | [`arche-ini.md`](arche-ini.md) |
| R70 | 命令行文档 | ✅ | [`cli.md`](cli.md) |
| R71 | 工具链文档 | ✅ | [`toolchains.md`](toolchains.md) |
| R72 | 命令行模式示例 | ✅ | `examples/01-hello-cli` |
| R73 | 静态库 + 依赖 + 多源文件示例 | ✅ | `examples/02-static-lib` |
| R74 | 动态库示例 | ✅ | `examples/03-shared-lib` |
| R75 | OpenCL 示例，路径硬编码在 INI 变量 | ✅ | `examples/04-opencl` |
| R76 | 环境变量独立示例 | ✅ | `examples/08-env-vars` |
| R77 | Android 示例 | ✅ | `examples/05-android` |
| R78 | ASan / flags 示例 | ✅ | `examples/06-asan` |
| R79 | header-only 示例 | ✅ | `examples/07-header-only` |
| R80 | copy_dlls 示例 | ✅ | `examples/09-copy-dlls` |

## 9. 代码规模与取舍

| # | 需求/约束 | 状态 | 说明 |
| --- | --- | --- | --- |
| R81 | 1000 行以内 | ⚠️ | 当前约 1700 行（含约 160 行空行）；未达成 |
| R82 | 不以行数牺牲核心功能 | ✅ | COM 发现、Android、DB、ASan、copy_dlls 都是明确需求 |
| R83 | 可进一步压缩 | ⚠️ | 可压缩注释/空行、合并分支；严格 1000 需砍功能 |

当前行数构成（粗略）：

| 部分 | 约行数 |
| --- | --- |
| utils（分词/变量/路径） | 210 |
| VS COM 发现 | 200 |
| Config/INI 解析 | 250 |
| Toolchain（MSVC/GCC/Android） | 190 |
| Project 依赖图 | 130 |
| Builder（增量/并行/DB） | 230 |
| 命令行模式 | 80 |
| CLI | 120 |
| 空行 | 155 |

严格 1000 行至少需要放弃：头文件依赖、并行编译、命令行模式、compile_commands、
Android 或 COM 发现中的若干项。这与 R6/R48/R59/R60/R65 冲突，因此当前未强行压缩。

## 10. 明确暂缓

| # | 项目 | 状态 | 原因 |
| --- | --- | --- | --- |
| R84 | `subdirs` / `add_subdirectory` | ❌ | 中等工程需要；设计已定，尚未实现 |
| R85 | `project name` | ➖ | 暂时没有用途；目标名全局唯一 |
| R86 | 任意脚本/生成器/安装规则 | ➖ | 保持轻量，交给外部脚本/打包工具 |
| R87 | 预编译头、响应文件 | ➖ | 非轻量工程核心场景 |
| R88 | macOS native | ➖ | 当前重点 Windows/Linux/Android |
| R89 | MinGW | ➖ | Windows 上暂用 MSVC/Android；配置名已预留 |

## 11. 如何判断是否覆盖你的需求

1. 先看第 1–8 节是否有你的场景；
2. 需要多目录目标时看 R16/R84（当前未实现 `subdirs`）；
3. 需要 Windows DLL 部署时看 R66/R67 和 `examples/09-copy-dlls`；
4. 需要 Android 时看 R48–R50 和 `examples/05-android`；
5. 需要 IDE 跳转时看 R65 和 `build/compile_commands.json`；
6. 需要新增需求时，按同样格式补一行，并注明状态和文档/示例链接。
