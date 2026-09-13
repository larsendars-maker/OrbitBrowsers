from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git','build','dist','gotovo','installer','venv','.venv','__pycache__'}
PATTERNS = {
    'Google API key': re.compile(r'AIza[0-9A-Za-z_-]{20,}'),
    'GitHub token': re.compile(r'(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}'),
    'OpenAI-style key': re.compile(r'\bsk-[A-Za-z0-9_-]{20,}'),
    'Private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'Bearer token literal': re.compile(r'Bearer\s+[A-Za-z0-9._-]{30,}'),
    'Hard-coded database URL': re.compile(r'postgres(?:ql)?://[^\s\"\']+'),
}
allowed_names = {'.env.example'}
found = []
for path in ROOT.rglob('*'):
    if not path.is_file() or any(part in SKIP for part in path.parts) or path.name in allowed_names:
        continue
    if path.suffix.lower() in {'.png','.ico','.jpg','.jpeg','.webp','.zip','.exe','.apk','.aab','.woff','.ttf'}:
        continue
    try:
        text = path.read_text(encoding='utf-8')
    except Exception:
        continue
    for name, pat in PATTERNS.items():
        if pat.search(text):
            found.append((path.relative_to(ROOT), name))
if found:
    for item in found:
        print(f'FOUND: {item[0]} -> {item[1]}')
    raise SystemExit(1)
print('No high-confidence secrets found.')
