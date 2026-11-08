#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arche: 轻量级 C/C++ 构建工具（make + Makefile 的简化替代）。

配置写在 arche.ini：
  [*]                全局设置和工具链
  [target]           目标（exe/static/shared）

工具链：
  auto               Windows 用 MSVC；Linux 用 GCC（默认）
  msvc / gcc / clang 显式本机工具链
  android-ndk        用 Android NDK 交叉编译

用法：
  arche                    构建全部目标
  arche app                构建 app 及其 requires
  arche main.cpp           临时编译源文件
  arche clean [target]     清理
  arche list               列出目标
"""

from __future__ import annotations

import argparse
import configparser
import ctypes
import difflib
import glob as globlib
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

VERSION = "0.4.0"
IS_WINDOWS = os.name == "nt"

GLOBAL_KEYS = {
    "toolchain", "cxx", "cc", "vs", "arch", "ndk", "api", "abi", "stl",
    "build_dir",
    "std", "config", "jobs", "flags", "cflags", "cxxflags", "ldflags",
    "include_dirs", "lib_dirs", "libs", "defines", "header_conflict_check",
}
TARGET_KEYS = {
    "type", "sources", "requires", "private_requires", "include_dirs", "lib_dirs",
    "libs", "defines", "flags", "cflags", "cxxflags", "ldflags", "copy_dlls",
    "links",
}
PATCH_KEYS = TARGET_KEYS - {"type"}
ALIASES = {"crate_type": "type", "kind": "type", "deps": "requires"}
TYPE_ALIASES = {
    "exe": "exe", "executable": "exe", "app": "exe", "binary": "exe",
    "static": "static", "staticlib": "static", "lib": "static",
    "shared": "shared", "sharedlib": "shared", "dll": "shared",
    "interface": "interface", "header": "interface",
    "header_only": "interface", "header-only": "interface",
}
ANDROID_ABIS = {
    "arm64-v8a": "aarch64-linux-android",
    "armeabi-v7a": "armv7a-linux-androideabi",
    "x86": "i686-linux-android",
    "x86_64": "x86_64-linux-android",
}


class ArcheError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


class BuildError(Exception):
    pass


def eprint(*args):
    print(*args, file=sys.stderr)


def decode(data: bytes) -> str:
    for enc in ("utf-8", "mbcs" if IS_WINDOWS else "utf-8"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


def fmt_cmd(argv: Sequence[object]) -> str:
    args = [str(a) for a in argv]
    return subprocess.list2cmdline(args) if IS_WINDOWS else shlex.join(args)


def dedup(items):
    seen, out = set(), []
    for item in items:
        key = str(item) if isinstance(item, Path) else item
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def split_tokens(value: str, comma: bool = False) -> List[str]:
    tokens, cur, quote = [], [], None
    for ch in value:
        if quote:
            if ch == quote:
                quote = None
            else:
                cur.append(ch)
        elif ch in "\"'":
            quote = ch
        elif ch in " \t\r\n" or (comma and ch == ","):
            if cur:
                tokens.append("".join(cur))
                cur = []
        else:
            cur.append(ch)
    if quote:
        raise ArcheError(f"配置值中引号未闭合: {value!r}")
    if cur:
        tokens.append("".join(cur))
    return tokens


_INC_RE = re.compile(r'^[ \t]*#[ \t]*include[ \t]*([<"])([^>"]+)[>"]', re.M)

_VAR_RE = re.compile(
    r"\$ENV\{([A-Za-z_][A-Za-z0-9_]*)\}|\$\{([A-Za-z_][A-Za-z0-9_]*)\}",
    re.IGNORECASE,
)


def _ref(match):
    return (True, match.group(1)) if match.group(1) else (False, match.group(2))


def expand_vars(value: str, where: str, variables: Dict[str, str]) -> str:
    """${NAME} 优先取 [*] 的 var.NAME，其次环境变量；都没有则报错。"""
    missing = []

    def repl(m):
        is_env, name = _ref(m)
        if is_env:
            env = os.environ.get(name)
            if env is not None:
                return env
        else:
            key = name.upper()
            if key in variables:
                return variables[key]
        missing.append(m.group(0))
        return m.group(0)

    text = _VAR_RE.sub(repl, str(value))
    if missing:
        raise ArcheError(
            f"{where} 引用了未定义的变量: {', '.join(dedup(missing))}"
            "（环境变量请写成 $ENV{NAME}）")
    return text


def resolve_variables(raw: Dict[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    stack: List[str] = []

    def resolve(name: str) -> str:
        if name in out:
            return out[name]
        if name in stack:
            i = stack.index(name)
            raise ArcheError(f"[*] 变量循环引用: {' -> '.join(stack[i:] + [name])}")
        stack.append(name)
        missing = []

        def repl(m):
            is_env, name = _ref(m)
            if is_env:
                env = os.environ.get(name)
                if env is not None:
                    return env
            else:
                ref = name.upper()
                if ref in raw:
                    return resolve(ref)
                if ref in out:
                    return out[ref]
            missing.append(m.group(0))
            return m.group(0)

        text = _VAR_RE.sub(repl, raw[name])
        stack.pop()
        if missing:
            raise ArcheError(
                f"[*] 变量 {name} 引用了未定义的变量: {', '.join(dedup(missing))}"
            )
        out[name] = text
        return text

    for name in raw:
        resolve(name)
    return out


def expand_path(value: str, base: Path, where: str, variables: Dict[str, str]) -> Path:
    text = os.path.expanduser(expand_vars(value, where, variables))
    path = Path(text)
    if not path.is_absolute():
        path = base / path
    return Path(os.path.abspath(str(path)))


def is_cxx(path: Path) -> bool:
    return path.suffix.lower() in (".cpp", ".cc", ".cxx", ".c++", ".cp")


def is_c(path: Path) -> bool:
    return path.suffix.lower() == ".c"


# --------------------------------------------------------------------------- #
# Visual Studio 发现（COM Setup Configuration，参考 vslocate.py）
# --------------------------------------------------------------------------- #


def _com_vs():
    """用 VS Setup Configuration COM 枚举 (version, path)。

    改编自 juicy.py / mjansson/vslocate：只保留用到的 vtable 方法。
    """
    if not IS_WINDOWS:
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

    result = []
    item = ctypes.POINTER(Instance)()
    fetched = ctypes.c_int()
    while True:
        if enum.contents.vtable.contents.Next(
                enum, 1, ctypes.byref(item), ctypes.byref(fetched)) != 0 or not fetched.value:
            break
        version = ctypes.c_wchar_p()
        path = ctypes.c_wchar_p()
        if item.contents.vtable.contents.GetInstallationVersion(
                item, ctypes.byref(version)) != 0:
            continue
        if item.contents.vtable.contents.GetInstallationPath(
                item, ctypes.byref(path)) != 0:
            continue
        if version.value and path.value:
            result.append((version.value, path.value))
    return result


_VS_CACHE: Optional[List[dict]] = None


def discover_vs() -> List[dict]:
    global _VS_CACHE
    if _VS_CACHE is None:
        merged = {}
        for version, path in _com_vs():
            install = Path(path)
            vcvars = install / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
            merged[os.path.normcase(str(install))] = {
                "version": version,
                "path": str(install),
                "vcvars": str(vcvars) if vcvars.is_file() else None,
            }
        _VS_CACHE = list(merged.values())
    return _VS_CACHE


def _vkey(version: str):
    return tuple(int(x) for x in version.split(".") if x.isdigit())


def _match_vs(version: str, selector: str) -> bool:
    years = {"2019": 16, "2022": 17, "2026": 18}
    if selector not in years:
        raise ArcheError(
            "vs 只支持 2019/2022/2026；2022 会匹配所有 17.x，包括 Preview")
    return version.split(".")[0] == str(years[selector])


def find_vcvars(vs: Optional[str], arch: str) -> dict:
    if arch not in ("x64", "x86", "arm64", "arm"):
        raise ArcheError(f"不支持的 arch: {arch!r}")
    available = [i for i in discover_vs() if i.get("vcvars")]
    if vs:
        available = [i for i in available if _match_vs(i["version"], vs)]
        if not available:
            raise ArcheError(f"没有找到匹配 vs={vs} 的 Visual Studio C++ 工具集")
    if not available:
        raise ArcheError(
            "没有找到可用的 Visual Studio C++ 工具集。\n"
            "请安装“使用 C++ 的桌面开发”工作负载，或用 arche --list-vs 查看。")
    available.sort(key=lambda i: _vkey(i["version"]), reverse=True)
    return available[0]


def load_vcvars(vcvars: str, arch: str):
    cmd = f'chcp 65001 >nul && call "{vcvars}" {arch} >nul && set'
    proc = subprocess.run(cmd, shell=True, capture_output=True)
    if proc.returncode != 0:
        raise ArcheError(f"vcvarsall.bat 执行失败:\n{decode(proc.stdout)[-1500:]}")
    env = {k.upper(): v for k, v in os.environ.items()}
    for line in decode(proc.stdout).splitlines():
        if "=" in line and not line.startswith("="):
            key, value = line.split("=", 1)
            env[key.upper()] = value
    cl = shutil.which("cl.exe", path=env.get("PATH", ""))
    if not cl:
        raise ArcheError("vcvarsall.bat 执行后找不到 cl.exe")
    bindir = Path(cl).parent
    return env, cl, str(bindir / "link.exe"), str(bindir / "lib.exe")


def list_vs() -> None:
    instances = discover_vs()
    if not instances:
        print("未检测到 Visual Studio。")
        return
    instances.sort(key=lambda i: _vkey(i["version"]), reverse=True)
    print(f"{'版本':<22}{'状态':<10}安装路径")
    for i in instances:
        status = "可用" if i["vcvars"] else "缺少 C++"
        print(f"{i['version']:<22}{status:<10}{i['path']}")


# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #


@dataclass
class Config:
    root: Path
    ini: Path
    toolchain: str = "auto"
    cxx: Optional[str] = None
    cc: Optional[str] = None
    vs: Optional[str] = None
    arch: str = "x64"
    ndk: Optional[Path] = None
    api: int = 21
    abi: str = "arm64-v8a"
    stl: str = "c++_static"
    std: Optional[str] = "c++17"
    config: str = "none"
    build_dir: Optional[Path] = None
    jobs: int = 0
    flags: List[str] = field(default_factory=list)
    cflags: List[str] = field(default_factory=list)
    cxxflags: List[str] = field(default_factory=list)
    ldflags: List[str] = field(default_factory=list)
    include_dirs: List[Path] = field(default_factory=list)
    lib_dirs: List[Path] = field(default_factory=list)
    libs: List[str] = field(default_factory=list)
    defines: List[str] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, bool] = field(default_factory=dict)
    choices: Dict[str, str] = field(default_factory=dict)
    choice_values: Dict[str, List[str]] = field(default_factory=dict)
    header_conflict_check: str = "error"


@dataclass
class Target:
    name: str
    type: str
    sources: List[Path]
    requires: List[str]
    include_dirs: List[Path]
    lib_dirs: List[Path]
    libs: List[str]
    defines: List[str]
    flags: List[str]
    cflags: List[str]
    cxxflags: List[str]
    ldflags: List[str]
    copy_dlls: List[Path]
    links: List[str]
    private_requires: List[str]
    artifact: Optional[Path] = None
    import_lib: Optional[Path] = None
    pdb: Optional[Path] = None
    obj_dir: Optional[Path] = None
    obj_paths: List[Path] = field(default_factory=list)
    depfile_paths: List[Path] = field(default_factory=list)
    includes: List[Path] = field(default_factory=list)
    public_includes: List[Path] = field(default_factory=list)
    link_targets: List["Target"] = field(default_factory=list)
    all_lib_dirs: List[Path] = field(default_factory=list)
    all_libs: List[str] = field(default_factory=list)
    all_flags: List[str] = field(default_factory=list)
    all_cflags: List[str] = field(default_factory=list)
    all_cxxflags: List[str] = field(default_factory=list)
    all_ldflags: List[str] = field(default_factory=list)
    all_defines: List[str] = field(default_factory=list)
    uses_cxx: bool = False


def _raw(cp: configparser.ConfigParser, section: str, allowed: Set[str],
         global_section: bool = False) -> Dict[str, str]:
    out = {}
    for key in cp.options(section):
        if global_section and (key.startswith("var.") or key.startswith("option.")
                               or key.startswith("choice.")):
            continue
        canonical = ALIASES.get(key, key)
        if canonical not in allowed:
            close = difflib.get_close_matches(canonical, sorted(allowed), n=1)
            hint = f"；是不是 {close[0]}？" if close else ""
            raise ArcheError(f"[{section}] 未知选项 {key!r}{hint}")
        if canonical in out:
            raise ArcheError(f"[{section}] 选项 {key!r} 重复")
        out[canonical] = cp.get(section, key)
    return out


def _list(raw: Dict[str, str], key: str, comma: bool = True) -> List[str]:
    return split_tokens(raw[key], comma) if key in raw else []


def _std(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return None if value.lower() in ("", "none") else value


def _variables(cp, section, overrides=None):
    raw = {}
    if section:
        for key in cp.options(section):
            if key.startswith("var."):
                name = key[4:].strip()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                    raise ArcheError(f"[*] 变量名不合法: {key!r}")
                raw[name.upper()] = cp.get(section, key)
    for name, value in (overrides or {}).items():
        raw[name.upper()] = value
    return resolve_variables(raw)


def _bool(value, where):
    text = value.strip().lower()
    if text in ("on", "1", "true", "yes"):
        return True
    if text in ("off", "0", "false", "no"):
        return False
    raise ArcheError(f"{where} 需要 on/off: {value!r}")


def _controls(cp, section, cfg, overrides):
    options, choices, values = {}, {}, {}
    if section:
        for key in cp.options(section):
            if key.startswith("option."):
                name = key[7:].strip().upper()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                    raise ArcheError(f"[*] option 名不合法: {key!r}")
                options[name] = _bool(cp.get(section, key), f"[*] {key}")
            elif key.startswith("choice."):
                rest = key[7:].strip()
                if rest.lower().endswith(".values"):
                    name = rest[:-7].strip().upper()
                    vals = split_tokens(cp.get(section, key), comma=True)
                    if not vals:
                        raise ArcheError(f"[*] {key} 不能为空")
                    values[name] = vals
                else:
                    choices[rest.upper()] = cp.get(section, key).strip()
    for name in values:
        if name not in choices:
            raise ArcheError(f"[*] choice.{name} 缺少当前值")
        if choices[name] not in values[name]:
            raise ArcheError(
                f"[*] choice.{name}={choices[name]!r} 不在 {values[name]} 中")
    for name in choices:
        if name not in values:
            raise ArcheError(f"[*] choice.{name} 缺少 choice.{name}.values")
    both = set(options) & set(choices)
    if both:
        raise ArcheError(f"[*] 不能同时定义 option/choice: {', '.join(both)}")
    var_names = {key[4:].upper() for key in (cp.options(section) if section else [])
                 if key.startswith("var.")}
    var_over = {}
    for name, value in overrides.items():
        key = name.upper()
        if key in options:
            options[key] = _bool(value, f"--set {name}")
        elif key in choices:
            if value not in values[key]:
                raise ArcheError(f"--set {name}={value!r} 不在 {values[key]} 中")
            choices[key] = value
        elif key in var_names:
            var_over[key] = value
        else:
            raise ArcheError(f"--set 未知变量/option/choice: {name}")
    cfg.options, cfg.choices, cfg.choice_values = options, choices, values
    return var_over


def _parse_global(cp, section, root, ini, overrides) -> Config:
    raw = _raw(cp, section, GLOBAL_KEYS, True) if section else {}
    cfg = Config(root=root, ini=ini)
    var_over = _controls(cp, section, cfg, overrides)
    cfg.variables = _variables(cp, section, var_over)
    if "toolchain" in raw:
        cfg.toolchain = raw["toolchain"].strip().lower()
        if cfg.toolchain not in ("auto", "msvc", "gcc", "clang", "android-ndk"):
            raise ArcheError("[*] toolchain 只能是 auto/msvc/gcc/clang/android-ndk")
    cfg.cxx = raw.get("cxx", "").strip() or None
    cfg.cc = raw.get("cc", "").strip() or None
    cfg.vs = raw.get("vs", "").strip() or None
    cfg.arch = raw.get("arch", "x64").strip().lower()
    if cfg.arch not in ("x64", "x86", "arm64", "arm"):
        raise ArcheError("[*] arch 只能是 x64/x86/arm64/arm")
    if "ndk" in raw:
        cfg.ndk = expand_path(raw["ndk"], root, "[*] ndk", cfg.variables)
    if "api" in raw:
        try:
            cfg.api = int(raw["api"].strip())
        except ValueError:
            raise ArcheError("[*] api 需要整数")
        if cfg.api < 1:
            raise ArcheError("[*] api 必须大于 0")
    if "abi" in raw:
        cfg.abi = raw["abi"].strip()
        if cfg.abi not in ANDROID_ABIS:
            raise ArcheError(f"[*] abi 只能是 {', '.join(ANDROID_ABIS)}")
    if "stl" in raw:
        cfg.stl = raw["stl"].strip().lower()
        if cfg.stl not in ("c++_shared", "c++_static", "none"):
            raise ArcheError("[*] stl 只能是 c++_shared/c++_static/none")
        if cfg.toolchain != "android-ndk":
            raise ArcheError("[*] stl 只用于 toolchain = android-ndk")
    if "std" in raw:
        cfg.std = _std(raw["std"])
    if "config" in raw:
        cfg.config = raw["config"].strip().lower()
        if cfg.config not in ("none", "debug", "release"):
            raise ArcheError("[*] config 只能是 none/debug/release")
    if "build_dir" in raw:
        if not raw["build_dir"].strip():
            raise ArcheError("[*] build_dir 不能为空")
        cfg.build_dir = expand_path(
            raw["build_dir"], root, "[*] build_dir", cfg.variables)
    else:
        cfg.build_dir = root / "build"
    if "header_conflict_check" in raw:
        cfg.header_conflict_check = raw["header_conflict_check"].strip().lower()
        if cfg.header_conflict_check not in ("error", "warn", "off"):
            raise ArcheError("[*] header_conflict_check 只能是 error/warn/off")
    if "jobs" in raw:
        try:
            cfg.jobs = int(raw["jobs"].strip())
        except ValueError:
            raise ArcheError("[*] jobs 需要整数")
        if cfg.jobs < 0:
            raise ArcheError("[*] jobs 不能是负数")
    cfg.flags = _list(raw, "flags", False)
    cfg.cflags = _list(raw, "cflags", False)
    cfg.cxxflags = _list(raw, "cxxflags", False)
    cfg.ldflags = _list(raw, "ldflags", False)
    cfg.defines = _list(raw, "defines", False)
    cfg.include_dirs = [
        expand_path(x, root, "[*] include_dirs", cfg.variables)
        for x in _list(raw, "include_dirs")
    ]
    cfg.lib_dirs = [
        expand_path(x, root, "[*] lib_dirs", cfg.variables)
        for x in _list(raw, "lib_dirs")
    ]
    cfg.libs = [expand_vars(x, "libs", cfg.variables) for x in _list(raw, "libs")]
    return cfg


def _sources(patterns: List[str], root: Path, variables: Dict[str, str]) -> List[Path]:
    result = []
    for pattern in patterns:
        wildcard = any(c in pattern for c in "*?[")
        path = expand_path(pattern, root, "sources", variables)
        if wildcard:
            matches = sorted(Path(x) for x in globlib.glob(str(path), recursive=True)
                             if Path(x).is_file())
            if not matches:
                raise ArcheError(f"sources 通配符没有匹配: {pattern}")
            result.extend(matches)
        elif not path.is_file():
            raise ArcheError(f"源文件不存在: {pattern}")
        else:
            result.append(path)
    return dedup(result)


def _parse_target(cp, section, root, variables) -> Target:
    name = section.strip()
    if not name or any(c in name for c in '/\\:*?"<>|'):
        raise ArcheError(f"目标名不合法: {section!r}")
    raw = _raw(cp, section, TARGET_KEYS)
    typ = raw.get("type", "exe").strip().lower()
    if typ not in TYPE_ALIASES:
        raise ArcheError(f"[{name}] type 只能是 exe/static/shared")
    patterns = _list(raw, "sources")
    if not patterns and TYPE_ALIASES[typ] != "interface":
        raise ArcheError(f"[{name}] 缺少 sources")
    requires = dedup(_list(raw, "requires"))
    private_requires = dedup(_list(raw, "private_requires"))
    links = dedup(_list(raw, "links"))
    groups = (set(requires), set(private_requires), set(links))
    overlap = (groups[0] & groups[1]) | (groups[0] & groups[2]) | (groups[1] & groups[2])
    if overlap:
        raise ArcheError(
            f"[{name}] 同一个依赖不能重复出现在 requires/private_requires/links: "
            f"{', '.join(overlap)}")
    return Target(
        name=name,
        type=TYPE_ALIASES[typ],
        sources=_sources(patterns, root, variables) if patterns else [],
        requires=requires,
        private_requires=private_requires,
        include_dirs=[
            expand_path(x, root, f"[{name}] include_dirs", variables)
            for x in _list(raw, "include_dirs")
        ],
        lib_dirs=[
            expand_path(x, root, f"[{name}] lib_dirs", variables)
            for x in _list(raw, "lib_dirs")
        ],
        libs=[expand_vars(x, "libs", variables) for x in _list(raw, "libs")],
        defines=_list(raw, "defines", False),
        flags=_list(raw, "flags", False),
        cflags=_list(raw, "cflags", False),
        cxxflags=_list(raw, "cxxflags", False),
        ldflags=_list(raw, "ldflags", False),
        copy_dlls=[expand_path(x, root, f"[{name}] copy_dlls", variables)
                   for x in _list(raw, "copy_dlls")],
        links=links,
    )


def _condition(text, cfg):
    text = text.strip()
    if text.startswith("!"):
        name = text[1:].strip().upper()
        if name not in cfg.options:
            raise ArcheError(f"补丁条件引用了未定义的 option: {name}")
        return not cfg.options[name]
    if "!=" in text:
        name, value = (x.strip() for x in text.split("!=", 1))
        name = name.upper()
        if name not in cfg.choices:
            raise ArcheError(f"补丁条件引用了未定义的 choice: {name}")
        return cfg.choices[name] != value
    if "=" in text:
        name, value = (x.strip() for x in text.split("=", 1))
        name = name.upper()
        if name not in cfg.choices:
            raise ArcheError(f"补丁条件引用了未定义的 choice: {name}")
        return cfg.choices[name] == value
    name = text.upper()
    if name in cfg.options:
        return cfg.options[name]
    if name in cfg.choices:
        raise ArcheError(f"choice 条件需要 NAME=value: {text}")
    raise ArcheError(f"补丁条件引用了未定义的 option: {name}")


def _check_deps(t):
    groups = (set(t.requires), set(t.private_requires), set(t.links))
    overlap = (groups[0] & groups[1]) | (groups[0] & groups[2]) | (groups[1] & groups[2])
    if overlap:
        raise ArcheError(
            f"[{t.name}] 同一个依赖不能重复出现在 requires/private_requires/links: "
            f"{', '.join(overlap)}")


def _apply_patch(t, cp, section, root, variables):
    raw = _raw(cp, section, PATCH_KEYS)
    t.sources = dedup(t.sources + _sources(_list(raw, "sources"), root, variables))
    t.include_dirs = dedup(t.include_dirs + [
        expand_path(x, root, f"[{section}] include_dirs", variables)
        for x in _list(raw, "include_dirs")])
    t.lib_dirs = dedup(t.lib_dirs + [
        expand_path(x, root, f"[{section}] lib_dirs", variables)
        for x in _list(raw, "lib_dirs")])
    t.copy_dlls = dedup(t.copy_dlls + [
        expand_path(x, root, f"[{section}] copy_dlls", variables)
        for x in _list(raw, "copy_dlls")])
    t.libs = dedup(t.libs + [expand_vars(x, "libs", variables)
                             for x in _list(raw, "libs")])
    t.defines = dedup(t.defines + _list(raw, "defines", False))
    t.flags = dedup(t.flags + _list(raw, "flags", False))
    t.cflags = dedup(t.cflags + _list(raw, "cflags", False))
    t.cxxflags = dedup(t.cxxflags + _list(raw, "cxxflags", False))
    t.ldflags = dedup(t.ldflags + _list(raw, "ldflags", False))
    t.requires = dedup(t.requires + _list(raw, "requires"))
    t.private_requires = dedup(t.private_requires + _list(raw, "private_requires"))
    t.links = dedup(t.links + _list(raw, "links"))
    _check_deps(t)


def _load(ini: Path, jobs: Optional[int], overrides,
          build_dir: Optional[str] = None) -> Tuple[Config, Dict[str, Target]]:
    cp = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        cp.read(ini, encoding="utf-8-sig")
    except (configparser.Error, OSError) as exc:
        raise ArcheError(f"读取 {ini.name} 失败: {exc}")
    if cp.defaults():
        raise ArcheError("[DEFAULT] 不支持，请把全局设置写在 [*]")
    globals_ = [s for s in cp.sections() if s == "*"]
    if len(globals_) > 1:
        raise ArcheError("只能有一个 [*] 节")
    section = globals_[0] if globals_ else None
    if section:
        bad = [k for k in cp.options(section)
               if k in ("sources", "type", "requires")]
        if bad:
            raise ArcheError("[*] 是全局节，不能写 sources/type/requires")
    cfg = _parse_global(cp, section, ini.parent, ini, overrides)
    if build_dir:
        cfg.build_dir = Path(build_dir).resolve()
    if jobs is not None:
        cfg.jobs = jobs
    targets, patches = {}, []
    for s in cp.sections():
        if s == "*":
            continue
        if ":" in s:
            patches.append(s)
            continue
        target = _parse_target(cp, s, ini.parent, cfg.variables)
        if target.name.lower() in {n.lower() for n in targets}:
            raise ArcheError(f"目标名重复: {target.name}")
        targets[target.name] = target
    for s in patches:
        name, cond = (x.strip() for x in s.split(":", 1))
        target = targets.get(name)
        if target is None:
            raise ArcheError(f"补丁段 [{s}] 引用了不存在的目标 [{name}]")
        if _condition(cond, cfg):
            _apply_patch(target, cp, s, ini.parent, cfg.variables)
    if not targets:
        raise ArcheError(f"{ini.name} 中没有目标")
    return cfg, targets


# --------------------------------------------------------------------------- #
# 工具链
# --------------------------------------------------------------------------- #


class Toolchain:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.env: Optional[Dict[str, str]] = None
        self.target_flag: List[str] = []
        self.stl_flags: List[str] = []
        self.obj_ext = ".obj" if IS_WINDOWS else ".o"
        tool = cfg.toolchain
        if tool == "auto":
            tool = "msvc" if IS_WINDOWS else "gcc"
        if tool == "android-ndk":
            self.kind = "android"
            self._setup_android()
        elif tool == "msvc":
            if not IS_WINDOWS:
                raise ArcheError("toolchain = msvc 只能在 Windows 上使用")
            self.kind = "msvc"
            self.exe_ext, self.static_prefix, self.static_ext = ".exe", "", ".lib"
            self.shared_prefix, self.shared_ext = "", ".dll"
            self.display = f"MSVC ({cfg.arch})"
        elif tool in ("gcc", "clang"):
            if IS_WINDOWS:
                raise ArcheError(
                    "Windows 上暂不支持 MinGW/gcc/clang；请用 toolchain = msvc，"
                    "或 toolchain = android-ndk")
            self.kind = "gnu"
            self.flavor = tool
            self.exe_ext, self.static_prefix, self.static_ext = "", "lib", ".a"
            self.shared_prefix, self.shared_ext = "lib", ".so"
            default_cxx = "clang++" if tool == "clang" else "g++"
            default_cc = "clang" if tool == "clang" else "gcc"
            self.cxx = shutil.which(cfg.cxx or os.environ.get("CXX") or default_cxx)
            self.cc = shutil.which(cfg.cc or os.environ.get("CC") or default_cc)
            self.ar = shutil.which(os.environ.get("AR", "ar"))
            self.display = "/".join(
                Path(p).name for p in (self.cxx, self.cc) if p) or tool
        else:
            raise ArcheError(f"未知 toolchain: {tool!r}")

    def _setup_android(self):
        cfg = self.cfg
        if not cfg.ndk:
            raise ArcheError("[*] toolchain=android-ndk 需要 ndk 路径")
        host = {"win32": "windows-x86_64", "linux": "linux-x86_64",
                "darwin": "darwin-x86_64"}.get(sys.platform)
        if not host:
            raise ArcheError(f"不支持的 Android 主机平台: {sys.platform}")
        bindir = cfg.ndk / "toolchains" / "llvm" / "prebuilt" / host / "bin"
        suffix = ".exe" if IS_WINDOWS else ""
        self.cxx = str(bindir / f"clang++{suffix}")
        self.cc = str(bindir / f"clang{suffix}")
        self.ar = str(bindir / f"llvm-ar{suffix}")
        if not Path(self.cxx).is_file():
            raise ArcheError(f"找不到 NDK clang++: {self.cxx}")
        triple = ANDROID_ABIS[cfg.abi]
        self.target_flag = [f"--target={triple}{cfg.api}"]
        self.stl_flags = {
            "c++_shared": [],
            "c++_static": ["-static-libstdc++"],
            "none": ["-nostdlib++"],
        }[cfg.stl]
        self.exe_ext, self.static_prefix, self.static_ext = "", "lib", ".a"
        self.shared_prefix, self.shared_ext = "lib", ".so"
        self.display = f"Android NDK {cfg.api} {cfg.abi}"

    def prepare(self):
        if self.kind == "msvc":
            info = find_vcvars(self.cfg.vs, self.cfg.arch)
            self.env, cl, link, lib = load_vcvars(info["vcvars"], self.cfg.arch)
            if self.cfg.cxx and Path(self.cfg.cxx).name.lower() not in ("cl", "cl.exe"):
                raise ArcheError("toolchain = msvc 时 cxx 必须是 cl.exe")
            self.cl, self.link, self.lib = cl, link, lib
            self.display = f"MSVC {info['version']} ({self.cfg.arch})"
        elif self.kind == "gnu":
            if not self.cxx and not self.cc:
                raise ArcheError("找不到 g++/gcc")
            if not self.ar:
                raise ArcheError("找不到 ar")
        else:
            if not Path(self.cxx).is_file() or not Path(self.ar).is_file():
                raise ArcheError("Android NDK 工具链不完整")

    def _flags(self, config: str) -> List[str]:
        if self.kind == "msvc":
            if config == "debug":
                return ["/Od", "/Z7"]
            return ["/O2", "/DNDEBUG"] if config == "release" else []
        if config == "debug":
            return ["-g", "-O0"]
        return ["-O2", "-DNDEBUG"] if config == "release" else []

    def _crt(self, config: str) -> str:
        return "/MDd" if config == "debug" else "/MD"

    def compile_cmd(self, t: Target, src: Path, obj: Path, dep: Path) -> List[str]:
        cxx = is_cxx(src)
        cfg = self.cfg
        if self.kind == "msvc":
            args = [self.cl, "/nologo", "/c", "/utf-8", self._crt(cfg.config)]
            args += self._flags(cfg.config)
            if cxx:
                args.append("/EHsc")
                if cfg.std:
                    args.append("/std:" + cfg.std.replace("gnu++", "c++"))
            args += ["/D" + d for d in t.all_defines]
            args += ["/I" + str(d) for d in t.includes]
            args += t.all_flags
            args += t.all_cxxflags if cxx else t.all_cflags
            args += ["/Fo" + str(obj), "/sourceDependencies", str(dep), str(src)]
            return args
        driver = self.cxx if cxx else self.cc
        if not driver:
            raise ArcheError(f"找不到编译 {src.name} 所需的编译器")
        args = [driver, *self.target_flag, "-c", "-o", str(obj),
                "-MMD", "-MF", str(dep)]
        if cxx and cfg.std:
            args.append("-std=" + cfg.std)
        args += self._flags(cfg.config)
        if t.type in ("static", "shared"):
            args.append("-fPIC")
        args += ["-D" + d for d in t.all_defines]
        args += ["-I" + str(d) for d in t.includes]
        args += t.all_flags
        args += t.all_cxxflags if cxx else t.all_cflags
        args.append(str(src))
        return args

    def _dep_arg(self, dep: Target) -> str:
        if self.kind == "msvc" and dep.type == "shared":
            return str(dep.import_lib or dep.artifact)
        return str(dep.artifact)

    def _lib_arg(self, lib: str) -> List[str]:
        if self.kind == "msvc":
            if lib.startswith(("/", "-")) or lib.lower().endswith((".lib", ".a")):
                return [lib]
            if "/" in lib or "\\" in lib:
                return [lib]
            return [lib + ".lib"]
        if lib.startswith("-"):
            return [lib]
        if "/" in lib or "\\" in lib or lib.lower().endswith(
                (".a", ".so", ".lib", ".dylib")):
            return [lib]
        return ["-l" + lib]

    def link_cmd(self, t: Target) -> List[str]:
        cfg = self.cfg
        if self.kind == "msvc":
            if t.type == "static":
                return [self.lib, "/nologo", "/OUT:" + str(t.artifact)] + [
                    str(p) for p in t.obj_paths]
            args = [self.link, "/nologo", "/INCREMENTAL:NO",
                    "/OUT:" + str(t.artifact)]
            if cfg.config == "debug":
                args += ["/DEBUG", "/PDB:" + str(t.pdb)]
            if t.type == "shared":
                args += ["/DLL", "/IMPLIB:" + str(t.import_lib)]
            args += [str(p) for p in t.obj_paths]
            args += [self._dep_arg(d) for d in t.link_targets
                     if d.type != "interface"]
            args += ["/LIBPATH:" + str(d) for d in t.all_lib_dirs]
            for lib in t.all_libs:
                args += self._lib_arg(lib)
            args += t.all_ldflags
            return args

        if t.type == "static":
            return [self.ar, "rcs", str(t.artifact)] + [
                str(p) for p in t.obj_paths]
        driver = self.cxx if t.uses_cxx else (self.cc or self.cxx)
        args = [driver, *self.target_flag]
        if t.type == "shared":
            args.append("-shared")
        args += ["-o", str(t.artifact)]
        args += [str(p) for p in t.obj_paths]
        args += [self._dep_arg(d) for d in t.link_targets
                 if d.type != "interface"]
        args += ["-L" + str(d) for d in t.all_lib_dirs]
        for lib in t.all_libs:
            args += self._lib_arg(lib)
        args += self.stl_flags
        if t.type == "shared":
            args.append("-Wl,-soname," + t.artifact.name)
        if t.type == "exe" and self.kind == "gnu":
            for d in dedup(x.artifact.parent for x in t.link_targets
                           if x.type == "shared"):
                args.append("-Wl,-rpath," + str(d))
        args += t.all_ldflags
        return args


# --------------------------------------------------------------------------- #
# 工程图
# --------------------------------------------------------------------------- #


class Project:
    def __init__(self, cfg: Config, targets: Dict[str, Target], tc: Toolchain):
        self.cfg, self.targets, self.tc = cfg, targets, tc
        self.build = cfg.build_dir
        self._finalize()

    def _finalize(self):
        tc = self.tc
        used = set()
        for t in self.targets.values():
            if t.type == "interface":
                continue
            out = self.build / t.name
            if t.type == "exe":
                artifact = out / (t.name + tc.exe_ext)
            elif t.type == "static":
                artifact = out / (tc.static_prefix + t.name + tc.static_ext)
            else:
                artifact = out / (tc.shared_prefix + t.name + tc.shared_ext)
            key = os.path.normcase(str(artifact))
            if key in used:
                raise ArcheError(f"产物路径冲突: {artifact}")
            used.add(key)
            t.artifact = artifact
            t.obj_dir = self.build / ".arche" / "obj" / t.name
            if t.type == "shared" and tc.kind == "msvc":
                t.import_lib = artifact.with_suffix(".lib")
            if tc.kind == "msvc" and t.type in ("exe", "shared"):
                t.pdb = artifact.with_suffix(".pdb")
            for src in t.sources:
                try:
                    rel = str(src.relative_to(self.cfg.root))
                except ValueError:
                    rel = "_external/" + hashlib.sha1(
                        str(src).encode()).hexdigest()[:10] + "/" + src.name
                obj = t.obj_dir / (rel.replace(":", "_") + tc.obj_ext)
                t.obj_paths.append(obj)
                t.depfile_paths.append(
                    Path(str(obj) + (".deps.json" if tc.kind == "msvc" else ".d")))
        self._resolve()

    def _order(self, roots: Optional[Sequence[str]]) -> List[Target]:
        names = list(roots) if roots else list(self.targets)
        for n in names:
            if n not in self.targets:
                close = difflib.get_close_matches(n, list(self.targets), n=1)
                hint = f"；是不是 {close[0]}？" if close else ""
                raise ArcheError(f"未知目标: {n}{hint}")
        result, state = [], {}

        def visit(n, stack):
            if state.get(n) == 2:
                return
            if state.get(n) == 1:
                i = stack.index(n)
                raise ArcheError(f"依赖环: {' -> '.join(stack[i:] + [n])}")
            state[n] = 1
            for req in (self.targets[n].requires + self.targets[n].private_requires
                        + self.targets[n].links):
                if req not in self.targets:
                    raise ArcheError(f"目标 [{n}] 依赖不存在的目标 [{req}]")
                visit(req, stack + [n])
            state[n] = 2
            result.append(self.targets[n])

        for n in names:
            visit(n, [])
        return result

    def _resolve(self):
        order = self._order(None)
        for t in order:
            t.uses_cxx = any(is_cxx(s) for s in t.sources) or any(
                r.uses_cxx for r in (self.targets[n]
                                     for n in t.requires + t.private_requires + t.links))
        for t in order:
            public = list(self.cfg.include_dirs) + list(t.include_dirs)
            for n in t.requires:
                public += self.targets[n].public_includes
            t.public_includes = dedup(public)
            inc = list(public)
            for n in t.private_requires:
                inc += self.targets[n].public_includes
            t.includes = dedup(inc)
            seen, deps = set(), []

            def add(n):
                if n in seen:
                    return
                seen.add(n)
                dep = self.targets[n]
                deps.append(dep)
                for x in dep.requires + dep.private_requires + dep.links:
                    add(x)

            for n in t.requires + t.private_requires + t.links:
                add(n)
            t.link_targets = deps
            dirs = list(self.cfg.lib_dirs) + list(t.lib_dirs)
            libs = list(t.libs)
            for d in deps:
                dirs += d.lib_dirs
                libs += d.libs
            t.all_lib_dirs = dedup(dirs)
            t.all_libs = dedup(libs + self.cfg.libs)
            t.all_flags = self.cfg.flags + t.flags
            t.all_cflags = self.cfg.cflags + t.cflags
            t.all_cxxflags = self.cfg.cxxflags + t.cxxflags
            t.all_ldflags = self.cfg.ldflags + t.ldflags
            t.all_defines = dedup(self.cfg.defines + t.defines)

    def check_headers(self, order):
        if self.cfg.header_conflict_check == "off":
            return
        problems = []
        for t in order:
            for src in t.sources:
                try:
                    text = src.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for m in _INC_RE.finditer(text):
                    quoted, name = m.group(1) == '"', m.group(2)
                    roots = ([src.parent] if quoted else []) + list(t.includes)
                    cands = dedup(r / name for r in dedup(roots) if (r / name).is_file())
                    if len(cands) > 1:
                        problems.append((t, src, name, cands))
        if not problems:
            return
        lines = []
        for t, src, name, cands in problems[:10]:
            lines.append(f"目标 [{t.name}] 的 {src} 中 #include \"{name}\" 有多个候选:")
            lines += [f"  - {c}" for c in cands]
        if len(problems) > 10:
            lines.append(f"  ... 另有 {len(problems) - 10} 处")
        msg = ("发现同名头文件冲突:\n" + "\n".join(lines) +
               "\n可以用下游目标的 links = <库> 只链接、不继承头文件目录，"
               "或设置 header_conflict_check = warn/off。")
        if self.cfg.header_conflict_check == "error":
            raise ArcheError(msg)
        eprint("[警告] " + msg)

    def order(self, roots):
        return self._order(roots)

    def clean(self, names):
        if names:
            self._order(names)
            for name in dict.fromkeys(names):
                t = self.targets[name]
                if t.obj_dir:
                    shutil.rmtree(t.obj_dir, ignore_errors=True)
                if t.artifact:
                    shutil.rmtree(t.artifact.parent, ignore_errors=True)
            return
        shutil.rmtree(self.build, ignore_errors=True)

    def _display(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.cfg.root))
        except ValueError:
            return str(path)

    def show(self):
        rows = [(t.name, t.type,
                 self._display(t.artifact) if t.artifact else "-",
                 ", ".join(t.requires + t.private_requires + t.links) or "-")
                for t in self.targets.values()]
        head = ("NAME", "TYPE", "OUTPUT", "REQUIRES/LINKS")
        widths = [max(len(r[i]) for r in rows + [head]) for i in range(4)]
        print(f"{head[0]:<{widths[0]}}  {head[1]:<{widths[1]}}  "
              f"{head[2]:<{widths[2]}}  {head[3]}")
        for r in rows:
            print(f"{r[0]:<{widths[0]}}  {r[1]:<{widths[1]}}  "
                  f"{r[2]:<{widths[2]}}  {r[3]}")


def load_project(ini: Path, jobs: Optional[int], overrides=None, build_dir=None) -> Project:
    cfg, targets = _load(ini, jobs, overrides or {}, build_dir)
    tc = Toolchain(cfg)
    return Project(cfg, targets, tc)


# --------------------------------------------------------------------------- #
# 增量构建
# --------------------------------------------------------------------------- #


@dataclass
class Job:
    target: Target
    source: Path
    obj: Path
    argv: List[str]


class Builder:
    def __init__(self, project: Project, args):
        self.p, self.cfg, self.tc = project, project.cfg, project.tc
        self.quiet, self.verbose, self.dry = args.quiet, args.verbose, args.dry_run
        self.force = args.force
        self.jobs = max(1, args.jobs if args.jobs and args.jobs > 0 else
                        self.cfg.jobs or min(16, os.cpu_count() or 4))
        self.compiled, self.dirty = set(), set()
        self.rebuilt, self.archived, self.linked = set(), set(), set()
        self.start = 0.0

    def run(self, roots) -> int:
        order = self.p.order(roots)
        forced = set(t.name for t in order) if self.force else set()
        if self.force and roots:
            forced = set(roots)
        self.tc.prepare()
        self.start = time.time()
        if not self.quiet:
            print(f"arche {VERSION} · {self.tc.display} · {self.cfg.config}"
                  f" · jobs={self.jobs}")
        self.p.check_headers(order)
        if not self.dry:
            self._write_db(order)
        jobs = []
        for t in order:
            for src, obj, dep in zip(t.sources, t.obj_paths, t.depfile_paths):
                argv = self.tc.compile_cmd(t, src, obj, dep)
                if t.name in forced or self._stale(src, obj, dep):
                    jobs.append(Job(t, src, obj, argv))
        self._compile(jobs)
        for t in order:
            if t.type == "interface":
                continue
            argv = self.tc.link_cmd(t)
            if t.name in forced or self._link_needed(t):
                self._link(t, argv)
        for t in order:
            if not self.dry and t.type not in ("static", "interface"):
                self._copy_dlls(t)
                self._copy_target_dlls(t)
        if not self.quiet:
            built = len(self.compiled)
            parts = []
            if built:
                parts.append(f"编译 {built} 个源文件")
            if self.archived:
                parts.append(f"归档 {len(self.archived)} 个静态库")
            if self.linked:
                parts.append(f"链接 {len(self.linked)} 个产物")
            print(f"构建完成：{'，'.join(parts) if parts else '全部目标已是最新'}"
                  f"，用时 {time.time() - self.start:.2f}s")
        return 0

    def _write_db(self, order):
        entries = []
        for t in order:
            for src, obj, dep in zip(t.sources, t.obj_paths, t.depfile_paths):
                entries.append({
                    "directory": str(self.cfg.root),
                    "file": str(src),
                    "output": str(obj),
                    "arguments": self.tc.compile_cmd(t, src, obj, dep),
                })
        path = self.p.build / "compile_commands.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        self._say(f"[DB] {self._rel(path)}")

    def _stale(self, src: Path, obj: Path, dep: Path) -> bool:
        if not obj.is_file():
            return True
        om = obj.stat().st_mtime
        if src.stat().st_mtime > om:
            return True
        deps = self._deps(dep)
        if deps is None:
            return True
        for d in deps:
            if not d.exists() or d.stat().st_mtime > om:
                return True
        return False

    def _deps(self, dep: Path) -> Optional[List[Path]]:
        if not dep.is_file():
            return None
        try:
            if self.tc.kind == "msvc":
                data = json.loads(dep.read_text(encoding="utf-8"))
                inc = data.get("Data", {}).get("Includes", [])
                return dedup(Path(x) if isinstance(x, str) else Path(x["Source"])
                             for x in inc)
            text = dep.read_text(encoding="utf-8", errors="replace")
            text = text.replace("\\\r\n", " ").replace("\\\n", " ")
            m = re.search(r":(?=\s)", text)
            if not m:
                return None
            words, cur = [], []
            i = 0
            rest = text[m.end():]
            while i < len(rest):
                ch = rest[i]
                if ch == "\\" and i + 1 < len(rest) and rest[i + 1] in " #\\":
                    cur.append(rest[i + 1])
                    i += 2
                elif ch.isspace():
                    if cur:
                        words.append("".join(cur))
                        cur = []
                    i += 1
                else:
                    cur.append(ch)
                    i += 1
            if cur:
                words.append("".join(cur))
            return [Path(w) if Path(w).is_absolute() else self.cfg.root / w
                    for w in dedup(words)]
        except (OSError, ValueError, KeyError):
            return None

    def _compile(self, jobs: List[Job]):
        if not jobs:
            return
        if self.jobs <= 1:
            for j in jobs:
                self._compile_one(j)
            return
        errors = []
        with ThreadPoolExecutor(max_workers=self.jobs) as pool:
            futures = {pool.submit(self._compile_one, j): j for j in jobs}
            for f in as_completed(futures):
                try:
                    f.result()
                except CancelledError:
                    continue
                except Exception as exc:
                    errors.append(str(exc))
                    for other in futures:
                        other.cancel()
        if errors:
            raise BuildError(errors[0] + (f"\n另有 {len(errors)-1} 个编译失败"
                                          if len(errors) > 1 else ""))

    def _compile_one(self, j: Job):
        if self.verbose or self.dry:
            self._say(f"  $ {fmt_cmd(j.argv)}")
        if self.dry:
            self.compiled.add(str(j.source))
            self.dirty.add(j.target.name)
            self._say(f"[CC] {j.target.name}: {self._rel(j.source)}")
            return
        j.obj.parent.mkdir(parents=True, exist_ok=True)
        self._run(j.argv, j.target.name, j.source)
        self.compiled.add(str(j.source))
        self.dirty.add(j.target.name)
        self._say(f"[CC] {j.target.name}: {self._rel(j.source)}")

    def _link_needed(self, t: Target) -> bool:
        if t.name in self.dirty or not t.artifact.is_file():
            return True
        am = t.artifact.stat().st_mtime
        for obj in t.obj_paths:
            if not obj.exists() or obj.stat().st_mtime > am:
                return True
        if t.type != "static":
            for d in t.link_targets:
                if d.name in self.rebuilt:
                    return True
                if d.artifact and (not d.artifact.exists()
                                   or d.artifact.stat().st_mtime > am):
                    return True
        return False

    def _link(self, t: Target, argv: List[str]):
        if self.verbose or self.dry:
            self._say(f"  $ {fmt_cmd(argv)}")
        tag = "[AR]" if t.type == "static" else "[LD]"
        if not self.dry:
            t.artifact.parent.mkdir(parents=True, exist_ok=True)
            self._run(argv, t.name, None)
            if t.type == "static":
                self.archived.add(t.name)
            else:
                self.linked.add(t.name)
        self.rebuilt.add(t.name)
        self._say(f"{tag} {t.name}: {self._rel(t.artifact)}")

    def _say(self, text):
        if not self.quiet:
            print(text)

    def _rel(self, path: Path):
        try:
            return path.relative_to(self.cfg.root)
        except ValueError:
            return path

    def _copy_target_dlls(self, t: Target):
        if not IS_WINDOWS or t.type in ("static", "interface") or not t.copy_dlls:
            return
        for pattern in t.copy_dlls:
            if pattern.is_dir():
                files = list(pattern.glob("*.dll"))
            elif any(c in str(pattern) for c in "*?["):
                files = [Path(x) for x in globlib.glob(str(pattern))
                         if Path(x).is_file()]
            elif pattern.is_file():
                files = [pattern]
            else:
                raise BuildError(f"copy_dlls 路径不存在: {pattern}")
            for src in files:
                dest = t.artifact.parent / src.name
                if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
                    shutil.copy2(src, dest)
                    self._say(f"[CP] {t.name}: {src.name}")

    def _copy_dlls(self, t: Target):
        if self.tc.kind != "msvc":
            return
        for d in t.link_targets:
            if d.type == "shared" and d.artifact.suffix.lower() == ".dll":
                dest = t.artifact.parent / d.artifact.name
                if dest != d.artifact:
                    shutil.copy2(d.artifact, dest)
        # MSVC AddressSanitizer 运行时 DLL 在 cl.exe 目录，复制到 exe 旁。
        flags = " ".join(t.all_flags + t.all_cflags + t.all_cxxflags + t.all_ldflags).lower()
        if "/fsanitize=address" in flags:
            dlls = list(Path(self.tc.cl).parent.glob("clang_rt.asan_dynamic*.dll"))
            if not dlls:
                eprint("[警告] 找不到 clang_rt.asan_dynamic*.dll，"
                       "请安装 VS 的 C++ AddressSanitizer 组件")
            for dll in dlls:
                dest = t.artifact.parent / dll.name
                if not dest.exists() or dll.stat().st_mtime > dest.stat().st_mtime:
                    shutil.copy2(dll, dest)
                    self._say(f"[CP] {t.name}: {dll.name}")

    def _run(self, argv: List[str], target: str, source: Optional[Path]):
        proc = subprocess.run(argv, cwd=str(self.cfg.root), env=self.tc.env,
                              capture_output=True)
        out = decode(proc.stdout) + decode(proc.stderr)
        if proc.returncode != 0:
            where = f"{target}: {source}" if source else target
            raise BuildError(
                f"目标 [{where}] 失败（退出码 {proc.returncode}）\n"
                f"  {fmt_cmd(argv)}\n{out.rstrip()}")
        return out


# --------------------------------------------------------------------------- #
# 命令行模式
# --------------------------------------------------------------------------- #


def _adhoc(args, sources: List[str], project: Optional[Project]) -> int:
    root = Path.cwd()
    if project:
        cfg, tc = project.cfg, project.tc
        inc = list(cfg.include_dirs)
        defines = list(cfg.defines)
        libdirs = list(cfg.lib_dirs)
        libs = list(cfg.libs)
        flags = list(cfg.flags)
    else:
        cfg = Config(root=root, ini=root / "arche.ini", jobs=args.jobs or 0)
        tc = Toolchain(cfg)
        inc, defines, libdirs, libs, flags = [], [], [], [], []
    files = _sources(sources, root, cfg.variables)
    if not files:
        raise ArcheError("临时编译需要至少一个源文件")
    cxx = any(is_cxx(p) for p in files)
    if not cxx and not all(is_c(p) for p in files):
        raise ArcheError("无法判断源文件语言（支持 .c/.cpp/.cc/.cxx）")
    if cxx and any(is_c(p) for p in files):
        raise ArcheError("命令行模式不支持混合 C/C++，请用 arche.ini")
    out = Path(args.output) if args.output else files[0].with_name(
        files[0].stem + tc.exe_ext)
    if not out.is_absolute():
        out = root / out
    if IS_WINDOWS and not out.suffix:
        out = out.with_name(out.name + ".exe")
    inc += [expand_path(p, root, "-I", cfg.variables) for p in args.includes]
    libdirs += [expand_path(p, root, "-L", cfg.variables) for p in args.lib_dirs]
    defines += args.defines
    flags += list(cfg.cxxflags) if cxx else list(cfg.cflags)
    libs += args.libs
    tc.prepare()
    if tc.kind == "msvc":
        argv = [tc.cl, "/nologo", "/utf-8", tc._crt(cfg.config)]
        argv += tc._flags(cfg.config)
        if cxx:
            argv.append("/EHsc")
            if cfg.std:
                argv.append("/std:" + cfg.std.replace("gnu++", "c++"))
        argv += ["/D" + d for d in defines]
        argv += ["/I" + str(d) for d in inc]
        argv += flags + args.extra
        argv += [str(p) for p in files]
        argv += ["/Fe" + str(out), "/link"]
        argv += ["/LIBPATH:" + str(d) for d in libdirs]
        for lib in libs:
            argv += tc._lib_arg(lib)
    else:
        argv = [tc.cxx if cxx else tc.cc, *tc.target_flag]
        if cxx and cfg.std:
            argv.append("-std=" + cfg.std)
        argv += tc._flags(cfg.config)
        argv += ["-D" + d for d in defines]
        argv += ["-I" + str(d) for d in inc]
        argv += flags + args.extra
        argv += [str(p) for p in files]
        argv += ["-o", str(out)]
        argv += tc.stl_flags
        argv += ["-L" + str(d) for d in libdirs]
        for lib in libs:
            argv += tc._lib_arg(lib)
    if args.verbose or args.dry_run:
        print(f"  $ {fmt_cmd(argv)}")
    if args.dry_run:
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(argv, cwd=str(root), env=tc.env, capture_output=True)
    text = decode(proc.stdout) + decode(proc.stderr)
    if proc.returncode != 0:
        raise BuildError(f"编译失败（退出码 {proc.returncode}）\n"
                         f"  {fmt_cmd(argv)}\n{text.rstrip()}")
    if not args.quiet:
        print(f"[EXE] {out}")
    return 0


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="arche", allow_abbrev=False,
        description="arche：轻量级 C/C++ 构建工具",
        epilog=("示例：\n  arche\n  arche app\n  arche main.cpp\n"
                "  arche --clean [目标]\n  arche --list\n  arche --list-vs"))
    p.add_argument("items", nargs="*", metavar="目标|源文件")
    p.add_argument("-S", "--source-dir", dest="directory")
    p.add_argument("-B", "--build-dir")
    p.add_argument("-f", "--file")
    p.add_argument("-j", "--jobs", type=int)
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("-q", "--quiet", action="store_true")
    p.add_argument("-n", "--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--set", dest="sets", action="append", default=[],
                   metavar="NAME=VALUE")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--clean", action="store_true")
    g.add_argument("--list", dest="list_targets", action="store_true")
    p.add_argument("--list-vs", action="store_true")
    p.add_argument("--version", action="version", version=f"arche {VERSION}")
    p.add_argument("-o", "--output")
    p.add_argument("-I", dest="includes", action="append", default=[])
    p.add_argument("-D", dest="defines", action="append", default=[])
    p.add_argument("-L", dest="lib_dirs", action="append", default=[])
    p.add_argument("-l", dest="libs", action="append", default=[])
    return p


def find_ini(explicit: Optional[str]) -> Optional[Path]:
    path = Path(explicit) if explicit else Path.cwd() / "arche.ini"
    if not path.is_file():
        if explicit:
            raise ArcheError(f"找不到 {path}")
        return None
    return path


def _parse_sets(items):
    result = {}
    for item in items:
        if "=" not in item:
            raise ArcheError(f"--set 需要 NAME=VALUE: {item!r}")
        name, value = item.split("=", 1)
        name = name.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ArcheError(f"--set 名称不合法: {name!r}")
        result[name] = value
    return result


def run(args) -> int:
    if args.verbose and args.quiet:
        raise ArcheError("-v 和 -q 不能同时使用")
    build_dir = Path(args.build_dir).resolve() if args.build_dir else None
    if args.directory:
        os.chdir(args.directory)
    if args.list_vs:
        list_vs()
        return 0
    items = list(args.items)
    ini = find_ini(args.file)
    overrides = _parse_sets(args.sets)
    if ini is None:
        if args.list_targets or args.clean:
            raise ArcheError("找不到 arche.ini")
        if overrides:
            raise ArcheError("--set 需要 arche.ini")
        if args.build_dir:
            raise ArcheError("-B/--build-dir 需要 arche.ini")
        if not items:
            raise ArcheError("请指定源文件，或提供 arche.ini")
        return _adhoc(args, items, None)
    project = load_project(ini, args.jobs, overrides, build_dir)
    if args.list_targets:
        if items:
            raise ArcheError("--list 不接受目标参数")
        project.show()
        return 0
    if args.clean:
        project.clean(items)
        return 0
    if args.output or args.includes or args.defines or args.lib_dirs or args.libs:
        if not items:
            raise ArcheError("临时编译选项需要至少一个源文件")
        if any(x in project.targets for x in items):
            raise ArcheError("临时编译选项不能用于 arche.ini 目标")
        return _adhoc(args, items, project)
    if not items:
        return Builder(project, args).run(None)
    targets, sources = [], []
    for item in items:
        if item in project.targets:
            targets.append(item)
        elif Path(item).is_file():
            path = Path(item).resolve()
            owner = next((t.name for t in project.targets.values()
                          if path in t.sources), None)
            if owner:
                targets.append(owner)
            else:
                sources.append(item)
        else:
            hint = {"list": "；查看目标请用 --list",
                    "clean": "；清理请用 --clean"}.get(item, "")
            raise ArcheError(f"未知目标/源文件: {item}{hint}")
    if targets and sources:
        raise ArcheError("不能同时构建目标和临时源文件")
    if sources:
        return _adhoc(args, sources, project)
    return Builder(project, args).run(targets)


def main(argv=None) -> int:
    if IS_WINDOWS:
        for s in (sys.stdout, sys.stderr):
            try:
                s.reconfigure(encoding="utf-8")
            except Exception:
                pass
    raw = list(sys.argv[1:] if argv is None else argv)
    extra = []
    if "--" in raw:
        i = raw.index("--")
        extra, raw = raw[i + 1:], raw[:i]
    args = parser().parse_args(raw)
    args.extra = extra
    try:
        return run(args)
    except ArcheError as exc:
        eprint(f"错误: {exc}")
        return exc.code
    except BuildError as exc:
        eprint(f"错误: {exc}")
        return 1
    except KeyboardInterrupt:
        eprint("已中断。")
        return 130


if __name__ == "__main__":
    sys.exit(main())
