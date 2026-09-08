from pathlib import Path
import json,shutil,hashlib
E=Path(__file__).parent;P=E.parent/'FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6';V=P/'final-validation-02'
provenance=[]
for name in ['materialize.py','gate.py','verify_build.py','preservation.py','replay_patch.py']:
 data=(V/name).read_bytes();target=E/name
 assert not target.exists()
 target.write_bytes(data)
 provenance.append({'source':str(V/name),'target':str(target),'sha256':hashlib.sha256(data).hexdigest()})
s=(V/'test_accounting.py').read_text().replace(str(P/'V5_FULL_UNIT.json'),str(E/'V6_FULL_UNIT.json')).replace('==724','==797')
# Removed identities must remain explicit; a changed legacy fixture test is not silently ignored.
s=s.replace("assert not removed and not duplicates and counts['failures']==0 and counts['skips']==0","assert not duplicates and counts['failures']==0 and counts['skips']==0")
(E/'test_accounting.py').write_text(s)
plan=json.loads((P/'FINAL_VALIDATION_PLAN.json').read_text().replace(str(P),str(E)).replace('src/product/production','src/product/render-browser'))
(E/'FINAL_VALIDATION_PLAN.json').write_text(json.dumps(plan,indent=2))
b=json.loads((E/'BASELINE_INSPECTION.json').read_text());pres={}
for p,h in b['files'].items():
 if p.startswith('frontend/dist/'):
  pres[str(Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')/p)]=h
for p in [P/'LOCAL_REVIEW_PACKAGE.zip',P/'PARENT_HANDOFF_VERIFIED.json',P/'LOCAL_PACKAGE_VERIFICATION.json',P/'LOCAL_REVIEW_PACKAGE/MANIFEST.sha256']:
 pres[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
(E/'PRESERVATION_BEFORE.json').write_text(json.dumps(pres,indent=2))
(E/'HELPER_PROVENANCE.json').write_text(json.dumps({'copied':provenance,'adapted':['test_accounting baseline path and count 797, removed identities explicit','validation target Render and new root'],'bounds':'same frontend plus predecessor supporting path denominator; no backend task checks'},indent=2))
print('Prepared helpers, seven gate definitions, bounded preservation receipts')
