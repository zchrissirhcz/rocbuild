import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import juicy

IS_WINDOWS = os.name == "nt"
IS_LINUX = sys.platform.startswith("linux")

# Local toolchain roots for the optional integration tests.
# Override via these environment variables, or edit the defaults on another machine.
ANDROID_NDK_ROOT = Path(os.environ.get(
    "JUICY_TEST_ANDROID_NDK", r"C:\soft\toolchains\android-ndk\r27c"))
QNX_SDP_ROOT = Path(os.environ.get(
    "JUICY_TEST_QNX_SDP", r"C:\soft\toolchains\qnx800"))
MINGW_ROOT = Path(os.environ.get(
    "JUICY_TEST_MINGW", r"C:\soft\toolchains\MinGW"))
PROJECT_ROOT = Path(__file__).resolve().parent
TEST_BUILD_ROOT = PROJECT_ROOT / "build-tests"
HAS_CMAKE = shutil.which("cmake") is not None
HAS_NINJA = shutil.which("ninja") is not None


def fresh_build_dir(name):
    build = TEST_BUILD_ROOT / name
    if build.exists():
        shutil.rmtree(build)
    build.mkdir(parents=True)
    return build


def parse(platform, *argv):
    parser = juicy.build_parser(platform)
    return parser.parse_known_args(list(argv))


def write_cache(build_dir, *lines):
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "CMakeCache.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


class PlatformSelectionTests(unittest.TestCase):
    def test_explicit_platform(self):
        cases = [
            (["-p", "android"], "android"),
            (["--platform=mingw"], "mingw"),
            (["-pqnx"], "qnx"),
            ([], None),
            (["-p", "bad"], None),
        ]
        for argv, expected in cases:
            with self.subTest(argv=argv):
                self.assertEqual(juicy.explicit_platform(argv), expected)

    def test_platforms(self):
        expected = set(juicy.VS_PLATFORMS) | {"android", "qnx", "mingw", "linux"}
        self.assertEqual(set(juicy.PLATFORMS), expected)

    def test_native_arch(self):
        cases = (("AMD64", "x64"), ("x86_64", "x64"),
                 ("aarch64", "arm64"), ("riscv64", "riscv64"))
        for machine, expected in cases:
            with self.subTest(machine=machine):
                with mock.patch("juicy.host_platform.machine", return_value=machine):
                    self.assertEqual(juicy.native_arch(), expected)

    @unittest.skipUnless(IS_WINDOWS, "Windows native platform")
    def test_windows_detects_latest_vs(self):
        if "WSL_DISTRO_NAME" in os.environ:
            self.skipTest("WSL environment")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            installs = []
            for version, name in (("17.0.1", "2022"), ("18.0.1", "2026")):
                vcvars = root / name / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
                vcvars.parent.mkdir(parents=True)
                vcvars.write_text("", encoding="utf-8")
                installs.append((version, str(root / name)))
            with mock.patch("juicy.get_vs_installations", return_value=installs):
                self.assertEqual(juicy.detect_platform(), "vs2026")

    @unittest.skipUnless(IS_WINDOWS, "Windows native platform")
    def test_windows_no_vs(self):
        with mock.patch("juicy.get_vs_installations", return_value=[]):
            self.assertIsNone(juicy.detect_platform())

    @unittest.skipUnless(IS_WINDOWS, "Windows native platform")
    def test_windows_wsl_returns_none(self):
        with mock.patch.dict(juicy.os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}):
            self.assertIsNone(juicy.detect_platform())

    @unittest.skipUnless(IS_LINUX, "Linux native platform")
    def test_linux_detects_native(self):
        self.assertEqual(juicy.detect_platform(), "linux")


class ParserTests(unittest.TestCase):
    def test_defaults(self):
        cases = {
            "vs2026": ("x64", "Visual Studio 18 2026"),
            "vs2022": ("x64", "Visual Studio 17 2022"),
            "vs2019": ("x64", "Visual Studio 16 2019"),
            "android": ("arm64-v8a", "Ninja"),
            "qnx": ("aarch64", "Ninja"),
            "mingw": ("x86_64", "Ninja"),
            "linux": (juicy.native_arch(), "Ninja"),
        }
        for platform, (arch, generator) in cases.items():
            with self.subTest(platform=platform):
                argv = ["-p", platform]
                if platform in ("android", "qnx"):
                    argv += ["-r", "dummy"]
                args, _ = parse(platform, *argv)
                self.assertEqual(args.arch, arch)
                self.assertEqual(juicy.effective_generator(args), generator)

    def test_root_required(self):
        for platform in ("android", "qnx"):
            with self.subTest(platform=platform):
                with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
                    parse(platform, "-p", platform)

    def test_android_options(self):
        args, _ = parse(
            "android", "-p", "android", "-r", "root",
            "--api", "24", "--stl", "c++_shared", "--arm-mode", "arm")
        self.assertEqual(args.api, "24")
        self.assertEqual(args.stl, "c++_shared")
        self.assertEqual(args.arm_mode, "arm")

    def test_short_help_is_platform_specific(self):
        android = juicy.build_parser("android").format_help()
        self.assertIn("NDK 根目录", android)
        self.assertNotIn("QNX SDP 根目录", android)

        qnx = juicy.build_parser("qnx").format_help()
        self.assertIn("QNX SDP 根目录", qnx)
        self.assertNotIn("NDK 根目录", qnx)

        linux = juicy.build_parser("linux").format_help()
        self.assertIn("本机架构", linux)
        self.assertNotIn("NDK 根目录", linux)

    def test_general_help(self):
        text = juicy.build_parser(None, full_help=True).format_help()
        self.assertIn("linux", text)
        self.assertIn("android", text)
        self.assertIn("QNX SDP", text)


class CrossCommandTests(unittest.TestCase):
    def test_android_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            toolchain = root / "build" / "cmake" / "android.toolchain.cmake"
            toolchain.parent.mkdir(parents=True)
            toolchain.write_text("", encoding="utf-8")
            args, extra = parse(
                "android", "-p", "android", "-a", "armv8-a", "-r", str(root),
                "--api", "24", "--stl", "c++_shared", "--arm-mode", "arm",
                "-S", ".", "-B", "build")
            cmd, env = juicy.make_cmd(args, extra)
            resolved = root.resolve()
        self.assertIn(
            f"-DCMAKE_TOOLCHAIN_FILE={juicy.TOOLCHAIN_DIR / 'android-ndk.cmake'}", cmd)
        self.assertIn(f"-DJUICY_TOOLCHAIN_ROOT={resolved}", cmd)
        self.assertIn("-DANDROID_ABI=arm64-v8a", cmd)
        self.assertIn("-DANDROID_PLATFORM=24", cmd)
        self.assertIn("-DANDROID_STL=c++_shared", cmd)
        self.assertIn("-DANDROID_ARM_MODE=arm", cmd)
        self.assertIsNone(env)

    def test_qnx_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch("juicy.qnx_env", return_value={"QNX": "1"}):
                args, extra = parse(
                    "qnx", "-p", "qnx", "-r", str(root), "-S", ".", "-B", "build")
                cmd, env = juicy.make_cmd(args, extra)
            resolved = root.resolve()
        self.assertIn(
            f"-DCMAKE_TOOLCHAIN_FILE={juicy.TOOLCHAIN_DIR / 'qnx-aarch64.cmake'}", cmd)
        self.assertIn(f"-DJUICY_TOOLCHAIN_ROOT={resolved}", cmd)
        self.assertIn("Ninja", cmd)
        self.assertEqual(env, {"QNX": "1"})

    def test_mingw_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args, extra = parse(
                "mingw", "-p", "mingw", "-a", "x64", "-r", str(root),
                "-S", ".", "-B", "build")
            cmd, env = juicy.make_cmd(args, extra)
            resolved = root.resolve()
        self.assertIn(
            f"-DCMAKE_TOOLCHAIN_FILE={juicy.TOOLCHAIN_DIR / 'mingw-x86_64.cmake'}", cmd)
        self.assertIn(f"-DJUICY_TOOLCHAIN_ROOT={resolved}", cmd)
        self.assertIsNone(env)

    @unittest.skipUnless(IS_WINDOWS, "MinGW root defaults on Windows")
    def test_mingw_default_root_is_left_to_toolchain(self):
        args, extra = parse("mingw", "-p", "mingw", "-S", ".", "-B", "build")
        cmd, env = juicy.make_cmd(args, extra)
        self.assertFalse(any("JUICY_TOOLCHAIN_ROOT" in arg for arg in cmd))
        self.assertIsNone(env)

    @unittest.skipUnless(IS_LINUX, "Linux requires -r for MinGW")
    def test_mingw_requires_root_on_linux(self):
        args, extra = parse("mingw", "-p", "mingw")
        with self.assertRaises(SystemExit):
            juicy.make_cmd(args, extra)


@unittest.skipUnless(IS_WINDOWS, "Windows native platform")
class WindowsNativeTests(unittest.TestCase):
    def test_vs_command(self):
        for platform, generator in juicy.VS_PLATFORMS.items():
            with self.subTest(platform=platform):
                args, extra = parse(
                    platform, "-p", platform, "-a", "x64", "-S", ".", "-B", "build",
                    "-DCMAKE_BUILD_TYPE=Release")
                cmd, env = juicy.make_cmd(args, extra)
                self.assertEqual(
                    cmd[:7],
                    ["cmake", "-S", ".", "-B", "build", "-G", generator])
                self.assertEqual(cmd[cmd.index("-A") + 1], "x64")
                self.assertIn("-DCMAKE_BUILD_TYPE=Release", cmd)
                self.assertIsNone(env)

    def test_vs_ninja_env(self):
        with mock.patch("juicy.msvc_env", return_value={"VS": "1"}):
            args, extra = parse(
                "vs2022", "-p", "vs2022", "-G", "Ninja", "-S", ".", "-B", "build")
            cmd, env = juicy.make_cmd(args, extra)
        self.assertNotIn("-A", cmd)
        self.assertEqual(env, {"VS": "1"})

    def test_vs_build_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vcvars = root / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
            vcvars.parent.mkdir(parents=True)
            vcvars.write_text("", encoding="utf-8")
            compiler = root / "VC" / "Tools" / "MSVC" / "14" / "bin" / \
                "Hostx64" / "x64" / "cl.exe"
            compiler.parent.mkdir(parents=True)
            compiler.write_text("", encoding="utf-8")
            build = root / "build"
            write_cache(
                build, f"CMAKE_CXX_COMPILER:FILEPATH={compiler}",
                "CMAKE_GENERATOR:INTERNAL=Ninja")
            with mock.patch(
                    "juicy.get_vs_installations",
                    return_value=[("17.0", str(root))]), \
                    mock.patch("juicy.vcvars_env", return_value={"VS": "1"}):
                self.assertEqual(juicy.build_env(build), {"VS": "1"})

    def test_linux_platform_rejected(self):
        args, extra = parse("linux", "-p", "linux", "-a", "x64")
        with self.assertRaises(SystemExit):
            juicy.make_cmd(args, extra)


@unittest.skipUnless(IS_LINUX, "Linux native platform")
class LinuxNativeTests(unittest.TestCase):
    def test_linux_command(self):
        args, extra = parse("linux", "-p", "linux", "-S", ".", "-B", "build")
        cmd, env = juicy.make_cmd(args, extra)
        self.assertEqual(cmd, ["cmake", "-S", ".", "-B", "build", "-G", "Ninja"])
        self.assertIsNone(env)

    def test_linux_build_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            write_cache(
                build, "CMAKE_CXX_COMPILER:FILEPATH=/usr/bin/c++",
                "CMAKE_GENERATOR:INTERNAL=Ninja")
            with mock.patch("juicy.get_vs_installations", return_value=[]):
                self.assertIsNone(juicy.build_env(build))

    def test_vs_platform_rejected(self):
        args, extra = parse("vs2022", "-p", "vs2022", "-a", "x64")
        with self.assertRaises(SystemExit):
            juicy.make_cmd(args, extra)

    def test_arch_must_be_native(self):
        bad = "arm64" if juicy.native_arch() != "arm64" else "x64"
        args, extra = parse("linux", "-p", "linux", "-a", bad)
        with self.assertRaises(SystemExit):
            juicy.make_cmd(args, extra)


class BuildEnvTests(unittest.TestCase):
    def test_qnx_cached_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "qnxsdp-env.bat").write_text("", encoding="utf-8")
            build = root / "build"
            write_cache(
                build, f"JUICY_TOOLCHAIN_ROOT:INTERNAL={root}",
                "CMAKE_GENERATOR:INTERNAL=Ninja")
            with mock.patch("juicy.qnx_env", return_value={"QNX": "1"}):
                self.assertEqual(juicy.build_env(build), {"QNX": "1"})

    def test_qnx_compiler_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "qnxsdp-env.bat").write_text("", encoding="utf-8")
            compiler = root / "host" / "win64" / "x86_64" / "usr" / "bin" / \
                "ntoaarch64-gcc.exe"
            compiler.parent.mkdir(parents=True)
            build = root / "build"
            write_cache(
                build, f"CMAKE_C_COMPILER:FILEPATH={compiler}",
                "CMAKE_GENERATOR:INTERNAL=Ninja")
            with mock.patch("juicy.qnx_env", return_value={"QNX": "1"}):
                self.assertEqual(juicy.build_env(build), {"QNX": "1"})


@unittest.skipUnless(HAS_CMAKE and HAS_NINJA, "cmake/ninja not found")
class LocalToolchainTests(unittest.TestCase):
    def _build(self, name, platform, root, arch, artifact):
        if not root.is_dir():
            self.skipTest(f"missing toolchain: {root}")
        build = fresh_build_dir(name)
        configure = [
            "-p", platform, "-a", arch, "-r", str(root),
            "-S", str(PROJECT_ROOT), "-B", str(build),
        ]
        self.assertEqual(juicy.main(configure), 0)
        self.assertTrue((build / "CMakeCache.txt").is_file())
        self.assertEqual(juicy.main(["build", "-B", str(build)]), 0)
        self.assertTrue((build / artifact).is_file())

    def test_android(self):
        self._build("android", "android", ANDROID_NDK_ROOT, "armv8-a", "hello")

    def test_qnx(self):
        self._build("qnx", "qnx", QNX_SDP_ROOT, "aarch64", "hello")

    def test_mingw(self):
        self._build("mingw", "mingw", MINGW_ROOT, "x86_64", "hello.exe")


@unittest.skipUnless(IS_WINDOWS, "Windows native build")
@unittest.skipUnless(HAS_CMAKE, "cmake not found")
class WindowsNativeBuildTests(unittest.TestCase):
    def test_native_build(self):
        platform = juicy.detect_platform()
        if platform is None:
            self.skipTest("no Visual Studio")
        for extra, name in (([], "windows-auto"), (["-p", platform], f"windows-{platform}")):
            with self.subTest(argv=extra):
                build = fresh_build_dir(name)
                self.assertEqual(
                    juicy.main(
                        [*extra, "-S", str(PROJECT_ROOT), "-B", str(build)]),
                    0)
                self.assertTrue((build / "CMakeCache.txt").is_file())
                self.assertEqual(juicy.main(["build", "-B", str(build)]), 0)
                self.assertTrue((build / "Debug" / "hello.exe").is_file())


@unittest.skipUnless(IS_LINUX, "Linux native build")
@unittest.skipUnless(HAS_CMAKE and HAS_NINJA, "cmake/ninja not found")
class LinuxNativeBuildTests(unittest.TestCase):
    def test_native_builds(self):
        cases = [
            ([], "linux-auto"),
            (["-p", "linux"], "linux-platform"),
            (["-p", "linux", "-a", juicy.native_arch()], "linux-arch"),
        ]
        for extra, name in cases:
            with self.subTest(case=name):
                build = fresh_build_dir(name)
                self.assertEqual(
                    juicy.main(
                        [*extra, "-S", str(PROJECT_ROOT), "-B", str(build)]),
                    0)
                self.assertTrue((build / "CMakeCache.txt").is_file())
                self.assertEqual(juicy.main(["build", "-B", str(build)]), 0)
                exe = build / "hello"
                self.assertTrue(exe.is_file())
                result = subprocess.run(
                    [str(exe)], capture_output=True, text=True)
                self.assertEqual(result.stdout.strip(), "hello")


class ToolTests(unittest.TestCase):
    def test_missing_cmake(self):
        with mock.patch("juicy.shutil.which", return_value=None):
            with self.assertRaises(SystemExit) as ctx:
                juicy.ensure_cmake()
        self.assertIn("cmake", str(ctx.exception))

    def test_missing_ninja(self):
        with mock.patch("juicy.shutil.which", return_value=None):
            with self.assertRaises(SystemExit) as ctx:
                juicy.ensure_ninja("Ninja", [])
        self.assertIn("ninja", str(ctx.exception))

    def test_custom_make_program_skips_ninja_check(self):
        with mock.patch("juicy.shutil.which", return_value=None):
            juicy.ensure_ninja("Ninja", ["-DCMAKE_MAKE_PROGRAM=ninja"])

    def test_run_prints_command(self):
        out = io.StringIO()
        with mock.patch("juicy.shutil.which", return_value="tool"), \
                mock.patch("juicy.subprocess.call", return_value=0), \
                redirect_stdout(out):
            self.assertEqual(juicy.run(["cmake", "--build", "build"]), 0)
        self.assertIn(
            "[juicy.py] running cmake command: cmake --build build",
            out.getvalue())


if __name__ == "__main__":
    unittest.main()
