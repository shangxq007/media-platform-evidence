from pathlib import Path
import json,collections,hashlib
import sys
E=Path(__file__).resolve().parent/sys.argv[1]

def identities(path):
 obj=json.loads(path.read_text());rows=[]
 for suite in obj['testResults']:
  file='frontend/'+suite['name'].split('/frontend/',1)[1]
  for a in suite['assertionResults']:
   identity=[file,a['ancestorTitles'],a['title']]
   rows.append({'identity':identity,'status':a['status'],'fullName':a['fullName']})
 return obj,rows
old,oldrows=identities(Path('/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/FULL_UNIT.json'));final,rows=identities(E/'FULL_UNIT.json')
key=lambda r:json.dumps(r['identity'],ensure_ascii=False,separators=(',',':'))
a=collections.Counter(key(r) for r in oldrows);b=collections.Counter(key(r) for r in rows)
added=list((b-a).elements());removed=list((a-b).elements());duplicates=[{'identity':json.loads(k),'count':v} for k,v in b.items() if v>1]
assert len(oldrows)==890 and len(a)==890 and all(r['status']=='passed' for r in oldrows)
assert final['numTotalTests']==len(rows) and final['numPassedTests']==sum(r['status']=='passed' for r in rows)
counts={'baseline':len(oldrows),'final':len(rows),'files':len(final['testResults']),'passed':sum(r['status']=='passed' for r in rows),'failures':sum(r['status']=='failed' for r in rows),'skips':sum(r['status'] not in ['passed','failed'] for r in rows),'added':len(added),'removed':len(removed),'duplicates':len(duplicates),'retained':sum((a&b).values())}
assert not duplicates and counts['failures']==0 and counts['skips']==0
out={'tree':(E/'FINAL_TREE.txt').read_text().strip(),'counts':counts,'canonical_identity':'[frontend-relative file, ancestorTitles array, exact title]; no flattened-string splitting','baseline_report_sha256':hashlib.sha256((Path('/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/FULL_UNIT.json')).read_bytes()).hexdigest(),'final_report_sha256':hashlib.sha256((E/'FULL_UNIT.json').read_bytes()).hexdigest(),'retained':[json.loads(k) for k in (a&b).elements()],'failed':[r['identity'] for r in rows if r['status']=='failed'],'skipped':[r['identity'] for r in rows if r['status'] not in ['passed','failed']],'added':[json.loads(k) for k in added],'removed':[json.loads(k) for k in removed],'duplicates':duplicates,'executed':rows,'historical_executed':oldrows}
(E/'TEST_IDENTITY_ACCOUNTING.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(counts))
