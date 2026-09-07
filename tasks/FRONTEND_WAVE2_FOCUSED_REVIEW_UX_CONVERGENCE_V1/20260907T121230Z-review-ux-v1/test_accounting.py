from pathlib import Path
import json,collections
E=Path(__file__).resolve().parent
P=E.parent/'FRONTEND_WAVE2_COMMAND_DISCOVERY_AND_ACCESSIBILITY_CONVERGENCE_V1'
def parse(path):
 j=json.loads(path.read_text());ids=[];states=collections.Counter();files=[]
 for f in j['testResults']:
  rel=f['name'].split('/frontend/')[-1];files.append(rel)
  for t in f['assertionResults']:
   ids.append(json.dumps([rel,t['ancestorTitles'],t['title']],ensure_ascii=False));states[t['status']]+=1
 assert len(ids)==j['numTotalTests'];assert states['passed']==j['numPassedTests'];assert states['failed']==j['numFailedTests']
 assert len(set(ids))==len(ids),'duplicate execution identities'
 return j,ids,states,files
old,oi,os,of=parse(P/'FULL_UNIT.json');new,ni,ns,nf=parse(E/'FULL_UNIT.json')
row={'baseline_tree':'43038f740997d0ebb3a8c67f293da7edab563fdb','final_tree':(E/'FINAL_TREE.txt').read_text().strip(),'baseline_tests':len(oi),'final_tests':len(ni),'final_files':len(nf),'final_status_counts':dict(ns),'added_identities':sorted(set(ni)-set(oi)),'removed_or_renamed_identities':sorted(set(oi)-set(ni)),'final_identities':sorted(ni),'baseline_reused_only_for_accounting':True}
(E/'TEST_ACCOUNTING.json').write_text(json.dumps(row,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in row.items() if k not in ['final_identities','added_identities','removed_or_renamed_identities']},indent=2));print('added',len(row['added_identities']),'removed/renamed',len(row['removed_or_renamed_identities']))
