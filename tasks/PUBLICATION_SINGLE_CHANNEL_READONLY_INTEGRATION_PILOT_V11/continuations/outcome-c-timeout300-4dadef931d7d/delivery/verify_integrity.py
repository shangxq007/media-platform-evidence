"""Offline packaging integrity only; no application imports or tests."""
from pathlib import Path, PurePosixPath
import hashlib, json, stat, sys, zipfile

def digest(b):
    return hashlib.sha256(b).hexdigest()

def verify(root, archive):
    root = Path(root)
    archive = Path(archive)
    manifest_bytes = (root / 'MANIFEST.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    entries = manifest['files']
    paths = [e['path'] for e in entries]
    assert len(paths) == len(set(paths)), 'duplicate manifest path'
    for p in paths:
        q = PurePosixPath(p)
        assert not q.is_absolute() and '..' not in q.parts and str(q) == p
        assert '\\' not in p and p != 'MANIFEST.json'
    expected = set(paths) | {'MANIFEST.json'}
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    assert actual == expected, 'payload membership mismatch'
    assert not any(p.is_symlink() for p in root.rglob('*')), 'symlink payload'
    allowlist = json.loads((root / 'ALLOWLIST.json').read_text())
    assert set(allowlist['zip_members']) == expected, 'allowlist mismatch'
    assert len(allowlist['zip_members']) == len(expected)
    by_path = {e['path']: e for e in entries}
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert len(names) == len(set(names)), 'duplicate ZIP entries'
        assert set(names) == expected, 'ZIP membership mismatch'
        assert z.testzip() is None, 'ZIP CRC error'
        for item in z.infolist():
            assert not item.is_dir()
            assert not stat.S_ISLNK(item.external_attr >> 16)
            data = z.read(item.filename)
            if item.filename == 'MANIFEST.json':
                assert data == manifest_bytes
                continue
            e = by_path[item.filename]
            local = (root / item.filename).read_bytes()
            assert len(data) == len(local) == e['bytes']
            assert digest(data) == digest(local) == e['sha256'], item.filename
    return {'decision':'PASS_OFFLINE_INTEGRITY_ONLY_NOT_ACCEPTANCE',
            'manifest_entries':len(entries), 'zip_members':len(expected),
            'payload_files_including_manifest':len(actual),
            'missing':0,'extra':0,'duplicate':0,'hash_mismatches':0,
            'manifest_sha256':digest(manifest_bytes),
            'zip_sha256':digest(archive.read_bytes()),'zip_bytes':archive.stat().st_size,
            'report_sha256':digest((root/'REPORT.zh-CN.md').read_bytes()),
            'machine_sha256':digest((root/'REPORT.machine.json').read_bytes()),
            'index_sha256':digest((root/'REVIEW_INDEX.json').read_bytes()),
            'network': 'NOT_USED','application_tests':'NOT_RUN',
            'independent_acceptance':'NOT_PERFORMED','publication':'NOT_PERFORMED'}

if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: python3 -B verify_integrity.py PAYLOAD ZIP')
    print(json.dumps(verify(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))
