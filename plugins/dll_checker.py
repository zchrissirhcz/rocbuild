import pefile
import os
import sys

def get_search_paths(exe_path):
    paths = []
    exe_dir = os.path.dirname(os.path.abspath(exe_path))
    system32 = os.path.join(os.environ['WINDIR'], 'System32')
    syswow64 = os.path.join(os.environ['WINDIR'], 'SysWOW64')
    env_paths = os.environ['PATH'].split(';')
    # 查找路径（可视系统、位数实际调整增减顺序）
    paths = [exe_dir, system32, syswow64] + env_paths
    # 去重
    paths = list(dict.fromkeys([p for p in paths if os.path.isdir(p)]))
    return paths

def find_dll(dll_name, paths):
    for p in paths:
        candidate = os.path.join(p, dll_name)
        if os.path.isfile(candidate):
            return candidate
    return None

def list_imported_dlls_and_paths(pe_path):
    pe = pefile.PE(pe_path)
    dlls = []
    search_paths = get_search_paths(pe_path)
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll = entry.dll.decode('ascii')
            path = find_dll(dll, search_paths)
            if path:
                status = f"\t{dll} => {path}"
            else:
                status = f"\t{dll} => not found"
            dlls.append(status)
    return dlls

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dll_checker.py <exe_path>")
        sys.exit(1)
    exe_path = sys.argv[1]
    if not os.path.exists(exe_path):
        print(f"Error: exe file <exe_path> does not exist!")
        sys.exit(2)
    for info in list_imported_dlls_and_paths(exe_path):
        print(info)
