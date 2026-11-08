# 示例目录

所有示例都只依赖 Python 标准库和本机 C/C++ 编译器。

| 目录 | 模式 | 演示内容 |
| --- | --- | --- |
| [01-hello-cli](01-hello-cli) | 命令行 | 直接编译单个/多个源文件，`-o`、`-I`、`-D`、`--` 透传 |
| [02-static-lib](02-static-lib) | 规则 | `type = static`、`requires`、多源文件（逗号/换行）、头文件目录自动传递、增量构建 |
| [03-shared-lib](03-shared-lib) | 规则 | `type = shared`、导入库、Windows DLL 复制、Linux rpath |
| [04-opencl](04-opencl) | 规则 | 在 `[*]` 里硬编码 OpenCL 路径变量，真实第三方库链接 |
| [05-android](05-android) | 规则 | Android NDK 交叉编译动态库 + 可执行文件 |
| [06-asan](06-asan) | 规则 | 分别设置编译 `flags` 和链接 `ldflags`，ASan 构建 |
| [07-header-only](07-header-only) | 规则 | `type = interface`，只传递 include 目录的 interface 目标 |
| [08-env-vars](08-env-vars) | 规则 | 显式使用环境变量 `$ENV{NAME}` |
| [09-copy-dlls](09-copy-dlls) | 规则 | `copy_dlls` 复制外部 SDK 的 DLL |
| [10-links](10-links) | 规则 | 下游用 `links` 只链接、不继承头文件；`header_conflict_check` 同名头文件报错 |
| [11-private-requires](11-private-requires) | 规则 | `private_requires`：foo 能看 cici，app 看不到 cici |
| [12-options](12-options) | 规则 | `option` / `choice` / `[target:条件]` 补丁段，OOP 与直接两种写法 |

## 运行方式

每个子目录都有自己的 `README.md`。进入对应目录后执行：

```bash
# Windows
python ..\..\arche.py

# Linux
python3 ../../arche.py
```

命令行示例不需要 `arche.ini`；其余示例在各自目录下已有 `arche.ini`。

构建产物默认位于各示例的 `build/` 目录，已经加入 `.gitignore`。
