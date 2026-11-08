# 01 · 命令行模式：编译单个源文件

这个目录**没有** `arche.ini`，演示最轻量的用法：直接把源文件交给 `arche.py`。

## Windows

```bat
python ..\..\arche.py hello.cpp
hello.exe
```

## Linux

```bash
python3 ../../arche.py hello.cpp
./hello
```

输出：

```text
hello from arche
```

## 常用变体

```bash
# 指定输出文件名
python3 ../../arche.py hello.cpp -o greet

# 打开优化并传递额外编译参数（-- 之后原样交给编译器）
python3 ../../arche.py hello.cpp -o hello_o2 -- -O2
```

Windows 下把命令中的 `python3` 换成 `python`，`./hello` 换成 `hello.exe`。

## 说明

- 命令行模式直接在源文件旁边生成可执行文件，不做增量构建，适合临时验证代码。
- 多个源文件也可以一起编译：
  `arche hello.cpp util.cpp -o hello`。
- 该模式会根据扩展名选择 C 或 C++ 编译器，但**不支持**在同一次调用里混合 C 和 C++；
  混合语言请用规则模式（见 `../02-static-lib`）。
