import subprocess
import unittest
import platform
import shutil
import os


if platform.system() == 'Windows':
    PLATFORM = 'vs2022'
elif platform.system() == 'Darwin':
    PLATFORM = 'mac'
elif platform.system() == 'Linux':
    PLATFORM = 'linux'


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
        if PLATFORM.startswith('vs'):
            self.check_generate('artifacts_path')
            self.check_build('artifacts_path', '--config Release')
            self.assertTrue(os.path.exists('build/artifacts_path/Release/foo_static.lib'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/foo_shared.dll'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/hello.exe'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/subfoo_static.lib'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/subfoo_shared.dll'))
            self.assertTrue(os.path.exists('build/artifacts_path/Release/subhello.exe'))
        elif PLATFORM == 'linux':
            self.check_generate('artifacts_path')
            self.check_build('artifacts_path')
            self.assertTrue(os.path.exists('build/artifacts_path/libfoo_static.a'))
            self.assertTrue(os.path.exists('build/artifacts_path/libfoo_shared.so'))
            self.assertTrue(os.path.exists('build/artifacts_path/hello'))
            self.assertTrue(os.path.exists('build/artifacts_path/libsubfoo_static.a'))
            self.assertTrue(os.path.exists('build/artifacts_path/libsubfoo_shared.so'))
            self.assertTrue(os.path.exists('build/artifacts_path/subhello'))
        elif PLATFORM == 'mac':
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