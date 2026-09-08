from pathlib import Path
import json,re,collections,hashlib
E=Path(__file__).resolve().parent
P=Path('/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/single-read-focus-continuity-v1')
def read(p):
 rows=[];file=None
 for line in p.read_text().splitlines():
  if '/frontend/src/' in line and line.startswith('/'):file='frontend/src/'+line.split('/frontend/src/',1)[1]
  m=re.match(r'\s*(\d+):(\d+)\s+(warning|error)\s+(.*?)\s{2,}(\S+)\s*$',line)
  if m:
   assert file
   rows.append([file,int(m[1]),int(m[2]),m[3],m[4],m[5]])
 return rows
old=read(P/'gates/lint.log');new=read(E/'gates/lint.log');assert len(old)==46
key=lambda x:json.dumps(x,ensure_ascii=False)
a=collections.Counter(map(key,old));b=collections.Counter(map(key,new));added=list((b-a).elements());removed=list((a-b).elements())
r={'baseline_warnings':len(old),'final_diagnostics':len(new),'new_diagnostics':[json.loads(x) for x in added],'removed_diagnostics':[json.loads(x) for x in removed],'baseline':old,'final':new,'baseline_log_sha256':hashlib.sha256((P/'gates/lint.log').read_bytes()).hexdigest()}
(E/'LINT_DIAGNOSTIC_ACCOUNTING.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k not in ['baseline','final']}));assert not added
