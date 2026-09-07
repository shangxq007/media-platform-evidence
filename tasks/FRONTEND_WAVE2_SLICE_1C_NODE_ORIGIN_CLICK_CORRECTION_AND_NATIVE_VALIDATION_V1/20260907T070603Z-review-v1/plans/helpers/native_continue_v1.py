import ast,sys,traceback,json
from pathlib import Path
R=Path(sys.argv[1]);kind=sys.argv[2];sys.path.insert(0,str(R));source=R/('native_routes.py' if kind=='routes' else 'native_lifecycle.py');tree=ast.parse(source.read_text());prefix=[]
for node in tree.body:
 if isinstance(node,ast.Try):block=node;break
 prefix.append(node)
ns={'__name__':'__independent_continuation__','__file__':str(source)};exec(compile(ast.Module(body=prefix,type_ignores=[]),str(source),'exec'),ns);b=ns['b'];failures=[]
body=block.body
if kind=='routes':
 # Earlier eight route/query checks already executed on this corrected tree. Retain them separately.
 body=body[2:]
 changed=[]
 for node in ast.walk(ast.Module(body=body,type_ignores=[])):
  if isinstance(node,ast.Constant) and node.value=='window.__oldStage=document.querySelector(".ff-workspace-canvas")':
   changed.append({'old':node.value,'new':'void('+node.value+')','reason':'Avoid serializing a DOM object; preserve identical assignment and all assertions/input.'});node.value=changed[-1]['new']
 assert len(changed)==1
 (R/'COLLECTION_CHANGE.json').write_text(json.dumps(changed,indent=2))
try:
 for node in body:
  before=len(b.checks)
  try:exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
  except AssertionError:
   failures.append({'line':node.lineno,'traceback':traceback.format_exc()})
   # Continue independent lifecycle assertions only after the original record retained FAIL.
   if kind!='lifecycle' or len(b.checks)!=before+1 or b.checks[-1]['passed']:raise
except BaseException:
 failures.append({'fatal':traceback.format_exc()});traceback.print_exc()
finally:
 (R/'COLLECTED_FAILURES.json').write_text(json.dumps(failures,indent=2))
 exec(compile(ast.Module(body=block.finalbody,type_ignores=[]),str(source),'exec'),ns)
sys.exit(1 if failures else 0)
