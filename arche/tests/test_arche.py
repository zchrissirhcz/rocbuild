# -*- coding: utf-8 -*-
"""arche 集成测试：在临时目录里真实编译、链接并运行产物。"""

import os
import json
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHE = ROOT / "arche.py"
IS_WINDOWS = os.name == "nt"
EXE = ".exe" if IS_WINDOWS else ""
NDK = Path(os.environ.get("ARCHE_ANDROID_NDK", r"C:\soft\toolchains\android-ndk\r27c"))


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="arche test "))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write(self, rel, text):
        p = self.tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def run_arche(self, *args, env=None, cwd=None):
        e = os.environ.copy()
        e["PYTHONIOENCODING"] = "utf-8"
        e["PYTHONUTF8"] = "1"
        if env:
            e.update(env)
        return subprocess.run(
            [sys.executable, str(ARCHE), *map(str, args)],
            cwd=str(cwd or self.tmp), env=e, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300)

    def run_exe(self, path):
        return subprocess.run([str(path)], cwd=str(self.tmp), capture_output=True,
                              text=True, encoding="utf-8", errors="replace")

    def ok(self, p):
        self.assertEqual(p.returncode, 0,
                         f"stdout:\n{p.stdout}\nstderr:\n{p.stderr}")

    def fail(self, p, code=2):
        self.assertEqual(p.returncode, code,
                         f"stdout:\n{p.stdout}\nstderr:\n{p.stderr}")

    def art(self, name, typ="exe"):
        base = self.tmp / "build" / name
        if typ == "exe":
            return base / (name + EXE)
        if typ == "static":
            return base / (name + ".lib" if IS_WINDOWS else "lib" + name + ".a")
        return base / (name + ".dll" if IS_WINDOWS else "lib" + name + ".so")

    # ---- 命令行模式 ----------------------------------------------------- #

    def test_adhoc_single(self):
        self.write("hello.cpp", '#include <cstdio>\nint main(){std::puts("hi");}\n')
        p = self.run_arche("hello.cpp")
        self.ok(p)
        exe = self.tmp / ("hello" + EXE)
        self.assertTrue(exe.is_file())
        self.assertIn("hi", self.run_exe(exe).stdout)

    def test_adhoc_multi_flags_and_spaces(self):
        self.write("inc/value.h", "#pragma once\n#define VALUE 7\n")
        self.write("util.cpp", "int util(){return 3;}\n")
        self.write("main.cpp", '#include <cstdio>\n#include "value.h"\n'
                              'int util();\nint main(){std::printf("%d\\n",VALUE+util()+EXTRA);}\n')
        out = self.tmp / "out dir" / "hello world"
        flag = "/O2" if IS_WINDOWS else "-O2"
        p = self.run_arche("main.cpp", "util.cpp", "-I", "inc", "-D", "EXTRA=5",
                           "-o", str(out), "--", flag)
        self.ok(p)
        exe = out.with_name(out.name + ".exe") if IS_WINDOWS else out
        self.assertTrue(exe.is_file())
        self.assertIn("15", self.run_exe(exe).stdout)

    def test_adhoc_c(self):
        self.write("hello.c", '#include <stdio.h>\nint main(void){puts("C");}\n')
        self.ok(self.run_arche("hello.c"))
        self.assertIn("C", self.run_exe(self.tmp / ("hello" + EXE)).stdout)

    # ---- 规则模式：静态库 ----------------------------------------------- #

    def static_project(self):
        self.write("inc/mathx.h", "#pragma once\nnamespace m{int add(int,int);}\n")
        self.write("src/mathx.cpp", '#include "mathx.h"\nnamespace m{int add(int a,int b){return a+b;}}\n')
        self.write("src/main.cpp", '#include <cstdio>\n#include "mathx.h"\n'
                                   'int main(){std::printf("%d\\n",m::add(2,3));}\n')
        self.write("arche.ini",
                   "[*]\nstd = c++17\nconfig = release\n\n"
                   "[mathx]\ntype = static\nsources = src/mathx.cpp\n"
                   "include_dirs = inc\n\n"
                   "[app]\ntype = exe\nsources = src/main.cpp\nrequires = mathx\n")

    def test_static_incremental_and_force_clean(self):
        self.static_project()
        p = self.run_arche()
        self.ok(p)
        self.assertIn("5", self.run_exe(self.art("app")).stdout)
        self.assertTrue(self.art("mathx", "static").is_file())

        p = self.run_arche()
        self.ok(p)
        self.assertNotIn("[CC]", p.stdout)

        p = self.run_arche("--force", "app")
        self.ok(p)
        self.assertIn("[CC] app:", p.stdout)
        self.assertNotIn("[CC] mathx:", p.stdout)

        p = self.run_arche("--clean", "app")
        self.ok(p)
        self.assertFalse(self.art("app").exists())
        self.assertTrue(self.art("mathx", "static").is_file())

    def test_static_header_dependency(self):
        self.static_project()
        self.ok(self.run_arche())
        now = time.time()
        os.utime(self.tmp / "inc/mathx.h", (now + 2, now + 2))
        p = self.run_arche()
        self.ok(p)
        self.assertIn("[CC] app:", p.stdout)
        self.assertIn("[CC] mathx:", p.stdout)

    def test_transitive_static(self):
        self.write("inc/base.h", "#pragma once\nnamespace b{int v();}\n")
        self.write("inc/mid.h", '#pragma once\n#include "base.h"\nnamespace mid{int twice();}\n')
        self.write("src/base.cpp", '#include "base.h"\nnamespace b{int v(){return 21;}}\n')
        self.write("src/mid.cpp", '#include "mid.h"\nnamespace mid{int twice(){return b::v()*2;}}\n')
        self.write("src/main.cpp", '#include <cstdio>\n#include "mid.h"\n'
                                   'int main(){std::printf("%d\\n",mid::twice());}\n')
        self.write("arche.ini",
                   "[base]\ntype = static\nsources = src/base.cpp\ninclude_dirs = inc\n\n"
                   "[mid]\ntype = static\nsources = src/mid.cpp\ninclude_dirs = inc\nrequires = base\n\n"
                   "[app]\ntype = exe\nsources = src/main.cpp\nrequires = mid\n")
        self.ok(self.run_arche())
        self.assertIn("42", self.run_exe(self.art("app")).stdout)

    def test_comma_sources_and_requires(self):
        self.write("a.cpp", "int a(){return 1;}\n")
        self.write("b.cpp", "int b(){return 2;}\n")
        self.write("main.cpp", '#include <cstdio>\nint a();int b();\n'
                               'int main(){std::printf("%d\\n",a()+b());}\n')
        self.write("arche.ini",
                   "[lib]\ntype = static\nsources = a.cpp, b.cpp\n\n"
                   "[app]\ntype = exe\nsources = main.cpp\nrequires = lib\n")
        self.ok(self.run_arche())
        self.assertIn("3", self.run_exe(self.art("app")).stdout)

    def test_legacy_aliases(self):
        self.write("a.cpp", "int a(){return 1;}\n")
        self.write("main.cpp", "int a();\nint main(){return a()-1;}\n")
        self.write("arche.ini",
                   "[a]\ncrate_type = static\nsources = a.cpp\n\n"
                   "[app]\ntype = exe\nsources = main.cpp\ndeps = a\n")
        self.ok(self.run_arche())
        self.assertTrue(self.art("app").is_file())

    # ---- 规则模式：动态库 ----------------------------------------------- #

    def test_shared_and_dll_copy(self):
        self.write("inc/greet.h", "#pragma once\n#include <string>\n"
                                  "#if defined(_WIN32)\n"
                                  "# ifdef GREET_BUILD\n#  define API __declspec(dllexport)\n"
                                  "# else\n#  define API __declspec(dllimport)\n# endif\n"
                                  "#else\n# define API\n#endif\n"
                                  "API std::string greet(const std::string&);\n")
        self.write("src/greet.cpp", '#include "greet.h"\n'
                                    'std::string greet(const std::string& n){return "Hi "+n;}\n')
        self.write("src/main.cpp", '#include <cstdio>\n#include "greet.h"\n'
                                   'int main(){std::printf("%s\\n",greet("a").c_str());}\n')
        self.write("arche.ini",
                   "[*]\nstd = c++17\n\n"
                   "[greet]\ntype = shared\nsources = src/greet.cpp\n"
                   "include_dirs = inc\ndefines = GREET_BUILD\n\n"
                   "[app]\ntype = exe\nsources = src/main.cpp\nrequires = greet\n")
        self.ok(self.run_arche())
        exe = self.art("app")
        self.assertTrue(self.art("greet", "shared").is_file())
        self.assertIn("Hi a", self.run_exe(exe).stdout)
        if IS_WINDOWS:
            self.assertTrue((exe.parent / "greet.dll").is_file())

    # ---- 语言、变量、目标名 --------------------------------------------- #

    def test_glob_mixed_c_cpp(self):
        self.write("inc/add.h", "#pragma once\n#ifdef __cplusplus\nextern \"C\" {\n#endif\n"
                                "int add(int,int);\n#ifdef __cplusplus\n}\n#endif\n")
        self.write("src/add.cpp", '#include "add.h"\nint add(int a,int b){return a+b;}\n')
        self.write("src/main.c", '#include <stdio.h>\n#include "add.h"\n'
                                 'int main(void){printf("%d\\n",add(20,22));}\n')
        self.write("arche.ini", "[*]\ninclude_dirs = inc\n\n"
                                "[app]\ntype = exe\nsources = src/*.c src/*.cpp\n")
        self.ok(self.run_arche())
        self.assertIn("42", self.run_exe(self.art("app")).stdout)

    def test_variables_with_spaces_and_nesting(self):
        self.write("inc dir/vendor.h", "#pragma once\n#define V 77\n")
        self.write("main.cpp", '#include <cstdio>\n#include "vendor.h"\n'
                               'int main(){std::printf("%d\\n",V);}\n')
        self.write("arche.ini", "[*]\nvar.ROOT = inc dir\nvar.SDK = ${ROOT}\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\ninclude_dirs = ${SDK}\n")
        self.ok(self.run_arche())
        self.assertIn("77", self.run_exe(self.art("app")).stdout)

    def test_environment_variable_expansion(self):
        self.write("inc dir/vendor.h", "#pragma once\n#define V 99\n")
        self.write("main.cpp", '#include <cstdio>\n#include "vendor.h"\n'
                               'int main(){std::printf("%d\\n",V);}\n')
        self.write("arche.ini", "[*]\nvar.SDK = $ENV{ARCHE_ENV_INC}\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\n"
                                "include_dirs = ${SDK}\n")
        self.ok(self.run_arche(env={"ARCHE_ENV_INC": "inc dir"}))
        self.assertIn("99", self.run_exe(self.art("app")).stdout)

    def test_variable_does_not_shadow_environment(self):
        self.write("inc/vendor.h", "#pragma once\n#define V 88\n")
        self.write("main.cpp", '#include <cstdio>\n#include "vendor.h"\n'
                               'int main(){std::printf("%d\\n",V);}\n')
        self.write("arche.ini", "[*]\nvar.SDK = inc\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\ninclude_dirs = ${SDK}\n")
        env = {"SDK": str(self.tmp / "missing")}
        self.ok(self.run_arche(env=env))
        self.assertIn("88", self.run_exe(self.art("app")).stdout)

    def test_variable_cycle_and_undefined(self):
        self.write("main.cpp", "int main(){return 0;}\n")
        self.write("arche.ini", "[*]\nvar.A = ${B}\nvar.B = ${A}\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\n")
        p = self.run_arche()
        self.fail(p)
        self.assertIn("循环", p.stderr)
        self.write("arche.ini", "[*]\nvar.SDK = ${ARCHE_NOPE_77}\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\n")
        p = self.run_arche()
        self.fail(p)
        self.assertIn("ARCHE_NOPE_77", p.stderr)

    def test_target_names_are_not_reserved(self):
        self.write("main.cpp", '#include <cstdio>\nint main(){std::puts("t");}\n')
        self.write("arche.ini",
                   "[*]\nstd = c++17\n\n"
                   "[arche]\ntype = exe\nsources = main.cpp\n\n"
                   "[build]\ntype = exe\nsources = main.cpp\n\n"
                   "[clean]\ntype = exe\nsources = main.cpp\n\n"
                   "[list]\ntype = exe\nsources = main.cpp\n")
        for name in ("arche", "build", "clean", "list"):
            p = self.run_arche(name)
            self.ok(p)
            self.assertTrue((self.tmp / "build" / name / (name + EXE)).is_file())
        p = self.run_arche("--list")
        self.ok(p)
        for name in ("arche", "build", "clean", "list"):
            self.assertIn(name, p.stdout)
        p = self.run_arche("--clean", "clean")
        self.ok(p)
        self.assertFalse((self.tmp / "build" / "clean").exists())
        self.assertTrue((self.tmp / "build" / "list" / ("list" + EXE)).exists())

    def test_cflags_and_cxxflags(self):
        common = "/DCOMMON=1" if IS_WINDOWS else "-DCOMMON=1"
        cflag = "/DC_ONLY=1" if IS_WINDOWS else "-DC_ONLY=1"
        cxxflag = "/DCXX_ONLY=1" if IS_WINDOWS else "-DCXX_ONLY=1"
        self.write("src/main.c", "#if !defined(COMMON) || !defined(C_ONLY) || defined(CXX_ONLY)\n"
                                 "#error wrong C flags\n#endif\n"
                                 "int c_value(void){return 1;}\n")
        self.write("src/main.cpp", "#include <cstdio>\n"
                                   "#if !defined(COMMON) || !defined(CXX_ONLY) || defined(C_ONLY)\n"
                                   "#error wrong C++ flags\n#endif\n"
                                   'extern "C" int c_value(void);\n'
                                   'int main(){std::printf("%d\\n",c_value());}\n')
        self.write("arche.ini",
                   f"[*]\nflags = {common}\ncflags = {cflag}\ncxxflags = {cxxflag}\n\n"
                   "[app]\ntype = exe\nsources = src/*.c src/*.cpp\n")
        self.ok(self.run_arche())
        self.assertIn("1", self.run_exe(self.art("app")).stdout)

    def test_compile_commands_json(self):
        self.static_project()
        self.ok(self.run_arche())
        db = self.tmp / "build" / "compile_commands.json"
        self.assertTrue(db.is_file())
        data = json.loads(db.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data), 2)
        files = {Path(e["file"]).name for e in data}
        self.assertIn("mathx.cpp", files)
        self.assertIn("main.cpp", files)
        for entry in data:
            self.assertTrue(entry["directory"])
            self.assertTrue(entry["arguments"])
            self.assertTrue(entry["file"])

    def test_header_only_target(self):
        self.write("include/geo.h", "#pragma once\ninline int twice(int x){return x*2;}\n")
        self.write("main.cpp", '#include <cstdio>\n#include "geo.h"\n'
                               'int main(){std::printf("%d\\n",twice(21));}\n')
        self.write("arche.ini",
                   "[geo]\ntype = interface\ninclude_dirs = include\n\n"
                   "[app]\ntype = exe\nsources = main.cpp\nrequires = geo\n")
        self.ok(self.run_arche())
        self.assertIn("42", self.run_exe(self.art("app")).stdout)
        p = self.run_arche("--list")
        self.ok(p)
        self.assertIn("interface", p.stdout)
        self.assertIn("geo", p.stdout)

    def test_jobs_are_source_level_parallel(self):
        spec = importlib.util.spec_from_file_location("arche_parallel_test", ARCHE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        barrier = threading.Barrier(4, timeout=5)
        builder = object.__new__(module.Builder)
        builder.jobs = 4

        def compile_one(_job):
            barrier.wait()
            time.sleep(0.05)

        builder._compile_one = compile_one
        builder._compile([object() for _ in range(4)])

    def test_custom_build_dir(self):
        self.write("main.cpp", '#include <cstdio>\nint main(){std::puts("out");}\n')
        self.write("arche.ini", "[*]\nbuild_dir = out\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\n")
        self.ok(self.run_arche())
        exe = self.tmp / "out" / "app" / ("app" + EXE)
        self.assertTrue(exe.is_file())
        self.assertTrue((self.tmp / "out" / "compile_commands.json").is_file())
        self.assertIn("out", self.run_exe(exe).stdout)
        self.ok(self.run_arche("--clean"))
        self.assertFalse((self.tmp / "out").exists())

        self.ok(self.run_arche("-B", "out2"))
        self.assertTrue((self.tmp / "out2" / "app" / ("app" + EXE)).is_file())

    def test_source_and_build_dir_flags(self):
        self.write("proj/main.cpp", "int main(){return 0;}\n")
        self.write("proj/arche.ini", "[app]\ntype = exe\nsources = main.cpp\n")
        self.ok(self.run_arche("-S", "proj", "-B", "out"))
        self.assertTrue((self.tmp / "out" / "app" / ("app" + EXE)).is_file())

    def test_option_patch(self):
        self.write("main.cpp", "#ifndef WITH_NPU_A\n#error missing\n#endif\n"
                               "int main(){return 0;}\n")
        self.write("arche.ini", "[*]\noption.WITH_NPU_A = off\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\n\n"
                                "[app:WITH_NPU_A]\ndefines = WITH_NPU_A=1\n")
        p = self.run_arche()
        self.fail(p, 1)
        self.ok(self.run_arche("--set", "WITH_NPU_A=on"))
        self.assertTrue(self.art("app").is_file())

    def test_choice_patch(self):
        self.write("main.cpp", '#include <cstdio>\nint main(){\n'
                               '#if defined(USE_A)\nstd::puts("A");\n'
                               '#elif defined(USE_B)\nstd::puts("B");\n'
                               '#else\nstd::puts("none");\n#endif\n}\n')
        self.write("arche.ini", "[*]\nchoice.NPU = a\nchoice.NPU.values = a, b\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\n\n"
                                "[app:NPU=a]\ndefines = USE_A=1\n\n"
                                "[app:NPU=b]\ndefines = USE_B=1\n")
        self.ok(self.run_arche())
        self.assertIn("A", self.run_exe(self.art("app")).stdout)
        self.ok(self.run_arche("--set", "NPU=b", "--force"))
        self.assertIn("B", self.run_exe(self.art("app")).stdout)
        p = self.run_arche("--set", "NPU=c")
        self.fail(p)
        self.assertIn("不在", p.stderr)

    def test_private_requires_headers(self):
        self.write("cici/include/cici.h", "#pragma once\n#define CICI 2\n")
        self.write("foo/include/foo.h", "#pragma once\nint foo_value();\n")
        self.write("foo/src/foo.cpp", '#include "cici.h"\n#include "foo.h"\n'
                                      "int foo_value(){return CICI;}\n")
        self.write("app/main.cpp", '#include <cstdio>\n#include "foo.h"\n'
                                   'int main(){std::printf("%d\\n",foo_value());}\n')
        self.write("arche.ini",
                   "[cici]\ntype = interface\ninclude_dirs = cici/include\n\n"
                   "[foo]\ntype = static\nsources = foo/src/foo.cpp\n"
                   "include_dirs = foo/include\nprivate_requires = cici\n\n"
                   "[app]\ntype = exe\nsources = app/main.cpp\nrequires = foo\n")
        self.ok(self.run_arche())
        self.assertIn("2", self.run_exe(self.art("app")).stdout)
        db = json.loads((self.tmp / "build/compile_commands.json").read_text("utf-8"))

        def args_for(suffix):
            return next(e["arguments"] for e in db
                        if Path(e["file"]).as_posix().endswith(suffix))

        app_args = args_for("app/main.cpp")
        foo_args = args_for("foo/src/foo.cpp")
        self.assertTrue(any("foo" in a.lower() and "include" in a.lower()
                            for a in app_args))
        self.assertFalse(any("cici" in a.lower() and "include" in a.lower()
                             for a in app_args))
        self.assertTrue(any("cici" in a.lower() and "include" in a.lower()
                            for a in foo_args))

    def test_links_only_and_header_conflict(self):
        self.write("main/config.h", "#define VALUE 1\n")
        self.write("lib/include/config.h", "#define VALUE 2\n")
        self.write("lib/src/lib.cpp", '#include "config.h"\n'
                                      "int lib_value(){return VALUE;}\n")
        self.write("main/main.cpp", '#include <cstdio>\n#include "config.h"\n'
                                   "int lib_value();\n"
                                   'int main(){std::printf("%d\\n",VALUE+lib_value());}\n')
        self.write("arche.ini",
                   "[lib]\ntype = static\nsources = lib/src/lib.cpp\n"
                   "include_dirs = lib/include\n\n"
                   "[app]\ntype = exe\nsources = main/main.cpp\nrequires = lib\n")
        p = self.run_arche()
        self.fail(p)
        self.assertIn("config.h", p.stderr)
        self.assertIn("links", p.stderr)

        # 只链接 lib，不把 lib 的 include 目录传给 app。
        self.write("arche.ini",
                   "[lib]\ntype = static\nsources = lib/src/lib.cpp\n"
                   "include_dirs = lib/include\n\n"
                   "[app]\ntype = exe\nsources = main/main.cpp\nlinks = lib\n")
        self.ok(self.run_arche())
        self.assertIn("3", self.run_exe(self.art("app")).stdout)

    # ---- 配置错误 -------------------------------------------------------- #

    def test_cycle_and_missing_requires(self):
        self.write("main.cpp", "int main(){return 0;}\n")
        self.write("arche.ini", "[a]\ntype = static\nsources = main.cpp\nrequires = b\n\n"
                                "[b]\ntype = static\nsources = main.cpp\nrequires = a\n")
        p = self.run_arche()
        self.fail(p)
        self.assertIn("依赖环", p.stderr)
        self.write("arche.ini", "[app]\ntype = exe\nsources = main.cpp\nrequires = nope\n")
        p = self.run_arche()
        self.fail(p)
        self.assertIn("nope", p.stderr)

    def test_unknown_key_and_unset_env(self):
        self.write("main.cpp", "int main(){return 0;}\n")
        self.write("arche.ini", "[app]\ntype = exe\nsources = main.cpp\nflagz = x\n")
        p = self.run_arche()
        self.fail(p)
        self.assertIn("flags", p.stderr)
        self.write("arche.ini", "[app]\ntype = exe\nsources = main.cpp\n"
                                "include_dirs = $ENV{ARCHE_UNSET_9F3}\n")
        p = self.run_arche()
        self.fail(p)
        self.assertIn("ARCHE_UNSET_9F3", p.stderr)

    def test_compile_failure(self):
        self.write("good.cpp", "int good(){return 0;}\n")
        self.write("main.cpp", "int main(){return 0;}\n")
        self.write("bad.cpp", "int bad(){ this is not c++; }\n")
        self.write("arche.ini", "[app]\ntype = exe\nsources = main.cpp bad.cpp good.cpp\n")
        p = self.run_arche("-j", "4")
        self.fail(p, 1)
        self.assertIn("bad.cpp", p.stderr.lower())
        self.assertNotIn("traceback", p.stderr.lower())

    def test_dry_run_and_clean_all(self):
        self.static_project()
        p = self.run_arche("-n")
        self.ok(p)
        self.assertIn("[CC]", p.stdout)
        self.assertIn("$", p.stdout)
        self.assertFalse((self.tmp / "build").exists())
        self.ok(self.run_arche())
        self.assertTrue((self.tmp / "build").exists())
        self.ok(self.run_arche("--clean"))
        self.assertFalse((self.tmp / "build").exists())

    def test_toolchain_auto_and_wrong_platform(self):
        self.write("main.cpp", "int main(){return 0;}\n")
        self.write("arche.ini", "[*]\ntoolchain = auto\n\n[app]\ntype = exe\nsources = main.cpp\n")
        self.ok(self.run_arche())
        wrong = "gcc" if IS_WINDOWS else "msvc"
        self.write("arche.ini", f"[*]\ntoolchain = {wrong}\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\n")
        p = self.run_arche()
        self.fail(p)
        self.assertIn("不支持" if IS_WINDOWS else "只能在 Windows", p.stderr)

    @unittest.skipIf(IS_WINDOWS, "Windows 暂不支持 clang 本机工具链")
    def test_toolchain_clang(self):
        if not shutil.which("clang++") or not shutil.which("clang"):
            self.skipTest("没有 clang")
        self.write("main.cpp", "int main(){return 0;}\n")
        self.write("arche.ini", "[*]\ntoolchain = clang\n\n"
                                "[app]\ntype = exe\nsources = main.cpp\n")
        p = self.run_arche()
        self.ok(p)
        self.assertTrue(self.art("app").is_file())

    # ---- 平台相关 -------------------------------------------------------- #

    @unittest.skipUnless(IS_WINDOWS, "仅 Windows")
    def test_list_vs(self):
        p = self.run_arche("--list-vs")
        self.ok(p)
        self.assertIn("版本", p.stdout)
        if "可用" not in p.stdout:
            self.skipTest("没有可用的 MSVC")

    @unittest.skipUnless(IS_WINDOWS, "仅 Windows")
    def test_vs_config_in_ini(self):
        listing = self.run_arche("--list-vs")
        if listing.returncode != 0 or "2022" not in listing.stdout:
            self.skipTest("没有 VS2022")
        self.write("main.cpp", "int main(){return 0;}\n")
        self.write("arche.ini", "[*]\nvs = 2022\n\n[app]\ntype = exe\nsources = main.cpp\n")
        p = self.run_arche()
        self.ok(p)
        self.assertIn("MSVC 17.", p.stdout)

    @unittest.skipUnless(IS_WINDOWS, "仅 Windows")
    def test_copy_external_dlls(self):
        self.write("dlls/fake.dll", "fake")
        self.write("main.cpp", "int main(){return 0;}\n")
        self.write("arche.ini", "[app]\ntype = exe\nsources = main.cpp\n"
                                "copy_dlls = dlls\n")
        self.ok(self.run_arche())
        dest = self.art("app").parent / "fake.dll"
        self.assertTrue(dest.is_file())
        dest.unlink()
        self.ok(self.run_arche())
        self.assertTrue(dest.is_file(), "目标已是最新时也应补齐 DLL")

    @unittest.skipUnless(IS_WINDOWS, "仅 Windows")
    def test_vs_short_version_rejected(self):
        self.write("main.cpp", "int main(){return 0;}\n")
        self.write("arche.ini", "[*]\nvs = 17\n\n[app]\ntype = exe\nsources = main.cpp\n")
        p = self.run_arche()
        self.fail(p)
        self.assertIn("2019/2022/2026", p.stderr)

    @unittest.skipUnless(IS_WINDOWS, "仅 Windows")
    def test_msvc_asan_flags_and_dll_copy(self):
        self.write("main.cpp", "#include <cstdio>\nint main(){int* p=new int[2];"
                               "p[2]=1;std::printf(\"%d\\n\",p[2]);delete[] p;}\n")
        self.write("arche.ini",
                   "[*]\nconfig = debug\nflags = /fsanitize=address\n"
                   "ldflags = /ignore:4300\n"
                   "defines = _DISABLE_VECTOR_ANNOTATION _DISABLE_STRING_ANNOTATION\n\n"
                   "[app]\ntype = exe\nsources = main.cpp\n")
        p = self.run_arche()
        self.ok(p)
        exe = self.art("app")
        self.assertTrue(exe.is_file())
        dlls = list(exe.parent.glob("clang_rt.asan_dynamic*.dll"))
        self.assertTrue(dlls, "ASan 运行时 DLL 没有复制到 exe 旁")
        r = self.run_exe(exe)
        self.assertIn("AddressSanitizer", (r.stdout + r.stderr))

    @unittest.skipIf(IS_WINDOWS, "仅 Linux")
    def test_gcc_asan_flags(self):
        self.write("main.cpp", "#include <cstdio>\nint main(){int* p=new int[2];"
                               "p[2]=1;std::printf(\"%d\\n\",p[2]);delete[] p;}\n")
        self.write("arche.ini",
                   "[*]\nconfig = debug\n"
                   "flags = -fsanitize=address -fno-omit-frame-pointer\n"
                   "ldflags = -fsanitize=address\n\n"
                   "[app]\ntype = exe\nsources = main.cpp\n")
        self.ok(self.run_arche())
        r = self.run_exe(self.art("app"))
        self.assertIn("AddressSanitizer", (r.stdout + r.stderr))

    @unittest.skipUnless((NDK / "toolchains/llvm/prebuilt").is_dir(), "没有 Android NDK")
    def test_android_stl_modes(self):
        self.write("main.cpp", "#include <string>\n#include <cstdio>\n"
                               "int main(){std::string s=\"stl\";printf(\"%s\\n\",s.c_str());}\n")
        self.write("main.c", "int main(void){return 0;}\n")
        self.write("arche.ini",
                   f"[*]\ntoolchain = android-ndk\nndk = {NDK}\napi = 21\n"
                   "abi = arm64-v8a\nstl = c++_static\nstd = c++17\n\n"
                   "[app]\ntype = exe\nsources = main.cpp\n")
        self.ok(self.run_arche())
        host = "windows-x86_64" if IS_WINDOWS else "linux-x86_64"
        readelf = NDK / "toolchains/llvm/prebuilt" / host / "bin" / (
            "llvm-readelf.exe" if IS_WINDOWS else "llvm-readelf")
        if readelf.is_file():
            out = subprocess.run([str(readelf), "-d", str(self.tmp / "build/app/app")],
                                 capture_output=True, text=True, errors="replace")
            self.assertNotIn("libc++_shared.so", out.stdout)
        self.write("arche.ini",
                   f"[*]\ntoolchain = android-ndk\nndk = {NDK}\napi = 21\n"
                   "abi = arm64-v8a\nstl = none\n\n"
                   "[app]\ntype = exe\nsources = main.c\n")
        self.ok(self.run_arche("--force"))
        self.assertTrue((self.tmp / "build/app/app").is_file())

    @unittest.skipUnless((NDK / "toolchains/llvm/prebuilt").is_dir(), "没有 Android NDK")
    def test_android_cross_compile(self):
        self.write("inc/greet.h", "#pragma once\n#include <string>\n"
                                  "std::string greet(const std::string&);\n")
        self.write("src/greet.cpp", '#include "greet.h"\n'
                                    'std::string greet(const std::string& n){return "A "+n;}\n')
        self.write("src/main.cpp", '#include <cstdio>\n#include "greet.h"\n'
                                   'int main(){std::printf("%s\\n",greet("b").c_str());}\n')
        self.write("arche.ini",
                   f"[*]\ntoolchain = android-ndk\nndk = {NDK}\napi = 21\n"
                   "abi = arm64-v8a\nstd = c++17\nconfig = release\n\n"
                   "[greet]\ntype = shared\nsources = src/greet.cpp\ninclude_dirs = inc\n\n"
                   "[app]\ntype = exe\nsources = src/main.cpp\nrequires = greet\n")
        p = self.run_arche()
        self.ok(p)
        app = self.tmp / "build" / "app" / "app"
        so = self.tmp / "build" / "greet" / "libgreet.so"
        self.assertTrue(app.is_file())
        self.assertTrue(so.is_file())
        host = "windows-x86_64" if IS_WINDOWS else "linux-x86_64"
        readelf = NDK / "toolchains/llvm/prebuilt" / host / "bin" / (
            "llvm-readelf.exe" if IS_WINDOWS else "llvm-readelf")
        if readelf.is_file():
            out = subprocess.run([str(readelf), "-h", str(app)],
                                 capture_output=True, text=True, errors="replace")
            self.assertIn("AArch64", out.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
