# 09 · 复制外部 DLL

这个示例演示 `copy_dlls` 的真实场景：`app` 链接一个**外部**共享库 `vendor`，
但不像 `requires` 那样把它作为 arche 目标。因此 arche 不会自动复制 DLL，必须用
`copy_dlls` 声明。

## 目录

```text
09-copy-dlls/
  vendor/          # 先构建，产出 vendor.dll / vendor.lib
  app/             # 链接 vendor，但不 requires
```

## Windows

先构建 vendor：

```bat
cd vendor
python ..\..\..\arche.py
```

再构建 app：

```bat
cd ..\app
python ..\..\..\arche.py
build\app\app.exe
```

输出：

```text
vendor_value() = 99
```

`app` 的 `arche.ini`：

```ini
[app]
type = exe
sources = main.cpp
include_dirs = ../vendor/include
lib_dirs = ../vendor/build/vendor
libs = vendor
copy_dlls = ../vendor/build/vendor
```

- `lib_dirs` / `libs` 负责链接 `vendor.lib`；
- `copy_dlls` 把 `vendor.dll` 复制到 `build/app/`；
- 如果目标已是最新，`copy_dlls` 也会补齐缺失的 DLL。

## Linux

`copy_dlls` 仅 Windows 生效。Linux 下需要用 `LD_LIBRARY_PATH` 或 rpath：

```bash
cd vendor && python3 ../../../arche.py
cd ../app && python3 ../../../arche.py
LD_LIBRARY_PATH=../vendor/build/vendor ./build/app/app
```

## 什么时候需要它

- 链接第三方 SDK 的 DLL（OpenCL、CUDA、Qt 插件等）；
- 运行时的 DLL 不在 `PATH`/`System32`；
- 希望构建产物目录可以直接打包/运行。

arche 自己构建的共享库依赖已经会自动复制，不需要重复写 `copy_dlls`。
