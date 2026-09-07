import ast,sys,json,traceback
from pathlib import Path
R=Path(sys.argv[1]);ROOT=R.parents[1];sys.path.insert(0,str(R));t=ast.parse((R/'native_lifecycle.py').read_text());prefix=[]
for n in t.body:
 if isinstance(n,ast.Try):break
 prefix.append(n)
exec(compile(ast.Module(body=prefix,type_ignores=[]),str(R/'native_lifecycle.py'),'exec'))
b.raw('Page.addScriptToEvaluateOnNewDocument',{'source':(ROOT/'helpers/passive_d1.js').read_text()})
try:
 check('D1-before');b.reset();ready();b.click(P);b.wait('__lifecycleProbe.snapshot()[0].selectedRefs.length===1');b.click('.ff-agent-launcher');b.wait('!!document.querySelector(".ff-agent-composer")');b.click('.ff-agent-composer button[type="submit"]');b.wait('!!document.querySelector("[data-testid=agent-proposal]")');pending=probe();assert pending['proposals'] and pending['snapshot'][0]['selectedRefs'];armed=b.ev('__boundary.arm()');b.ev('__boundary.installLate()');
 b.raw('Page.navigate',{'url':'http://127.0.0.1:4196/lifecycle-away'});b.wait('document.title==="External lifecycle fixture"');away=probe();back();restored=probe();trace=b.ev('({documentId:__boundary.documentId,rows:__boundary.rows,snapshot:__boundary.snapshot()})');hide=[e for e in restored['events'] if e['event']=='pagehide'];actual=restored['id']==pending['id'] and any(e['persisted'] for e in restored['events'] if e['event']=='pageshow')
 (R/'D1_TRACE.json').write_text(json.dumps({'armed':armed,'pending':pending,'away':away,'restored':restored,'trace':trace,'actual_bfcache':actual},indent=2));assert actual,'actual BFCache prerequisite';ok=bool(hide) and all(not s['selectedRefs'] and s['primaryRef'] is None and s['lifetime']!=pending['snapshot'][0]['lifetime'] for e in hide for s in e['snapshot']);check('D1-after');record('real-pagehide-retires-before-suspension','historical unchanged assertion; expected diagnostic failure',hide,ok)
except Exception as x:
 (R/'FAILURE.json').write_text(json.dumps({'error':str(x),'traceback':traceback.format_exc(),'expected_original_assertion_failure':bool(b.checks and b.checks[-1]['test_identity']=='real-pagehide-retires-before-suspension')},indent=2));raise
finally:
 (R/'RESULTS.json').write_text(json.dumps({'kind':'DIAGNOSTIC_NOT_ACCEPTANCE','checks':b.checks},indent=2));(R/'COMMANDS.json').write_text(json.dumps(b.commands,indent=2));b.ws.close()
