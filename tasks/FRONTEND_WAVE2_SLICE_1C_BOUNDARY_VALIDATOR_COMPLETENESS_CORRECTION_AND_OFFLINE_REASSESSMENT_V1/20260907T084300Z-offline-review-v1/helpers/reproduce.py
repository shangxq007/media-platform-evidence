from pathlib import Path
import json,copy,hashlib,sys
R=Path(__file__).resolve().parents[1];old=R/'inputs/helpers/boundary_validator.py';ns={};exec(compile(old.read_text(),str(old),'exec'),ns);p=R/'inputs/runs/lifecycle-v2/DEPARTURE_BOUNDARY_PROOF.json';proof=json.loads(p.read_text());assert proof['armed']['documentId']=='cfd39554-a87b-41e3-b420-7479a0c278c6' and (proof['armed']['store'],proof['armed']['lifetime'],proof['armed']['revision'])==(2,3,2)
rows=[]
for key in ['lifetime','primary']:
 t=copy.deepcopy(proof['trace'])
 for r in t['rows']:
  if r['seq'] in [8,10,11]:
   for s in r['stores']:del s[key]
 b=json.dumps(t,indent=2).encode();f=R/'results'/('counterexample-'+key+'.json');f.write_bytes(b);result=ns['verify'](t,proof['armed'],proof['actual_bfcache']);rows.append({'case':'MISSING_RETIRED_LIFETIME' if key=='lifetime' else 'MISSING_PRIMARY_STATE','delete_key':key,'rows':[8,10,11],'input_file':f.name,'input_sha256':hashlib.sha256(b).hexdigest(),'expected_passed':False,'old_actual':result});assert result['passed'] is True and result['errors']==[]
(R/'results/REVIEWER_COUNTEREXAMPLE_REPRODUCTION.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'old_validator_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'controls':rows,'false_acceptances_reproduced':len(rows)},indent=2));print(json.dumps(rows,indent=2));sys.exit(1) # expected RED: old implementation falsely accepts both
