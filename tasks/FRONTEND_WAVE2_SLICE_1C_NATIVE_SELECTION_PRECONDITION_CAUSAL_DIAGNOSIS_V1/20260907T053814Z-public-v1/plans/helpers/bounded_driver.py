import ast,sys,json,traceback,hashlib
from pathlib import Path
R=Path(sys.argv[1]);TASK=R.parents[1]
sys.path.insert(0,str(R))
source=R/'native_routes.py'
tree=ast.parse(source.read_text(),filename=str(source))
# Execute original imports, browser setup, observer installation, and definitions only.
# The first top-level try contains ALL acceptance scenarios and is intentionally not executed.
prefix=[]
for node in tree.body:
 if isinstance(node,ast.Try):break
 prefix.append(node)
ns={'__name__':'__bounded_diagnostic__','__file__':str(source)}
exec(compile(ast.Module(body=prefix,type_ignores=[]),str(source),'exec'),ns)
b=ns['b'];exit_code=0
try:
 b.raw('Page.addScriptToEvaluateOnNewDocument',{'source':(TASK/'helpers/passive.js').read_text()})
 if (R/'logpoints.json').exists():
  b.raw('Debugger.enable',{})
  for point in json.loads((R/'logpoints.json').read_text()):
   result=b.raw('Debugger.setBreakpointByUrl',point['params'])
   print('LOGPOINT',point['name'],json.dumps(result),flush=True)
 # This is the exact original function and assertion, no substitute input calls.
 ns['selected']()
 print('PRECONDITION_UNEXPECTEDLY_SURVIVED; BOUNDED_STOP_NO_ACCEPTANCE_CONTINUATION')
except BaseException:
 exit_code=1;traceback.print_exc()
finally:
 try:
  data=b.ev('({rows:__diag.rows,snapshot:__lifecycleProbe.snapshot(),historicalObservations:__lifecycleProbe.observations,geometry:__diag.geometry(),gestures:__diag.gestures()})')
  (R/'trace.json').write_text(json.dumps(data,indent=2))
  b.shot('final-state')
 except BaseException:
  traceback.print_exc();exit_code=2
 (R/'bounded-result.json').write_text(json.dumps({'native_exit':exit_code,'checks_completed':len(b.checks),'original_assertion':'native_routes.py:11','execution':'original AST prefix plus one original selected() call; excluded all acceptance loops','status':'EXPECTED_DIAGNOSTIC_REPRODUCTION' if exit_code==1 else 'UNEXPECTED_RESULT_REQUIRES_DIAGNOSIS'},indent=2))
 (R/'native-commands.json').write_text(json.dumps(b.commands,indent=2))
 b.ws.close()
sys.exit(exit_code)
