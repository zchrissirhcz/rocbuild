#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

PKG_REPO = "/Users/zz/play/pkgs"

def install_package(recipe: str):
    """
    @param recipe: <pkg_name>/<pkg_version>
    e.g. CLI11/2.3.2
    """

    rocpkg_dir = Path('.rocpkg')
    rocpkg_dir.mkdir(exist_ok=True)
    
    pkg_name, pkg_version = recipe.split('/')
    install_cmd = f'git clone {PKG_REPO} -b {pkg_name}/{pkg_version} .rocpkg/{pkg_name}-{pkg_version}'
    
    print(f'[debug] install cmd: {install_cmd}')
    
    try:
        subprocess.run(install_cmd, shell=True, check=True)
        print(f'[info] success {recipe}')
    except subprocess.CalledProcessError as e:
        print(f'[error] failed: {e}', file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print('Usage: rocpkg install <包名>/<版本号>')
        print('e.g.: rocpkg install CLI11/2.4.2')
        sys.exit(1)
        
    command = sys.argv[1]
    if command != 'install':
        print(f'[error] unknown command: {command}')
        sys.exit(1)
        
    recipe = sys.argv[2]
    if '/' not in recipe:
        print('[error] failed to parse recipe. format: <pkg_name>/<pkg_version>')
        sys.exit(1)
        
    install_package(recipe)

def examples():
    install_package("CLI11/2.3.2")

if __name__ == '__main__':
    main()
