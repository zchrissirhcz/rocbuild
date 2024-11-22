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

            self.check_generate('artifacts_path', args='-G "Visual Studio 17 2022" -A x64')
            self.check_build('artifacts_path', '--config Release')
            self.assertTrue(os.path.exists('build/artifacts_path/Release/foo_static.lib'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/foo_shared.dll'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/hello.exe'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/subfoo_static.lib'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/subfoo_shared.dll'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/subhello.exe'))
        elif os_name == 'linux':
            self.check_generate('artifacts_path')
            self.check_build('artifacts_path')
            self.assertTrue(os.path.exists('build/artifacts_path/libfoo_static.a'))
            self.assertTrue(os.path.exists('build/artifacts_path/libfoo_shared.so'))
            self.assertTrue(os.path.exists('build/artifacts_path/hello'))
            self.assertTrue(os.path.exists('build/artifacts_path/libsubfoo_static.a'))
            self.assertTrue(os.path.exists('build/artifacts_path/libsubfoo_shared.so'))
            self.assertTrue(os.path.exists('build/artifacts_path/subhello'))
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


if __name__ == "__main__":
    unittest.main()