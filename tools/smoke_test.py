from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parents[1]
REQUIRED=[
    'orbit_browser.py','orbit_pages.py','orbit_storage.py','orbit_secure.py',
    'web/index.html','web/games.html','android/app/src/main/java/com/orbit/browser/MainActivity.kt',
    '.github/workflows/build-windows.yml','.github/workflows/build-android.yml'
]
for rel in REQUIRED:
    p=ROOT/rel
    if not p.exists():
        raise SystemExit(f'MISSING: {rel}')

for p in ROOT.glob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
print('Orbit smoke test: OK')
