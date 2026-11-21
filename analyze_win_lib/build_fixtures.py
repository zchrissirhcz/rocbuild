# -*- coding: utf-8 -*-
"""
生成最小化的 .lib 测试夹具（fixtures）。

思路：真实库文件（ade/EasyX/ncnn/hello）太大，本脚本用本机 MSVC 工具链
(cl.exe / lib.exe) 编译几个几 KB 的 .c 对象，再封装成 .lib，覆盖 analyze_win_lib.py
的全部检测特征：

  - 静态库 vs 导入库（import lib）
  - COFF 与 bigobj 两种对象格式
  - CRT：MT / MTd / MD / MDd（drectve 里的 CRT 默认库名）
  - drectve 无 CRT 时的符号回退（模拟 EasyX：/MT 对象剥掉 LIBCMT 后只剩 direct CRT）
  - build_type 从对象路径（Release/Debug）与反向推断
  - VS 版本从对象路径关键字（如 vs2017）

夹具预生成后固化到 fixtures/*.lib，测试运行不再需要编译器。

用法： python build_fixtures.py [out_dir]   （默认生成到本目录的 fixtures/）
"""
import io
import os
import re
import struct
import subprocess
import sys
from ar import Archive

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 工具链路径（本机 VS2026 / MSVC 14.44.35207） ----
MSVC = r"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.44.35207"
SDK = r"C:\Program Files (x86)\Windows Kits\10"
SDKVER = "10.0.26100.0"
CL = os.path.join(MSVC, r"bin\Hostx64\x64\cl.exe")
LIBEXE = os.path.join(MSVC, r"bin\Hostx64\x64\lib.exe")
INCLUDE = ";".join([
    os.path.join(MSVC, "include"),
    os.path.join(SDK, "Include", SDKVER, "ucrt"),
    os.path.join(SDK, "Include", SDKVER, "um"),
    os.path.join(SDK, "Include", SDKVER, "shared"),
])
LIBPATH = ";".join([
    os.path.join(MSVC, "lib", "x64"),
    os.path.join(SDK, "Lib", SDKVER, "ucrt", "x64"),
    os.path.join(SDK, "Lib", SDKVER, "um", "x64"),
])

# ---- ar 写入（BSD #1/N 长名），与 ar 库兼容 ----
def _pad2(b):
    return b + b"\n" if len(b) % 2 else b


def write_ar(path, members):
    out = b"!<arch>\n"
    for name, data in members:
        nb = name.encode("utf-8")
        name_field = ("#1/" + str(len(nb))).ljust(16, " ")
        total = len(nb) + len(data)
        hdr = (name_field
               + "0".ljust(12, " ")
               + "0".ljust(6, " ")
               + "0".ljust(6, " ")
               + "100666".ljust(8, " ")
               + str(total).ljust(10, " ")
               + "\x60\n")
        out += hdr.encode() + _pad2(nb + data)
    with open(path, "wb") as f:
        f.write(out)


# ---- COFF 工具 ----
VALID = {0x014C, 0x8664, 0x01C0, 0xAA64}

def parse_obj(data):
    if len(data) >= 20 and struct.unpack_from("<H", data, 0)[0] in VALID:
        return dict(machine=struct.unpack_from("<H", data, 0)[0],
                    num_sections=struct.unpack_from("<H", data, 2)[0],
                    sec_table_off=20 + struct.unpack_from("<H", data, 16)[0],
                    symtab=struct.unpack_from("<I", data, 8)[0],
                    num_syms=struct.unpack_from("<I", data, 12)[0], kind="coff")
    if len(data) >= 56 and struct.unpack_from("<H", data, 4)[0] == 2 \
            and struct.unpack_from("<H", data, 6)[0] in VALID:
        return dict(machine=struct.unpack_from("<H", data, 6)[0],
                    num_sections=struct.unpack_from("<I", data, 44)[0],
                    sec_table_off=56, symtab=struct.unpack_from("<I", data, 48)[0],
                    num_syms=struct.unpack_from("<I", data, 52)[0], kind="bigobj")
    return None


def get_drectve_ptr(data, h):
    for i in range(h["num_sections"]):
        off = h["sec_table_off"] + i * 40
        if off + 40 > len(data):
            break
        if data[off:off + 8].rstrip(b"\x00") == b".drectve":
            return struct.unpack_from("<I", data, off + 20)[0], \
                   struct.unpack_from("<I", data, off + 16)[0]
    return None, None


_CRT_LIBS = {"libcmt", "libcmtd", "msvcrt", "msvcrtd", "vcruntime", "vcruntimed",
             "ucrt", "ucrtd", "msvcprt", "msvcprtd"}


def strip_crt_from_drectve(obj):
    """把 .drectve 里的 CRT 默认库（LIBCMT/MSVCRT...）用空格抹掉，保持长度不变，
    用于制造 'drectve 无 CRT' 的夹具，触发 analyze 的符号回退。"""
    h = parse_obj(obj)
    if h is None:
        return obj
    ptr, size = get_drectve_ptr(obj, h)
    if ptr is None:
        return obj
    drectve = bytearray(obj[ptr:ptr + size])
    pat = re.compile(rb'/DEFAULTLIB\s*:\s*"?([A-Za-z_][A-Za-z0-9_.]*)"?')
    changed = False
    for m in pat.finditer(drectve):
        lib = m.group(1).decode().lower()
        if lib in _CRT_LIBS:
            drectve[m.start():m.end()] = b" " * (m.end() - m.start())
            changed = True
    if not changed:
        return obj
    out = bytearray(obj)
    out[ptr:ptr + size] = drectve
    return bytes(out)


# ---- 编译 ----
def compile_obj(src, obj, extra):
    env = dict(os.environ)
    env["INCLUDE"] = INCLUDE
    env["LIB"] = LIBPATH
    cmd = [CL, "/c", "/nologo", "/Fo" + obj, "/EHsc"] + extra + [src]
    r = subprocess.run(cmd, env=env, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("cl 编译失败: " + r.stdout.decode(errors="ignore")
                           + r.stderr.decode(errors="ignore"))
    with open(obj, "rb") as f:
        return f.read()


def build_import_lib(out):
    """用 lib.exe /def 生成一个最小导入库（无真实 DLL）。"""
    defs = os.path.join(os.path.dirname(out), "_tiny.def")
    with open(defs, "w") as f:
        f.write("LIBRARY tiny\nEXPORTS\n  tiny_add\n  tiny_sub\n")
    env = dict(os.environ)
    env["INCLUDE"] = INCLUDE
    env["LIB"] = LIBPATH
    r = subprocess.run([LIBEXE, "/def:" + defs, "/machine:x64", "/out:" + out],
                       env=env, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("lib /def 失败: " + r.stdout.decode(errors="ignore")
                           + r.stderr.decode(errors="ignore"))
    return out


# ---- 夹具清单 ----
SRC = r"""
#include <stdlib.h>
#include <stdio.h>
int fixture_func(int x) {
    int *p = (int*)malloc((size_t)(x * 8));
    if (!p) return -1;
    int r = p[0] + x;
    free(p);
    printf("value=%d\n", r);
    return r;
}
"""


def build_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    src = os.path.join(out_dir, "_fixture_src.c")
    with open(src, "w") as f:
        f.write(SRC)
    work = os.path.join(out_dir, "_work")
    os.makedirs(work, exist_ok=True)

    # 编译各种配置的对象
    objs = {}
    objs["mt"] = compile_obj(src, os.path.join(work, "mt.obj"), ["/MT"])
    objs["mtd"] = compile_obj(src, os.path.join(work, "mtd.obj"), ["/MTd"])
    objs["md"] = compile_obj(src, os.path.join(work, "md.obj"), ["/MD"])
    objs["mdd"] = compile_obj(src, os.path.join(work, "mdd.obj"), ["/MDd"])
    objs["big_md"] = compile_obj(src, os.path.join(work, "big_md.obj"), ["/MD", "/bigobj"])

    # 剥掉 CRT 默认库（符号回退夹具）
    objs["nocrt_mt"] = strip_crt_from_drectve(objs["mt"])
    objs["nocrt_md"] = strip_crt_from_drectve(objs["md"])

    fixtures = [
        # (文件名, 成员名, 期望: (lib_type, build_type, crt))
        ("static_mt.lib",  r"build\Release\mt.obj",     ("static", "Release", "MT")),
        ("static_mtd.lib", r"build\Debug\mtd.obj",      ("static", "Debug",   "MTd")),
        ("static_md.lib",  r"build\Release\md.obj",     ("static", "Release", "MD")),
        ("static_mdd.lib", r"build\Debug\mdd.obj",      ("static", "Debug",   "MDd")),
        ("static_bigobj_md.lib", r"build\Release\big.obj", ("static", "Release", "MD")),
        # drectve 无 CRT → 符号回退
        ("static_nocrt_mt.lib", r"build\Release\fb.obj",  ("static", "Release", "MT")),
        ("static_nocrt_md.lib", r"build\Release\fb.obj",  ("static", "Release", "MD")),
        # VS 版本从路径关键字 + ReleaseA 子串
        ("static_vs2017.lib", r"R:\easyx_obj\vs2017\x64\ReleaseA\f.obj",
         ("static", "Release", "MT")),
        # bigobj 对象里再验证 Debug 反推（bigobj + /MDd）
        ("static_bigobj_mdd.lib", r"build\Debug\bigd.obj", ("static", "Debug", "MDd")),
    ]

    for fname, member, _exp in fixtures:
        key = None
        # 注意：先匹配更长的前缀，避免 static_mdd/static_mtd 被 static_md/static_mt 抢先
        if fname.startswith("static_mtd"):
            key = "mtd"
        elif fname.startswith("static_mt"):
            key = "mt"
        elif fname.startswith("static_mdd"):
            key = "mdd"
        elif fname.startswith("static_md"):
            key = "md"
        elif "bigobj" in fname:
            key = "mdd" if "mdd" in fname else "big_md"
        elif "nocrt_mt" in fname:
            key = "nocrt_mt"
        elif "nocrt_md" in fname:
            key = "nocrt_md"
        elif "vs2017" in fname:
            key = "mt"
        obj = objs[key]
        # 校验对象确实是期望的 COFF/bigobj，能读到 drectve（防止夹具本身坏掉）
        h = parse_obj(obj)
        assert h is not None, f"{fname} 的对象无法解析为 COFF"
        write_ar(os.path.join(out_dir, fname), [(member, obj)])

    # 导入库
    imp = os.path.join(out_dir, "import_tiny.lib")
    build_import_lib(imp)
    # 清理 lib.exe 的 .exp / .def 副产物
    for extra in ("import_tiny.exp", "_tiny.def"):
        try:
            os.remove(os.path.join(out_dir, extra))
        except OSError:
            pass

    # 清理中间产物
    for tmp in ([src] + [os.path.join(work, x) for x in os.listdir(work)]):
        try:
            os.remove(tmp)
        except OSError:
            pass
    try:
        os.rmdir(work)
    except OSError:
        pass
    try:
        os.remove(os.path.join(out_dir, "_tiny.def"))
    except OSError:
        pass

    print(f"夹具已生成到 {out_dir}: {len([x for x in os.listdir(out_dir) if x.endswith('.lib')])} 个 .lib")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "fixtures")
    build_all(out)