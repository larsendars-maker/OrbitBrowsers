from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ICON = ROOT / 'assets' / 'orbit_icon.ico'
VERSION = ROOT / 'version_info.txt'
DIST = ROOT / 'build_out'
WORK = ROOT / 'build_work'
SPEC = ROOT / 'build_spec'

cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--noconfirm', '--clean', '--windowed', '--onefile', '--noconsole',
    '--name', 'OrbitBrowser',
    '--distpath', str(DIST),
    '--workpath', str(WORK),
    '--specpath', str(SPEC),
    '--add-data', f'{ROOT / "assets"};assets',
    '--icon', str(ICON),
    '--version-file', str(VERSION),
    str(ROOT / 'orbit_browser.py'),
]

subprocess.check_call(cmd, cwd=ROOT)
exe = DIST / 'OrbitBrowser.exe'
if not exe.exists():
    raise SystemExit('OrbitBrowser.exe was not produced')
print(f'EXE: {exe}')
