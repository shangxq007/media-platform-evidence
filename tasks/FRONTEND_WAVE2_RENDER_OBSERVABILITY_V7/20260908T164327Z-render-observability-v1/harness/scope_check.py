from pathlib import Path
import hashlib
import json
import os
import subprocess

E = Path(__file__).resolve().parent
W = Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
baseline = json.loads((E / 'BASELINE_INSPECTION.json').read_text())
allowlist = set(json.loads((E / 'ALLOWLIST.json').read_text()))

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
def git(*args: str) -> str:
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(W), *args], env=env).decode().strip()

assert git('rev-parse', 'HEAD') == baseline['head']
assert git('symbolic-ref', 'HEAD') == baseline['branch']
assert sha256(Path(baseline['index_path'])) == baseline['index_sha256']

paths = set(git('ls-files', '--cached', '--others', '--exclude-standard', '--', 'frontend', *sorted(path for path in baseline['files'] if not path.startswith('frontend/'))).splitlines())
changed = []
deleted = []
for path in sorted(paths | set(baseline['files'])):
    file = W / path
    if path not in paths or not file.is_file():
        deleted.append(path)
        continue
    mode = '100755' if file.stat().st_mode & 0o111 else '100644'
    if path not in baseline['files'] or sha256(file) != baseline['files'][path] or mode != baseline['modes'][path]:
        changed.append(path)

outside = sorted(set(changed) - allowlist)
missing_expected = sorted(allowlist - set(changed))
result = {
    'head': baseline['head'],
    'branch': baseline['branch'],
    'real_index_unchanged': True,
    'changed_from_accepted_working_tree': changed,
    'deleted': deleted,
    'outside_allowlist': outside,
    'allowlisted_but_unchanged': missing_expected,
    'unchanged_baseline_paths_outside_allowlist': len(set(baseline['files']) - allowlist),
}
print(json.dumps(result, indent=2))
assert not deleted and not outside and not missing_expected
