# -*- coding: utf-8 -*-
"""
analyze_win_lib 的单元测试。

夹具：fixtures/*.lib 用 build_fixtures.py 以真实 MSVC 工具链编译的极小对象
（每个几 KB）封装而成，覆盖全部检测特征：
  - 静态库 / 导入库
  - COFF / bigobj
  - CRT: MT/MTd/MD/MDd
  - drectve 无 CRT 时的符号回退
  - build_type 从对象路径 / 反向推断
  - VS 版本从对象路径关键字

运行（在 rocbuild 根目录）：
  python -m unittest discover -s analyze_win_lib -v
或直接在 analyze_win_lib 目录：
  python test_analyze_win_lib.py
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")

# analyze_win_lib.py 与本测试同目录，直接加 HERE 到搜索路径
sys.path.insert(0, HERE)
import analyze_win_lib as m


def analyze(name):
    return m.analyze_lib(os.path.join(FIXTURES, name))


class TestFixtureStatic(unittest.TestCase):
    """静态库：CRT 从 drectve 判定。"""

    CASES = [
        ("static_mt.lib",  "Release", "MT"),
        ("static_mtd.lib", "Debug",   "MTd"),
        ("static_md.lib",  "Release", "MD"),
        ("static_mdd.lib", "Debug",   "MDd"),
    ]

    def test_crt_and_build_type(self):
        for name, build_type, crt in self.CASES:
            with self.subTest(lib=name):
                r = analyze(name)
                self.assertEqual(r["lib_type"], "static lib (静态库)", name)
                self.assertFalse(r["is_import"], name)
                self.assertEqual(r["build_type"], build_type, name)
                self.assertEqual(r["crt"], crt, name)


class TestFixtureBigobj(unittest.TestCase):
    """bigobj（/bigobj 生成的 EXTENDED COFF）也要能正确解析。"""

    def test_bigobj_md(self):
        r = analyze("static_bigobj_md.lib")
        self.assertFalse(r["is_import"])
        self.assertEqual(r["build_type"], "Release")
        self.assertEqual(r["crt"], "MD")

    def test_bigobj_mdd(self):
        r = analyze("static_bigobj_mdd.lib")
        self.assertEqual(r["build_type"], "Debug")
        self.assertEqual(r["crt"], "MDd")

    def test_bigobj_kind_detected(self):
        # 确认对象确实被识别为 bigobj 格式
        with open(os.path.join(FIXTURES, "static_bigobj_md.lib"), "rb") as f:
            blob = f.read()
        a = m.Archive(io.BytesIO(blob))
        obj = a.open(a.entries[0], mode="rb").read()
        self.assertEqual(m.parse_obj(obj)["kind"], "bigobj")


class TestFixtureNoCrt(unittest.TestCase):
    """drectve 里没有 CRT 默认库时（模拟 EasyX），应走符号回退。"""

    def test_nocrt_mt(self):
        # /MT 对象剥掉 LIBCMT 后，符号直接引用 malloc/free -> MT
        r = analyze("static_nocrt_mt.lib")
        self.assertEqual(r["build_type"], "Release")
        self.assertEqual(r["crt"], "MT")
        self.assertIn("符号回退", r["crt_basis"])

    def test_nocrt_md(self):
        # /MD 对象剥掉 MSVCRT 后，符号带 __imp_ -> MD
        r = analyze("static_nocrt_md.lib")
        self.assertEqual(r["build_type"], "Release")
        self.assertEqual(r["crt"], "MD")
        self.assertIn("符号回退", r["crt_basis"])


class TestFixtureVs(unittest.TestCase):
    """VS 版本从对象路径关键字推断。"""

    def test_vs2017(self):
        r = analyze("static_vs2017.lib")
        self.assertEqual(r["vs_year"], 2017)
        self.assertEqual(r["crt"], "MT")
        # 路径里是 ReleaseA，应识别为 Release
        self.assertEqual(r["build_type"], "Release")


class TestFixtureImport(unittest.TestCase):
    """导入库（DLL 配套）：判定为 import，CRT 为 N/A。"""

    def test_import_lib(self):
        r = analyze("import_tiny.lib")
        self.assertTrue(r["is_import"])
        self.assertEqual(r["lib_type"], "import lib (DLL 配套)")
        self.assertEqual(r["crt"], "N/A (import lib)")
        self.assertEqual(r["build_type"], None)


class TestFilenameIndependence(unittest.TestCase):
    """Debug 判断基于库内容，而非 .lib 文件名后缀（foo_d.lib / foo__d.lib）。"""

    def _analyze_copied_as(self, src, new_name):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, new_name)
            shutil.copy(os.path.join(FIXTURES, src), p)
            return m.analyze_lib(p)

    def test_release_not_fooled_by_d_suffix(self):
        # 真 Release/MD 的库，改名 foo_d.lib / foo__d.lib 后应仍是 Release/MD
        for new in ("foo_d.lib", "foo__d.lib"):
            with self.subTest(name=new):
                r = self._analyze_copied_as("static_md.lib", new)
                self.assertEqual(r["build_type"], "Release")
                self.assertEqual(r["crt"], "MD")

    def test_debug_detected_without_d_suffix(self):
        # 真 Debug/MDd 的库，改名不带 d 的后缀后应仍是 Debug/MDd
        r = self._analyze_copied_as("static_mdd.lib", "plain_name.lib")
        self.assertEqual(r["build_type"], "Debug")
        self.assertEqual(r["crt"], "MDd")


if __name__ == "__main__":
    unittest.main(verbosity=2)