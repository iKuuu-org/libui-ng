"""只在预构建仓库的 CI 使用；应用开发者直接下载 Release。"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
target = os.environ['LIBUI_PLATFORM']
arch = os.environ['LIBUI_ARCH']
host_arch = 'arm64' if platform.machine().lower() in ('aarch64', 'arm64') else 'x64'
if arch != host_arch:
    raise RuntimeError('Build on a native runner of the requested architecture')
subprocess.run([sys.executable, '-m', 'pip', 'install', 'meson==1.3.2', 'ninja==1.11.1.3'], check=True)
if target == 'windows':
    vswhere = Path(os.environ['ProgramFiles(x86)']) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    vs = subprocess.check_output([str(vswhere), '-latest', '-products', '*', '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'], text=True).strip()
    devcmd = Path(vs) / 'Common7/Tools/VsDevCmd.bat'
    command = f'call "{devcmd}" -arch=x64 -host_arch=x64 >nul && set'
    settings = subprocess.check_output(f'cmd /d /s /c "{command}"', text=True, errors='replace')
    os.environ.update(line.split('=', 1) for line in settings.splitlines() if '=' in line and not line.startswith('='))
if target == 'macos':
    os.environ['MACOSX_DEPLOYMENT_TARGET'] = '11.0' if arch == 'arm64' else '10.15'

options = ['--buildtype=release', '--default-library=shared', '-Dtests=false', '-Dexamples=false']
if target == 'windows':
    options.append('-Db_vscrt=mt')
subprocess.run([sys.executable, '-m', 'mesonbuild.mesonmain', 'setup', 'build', *options], check=True)
subprocess.run([sys.executable, '-m', 'mesonbuild.mesonmain', 'compile', '-C', 'build'], check=True)
out = ROOT / 'build/meson-out'
name = {'windows': 'libui.dll', 'linux': 'libui.so', 'macos': 'libui.dylib'}[target]
library = out / name
smoke = out / ('smoke.exe' if target == 'windows' else 'smoke')
if target == 'windows':
    subprocess.run(['cl.exe', '/nologo', '/MT', '/I.', 'packaging/smoke.c', str(out / 'libui.lib'), '/Fe:' + str(smoke)], check=True)
    dependencies = subprocess.check_output(['dumpbin.exe', '/DEPENDENTS', str(library)], text=True, errors='replace')
    if re.search(r'(MSVCP|VCRUNTIME|api-ms-win-crt|ucrtbase)', dependencies, re.I):
        raise RuntimeError('The standalone DLL must not need an external VC runtime')
else:
    subprocess.run(['cc', '-I.', 'packaging/smoke.c', str(library), '-Wl,-rpath,' + str(out), '-o', str(smoke)], check=True)
    dependencies = subprocess.check_output(['readelf', '--version-info', str(library)] if target == 'linux' else ['otool', '-L', str(library)], text=True)
    if target == 'linux':
        versions = [tuple(map(int, v.split('.'))) for v in re.findall(r'GLIBC_([0-9.]+)', dependencies)]
        if max(versions) > (2, 31):
            raise RuntimeError('The Linux library exceeds the glibc 2.31 baseline')
subprocess.run((['xvfb-run', '-a'] if target == 'linux' else []) + [str(smoke)], check=True, timeout=30)

revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
metadata = {
    'source': 'https://github.com/iKuuu-org/libui-ng', 'commit': revision,
    'upstream': '43ba1ef553c8993a43a67f1ce6e35983a2660d8c',
    'platform': target, 'arch': arch,
    'library_sha256': hashlib.sha256(library.read_bytes()).hexdigest(),
    'dependencies': dependencies,
}
dist = ROOT / 'dist'
dist.mkdir(exist_ok=True)
archive = dist / f'libui-{target}-{arch}.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
    output.write(library, name)
    output.write(ROOT / 'LICENSE.md', 'LICENSE.md')
    output.writestr('SOURCE.json', json.dumps(metadata, indent=2) + '\n')
print(archive, hashlib.sha256(archive.read_bytes()).hexdigest())
