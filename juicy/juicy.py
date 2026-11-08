#!/usr/bin/env python3
import argparse
import ctypes
import os
import platform as host_platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

__version__ = "0.1.0"
BANNER = f"juicy {__version__} - 用平台参数生成并执行 cmake 命令的小工具"


class JuicyParser(argparse.ArgumentParser):
    def format_help(self):
        return BANNER + "\n\n" + super().format_help()

VS_PLATFORMS = {
    "vs2026": "Visual Studio 18 2026",
    "vs2022": "Visual Studio 17 2022",
    "vs2019": "Visual Studio 16 2019",
}
VS_ARCH = {
    "x64": "x64",
    "amd64": "x64",
    "x86": "Win32",
    "win32": "Win32",
    "arm": "ARM",
    "arm64": "ARM64",
    "aarch64": "ARM64",
}
VS_MAJOR = {name: generator.split()[2] for name, generator in VS_PLATFORMS.items()}
VS_BY_MAJOR = {major: name for name, major in VS_MAJOR.items()}
VCVARS_ARCH = {"x64": "x64", "Win32": "x86", "ARM": "arm", "ARM64": "arm64"}
PLATFORMS = (*VS_PLATFORMS, "android", "qnx", "mingw", "linux")
TOOLCHAIN_DIR = Path(__file__).resolve().parent / "toolchains"


def native_arch():
    machine = host_platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x64"
    if machine in ("aarch64", "arm64"):
        return "arm64"
    return machine

# NDK 只认这些 ABI; 左边是常用的架构别名.
ANDROID_ABI = {
    "arm64-v8a": "arm64-v8a",
    "armv8-a": "arm64-v8a",
    "arm64": "arm64-v8a",
    "aarch64": "arm64-v8a",
    "armeabi-v7a": "armeabi-v7a",
    "armv7-a": "armeabi-v7a",
    "armv7": "armeabi-v7a",
    "x86": "x86",
    "i686": "x86",
    "x86_64": "x86_64",
    "x64": "x86_64",
    "riscv64": "riscv64",
}
ANDROID_ABI_HINT = "arm64-v8a(armv8-a / arm64), armeabi-v7a(armv7-a), x86, x86_64, riscv64"
ANDROID_STL = ("c++_static", "c++_shared", "system", "none")

GENERAL_EPILOG = """\
平台:
  vs2026   Visual Studio 18 2026
  vs2022   Visual Studio 17 2022
  vs2019   Visual Studio 16 2019
  android  Android NDK(需要 -r 指定 NDK 根目录)
  qnx      QNX SDP(需要 -r 指定 SDP 根目录)
  mingw    MinGW-w64(-r 可选, 默认 C:/soft/toolchains/MinGW)
  linux    Linux native(-p 可省略)

未指定 -p 时, Windows 上自动选择已安装的最新 Visual Studio;
Linux/WSL 上使用 native 构建; 其他平台请显式指定 -p.

构建:
  python juicy.py build -B build    # 所有平台通用, 自动沿用 configure 环境

示例:
  python juicy.py -S . -B build               # Windows 最新 VS / Linux native
  python juicy.py -p linux -a x64 -S . -B build
  python juicy.py -p vs2022 -a x64 -S . -B build
  python juicy.py build -B build
  python juicy.py -p android -a armv8-a -r C:\\soft\\toolchains\\android-ndk\\r27c -S . -B build
  python juicy.py -p qnx -a aarch64 -r C:\\soft\\toolchains\\qnx800 -S . -B build-qnx
  python juicy.py -p mingw -a x86_64 -r C:\\soft\\toolchains\\MinGW -S . -B build-mingw
  python juicy.py -p android --help    # 查看 android 平台专有参数
"""


def build_epilog(platform):
    if platform == "android":
        return """\
示例:
  python juicy.py -p android -a armv8-a -r C:\\soft\\toolchains\\android-ndk\\r27c -S . -B build
  python juicy.py build -B build
"""
    if platform == "qnx":
        return """\
示例:
  python juicy.py -p qnx -a aarch64 -r C:\\soft\\toolchains\\qnx800 -S . -B build-qnx
  python juicy.py build -B build-qnx
"""
    if platform == "mingw":
        return """\
示例:
  python juicy.py -p mingw -a x86_64 -r C:\\soft\\toolchains\\MinGW -S . -B build-mingw
  python juicy.py build -B build-mingw
"""
    if platform == "linux":
        return """\
示例:
  python juicy.py -p linux -a x64 -S . -B build
  python juicy.py build -B build
"""
    if platform in VS_PLATFORMS:
        return f"""\
示例:
  python juicy.py -p {platform} -a x64 -S . -B build
  python juicy.py -p {platform} -G Ninja -S . -B build
  python juicy.py build -B build
"""
    return GENERAL_EPILOG


def explicit_platform(argv):
    """返回显式 -p 指定的平台; 没写或非法时返回 None."""
    for i, arg in enumerate(argv):
        if arg in ("-p", "--platform") and i + 1 < len(argv):
            value = argv[i + 1]
        elif arg.startswith("--platform="):
            value = arg.split("=", 1)[1]
        elif arg.startswith("-p") and not arg.startswith("--") and len(arg) > 2:
            value = arg[2:]
        else:
            continue
        return value if value in PLATFORMS else None
    return None


def fail(message):
    sys.exit(f"juicy: {message}")


def ensure_cmake():
    if shutil.which("cmake") is None:
        fail("找不到 cmake, 请确认它已安装并在 PATH 中")


def ensure_ninja(generator, args):
    if not generator or not generator.startswith("Ninja"):
        return
    if shutil.which("ninja") is not None:
        return
    if any("CMAKE_MAKE_PROGRAM" in str(arg) for arg in args):
        return
    fail(f"生成器 {generator} 需要 ninja 在 PATH 中, 请安装 ninja 或将其加入 PATH")


def default_generator(platform):
    if platform in ("android", "qnx", "mingw", "linux"):
        return "Ninja"
    if platform in VS_PLATFORMS:
        return VS_PLATFORMS[platform]
    return None


def effective_generator(args):
    return args.generator or default_generator(args.platform)


def build_parser(platform, full_help=False):
    android = platform == "android"
    vs = platform in VS_PLATFORMS
    if android:
        default_arch = "arm64-v8a"
        arch_help = f"Android ABI: {ANDROID_ABI_HINT}(默认 %(default)s)"
        generator_help = "CMake 生成器(默认 Ninja)"
        root_help = "NDK 根目录(必填), 例如 C:\\soft\\toolchains\\android-ndk\\r27c"
    elif platform == "qnx":
        default_arch = "aarch64"
        arch_help = "目标架构: aarch64(默认 %(default)s)"
        generator_help = "CMake 生成器(默认 Ninja)"
        root_help = "QNX SDP 根目录(必填), 例如 C:\\soft\\toolchains\\qnx800"
    elif platform == "mingw":
        default_arch = "x86_64"
        arch_help = "目标架构: x86_64(默认 %(default)s)"
        generator_help = "CMake 生成器(默认 Ninja)"
        root_help = "MinGW 根目录(可选, 默认 C:/soft/toolchains/MinGW)"
    elif platform == "linux":
        default_arch = native_arch()
        arch_help = "目标架构: 本机架构(默认 %(default)s)"
        generator_help = "CMake 生成器(默认 Ninja)"
        root_help = "仅 android/qnx/mingw 使用"
    elif vs:
        default_arch = "x64"
        arch_help = "目标架构: x64 / x86 / ARM / ARM64(默认 %(default)s)"
        generator_help = f"CMake 生成器(默认 {VS_PLATFORMS[platform]})"
        root_help = "仅 android/qnx/mingw 使用"
    else:
        default_arch = None
        arch_help = "目标架构(由平台决定)"
        generator_help = "CMake 生成器"
        root_help = "工具链根目录(android/qnx 必填, mingw 可选)"
    platform_help = "目标平台" if platform else "目标平台(Windows 上不指定时自动检测最新 Visual Studio)"

    if full_help:
        description = (
            "把平台参数翻译成 cmake config 命令, 打印并执行.\n"
            "未识别的参数会原样传给 cmake(例如 -DCMAKE_BUILD_TYPE=Release).\n"
            "VS 平台配 Ninja 等非 VS 生成器时, 会自动查找 VS 并加载 vcvarsall 环境.")
    else:
        description = (
            "把平台参数翻译成 cmake config 命令, 打印并执行.\n"
            "未识别的参数会原样传给 cmake(例如 -DCMAKE_BUILD_TYPE=Release).")

    parser = JuicyParser(
        prog="juicy.py",
        description=description,
        epilog=GENERAL_EPILOG if full_help else build_epilog(platform),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument(
        "-p", "--platform", choices=PLATFORMS, default=platform, help=platform_help)
    parser.add_argument("-V", "--version", action="version", version=f"juicy {__version__}")
    parser.add_argument(
        "-a", "--arch", metavar="ARCH", default=default_arch, help=arch_help)
    parser.add_argument(
        "-r", "--root", metavar="DIR", help=root_help,
        required=platform in ("android", "qnx"))
    parser.add_argument("-S", "--source", metavar="DIR", default=".", help="源码目录(默认 %(default)s)")
    parser.add_argument("-B", "--build", metavar="DIR", default="build", help="构建目录(默认 %(default)s)")
    parser.add_argument("-G", "--generator", metavar="GEN", help=generator_help)

    if android:
        group = parser.add_argument_group("android 平台参数")
        group.add_argument(
            "--api", metavar="LEVEL",
            help="ANDROID_PLATFORM(可选): API 级别, 如 21, android-35 或 latest; 默认取 NDK 最低版本")
        group.add_argument(
            "--stl", choices=ANDROID_STL,
            help="ANDROID_STL(可选, 默认 c++_static)")
        group.add_argument(
            "--arm-mode", choices=("thumb", "arm"),
            help="ANDROID_ARM_MODE(可选, 默认 thumb), 仅 armeabi-v7a 有效")
    return parser


def get_vs_installations():
    """用 VS Setup Configuration COM 枚举 (version, path).

    改编自 https://github.com/mjansson/vslocate(public domain).
    """
    if os.name != "nt":
        return []

    class InstanceVTable(ctypes.Structure):
        pass

    class Instance(ctypes.Structure):
        _fields_ = [("vtable", ctypes.POINTER(InstanceVTable))]

    class EnumVTable(ctypes.Structure):
        pass

    class EnumInstances(ctypes.Structure):
        _fields_ = [("vtable", ctypes.POINTER(EnumVTable))]

    class ConfigVTable(ctypes.Structure):
        pass

    class Configuration(ctypes.Structure):
        _fields_ = [("vtable", ctypes.POINTER(ConfigVTable))]

    path_fn = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.POINTER(Instance), ctypes.POINTER(ctypes.c_wchar_p))
    version_fn = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.POINTER(Instance), ctypes.POINTER(ctypes.c_wchar_p))
    next_fn = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.POINTER(EnumInstances), ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(Instance)), ctypes.POINTER(ctypes.c_int))
    enum_fn = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.POINTER(Configuration),
        ctypes.POINTER(ctypes.POINTER(EnumInstances)))
    get_config_fn = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.POINTER(ctypes.POINTER(Configuration)), ctypes.c_void_p)

    InstanceVTable._fields_ = [
        ("QueryInterface", ctypes.c_void_p), ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p), ("GetInstanceId", ctypes.c_void_p),
        ("GetInstallDate", ctypes.c_void_p), ("GetInstallationName", ctypes.c_void_p),
        ("GetInstallationPath", path_fn), ("GetInstallationVersion", version_fn),
    ]
    EnumVTable._fields_ = [
        ("QueryInterface", ctypes.c_void_p), ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p), ("Next", next_fn),
    ]
    ConfigVTable._fields_ = [
        ("QueryInterface", ctypes.c_void_p), ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p), ("EnumInstances", enum_fn),
    ]

    dll_path = os.path.expandvars(
        r"$ProgramData\Microsoft\VisualStudio\Setup\x64"
        r"\Microsoft.VisualStudio.Setup.Configuration.Native.dll")
    try:
        dll = ctypes.WinDLL(dll_path)
    except OSError:
        return []

    get_config = get_config_fn(("GetSetupConfiguration", dll))
    config = ctypes.POINTER(Configuration)()
    if get_config(ctypes.byref(config), None) != 0:
        return []

    enum = ctypes.POINTER(EnumInstances)()
    if config.contents.vtable.contents.EnumInstances(config, ctypes.byref(enum)) != 0:
        return []

    installations = []
    item = ctypes.POINTER(Instance)()
    fetched = ctypes.c_int()
    while True:
        if enum.contents.vtable.contents.Next(
                enum, 1, ctypes.byref(item), ctypes.byref(fetched)) != 0 or not fetched.value:
            break
        version = ctypes.c_wchar_p()
        path = ctypes.c_wchar_p()
        if item.contents.vtable.contents.GetInstallationVersion(item, ctypes.byref(version)) != 0:
            continue
        if item.contents.vtable.contents.GetInstallationPath(item, ctypes.byref(path)) != 0:
            continue
        installations.append((version.value, path.value))
    return installations


def version_key(text):
    return tuple(int(part) for part in text.split(".") if part.isdigit())


def detect_platform():
    """Windows 选最新 VS; Linux/WSL 用 native; 其他平台返回 None."""
    if os.name != "nt":
        return "linux" if sys.platform.startswith("linux") else None
    if "WSL_DISTRO_NAME" in os.environ:
        return None
    candidates = []
    for version, path in get_vs_installations():
        if not version:
            continue
        platform = VS_BY_MAJOR.get(version.split(".")[0])
        if platform is None:
            continue
        vcvars = Path(path) / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
        if vcvars.is_file():
            candidates.append((version_key(version), platform))
    return max(candidates)[1] if candidates else None


def find_vs(platform):
    """找到指定 VS 大版本中最高版本的 vcvarsall.bat."""
    major = VS_MAJOR[platform]
    installs = [
        (version, path) for version, path in get_vs_installations()
        if version and version.split(".")[0] == major
    ]
    installs.sort(key=lambda item: version_key(item[0]), reverse=True)
    for version, path in installs:
        vcvars = Path(path) / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
        if vcvars.is_file():
            return version, vcvars
    return None


def _env_from_lines(lines):
    env = {key.upper(): value for key, value in os.environ.items()}
    for line in lines:
        key, sep, value = line.partition("=")
        if sep and key:
            env[key.upper()] = value
    return env


def vcvars_env(vcvars, arch, version):
    """执行 vcvarsall 并返回完整环境."""
    result = subprocess.run(
        f'call "{vcvars}" {arch} >nul && set',
        shell=True, capture_output=True, text=True, errors="replace",
    )
    if result.returncode != 0:
        print(f"juicy: 加载 VS 环境失败({vcvars} {arch}), 直接在现有环境中运行 cmake.",
              file=sys.stderr)
        return None

    print(f"juicy: 使用 Visual Studio {version} 的环境: {vcvars.parents[3]}", file=sys.stderr)
    return _env_from_lines(result.stdout.splitlines())


def qnx_env(root):
    """执行 qnxsdp-env.bat/.sh 并返回完整环境."""
    if os.name == "nt":
        script = root / "qnxsdp-env.bat"
        if not script.is_file():
            print(f"juicy: 找不到 {script}", file=sys.stderr)
            return None
        result = subprocess.run(
            f'call "{script}" >nul && set',
            shell=True, capture_output=True, text=True, errors="replace",
        )
        lines = result.stdout.splitlines()
    else:
        script = root / "qnxsdp-env.sh"
        if not script.is_file():
            print(f"juicy: 找不到 {script}", file=sys.stderr)
            return None
        result = subprocess.run(
            ["bash", "-c", f'source "{script}" >/dev/null && env -0'],
            capture_output=True, text=True, errors="replace",
        )
        lines = result.stdout.split("\0")

    if result.returncode != 0:
        print(f"juicy: 加载 QNX 环境失败({script}), 直接在现有环境中运行 cmake.",
              file=sys.stderr)
        return None
    print(f"juicy: 使用 QNX SDP 环境: {root}", file=sys.stderr)
    return _env_from_lines(lines)


def msvc_env(platform, arch):
    """按 -p/-a 找 VS 并加载 vcvarsall 环境; 找不到时返回 None."""
    found = find_vs(platform)
    if found is None:
        print(f"juicy: 未找到 Visual Studio {VS_MAJOR[platform]}.x 的 vcvarsall.bat, "
              "直接在现有环境中运行 cmake.", file=sys.stderr)
        return None
    version, vcvars = found
    vc_arch = VCVARS_ARCH.get(VS_ARCH.get(arch, arch), arch)
    return vcvars_env(vcvars, vc_arch, version)


def read_cache(build_dir):
    cache = Path(build_dir) / "CMakeCache.txt"
    if not cache.is_file():
        fail(f"找不到 {cache}, 请先用 juicy.py 配置, 或用 -B 指定正确的构建目录")
    values = {}
    for line in cache.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith(("#", "//")) or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.split(":", 1)[0]] = value
    return values


def build_env(build_dir):
    """从 CMakeCache.txt 还原构建需要的 VS/QNX 环境."""
    cache = read_cache(build_dir)
    toolchain_root = cache.get("JUICY_TOOLCHAIN_ROOT", "")
    if not toolchain_root:
        compiler = Path(cache.get("CMAKE_C_COMPILER", ""))
        if compiler.name.lower().startswith("nto") and len(compiler.parents) > 5:
            toolchain_root = str(compiler.parents[5])
    if toolchain_root:
        root = Path(toolchain_root)
        if (root / "qnxsdp-env.bat").is_file() or (root / "qnxsdp-env.sh").is_file():
            return qnx_env(root)
    if cache.get("CMAKE_GENERATOR", "").startswith("Visual Studio"):
        return None
    compiler = Path(cache.get("CMAKE_CXX_COMPILER") or cache.get("CMAKE_C_COMPILER", ""))
    for version, root in get_vs_installations():
        root = Path(root)
        vcvars = root / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
        if vcvars.is_file() and compiler.is_relative_to(root):
            arch = compiler.parent.name.lower()
            return vcvars_env(vcvars, VCVARS_ARCH.get(arch, arch), version)
    if compiler.name.lower() in ("cl.exe", "clang-cl.exe"):
        print("juicy: 未能从 build 目录还原 VS 环境, 直接在现有环境中构建.", file=sys.stderr)
    return None


def make_cmd(args, extra):
    arch = args.arch.lower()
    env = None
    if args.platform == "android":
        if not args.root:
            fail("android 平台需要用 -r 指定 NDK 根目录")
        root = Path(args.root).expanduser().resolve()
        ndk_toolchain = root / "build" / "cmake" / "android.toolchain.cmake"
        if not ndk_toolchain.is_file():
            fail(f"找不到 NDK 工具链文件: {ndk_toolchain}\n"
                 r"请用 -r 指定 NDK 根目录, 例如 -r C:\soft\toolchains\android-ndk\r27c")
        toolchain = TOOLCHAIN_DIR / "android-ndk.cmake"
        if not toolchain.is_file():
            fail(f"找不到 Android toolchain 文件: {toolchain}")
        abi = ANDROID_ABI.get(arch)
        if abi is None:
            fail(f"未知 Android ABI: {args.arch}, 可选: {ANDROID_ABI_HINT}")
        cmd = [
            "cmake", "-S", args.source, "-B", args.build,
            "-G", effective_generator(args),
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
            f"-DJUICY_TOOLCHAIN_ROOT={root}",
            f"-DANDROID_ABI={abi}",
        ]
        if args.api:
            cmd.append(f"-DANDROID_PLATFORM={args.api}")
        if args.stl:
            cmd.append(f"-DANDROID_STL={args.stl}")
        if args.arm_mode:
            cmd.append(f"-DANDROID_ARM_MODE={args.arm_mode}")
    elif args.platform == "qnx":
        if not args.root:
            fail("qnx 平台需要用 -r 指定 QNX SDP 根目录")
        if arch not in ("aarch64", "arm64"):
            fail(f"QNX 目前只支持 aarch64, 不支持 {args.arch}")
        root = Path(args.root).expanduser().resolve()
        toolchain = TOOLCHAIN_DIR / "qnx-aarch64.cmake"
        if not toolchain.is_file():
            fail(f"找不到 QNX toolchain 文件: {toolchain}")
        env = qnx_env(root)
        if env is None:
            fail(f"无法加载 QNX 环境: {root}")
        cmd = [
            "cmake", "-S", args.source, "-B", args.build,
            "-G", effective_generator(args),
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
            f"-DJUICY_TOOLCHAIN_ROOT={root}",
        ]
    elif args.platform == "mingw":
        if arch not in ("x86_64", "x64", "amd64"):
            fail(f"MinGW 目前只支持 x86_64, 不支持 {args.arch}")
        if not args.root and os.name != "nt":
            fail("Linux 上 -p mingw 需要用 -r 指定 MinGW 根目录")
        toolchain = TOOLCHAIN_DIR / "mingw-x86_64.cmake"
        if not toolchain.is_file():
            fail(f"找不到 MinGW toolchain 文件: {toolchain}")
        cmd = [
            "cmake", "-S", args.source, "-B", args.build,
            "-G", effective_generator(args),
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
        ]
        if args.root:
            root = Path(args.root).expanduser().resolve()
            cmd.append(f"-DJUICY_TOOLCHAIN_ROOT={root}")
    elif args.platform == "linux":
        if os.name == "nt" or not sys.platform.startswith("linux"):
            fail("linux 平台只能在 Linux/WSL 上使用")
        if args.root:
            fail("-r 仅用于 android/qnx/mingw 平台")
        if arch in ("x64", "x86_64", "amd64"):
            arch = "x64"
        elif arch in ("arm64", "aarch64"):
            arch = "arm64"
        if arch != native_arch():
            fail(f"linux 平台目前只支持 native 构建, 当前主机是 {native_arch()}")
        cmd = [
            "cmake", "-S", args.source, "-B", args.build,
            "-G", effective_generator(args),
        ]
    else:
        if os.name != "nt" or "WSL_DISTRO_NAME" in os.environ:
            fail("vs2026/vs2022/vs2019 平台只能在 Windows 上使用")
        if args.root:
            fail("-r 仅用于 android/qnx/mingw 平台")
        generator = effective_generator(args)
        cmd = ["cmake", "-S", args.source, "-B", args.build, "-G", generator]
        if generator.startswith("Visual Studio"):
            cmd += ["-A", VS_ARCH.get(arch, args.arch)]
        else:
            env = msvc_env(args.platform, arch)
    return cmd + extra, env


def run(cmd, env=None):
    ensure_cmake()
    if "-G" in cmd:
        ensure_ninja(cmd[cmd.index("-G") + 1], cmd)
    line = subprocess.list2cmdline(cmd) if os.name == "nt" else shlex.join(cmd)
    print(f"[juicy.py] running cmake command: {line}", flush=True)
    try:
        return subprocess.call(cmd, env=env)
    except FileNotFoundError:
        fail("找不到 cmake, 请确认它已安装并在 PATH 中")
    except KeyboardInterrupt:
        return 130


def build_main(argv):
    parser = JuicyParser(
        prog="juicy.py build",
        description="构建已有的 build 目录; 从 CMakeCache.txt 自动还原 VS/QNX 环境(如需要).",
        epilog="示例:\n"
        "  python juicy.py build -B build\n"
        "  python juicy.py build -B build -j 8 --target hello",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument(
        "-B", "--build-dir", metavar="DIR", default="build",
        help="构建目录(默认 %(default)s)")
    parser.add_argument("-V", "--version", action="version", version=f"juicy {__version__}")
    args, extra = parser.parse_known_args(argv)
    return run(["cmake", "--build", args.build_dir] + extra, build_env(args.build_dir))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "build":
        return build_main(argv[1:])
    explicit = explicit_platform(argv)
    platform = explicit or detect_platform()
    if not argv:
        build_parser(platform, full_help=True).print_help()
        return 0
    parser = build_parser(platform, full_help=explicit is None)
    args, extra = parser.parse_known_args(argv)
    if args.platform is None:
        parser.error("未指定 -p, 且未检测到 Visual Studio; 请用 -p 指定平台")
    ensure_cmake()
    ensure_ninja(effective_generator(args), extra)
    cmd, env = make_cmd(args, extra)
    return run(cmd, env)


if __name__ == "__main__":
    sys.exit(main())
