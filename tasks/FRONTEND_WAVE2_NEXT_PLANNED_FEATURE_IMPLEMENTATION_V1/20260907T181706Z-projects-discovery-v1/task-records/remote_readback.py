"""Anonymous full fixed-commit byte readback; no credential fallback."""
from pathlib import Path
import json,hashlib,urllib.request,urllib.parse,concurrent.futures,time,datetime
E=Path(__file__).resolve().parent;P=E/'public'
local=json.loads((E/'LOCAL_EVIDENCE_COMMIT.json').read_text());commit=local['evidence_commit'];prefix=local['package_path']
base=f'https://raw.githubusercontent.com/shangxq007/media-platform-evidence/{commit}/{prefix}/'
files=[{'path':str(p.relative_to(P)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(P.rglob('*')) if p.is_file()]
R=E/'remote-readback';R.mkdir(exist_ok=False)
def one(row):
 out=dict(row);out['url']=base+urllib.parse.quote(row['path'],safe='/');attempts=[]
 for attempt in range(1,4):
  try:
   opener=urllib.request.build_opener(urllib.request.ProxyHandler({'http':'http://127.0.0.1:7890','https':'http://127.0.0.1:7890'}))
   with opener.open(urllib.request.Request(out['url'],headers={'User-Agent':'projects-discovery-evidence-readback'}),timeout=45) as response:
    data=response.read();out.update(status=response.status,remote_bytes=len(data),remote_sha256=hashlib.sha256(data).hexdigest())
   out['match']=out['remote_bytes']==out['bytes'] and out['remote_sha256']==out['sha256'];out['attempts']=attempts+[{'attempt':attempt,'status':out['status']}]
   if row['path'] in ['MANIFEST.json','INDEX.md','RECONSTRUCTION_MAP.json']:(R/row['path']).write_bytes(data)
   return out
  except Exception as err:
   attempts.append({'attempt':attempt,'error_type':type(err).__name__,'error':str(err)})
   if attempt<3:time.sleep(attempt)
 out.update(match=False,attempts=attempts);return out
start=time.time();results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 for out in pool.map(one,files):
  results.append(out)
  with (R/'files.jsonl').open('a') as f:f.write(json.dumps(out)+'\n')
  if len(results)%50==0:print('READBACK',len(results),flush=True)
matched=sum(x['match'] for x in results)
receipt={'evidence_commit':commit,'package_path':prefix,'anonymous':True,'authentication_fallback':False,'expected_files':len(files),'verified_files':matched,'differences':len(files)-matched,'manifest_sha256':hashlib.sha256((R/'MANIFEST.json').read_bytes()).hexdigest() if (R/'MANIFEST.json').exists() else None,'elapsed_seconds':time.time()-start,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':results,'status':'PASS' if matched==len(files) else 'FAIL'}
(E/'REMOTE_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='files'},indent=2))
assert matched==len(files)
