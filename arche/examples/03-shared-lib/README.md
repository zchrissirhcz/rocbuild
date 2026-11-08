# 03 · 规则模式：动态库 + 可执行文件

演示 `type = shared` 以及可执行文件对动态库的依赖。

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
Hello, arche!
```

## 产物与运行时路径

Windows：

```text
build/
  greet/
    greet.dll
    greet.lib        # 导入库，供 app 链接
  app/
    app.exe
    greet.dll        # arche 自动复制，保证 app.exe 能直接运行
```

Linux：

```text
build/
  greet/
    libgreet.so
  app/
    app              # 已写入指向 build/greet 的 rpath
```

在 Linux 上可以用 `readelf -d build/app/app | grep -E 'RPATH|RUNPATH'` 检查 rpath。

## Windows 导出宏

Windows 的动态库需要显式导出符号。本示例用 `GREET_BUILD` 区分“构建库”和
“使用库”两种情况：

```cpp
#ifdef GREET_BUILD
#  define GREET_API __declspec(dllexport)
#else
#  define GREET_API __declspec(dllimport)
#endif
```

`greet` 目标定义 `GREET_API` 为 `dllexport`，`app` 看到的是 `dllimport`。

## 说明

- 动态库目标自动带 `-fPIC`（Linux/Android）。
- 可执行文件依赖动态库时自动添加 rpath（仅 Linux）。
- `--clean app` 只删除 app 的产物，不会删除 greet 的产物。
