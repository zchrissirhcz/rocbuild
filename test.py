import subprocess
import unittest
import platform
import shutil
import os


if platform.system() == 'Windows':
    os_name = 'windows'
elif platform.system() == 'Darwin':
    os_name = 'mac'
elif platform.system() == 'Linux':
    os_name = 'linux'


def decode(buf):
    try:
        return buf.decode('utf-8')
    except:
        return buf.decode('cp936')


def check_output(cmd):
    print('[cmd]', cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    out = p.stdout.read()
    p.communicate()
    # print(decode(out)) # debug
    return p.returncode, decode(out)


class RocBuildTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def check_generate(self, project_name, expected_ret=0, args=''):
        cmd = f'cmake -S tests/{project_name} -B build/{project_name} {args}'
        ret, out = check_output(cmd)
        self.assertEqual(expected_ret, ret, out)
        return out.replace('\r\n', '\n')

    def check_build(self, project_name, args=''):
        cmd = f'cmake --build build/{project_name} {args}'
        ret, out = check_output(cmd)
        self.assertEqual(0, ret, out)
        return out.replace('\r\n', '\n')

    def test_artifact_path(self):
        if os_name == 'windows':
            # determine if cl.exe is available
            ret, out = check_output('cl')
            if ret == 0:
                self.check_generate('artifacts_path', args='-G "Ninja Multi-Config"')
                self.check_build('artifacts_path', '--config Release')
                self.assertTrue(os.path.exists('build/artifacts_path/Release/foo_static.lib'))
                self.assertTrue(os.path.exists('build/artifacts_path/Release/foo_shared.dll'))
                self.assertTrue(os.path.exists('build/artifacts_path/Release/hello.exe'))
                self.assertTrue(os.path.exists('build/artifacts_path/Release/subfoo_static.lib'))
                self.assertTrue(os.path.exists('build/artifacts_path/Release/subfoo_shared.dll'))
                self.assertTrue(os.path.exists('build/artifacts_path/Release/subhello.exe'))
                shutil.rmtree('build/artifacts_path')

                self.check_generate('artifacts_path', args="-G Ninja")
                self.check_build('artifacts_path', '--config Release')
                self.assertTrue(os.path.exists('build/artifacts_path/foo_static.lib'))
                self.assertTrue(os.path.exists('build/artifacts_path/foo_shared.dll'))
                self.assertTrue(os.path.exists('build/artifacts_path/hello.exe'))
                self.assertTrue(os.path.exists('build/artifacts_path/subfoo_static.lib'))
                self.assertTrue(os.path.exists('build/artifacts_path/subfoo_shared.dll'))
                self.assertTrue(os.path.exists('build/artifacts_path/subhello.exe'))
                shutil.rmtree('build/artifacts_path')

            self.check_generate('artifacts_path')
            self.check_build('artifacts_path', '--config Release')
            self.assertTrue(os.path.exists('build/artifacts_path/Release/foo_static.lib'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/foo_shared.dll'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/hello.exe'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/subfoo_static.lib'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/subfoo_shared.dll'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/subhello.exe'))
            shutil.rmtree('build/artifacts_path')
        elif os_name == 'linux':
            self.check_generate('artifacts_path')
            self.check_build('artifacts_path')
            self.assertTrue(os.path.exists('build/artifacts_path/libfoo_static.a'))
            self.assertTrue(os.path.exists('build/artifacts_path/libfoo_shared.so'))
            self.assertTrue(os.path.exists('build/artifacts_path/hello'))
            self.assertTrue(os.path.exists('build/artifacts_path/libsubfoo_static.a'))
            self.assertTrue(os.path.exists('build/artifacts_path/libsubfoo_shared.so'))
            self.assertTrue(os.path.exists('build/artifacts_path/subhello'))
            shutil.rmtree('build/artifacts_path')
        elif os_name == 'mac':
            self.check_generate('artifacts_path')
            self.check_build('artifacts_path')
            self.assertTrue(os.path.exists('build/artifacts_path/libfoo_static.a'))
            self.assertTrue(os.path.exists('build/artifacts_path/libfoo_shared.dylib'))
            self.assertTrue(os.path.exists('build/artifacts_path/hello'))
            self.assertTrue(os.path.exists('build/artifacts_path/libsubfoo_static.a'))
            self.assertTrue(os.path.exists('build/artifacts_path/libsubfoo_shared.dylib'))
            self.assertTrue(os.path.exists('build/artifacts_path/subhello'))
            shutil.rmtree('build/artifacts_path')

    def test_debug_postfix(self):
        if os_name == 'windows':
            # msbuild
            self.check_generate('debug_postfix')
            self.check_build('debug_postfix', '--config Debug')
            self.assertTrue(os.path.exists('build/debug_postfix/Debug/foo_d.lib'))
            self.assertTrue(os.path.exists('build/debug_postfix/Debug/hello_d.exe'))
            shutil.rmtree('build/debug_postfix')

            ret, out = check_output('cl')
            if ret == 0:
                # ninja
                self.check_generate('debug_postfix', args='-G Ninja')
                self.check_build('debug_postfix')
                self.assertTrue(os.path.exists('build/debug_postfix/foo.lib'))
                self.assertTrue(os.path.exists('build/debug_postfix/hello.exe'))
                shutil.rmtree('build/debug_postfix')

                self.check_generate('debug_postfix', args='-G Ninja -DCMAKE_BUILD_TYPE=Debug')
                self.check_build('debug_postfix')
                self.assertTrue(os.path.exists('build/debug_postfix/foo.lib'))
                self.assertTrue(os.path.exists('build/debug_postfix/hello.exe'))
                shutil.rmtree('build/debug_postfix')

                # Ninja Multi-Config
                self.check_generate('debug_postfix', args='-G "Ninja Multi-Config"')
                self.check_build('debug_postfix', '--config Debug')
                self.assertTrue(os.path.exists('build/debug_postfix/Debug/foo_d.lib'))
                self.assertTrue(os.path.exists('build/debug_postfix/Debug/hello_d.exe'))
                shutil.rmtree('build/debug_postfix')
        else:
            # Ninja Multi-Config
            self.check_generate('debug_postfix', args='-G "Ninja Multi-Config"')
            self.check_build('debug_postfix')
            self.assertTrue(os.path.exists('build/debug_postfix/Debug/libfoo_d.a'))
            self.assertTrue(os.path.exists('build/debug_postfix/Debug/hello_d'))
            shutil.rmtree('build/debug_postfix')

            # make
            self.check_generate('debug_postfix')
            self.check_build('debug_postfix')
            self.assertTrue(os.path.exists('build/debug_postfix/libfoo.a'))
            self.assertTrue(os.path.exists('build/debug_postfix/hello'))
            shutil.rmtree('build/debug_postfix')

            self.check_generate('debug_postfix', args='-DCMAKE_BUILD_TYPE=Debug')
            self.check_build('debug_postfix')
            self.assertTrue(os.path.exists('build/debug_postfix/libfoo.a'))
            self.assertTrue(os.path.exists('build/debug_postfix/hello'))
            shutil.rmtree('build/debug_postfix')

    def test_hide_symbols(self):
        if os_name == 'linux':
            self.check_generate('hide_symbols', args='-DHIDDEN=1')
            self.check_build('hide_symbols')
            cmd = 'nm -C build/hide_symbols/libbar.so | grep " T "'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            out = out.replace('\r\n', '\n')
            lines = out.strip().split('\n')
            self.assertEqual(len(lines), 1, lines)
            self.assertTrue(lines[0].endswith(' T bar'))
            shutil.rmtree('build/hide_symbols')

            self.check_generate('hide_symbols', args='-DHIDDEN=0')
            self.check_build('hide_symbols')
            cmd = f'nm -C build/hide_symbols/libbar.so | grep " T "'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            out = out.replace('\r\n', '\n')
            lines = out.strip().split('\n')
            self.assertEqual(len(lines), 2, lines)
            self.assertTrue(lines[0].endswith(' T bar'))
            self.assertTrue(lines[1].endswith(' T bar_internal'))
            shutil.rmtree('build/hide_symbols')
        elif os_name == 'mac':
            self.check_generate('hide_symbols', args='-DHIDDEN=1')
            self.check_build('hide_symbols')
            cmd = 'nm -C build/hide_symbols/libbar.dylib | grep " T "'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            out = out.replace('\r\n', '\n')
            lines = out.strip().split('\n')
            self.assertEqual(len(lines), 1, lines)
            self.assertTrue(lines[0].endswith(' T _bar'))
            shutil.rmtree('build/hide_symbols')

            self.check_generate('hide_symbols', args='-DHIDDEN=0')
            self.check_build('hide_symbols')
            cmd = f'nm -C build/hide_symbols/libbar.dylib | grep " T "'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            out = out.replace('\r\n', '\n')
            lines = out.strip().split('\n')
            self.assertEqual(len(lines), 2, lines)
            self.assertTrue(lines[0].endswith(' T _bar'))
            self.assertTrue(lines[1].endswith(' T _bar_internal'))
            shutil.rmtree('build/hide_symbols')

    def test_copy_dlls(self):
        if os_name == 'windows':
            self.check_generate('copy_dlls', args='-DCOPY_DLLS=0')
            self.check_build('copy_dlls', args='--config Release')
            items = os.listdir('build/copy_dlls/test/Release')
            self.assertEqual(len(items), 1, items)
            self.assertTrue(items[0] == 'test.exe')
            shutil.rmtree('build/copy_dlls')

            self.check_generate('copy_dlls', args='-DCOPY_DLLS=1')
            self.check_build('copy_dlls', args='--config Release')
            items = os.listdir('build/copy_dlls/test/Release')
            self.assertEqual(len(items), 4)
            self.assertTrue(items[0] == 'bar.dll')
            self.assertTrue(items[1] == 'baz.dll')
            self.assertTrue(items[2] == 'foo.dll')
            self.assertTrue(items[3] == 'test.exe')
            shutil.rmtree('build/copy_dlls')

    def test_link_as_needed(self):
        if os_name == 'linux':
            self.check_generate('link_as_needed', args='-DLINK_AS_NEEDED=0')
            self.check_build('link_as_needed')
            cmd = 'ldd build/link_as_needed/libfoo_math.so'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            self.assertIn('libfoo.so =>', out)
            shutil.rmtree('build/link_as_needed')

            self.check_generate('link_as_needed', args='-DLINK_AS_NEEDED=1')
            self.check_build('link_as_needed')
            cmd = 'ldd build/link_as_needed/libfoo_math.so'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            self.assertTrue('libfoo.so =>' not in out)
            shutil.rmtree('build/link_as_needed')
        elif os_name == 'mac':
            self.check_generate('link_as_needed', args='-DLINK_AS_NEEDED=0')
            self.check_build('link_as_needed')
            cmd = 'otool -L build/link_as_needed/libfoo_math.dylib'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            self.assertIn('@rpath/libfoo.dylib', out)
            shutil.rmtree('build/link_as_needed')

            self.check_generate('link_as_needed', args='-DLINK_AS_NEEDED=1')
            self.check_build('link_as_needed')
            cmd = 'otool -L build/link_as_needed/libfoo_math.dylib'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            self.assertTrue('@rpath/libfoo.dylib' not in out)
            shutil.rmtree('build/link_as_needed')

    def test_unused_data_and_function(self):
        if os_name == 'mac':
            self.check_generate('unused_data_and_function', args='-DCMAKE_BUILD_TYPE=Release -DREMOVE_UNUSED_DATA_AND_FUNCTION=0')
            self.check_build('unused_data_and_function')
            cmd = 'objdump -t build/unused_data_and_function/test'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            out = out.replace('\r\n', '\n')
            lines = out.strip().split('\n')
            self.assertTrue(any(line.strip().endswith("g     F __TEXT,__text _unused_function") for line in lines))
            self.assertTrue(any(line.strip().endswith("g     O __DATA,__data _unused_global_variable") for line in lines))
            shutil.rmtree('build/unused_data_and_function')

            self.check_generate('unused_data_and_function', args='-DCMAKE_BUILD_TYPE=Release -DREMOVE_UNUSED_DATA_AND_FUNCTION=1')
            self.check_build('unused_data_and_function')
            cmd = 'objdump -t build/unused_data_and_function/test'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            out = out.replace('\r\n', '\n')
            lines = out.strip().split('\n')
            self.assertTrue(all(not line.strip().endswith("g     F __TEXT,__text _unused_function") for line in lines))
            self.assertTrue(all(not line.strip().endswith("g     O __DATA,__data _unused_global_variable") for line in lines))
            shutil.rmtree('build/unused_data_and_function')
        elif os_name == 'linux':
            self.check_generate('unused_data_and_function', args='-DCMAKE_BUILD_TYPE=Release -DREMOVE_UNUSED_DATA_AND_FUNCTION=0')
            self.check_build('unused_data_and_function')
            cmd = 'objdump -t build/unused_data_and_function/test'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            out = out.replace('\r\n', '\n')
            lines = out.strip().split('\n')
            self.assertTrue(any(line.strip().endswith(" unused_function") for line in lines))
            self.assertTrue(any(line.strip().endswith(" unused_global_variable") for line in lines))
            shutil.rmtree('build/unused_data_and_function')

            self.check_generate('unused_data_and_function', args='-DCMAKE_BUILD_TYPE=Release -DREMOVE_UNUSED_DATA_AND_FUNCTION=1')
            self.check_build('unused_data_and_function')
            cmd = 'objdump -t build/unused_data_and_function/test'
            ret, out = check_output(cmd)
            self.assertEqual(0, ret, out)
            out = out.replace('\r\n', '\n')
            lines = out.strip().split('\n')
            self.assertTrue(all(not line.strip().endswith(" unused_function") for line in lines))
            self.assertTrue(all(not line.strip().endswith(" unused_global_variable") for line in lines))
            shutil.rmtree('build/unused_data_and_function')

if __name__ == "__main__":
    unittest.main()