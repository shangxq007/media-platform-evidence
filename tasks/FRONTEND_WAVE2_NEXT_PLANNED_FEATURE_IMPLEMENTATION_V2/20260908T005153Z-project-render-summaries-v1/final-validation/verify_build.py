from pathlib import Path
import json,hashlib,re,urllib.parse
E=Path(__file__).resolve().parent;B=E/'build'
T=(E/'FINAL_TREE.txt').read_text().strip()
files=[{'path':str(p.relative_to(B)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(B.rglob('*')) if p.is_file()]
assert files
refs=[]
for p in B.rglob('*'):
 if not p.is_file() or p.suffix not in ['.html','.js','.css']:continue
 text=p.read_text()
 candidates=[]
 if p.suffix=='.html':candidates+=re.findall(r'(?:src|href)=["\']([^"\']+)',text)
 if p.suffix=='.css':candidates+=re.findall(r'url\(["\']?([^\)"\']+)',text)
 if p.suffix=='.js':candidates+=re.findall(r'["\']((?:/assets/|\./)[^"\'\s]+\.(?:js|css|woff2?|svg|png)(?:\?[^"\']*)?)["\']',text)
 for ref in candidates:
  u=urllib.parse.urlsplit(ref)
  if u.scheme or u.netloc or not u.path:continue
  target=B/u.path.lstrip('/') if u.path.startswith('/') else p.parent/u.path
  target=target.resolve();assert target.is_relative_to(B.resolve()),(p,ref)
  refs.append({'from':str(p.relative_to(B)),'ref':ref,'target':str(target.relative_to(B)),'exists':target.is_file()})
optional=[]
for x in refs:
 x['required']=True
 if x['from']=='index.html' and x['ref']=='/vite.svg':
  # Exact rel=icon entry only: historical optional browser favicon, never JS/CSS.
  assert '<link rel="icon" type="image/svg+xml" href="/vite.svg"' in (B/'index.html').read_text()
  assert (Path('/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/single-read-focus-continuity-v1/snapshot/frontend/index.html')).read_bytes()==(E/'snapshot/frontend/index.html').read_bytes()
  assert not (Path('/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/single-read-focus-continuity-v1/build/vite.svg')).exists()
  x['required']=False;x['classification']='historical missing optional favicon; outside Render browser increment scope';optional.append(x)
assert refs and all(x['exists'] for x in refs if x['required']),refs
manifest={'implementation_tree':T,'output':str(B),'files':files,'local_asset_references':refs,'optional_historical_missing':optional,'required_missing':0,'reference_scope':'HTML src/href, CSS url, statically emitted JS relative asset literals; complete emitted path/hash census independent of reference discovery'}
raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();(E/'BUILD_MANIFEST.json').write_bytes(raw)
sha=hashlib.sha256(raw).hexdigest();(E/'BUILD_MANIFEST.sha256').write_text(sha+'  BUILD_MANIFEST.json\n')
print(json.dumps({'tree':T,'files':len(files),'references':len(refs),'required_missing':0,'optional_historical_missing':len(optional),'manifest_sha256':sha}))
