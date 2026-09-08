from pathlib import Path
import os,json,subprocess,hashlib,io,tarfile
E=Path(__file__).resolve().parent;b=json.loads((E/'BASELINE_INSPECTION.json').read_text());T=(E/'FINAL_TREE.txt').read_text().strip();S=E/'patch-replay';S.mkdir(exist_ok=False)
subprocess.run(['git','init','--quiet',str(S)],check=True)
alts=[str(E/'objects')]+b['object_alternates'];(S/'.git/objects/info/alternates').write_text('\n'.join(alts)+'\n')
def g(*a):return subprocess.check_output(['git','-C',str(S),*a])
g('read-tree',b['accepted_tree']);g('checkout-index','--all');g('update-index','--refresh')
assert g('write-tree').decode().strip()==b['accepted_tree']
p=subprocess.run(['git','-C',str(S),'apply','--index','--binary',str(E/'TASK_DELTA.patch')],capture_output=True,text=True)
assert p.returncode==0,p.stderr
rebuilt=g('write-tree').decode().strip();assert rebuilt==T
(E/'PATCH_REPLAY.json').write_text(json.dumps({'baseline_tree':b['accepted_tree'],'expected_final_tree':T,'replayed_tree':rebuilt,'native_apply_exit':p.returncode,'complete_patch_sha256':hashlib.sha256((E/'TASK_DELTA.patch').read_bytes()).hexdigest(),'product_index_or_ref_mutations':0},indent=2))
print('COMPLETE_PATCH_REPLAY=PASS',rebuilt)
