from pathlib import Path
import json
import subprocess

E = Path(__file__).resolve().parent
W = Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')

for path in [E / 'ALLOWLIST.json', W / 'frontend/src/localization/source-manifest.json']:
    json.loads(path.read_text())
    print(f'JSON_VALID={path}')

request_path = W / 'frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv'
rows = [line.split('\t') for line in request_path.read_text().splitlines()]
assert rows and all(len(row) == 12 for row in rows), [(index + 1, len(row)) for index, row in enumerate(rows) if len(row) != 12]
ids = [row[0] for row in rows[1:]]
assert len(ids) == len(set(ids))
assert ids.count('FB-GAP-005') == 1
print(f'BACKEND_REQUEST_TSV_ROWS={len(rows) - 1}')
print('BACKEND_REQUEST_DUPLICATE_IDS=0')

for name in ['frontend-current-governed-scope-ledger-v1.tsv', 'frontend-product-path-classification-v1.tsv']:
    path = W / 'docs/architecture/governance' / name
    rows = [line.split('\t') for line in path.read_text().splitlines() if line and not line.startswith('#')]
    assert rows and all(len(row) == 4 if 'current-governed' in name else len(row) == 3 for row in rows)
    paths = [row[0] for row in rows[1:]]
    assert len(paths) == len(set(paths))
    assert paths.count('frontend/src/product/render-browser/render-browser.css') == 1
    print(f'{name}:ROWS={len(rows) - 1}:DUPLICATE_PATHS=0:RENDER_CSS=1')

subprocess.run(['git', '-C', str(W), 'diff', '--check'], check=True)
print('GIT_DIFF_CHECK=PASS')
