"""Parent invokes only AFTER its successful external Vite build."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
inputs=json.loads((P/'FIXTURE_HOST_INPUTS.json').read_text())
assert inputs['FINAL_EXACT_IMPLEMENTATION_TREE']==(P.parent/'final-validation-01/FINAL_TREE.txt').read_text().strip()
S=Path(inputs['snapshot'])
for row in inputs['files']:assert hashlib.sha256((S/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
assert (P/'build/index.html').is_file() and (P/'build/fixture.html').is_file()
def census(root):return [{'path':str(f.relative_to(root)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(root.rglob('*')) if f.is_file() and 'node_modules' not in f.parts]
record={'FINAL_EXACT_IMPLEMENTATION_TREE':inputs['FINAL_EXACT_IMPLEMENTATION_TREE'],'fixture_input_sha256':hashlib.sha256((P/'FIXTURE_HOST_INPUTS.json').read_bytes()).hexdigest(),'host':census(P/'fixture-host'),'build':census(P/'build'),'claim':'Post-build byte binding, not proof of a successful gate. Parent must retain actual build command and log.'}
with (P/'BUILD_BINDING.json').open('x') as f:json.dump(record,f,indent=2)
print('BUILD_BINDING.json written; parent must retain build log')
