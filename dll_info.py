#!/usr/bin/env python3
r"""Inspect a Windows DLL: file version, Visual Studio version, build mode, exports.

This intentionally uses pefile for the PE structures and VERSIONINFO resource.
It is a command-line tool, not a full PE parser.

    python dll_info.py C:\Windows\System32\kernel32.dll
    python dll_info.py --json C:\Windows\System32\user32.dll
    python dll_info.py --limit 20 C:\Windows\System32\shell32.dll
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import pefile
except ImportError:  # handled in main()
    pefile = None


__version__ = "2.1.0"

DEBUG_CRT = {
    "msvcrtd.dll",
    "msvcr70d.dll",
    "msvcr71d.dll",
    "msvcr80d.dll",
    "msvcr90d.dll",
    "msvcr100d.dll",
    "msvcr110d.dll",
    "msvcr120d.dll",
    "vcruntime140d.dll",
    "vcruntime140_1d.dll",
    "vcruntime140_threadsd.dll",
    "msvcp140d.dll",
    "msvcp140_1d.dll",
    "msvcp140_2d.dll",
    "ucrtbased.dll",
    "mfc140d.dll",
}
RELEASE_CRT = ("vcruntime140", "ucrtbase", "api-ms-win-crt-", "msvcp140", "msvcr", "mfc")


def read_version(pe) -> tuple[str | None, str | None]:
    """Return (FileVersion, ProductVersion) from the VERSIONINFO resource."""
    for group in getattr(pe, "FileInfo", []):
        for item in group:
            for table in getattr(item, "StringTable", []):
                entries = table.entries or {}
                if b"FileVersion" in entries or b"ProductVersion" in entries:
                    def text(key):
                        return entries[key].decode("utf-8", "replace") if key in entries else None

                    return text(b"FileVersion"), text(b"ProductVersion")
    return None, None


def visual_studio(major: int, minor: int) -> str:
    """Map an MSVC linker version to a Visual Studio family."""
    if major == 14:
        if minor >= 50:
            name, toolset = "Visual Studio 2026", "v145"
        elif minor >= 30:
            name, toolset = "Visual Studio 2022", "v143"
        elif minor >= 20:
            name, toolset = "Visual Studio 2019", "v142"
        elif minor >= 10:
            name, toolset = "Visual Studio 2017", "v141"
        else:
            name, toolset = "Visual Studio 2015", "v140"
        return f"{name} (MSVC {major}.{minor}, {toolset})"
    if major == 12:
        return "Visual Studio 2013 (MSVC 12.0, v120)"
    if major == 11:
        return "Visual Studio 2012 (MSVC 11.0, v110)"
    if major == 10:
        return "Visual Studio 2010 (MSVC 10.0, v100)"
    if major == 9:
        return "Visual Studio 2008 (MSVC 9.0, v90)"
    if major == 8:
        return "Visual Studio 2005 (MSVC 8.0, v80)"
    if major == 7:
        return "Visual Studio 2003 (MSVC 7.1, v71)" if minor == 10 else "Visual Studio 2002 (MSVC 7.0, v70)"
    if major == 6:
        return "Visual Studio 6.0 (MSVC 6.0, v60)"
    return f"Unknown toolchain (linker {major}.{minor})"


def read_pdb(pe) -> str | None:
    for entry in getattr(pe, "DIRECTORY_ENTRY_DEBUG", []):
        if entry.struct.Type == 2:  # IMAGE_DEBUG_TYPE_CODEVIEW
            name = getattr(entry.entry, "PdbFileName", b"")
            if name:
                return name.decode("utf-8", "replace").rstrip("\0")
    return None


def build_mode(pe, pdb: str | None, filename: str) -> tuple[str, str]:
    if filename.lower() in DEBUG_CRT:
        return "Debug", f"known debug runtime: {filename}"
    imports = {entry.dll.decode("ascii", "ignore").lower() for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])}
    debug_crt = sorted(imports & DEBUG_CRT)
    if debug_crt:
        return "Debug", "debug CRT: " + ", ".join(debug_crt)
    if b"Run-Time Check Failure #" in pe.__data__:
        return "Debug", "debug runtime string (Run-Time Check Failure)"
    if pdb and "\\debug\\" in pdb.replace("/", "\\").lower():
        return "Debug", "PDB path contains \\Debug\\"

    release_crt = sorted(name for name in imports if name.startswith(RELEASE_CRT))
    if release_crt:
        return "Release", "release CRT: " + ", ".join(release_crt[:3])
    if pdb:
        return "Release", "no debug markers; a PDB alone is not proof of Debug"
    return "Release", "no debug CRT or debug-runtime markers"


def read_exports(pe) -> list[dict]:
    export = getattr(pe, "DIRECTORY_ENTRY_EXPORT", None)
    if export is None:
        return []
    result = []
    for symbol in export.symbols:
        result.append(
            {
                "ordinal": symbol.ordinal,
                "name": symbol.name.decode("utf-8", "replace") if symbol.name else None,
                "forwarder": symbol.forwarder.decode("utf-8", "replace") if symbol.forwarder else None,
            }
        )
    return result


def inspect(path: str | os.PathLike[str]) -> dict:
    path = os.path.abspath(os.fspath(path))
    pe = pefile.PE(path)
    try:
        file_version, product_version = read_version(pe)
        pdb = read_pdb(pe)
        mode, reason = build_mode(pe, pdb, os.path.basename(path))
        header = pe.OPTIONAL_HEADER
        return {
            "file": path,
            "file_version": file_version,
            "product_version": product_version,
            "visual_studio": visual_studio(header.MajorLinkerVersion, header.MinorLinkerVersion),
            "build_mode": mode,
            "build_reason": reason,
            "pdb": pdb,
            "exports": read_exports(pe),
        }
    finally:
        pe.close()


def show(info: dict, limit: int = 0) -> None:
    print(f"File: {info['file']}")
    print(f"  File version: {info['file_version'] or '(none)'}")
    print(f"  Product version: {info['product_version'] or '(none)'}")
    print(f"  Visual Studio: {info['visual_studio']}")
    print(f"  Build mode: {info['build_mode']} ({info['build_reason']})")
    if info["pdb"]:
        print(f"  PDB: {info['pdb']}")
    print(f"  Exports: {len(info['exports'])}")
    shown = info["exports"] if limit <= 0 else info["exports"][:limit]
    for symbol in shown:
        name = symbol["name"] or f"[ordinal {symbol['ordinal']}]"
        if symbol["forwarder"]:
            name += f" -> {symbol['forwarder']}"
        print(f"    {symbol['ordinal']:6d}  {name}")
    if len(shown) < len(info["exports"]):
        print(f"    ... {len(info['exports']) - len(shown)} more (use --limit 0 for all)")


def _self_test() -> int:
    import subprocess
    import unittest

    root = Path(__file__).resolve().parent
    system32 = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32"
    syswow64 = Path(os.environ.get("WINDIR", r"C:\Windows")) / "SysWOW64"

    class Tests(unittest.TestCase):
        def test_common_dlls(self) -> None:
            for name in (
                "kernel32.dll",
                "user32.dll",
                "shell32.dll",
                "advapi32.dll",
                "ole32.dll",
                "ntdll.dll",
                "ucrtbase.dll",
                "msvcrt.dll",
            ):
                path = system32 / name
                if not path.is_file():
                    continue
                with self.subTest(dll=name):
                    info = inspect(path)
                    self.assertRegex(info["file_version"] or "", r"^\d+\.\d+")
                    self.assertTrue(info["visual_studio"].startswith("Visual Studio"))
                    self.assertEqual(info["build_mode"], "Release")
                    self.assertGreater(len(info["exports"]), 0)

        def test_kernel32_exports_and_forwarders(self) -> None:
            info = inspect(system32 / "kernel32.dll")
            names = {symbol["name"] for symbol in info["exports"]}
            self.assertIn("GetProcAddress", names)
            self.assertIn("LoadLibraryW", names)
            self.assertTrue(any(symbol["forwarder"] for symbol in info["exports"]))

        @unittest.skipUnless((system32 / "vcruntime140d.dll").is_file(), "debug VC runtime not installed")
        def test_debug_runtime_is_debug(self) -> None:
            info = inspect(system32 / "vcruntime140d.dll")
            self.assertEqual(info["build_mode"], "Debug")
            self.assertIn("debug", info["build_reason"].lower())

        @unittest.skipUnless((syswow64 / "kernel32.dll").is_file(), "SysWOW64 kernel32.dll not available")
        def test_32bit_dll(self) -> None:
            info = inspect(syswow64 / "kernel32.dll")
            self.assertTrue(info["file_version"])
            self.assertGreater(len(info["exports"]), 0)

        def test_versionless_dll(self) -> None:
            path = system32 / "AIComponentMgmt.dll"
            if not path.is_file():
                self.skipTest("versionless test DLL is not present")
            info = inspect(path)
            self.assertIsNone(info["file_version"])
            self.assertIsNone(info["product_version"])

        def test_cli_json(self) -> None:
            result = subprocess.run(
                [sys.executable, str(root / "dll_info.py"), "--json", str(system32 / "kernel32.dll")],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            info = json.loads(result.stdout)
            self.assertEqual(Path(info["file"]).name.lower(), "kernel32.dll")
            self.assertTrue(info["file_version"])
            self.assertEqual(info["build_mode"], "Release")
            self.assertGreater(len(info["exports"]), 100)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv: list[str] | None = None) -> int:
    if pefile is None:
        print("error: pefile is required; run: python -m pip install pefile", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(description="Inspect DLL version, toolchain, build mode and exports.")
    parser.add_argument("paths", metavar="DLL", nargs="*", type=Path)
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument("--limit", type=int, default=0, metavar="N", help="max exports to print (0 = all)")
    parser.add_argument("--test", action="store_true", help="run built-in tests")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    if args.test:
        return _self_test()
    if not args.paths:
        parser.error("at least one DLL is required (or use --test)")

    results = []
    status = 0
    for path in args.paths:
        try:
            results.append(inspect(path))
        except (OSError, pefile.PEFormatError) as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            status = 2

    if args.json:
        payload = results[0] if len(results) == 1 else results
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        for index, info in enumerate(results):
            if index:
                print()
            show(info, args.limit)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
