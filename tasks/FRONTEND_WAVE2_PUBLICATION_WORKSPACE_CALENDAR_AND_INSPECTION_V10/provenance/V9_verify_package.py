from pathlib import Path
import hashlib,json,zipfile,collections,re
E=Path(__file__).resolve().parent;P=E/'LOCAL_REVIEW_PACKAGE';Z=E/'LOCAL_REVIEW_PACKAGE.zip'
def digest(b):return hashlib.sha256(b).hexdigest()
manifest=(P/'MANIFEST.sha256').read_bytes();rows=[line.split('  ',1) for line in manifest.decode().splitlines()];expected=dict((name,h) for h,name in rows)
assert len(rows)==len(expected) and 'MANIFEST.sha256' not in expected
local={str(f.relative_to(P)) for f in P.rglob('*') if f.is_file()};wanted=set(expected)|{'MANIFEST.sha256'};assert local==wanted
for name,h in expected.items():assert digest((P/name).read_bytes())==h,name
with zipfile.ZipFile(Z) as archive:
 names=archive.namelist();dups=[n for n,c in collections.Counter(names).items() if c>1];assert not dups and set(names)==wanted
 assert archive.testzip() is None
 for name in names:
  assert not name.startswith('/') and '..' not in Path(name).parts
  actual=archive.read(name);assert actual==(P/name).read_bytes(),name
  assert digest(actual)==(digest(manifest) if name=='MANIFEST.sha256' else expected[name]),name
copied=json.loads((P/'SELECTED_ORIGINALS.json').read_text())
for item in copied:
 assert digest(Path(item['source']).read_bytes())==item['sha256'],item['source']
 assert digest((P/item['payload']).read_bytes())==item['sha256'],item['payload']
chunks=json.loads((P/'BUILD_CHUNK_RECONSTRUCTION.json').read_text());parts=0
for c in chunks:
 joined=[]
 for order,x in enumerate(c['parts']):
  assert x['order']==order
  b=(P/x['path']).read_bytes();b.decode('utf-8');assert len(b)==x['bytes'] and digest(b)==x['sha256'];joined.append(b);parts+=1
 b=b''.join(joined);assert len(b)==c['bytes'] and digest(b)==c['sha256'] and b==(P/c['original']).read_bytes()
# Independently scan final payload including generated scan report and manifest.
patterns=[rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}',rb'(?:AKIA|ASIA)[A-Z0-9]{16}',rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}',rb'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',rb'https?://[^/\s:@]+:[^/\s@]+@']
assignment=rb'(?i)(?:password|client_secret|access_token|refresh_token|api_key|authorization)\s*[=:]\s*[\x22\x27][^\x22\x27\r\n]{12,}[\x22\x27]'
allow=[b'test-access-original',b'test-renewal',b'test-next-renewal',b'test-renewed-navigation',b'NON_CREDENTIAL_SIMULATION_'];hitcount=0
for name in wanted:
 b=(P/name).read_bytes()
 for pat in patterns:assert not re.search(pat,b),name
 for m in re.finditer(assignment,b):assert any(v in m.group() for v in allow),name;hitcount+=1
index=json.loads((P/'REVIEW_INDEX.json').read_text())
for k in ['EVIDENCE_DELIVERY_STATUS','EVIDENCE_COMMIT_SHA','REVIEW_INDEX_URL','MACHINE_INDEX_URL','PUBLIC_MANIFEST_SHA256','REMOTE_VERIFICATION']:assert index[k]=='NOT_YET_PUBLISHED'
assert index['PRODUCT_PUBLICATION']=='NOT_PERFORMED' and index['INDEPENDENT_REVIEW']=='REQUIRED'
result={'status':'PASS_LOCAL_PACKAGE_INTEGRITY_ONLY','package_directory':str(P),'zip':str(Z),'manifest_sha256':digest(manifest),'zip_sha256':digest(Z.read_bytes()),'payload_files_excluding_manifest':len(expected),'archive_entries_including_manifest':len(names),'payload_bytes_excluding_manifest':sum((P/n).stat().st_size for n in expected),'local_bytes_including_manifest':sum((P/n).stat().st_size for n in wanted),'zip_bytes':Z.stat().st_size,'manifest_bytes':len(manifest),'manifest_duplicate_paths':0,'zip_duplicate_entries':0,'extra_files':0,'missing_files':0,'hash_mismatches':0,'original_selected_files_rehashed_unchanged':len(copied),'chunked_assets_reconstructed':len(chunks),'utf8_parts_verified':parts,'final_screenshots':sum(len(list((P/'browser-v9'/r).glob('*.png'))) for r in ['final03-run-01','final03-run-02']),'historical_red_screenshots':1,'final_payload_bytes_scanned':sum((P/n).stat().st_size for n in wanted),'final_payload_files_scanned':len(wanted),'reviewed_test_literal_hits':hitcount,'unresolved_credential_hits':0,'independent_acceptance':'NOT_PERFORMED_PACKAGING_ONLY','publication':'NOT_YET_PUBLISHED','parent_visual_scope':'6 representative images per included parent record; not all32','verification_method':'Separate verifier process reparsed manifest, read every local file and decompressed ZIP entry, checked exact sets and duplicates, SHA256, CRC, original-byte preservation, UTF8 reconstruction and final-byte bounded credential patterns.'}
(E/'PACKAGE_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
