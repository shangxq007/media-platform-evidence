from pathlib import Path
import json,hashlib,time
E=Path(__file__).parent
ROOT=Path('[LOCAL_TASK_ROOT]')
def check(label):
 source=json.loads((ROOT/'inputs/SOURCE_MANIFEST.json').read_text());build=json.loads((E/'BUILD_ARTIFACT_BOUNDARY.json').read_text())
 bad=[p for p,h in source['files'].items() if hashlib.sha256((ROOT/'snapshot'/p).read_bytes()).hexdigest()!=h]
 bad += [p for p,h in build['build_artifacts'].items() if hashlib.sha256((ROOT/'build'/p).read_bytes()).hexdigest()!=h]
 row={'label':label,'time':time.time(),'tree':source['tree'],'source_entries':len(source['files']),'build_entries':len(build['build_artifacts']),'changed':bad,'backend_refs_not_monitored':True}
 with (E/'SCOPE_TRIPWIRE.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 assert not bad,row
 return row
