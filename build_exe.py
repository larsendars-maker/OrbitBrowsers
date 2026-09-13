from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ICON = ROOT / 'assets' / 'orbit_icon.ico'
VERSION = ROOT / 'version_info.txt'

subprocess.check_call([
    sys.executable, '-m', 'PyInstaller',
    '--noconfirm', '--clean', '--windowed', '--onedir', '--noconsole',
    '--name', 'OrbitBrowser', '--distpath', str(ROOT / 'build_out'), '--workpath', str(ROOT / 'build_work'), '--specpath', str(ROOT / 'build_spec'),
    '--add-data', f'{ROOT / "assets"};assets',
    '--icon', str(ICON),
    '--version-file', str(VERSION),
    str(ROOT / 'orbit_browser.py'),
], cwd=ROOT)
print('EXE: build_out/OrbitBrowser/OrbitBrowser.exe')
