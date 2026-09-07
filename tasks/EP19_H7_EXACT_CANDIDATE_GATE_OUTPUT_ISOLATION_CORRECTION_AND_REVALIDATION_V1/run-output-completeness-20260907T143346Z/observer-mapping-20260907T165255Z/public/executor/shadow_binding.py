"""Bind unchanged historical reconciliation to the observer's actual acceptance."""
from pathlib import Path
import hashlib,json
import frozen_shadow_monitor as frozen
from execution import exact
from coverage import put

def dh(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
def bind(root,env,declared,dest):
    root=Path(root);before=frozen.snapshot(root,env);put(dest/'shadow-before.json',before)
    def finish(events,tag):
        after=frozen.snapshot(root,env);put(dest/'shadow-after.json',after)
        relative=[{**e,'path':str(Path(e['path']).relative_to(root))} for e in events if Path(e['path']).is_relative_to(root)]
        # Only actual tracked/Git events enter the original whole-repository reducer.
        tracked={r['path'] for r in before['entries']}
        relative=[e for e in relative if e['path'] in tracked or e['path'].startswith('.git/')]
        try:paths=exact(root);content={'result':'PASS','checked':len(paths),'mismatches':[]}
        except Exception as error:content={'result':'FAIL','checked':0,'mismatches':[str(error)]}
        semantic=frozen.reconcile('SHADOW',before,after,relative,declared,content['mismatches'])
        put(dest/'shadow-events.json',relative);put(dest/'shadow-final-content.json',content)
        proof={'result':'PASS' if semantic['result']=='PASS' and content['result']=='PASS' else 'FAIL',
               'run_binding':tag,'root':str(root),'before_sha256':dh(before),'after_sha256':dh(after),
               'events_sha256':dh(relative),'final_content_sha256':dh(content),
               'semantic_check':semantic,'final_content_check':content,
               'evidence':{'before':before,'after':after,'events':relative,'final_content':content},
               'evidence_digest_encoding':'sha256(json.dumps(value,sort_keys=True).encode())'}
        put(dest/'shadow-reconciliation.json',proof);return proof
    return finish
