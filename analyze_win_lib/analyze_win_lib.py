# -*- coding: utf-8 -*-
"""
实验脚本：分析 MSVC 编译的 .lib 库文件信息
  - 判断是 import lib（DLL 配套）还是静态库
  - 若是静态库：判定 VS 版本、Debug/Release、CRT (MT/MTd/MD/MDd)

方法：
  1. import lib vs 静态库：静态库成员是可解析的 COFF/bigobj .obj 文件；
     import lib 成员含 .idata 导入目录段，且成员名多为 *.dll。
  2. VS 版本：优先从 .debug$S 中 "\\MSVC\\<版本>\\include" 提取精确工具链版本；
     否则从 obj 路径关键字（vs2015/vs2017/vs2022...）推断。
  3. Debug/Release：从 obj 路径关键字（Debug/Release/RelWithDebInfo/MinSizeRel）推断，
     并可用 CRT 库的 'd' 后缀佐证。
  4. CRT (MT/MTd/MD/MDd)：
     a) 主信号：.drectve 中的 /DEFAULTLIB 与 /FAILIFMISMATCH:RuntimeLibrary
        - libcmt -> MT, libcmtd -> MTd
        - MSVCRT/msvcrt/vcruntime/ucrt/msvcprt -> MD
        - MSVCRTD/msvcrtd/vcruntimed/ucrtd/msvcprtd -> MDd
     b) 回退（drectve 无 CRT 默认库时）：检查未定义外部符号，
        若 CRT 函数以 __imp_ 前缀出现（如 __imp_malloc）-> MD；
        若 CRT 函数直接出现（malloc、operator new）-> MT。

注意：Debug/Release 的 'd' 判断完全基于库文件内部内容（drectve 的 CRT 库名、
obj 路径的构建目录），与 .lib 文件名后缀（如 foo_d.lib / foo__d.lib）无关。
"""
import re
import struct
import sys
import io
from ar import Archive

VALID_MACHINES = {0x014C, 0x8664, 0x01C0, 0xAA64}
MACHINE_NAMES = {0x014C: "x86", 0x8664: "x64", 0x01C0: "ARM", 0xAA64: "ARM64"}

# ---------------- 基础 COFF/bigobj 解析 ----------------
def _u16(d, o): return struct.unpack_from("<H", d, o)[0]
def _u32(d, o): return struct.unpack_from("<I", d, o)[0]


def parse_obj(data):
    """识别标准 COFF 或 bigobj，返回头信息 dict；非 obj 返回 None。"""
    # 标准 COFF
    if len(data) >= 20 and _u16(data, 0) in VALID_MACHINES:
        return dict(machine=_u16(data, 0), num_sections=_u16(data, 2),
                    sec_table_off=20 + _u16(data, 16),
                    symtab=_u32(data, 8), num_syms=_u32(data, 12), kind="coff")
    # bigobj（MSVC /bigobj，实测布局）：machine@6, version@4==2,
    # num_sections@44, symtab@48, numsyms@52, 段表@56
    if len(data) >= 56 and _u16(data, 4) == 2 and _u16(data, 6) in VALID_MACHINES:
        return dict(machine=_u16(data, 6), num_sections=_u32(data, 44),
                    sec_table_off=56, symtab=_u32(data, 48), num_syms=_u32(data, 52), kind="bigobj")
    return None


def get_sections(data, h):
    secs = []
    for i in range(h["num_sections"]):
        off = h["sec_table_off"] + i * 40
        if off + 40 > len(data):
            break
        secs.append(data[off:off + 8].rstrip(b"\x00").decode("ascii", errors="ignore"))
    return secs


def get_drectve(data, h):
    for i in range(h["num_sections"]):
        off = h["sec_table_off"] + i * 40
        if off + 40 > len(data):
            break
        if data[off:off + 8].rstrip(b"\x00") == b".drectve":
            sz = _u32(data, off + 16); ptr = _u32(data, off + 20)
            return data[ptr:ptr + sz]
    return None


def undefined_symbols(data, h):
    """返回未定义外部符号名列表（正确解析 string table）。"""
    if h is None or h.get("symtab", 0) == 0:
        return []
    st = h["symtab"]
    strtab = data[st + h["num_syms"] * 18:]
    out = []
    i = 0
    while i < h["num_syms"]:
        off = st + i * 18
        if off + 18 > len(data):
            break
        raw = data[off:off + 8]
        sec = struct.unpack_from("<h", data, off + 12)[0]
        storage = data[off + 16]
        if raw[:4] == b"\x00\x00\x00\x00":
            soff = _u32(data, off + 4)
            end = strtab.find(b"\x00", soff)
            name = strtab[soff:end if end != -1 else None].decode("ascii", errors="ignore")
        else:
            name = raw.rstrip(b"\x00").decode("ascii", errors="ignore")
        if sec == 0:
            out.append(name)
        i += 1
        if storage == 2:
            i += 1
    return out


# ---------------- CRT 判别 ----------------
# 常见 C 运行库函数名（不带前导下划线）
CRT_C_FUNCS = {
    "malloc", "calloc", "realloc", "free", "printf", "sprintf", "snprintf", "fprintf",
    "vprintf", "vsprintf", "vsnprintf", "puts", "putchar", "gets", "getchar", "scanf",
    "sscanf", "fscanf", "strlen", "strcpy", "strncpy", "strcat", "strncat", "strcmp",
    "strncmp", "strstr", "strchr", "strrchr", "strtok", "strtok_s", "strerror", "memcpy",
    "memmove", "memset", "memchr", "memcmp", "fopen", "fclose", "fread", "fwrite", "fseek",
    "ftell", "fflush", "fgetc", "fputc", "fgets", "fputs", "feof", "ferror", "rewind",
    "time", "clock", "difftime", "mktime", "gmtime", "localtime", "strftime", "abs", "labs",
    "llabs", "sqrt", "sqrtf", "pow", "powf", "sin", "cos", "tan", "asin", "acos", "atan",
    "exp", "log", "log10", "floor", "ceil", "fabs", "fmod", "atan2", "rand", "srand",
    "qsort", "qsort_s", "bsearch", "exit", "abort", "atexit", "getenv", "system", "setjmp",
    "longjmp", "toupper", "tolower", "isalpha", "isdigit", "isalnum", "isspace", "isxdigit",
    "strtol", "strtoul", "strtod", "strtof", "strtoll", "atoi", "atol", "atof", "atoll",
    "wcscpy", "wcscat", "wcslen", "wcscmp", "wcsncpy", "wcsstr", "wcschr",
}
# MSVC 特定运行库辅助函数
CRT_MSVC_FUNCS = {"__stdio_common_vfprintf", "__stdio_common_printf", "__stdio_common_fprintf",
                  "__stdio_common_vsnprintf", "_malloc_base", "_free_base", "_calloc_base",
                  "_realloc_base", "_expand_base", "_msize_base", "_strdup_base", "_wcsdup_base"}

def is_crt_name(name):
    if name in CRT_C_FUNCS or name in CRT_MSVC_FUNCS:
        return True
    # C++ operator new/delete（mangled）
    if name.startswith(("??2@", "??3@", "??_U@", "??_V@", "??2_", "??3_")):
        return True
    if re.match(r"^\?(_?)\w+@@", name):  # 保守：不把任意 C++ mangled 当 CRT
        return False
    return False


# Debug CRT 专有符号：仅 Debug 构建可能出现（_malloc_dbg 等，仅作佐证，不作主判据）
_DEBUG_CRT_RE = re.compile(
    r"(_malloc_dbg|_calloc_dbg|_realloc_dbg|_free_dbg|_strdup_dbg|_wcsdup_dbg|"
    r"_aligned_malloc_dbg|_msize_dbg|_expand_dbg|__CrtDbgReportW?|_CrtSetDbgFlag|"
    r"_CrtSetBreakAlloc|_CrtCheckMemory|_CrtDbgReport)")

def is_debug_from_symbols(undef_syms):
    """若未定义符号中出现 Debug CRT 专属函数，则判定为 Debug 构建（弱信号）。"""
    return any(_DEBUG_CRT_RE.search(s) for s in undef_syms)


def crt_from_drectve(drectve):
    """从 .drectve 的 /DEFAULTLIB 与 /FAILIFMISMATCH:RuntimeLibrary 判定 CRT。
    返回 (crt, 依据列表)。"""
    if not drectve:
        return None, []
    # 首选 RuntimeLibrary= 指令（MD_DynamicRelease / MD_DynamicDebug / MT_StaticRelease ...）
    for v in re.findall(rb'RuntimeLibrary=([A-Za-z_]+)', drectve):
        v = v.decode()
        if "Dynamic" in v and v.endswith("Release"):
            return "MD", [f"RuntimeLibrary={v}"]
        if "Dynamic" in v and v.endswith("Debug"):
            return "MDd", [f"RuntimeLibrary={v}"]
        if "Static" in v and v.endswith("Release"):
            return "MT", [f"RuntimeLibrary={v}"]
        if "Static" in v and v.endswith("Debug"):
            return "MTd", [f"RuntimeLibrary={v}"]
    libs = [x.decode(errors="ignore").lower() for x in
            re.findall(rb'/DEFAULTLIB:"?([^"\s]+)"?', drectve, re.I)]
    hits = []
    crt = None
    for l in libs:
        base = l.split(".lib")[0]
        if base in ("libcmt",): crt, hits = "MT", [l]
        elif base == "libcmtd": crt, hits = "MTd", [l]
        elif base in ("msvcrt", "vcruntime", "ucrt", "msvcprt"): crt, hits = "MD", [l]
        elif base in ("msvcrtd", "vcruntimed", "ucrtd", "msvcprtd"): crt, hits = "MDd", [l]
        if crt:
            break
    return crt, hits


def crt_from_symbols(undef_syms):
    """回退：通过未定义符号判别 MT/MD。返回 ('MT'|'MD'|None, 依据)。"""
    imp_crt = set()
    direct_crt = set()
    for s in undef_syms:
        if s.startswith("__imp_"):
            core = s[len("__imp_"):]
            if is_crt_name(core):
                imp_crt.add(core)
        else:
            if is_crt_name(s):
                direct_crt.add(s)
    if imp_crt:
        return "MD", ("__imp_CRT: " + ", ".join(sorted(imp_crt)[:4]))
    if direct_crt:
        return "MT", ("direct CRT: " + ", ".join(sorted(direct_crt)[:4]))
    return None, None


# ---------------- VS 版本 ----------------
VS_KEYWORDS = ["vs2026", "vs2022", "vs2019", "vs2017", "vs2015",
               "vc2022", "vc2019", "vc2017", "vc2015", "2022", "2019", "2017", "2015"]
VS_YEAR_MAP = {"vs2026": 2026, "vs2022": 2022, "vs2019": 2019, "vs2017": 2017, "vs2015": 2015,
               "vc2022": 2022, "vc2019": 2019, "vc2017": 2017, "vc2015": 2015}

def vs_from_paths(paths):
    for kw in VS_KEYWORDS:
        for p in paths:
            if kw.lower() in p.lower():
                yr = VS_YEAR_MAP.get(kw.lower())
                if yr:
                    return yr
    return None

def msvc_version_from_debug(blob):
    """从原始字节中找 \\MSVC\\<版本>\\include 路径。返回版本字符串。"""
    for m in re.finditer(rb'\\MSVC\\(\d+\.\d+\.\d+)\\(?:include|lib)', blob):
        return m.group(1).decode()
    return None

BUILD_TYPE_KEYWORDS = ["Debug", "Release", "RelWithDebInfo", "MinSizeRel"]

def build_type_from_paths(paths):
    # 先精确匹配目录分隔符形式
    for kw in BUILD_TYPE_KEYWORDS:
        for p in paths:
            if (".dir\\" + kw + "\\") in p or ("\\" + kw + "\\") in p:
                return kw
    # 再作为子串匹配（如 ReleaseA / DebugA / MinSizeRel 等变体）
    for kw in BUILD_TYPE_KEYWORDS:
        for p in paths:
            if kw in p:
                return kw
    return None


# ---------------- 主流程 ----------------
def analyze_lib(path):
    # 整文件一次性读入内存，再在内存上解析 ar，避免大文件 seek 读取不稳定
    with open(path, "rb") as f:
        blob = f.read()
    archive = Archive(io.BytesIO(blob))
    entries = list(archive)
    # 读出所有成员字节（用索引作 key，避免同名成员被折叠）
    member_data = {}
    for idx, e in enumerate(entries):
        try:
            member_data[idx] = archive.open(e, mode="rb").read()
        except Exception:
            member_data[idx] = b""

    obj_paths = []
    undef_all = []
    drectves = []
    has_idata = False
    member_names = [e.name for e in entries]
    all_blob = bytearray()

    for idx, e in enumerate(entries):
        m = member_data[idx]
        all_blob += m[:4096]
        h = parse_obj(m)
        if h is None:
            continue
        secs = get_sections(m, h)
        if any(s.startswith(".idata") for s in secs):
            has_idata = True
        # 记录 .obj 路径（成员名）
        if e.name.lower().endswith(".obj"):
            obj_paths.append(e.name)
        dv = get_drectve(m, h)
        if dv:
            drectves.append(dv)
        undef_all.extend(undefined_symbols(m, h))

    # ---- 类型判定 ----
    import_like_names = any(n.lower().endswith(".dll") for n in member_names)
    is_import = has_idata or import_like_names
    lib_type = "import lib (DLL 配套)" if is_import else "static lib (静态库)"

    # ---- 成员/路径 ----
    obj_paths = list(dict.fromkeys(obj_paths))
    representative = obj_paths[0] if obj_paths else (member_names[0] if member_names else "")

    # ---- VS 版本 ----
    vs_year = vs_from_paths(obj_paths + member_names)
    msvc_ver = msvc_version_from_debug(bytes(all_blob))
    if msvc_ver:
        # 14.51.x -> VS2026, 14.4x -> VS2022, 14.3x -> VS2022, 14.2x -> VS2019, 14.1x -> VS2017
        mm = re.match(r"(\d+)\.(\d+)", msvc_ver)
        if mm:
            maj, minor = int(mm.group(1)), int(mm.group(2))
            if maj == 14 and minor >= 50: vs_year = 2026
            elif maj == 14 and minor >= 40: vs_year = 2022
            elif maj == 14 and minor >= 30: vs_year = 2022
            elif maj == 14 and minor >= 20: vs_year = 2019
            elif maj == 14 and minor >= 10: vs_year = 2017
            elif maj == 14 and minor >= 0: vs_year = 2015
    vs_label = f"VS{vs_year}" if vs_year else "Unknown"
    if msvc_ver:
        vs_label += f" (toolset {msvc_ver})"

    # ---- build type ----
    build_type = build_type_from_paths(obj_paths)

    # ---- CRT ----
    crt = None
    crt_basis = ""
    if is_import:
        # import lib 是 DLL 的导入桩，本身不决定 CRT；DLL 自己携带运行时
        crt = "N/A (import lib)"
        crt_basis = "DLL 的 CRT 由 DLL 自身决定"
    else:
        for dv in drectves:
            c, hits = crt_from_drectve(dv)
            if c:
                crt = c
                crt_basis = "drectve: " + ",".join(hits)
                break
        if crt is None:
            c, basis = crt_from_symbols(undef_all)
            if c:
                # 用 Debug 证据决定 'd'：路径 build_type 优先，其次 debug-CRT 符号
                debug_evidence = build_type == "Debug" or (build_type is None and is_debug_from_symbols(undef_all))
                if debug_evidence:
                    crt = c + "d"
                else:
                    crt = c
                crt_basis = "符号回退: " + (basis or "")
        # 若 CRT 来自 drectve 而 build_type 缺失，则用 'd' 反推 build_type
        if build_type is None and crt in ("MTd", "MDd"):
            build_type = "Debug"
        elif build_type is None and crt in ("MT", "MD"):
            build_type = "Release"

    # ---- _MSC_VER 提示（FAILIFMISMATCH 中的最低要求版本） ----
    msc_hint = set()
    for dv in drectves:
        for x in re.findall(rb'_MSC_VER=(\d+)', dv):
            msc_hint.add(x.decode())

    return dict(path=path, lib_type=lib_type, is_import=is_import,
                vs_label=vs_label, vs_year=vs_year, msvc_toolset=msvc_ver,
                build_type=build_type, crt=crt, crt_basis=crt_basis,
                msc_hint=sorted(msc_hint),
                member_count=len(member_names), obj_count=len(obj_paths),
                representative=representative)


def main():
    libs = [
        r"C:\pkgs\opencv\4.12.0\vs2022-x64-static\lib\ade.lib",
        r"C:\pkgs\EasyX_20240225\lib\VC2015\x64\EasyXa.lib",
        r"C:\Users\zz\Downloads\EasyX_26.10.25\lib_vc2015\x64\EasyXa.lib",
        r"C:\pkgs\ncnn\20250916\windows-vs2022-shared\x64\lib\ncnn.lib",
        r"C:\work\play\test\build\Debug\hello.lib",
    ]
    for p in libs:
        r = analyze_lib(p)
        print("=" * 72)
        print(f"FILE : {r['path']}")
        print(f"类型 : {r['lib_type']}  (成员 {r['member_count']} 个, 其中 .obj {r['obj_count']} 个)")
        print(f"代表 : {r['representative']}")
        print(f"VS   : {r['vs_label']}" + (f"  (_MSC_VER 要求 {r['msc_hint']})" if r['msc_hint'] else ""))
        print(f"构建 : {r['build_type']}")
        print(f"CRT  : {r['crt']}   [{r['crt_basis']}]")


if __name__ == "__main__":
    main()