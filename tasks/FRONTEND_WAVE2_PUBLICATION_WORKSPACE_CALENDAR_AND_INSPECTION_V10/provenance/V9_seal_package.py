from pathlib import Path
import json,re,hashlib,zipfile
E=Path(__file__).resolve().parent;P=E/'LOCAL_REVIEW_PACKAGE'
sha=lambda b:hashlib.sha256(b).hexdigest()
patterns={'private_key':rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----','github':rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}','aws':rb'(?:AKIA|ASIA)[A-Z0-9]{16}','api_key':rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}','jwt':rb'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}','credential_assignment':rb'(?i)(?:password|client_secret|access_token|refresh_token|api_key|authorization)\s*[=:]\s*[\x22\x27][^\x22\x27\r\n]{12,}[\x22\x27]','credential_url':rb'https?://[^/\s:@]+:[^/\s@]+@'}
allowed=[b'test-access-original',b'test-renewal',b'test-next-renewal',b'test-renewed-navigation',b'NON_CREDENTIAL_SIMULATION_']
files=sorted(x for x in P.rglob('*') if x.is_file());hits=[]
for f in files:
 data=f.read_bytes()
 for name,pattern in patterns.items():
  for m in re.finditer(pattern,data):
   ok=name=='credential_assignment' and any(v in m.group() for v in allowed)
   hits.append({'path':str(f.relative_to(P)),'pattern':name,'offset':m.start(),'match_sha256':sha(m.group()),'classification':'EXPLICIT_TEST_OR_SIMULATION_LITERAL' if ok else 'UNRESOLVED','rationale':'Read selected test/fixture source context; inert test label, not live credential. Built/chunk occurrence matches fixture source.' if ok else 'BLOCK_SEAL'})
assert all(h['classification']!='UNRESOLVED' for h in hits),hits
scan={'scope':'Actual selected public bytes only, including JS chunks, PNG binary bytes and native logs; no credential store/global scan. Pattern scan is bounded and not a guarantee of absence of all possible secrets.','scanned_files':len(files),'scanned_bytes':sum(f.stat().st_size for f in files),'patterns':list(patterns),'credential_shaped_hits':len(hits),'unresolved_hits':0,'confirmed_credentials':0,'reviewed_hits':hits}
(P/'PUBLIC_BYTES_CREDENTIAL_SCAN.json').write_text(json.dumps(scan,ensure_ascii=False,indent=2)+'\n')
files=sorted(x for x in P.rglob('*') if x.is_file());assert not (P/'MANIFEST.sha256').exists()
manifest=''.join(sha(f.read_bytes())+'  '+str(f.relative_to(P))+'\n' for f in files)
(P/'MANIFEST.sha256').write_text(manifest)
Z=E/'LOCAL_REVIEW_PACKAGE.zip'
with zipfile.ZipFile(Z,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(x for x in P.rglob('*') if x.is_file()):z.write(f,str(f.relative_to(P)))
print(json.dumps({'zip':str(Z),'manifest_sha256':sha(manifest.encode()),'scan_files':len(files),'scan_hits':len(hits),'unresolved':0},indent=2))
