from pathlib import Path
import os,json
from execution import D,SHA,TREE,exact,git
P=D.parent/'EP19_H7_PRODUCTION_INPUT_BOUNDARY_CORRECTION_AND_PACK_MONITOR_QUALIFICATION_V1';B=D/'sources/backend';F=D/'sources/frontend';R=Path('/home/user/Documents/workspace/projects/media-platform');shadow=D/'sources/shadow-fixture'
def put(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2,sort_keys=True);f.write('\n')
# Data inputs and prior failed scenes are separate from mutable build namespaces.
failed=P/'candidate';protected=exact(B)+exact(F)+exact(shadow)
protected.extend(R/os.fsdecode(n) for n in git(R,'ls-files','-z').split(b'\0') if n)
protected.extend(failed/os.fsdecode(n) for n in git(failed,'ls-files','-z').split(b'\0') if n)
protected.extend(failed/os.fsdecode(n) for n in git(failed,'ls-files','--others','--exclude-standard','-z').split(b'\0') if n)
protected.extend(p for p in P.iterdir() if p.is_file());protected.extend(p for p in (P/'owned').rglob('*') if p.is_file())
protected.extend(p for p in (D/'inputs').rglob('*') if p.is_file())
registry=json.loads((D/'observations/BEFORE.json').read_text())['registrations'];blocks=[x for x in registry.split('\n\n') if 'branch refs/heads/agent/frontend-wave2-product-ux-v1' in x.splitlines()];assert len(blocks)==1
registered=Path(next(x[len('worktree '):] for x in blocks[0].splitlines() if x.startswith('worktree ')))
front_meta=(registered/'.git').read_text().strip();assert front_meta.startswith('gitdir: ');front_meta=Path(front_meta[len('gitdir: '):]);assert front_meta.is_relative_to(R/'.git/worktrees')
ref='refs/heads/agent/frontend-wave2-product-ux-v1';tracking='refs/remotes/origin/agent/frontend-wave2-product-ux-v1'
allowed=[B/'.gradle',F/'frontend/node_modules',shadow/'.gradle',*[p for root in [B,shadow] for p in [root/'build',*((x.parent/'build') for x in root.rglob('build.gradle.kts'))]]]
put('PROTECTION_SCOPE.json',{'protected':sorted(set(map(str,protected))),'repositories':list(map(str,[R,failed,B,F,shadow])),'metadata_roots':list(map(str,[R/'.git',failed/'.git',B/'.git',F/'.git',shadow/'.git'])),'allowed':list(map(str,allowed)),'cross_lane':list(map(str,[R/'.git'/ref,R/'.git/logs'/ref,R/'.git'/tracking,R/'.git/logs'/tracking,front_meta])),'shared_git':str(R/'.git'),'shadow_root':str(shadow),'shadow_declared':['typed-schema-module/jooq-baseline.properties','typed-schema-module/jooq-plain-sql-allowlist.txt','typed-schema-module/jooq-dynamic-identifier-allowlist.txt']})
print('PROTECTION_SCOPE_MATERIALIZED_FROM_RECORDED_REGISTRY')
