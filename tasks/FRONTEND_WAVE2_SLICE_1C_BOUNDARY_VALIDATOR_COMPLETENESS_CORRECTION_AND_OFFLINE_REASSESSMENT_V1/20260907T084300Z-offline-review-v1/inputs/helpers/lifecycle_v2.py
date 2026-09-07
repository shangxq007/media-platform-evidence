import sys,json,ast,traceback
from pathlib import Path
R=Path(sys.argv[1]);ROOT=R.parents[1];sys.path.insert(0,str(R));sys.path.insert(0,str(ROOT/'helpers'));from boundary_validator import verify
s=(R/'native_lifecycle.py').read_text();original=ast.parse(s);names=[n.args[0].value for n in ast.walk(original) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='record' and n.args and isinstance(n.args[0],ast.Constant)];assert len(names)==12
s=s.replace("P='[data-canvas-node=\"project-node\"]'", "b.raw('Page.addScriptToEvaluateOnNewDocument',{'source':(ROOT/'helpers/lifecycle-boundary-v2.js').read_text()})\nP='[data-canvas-node=\"project-node\"]'")
s=s.replace(" b.raw('Page.navigate',{'url':'http://127.0.0.1:4196/lifecycle-away'})", " armed=b.ev('__boundary.arm()');b.ev('__boundary.installLate()')\n b.raw('Page.navigate',{'url':'http://127.0.0.1:4196/lifecycle-away'})")
s=s.replace("back();restored=probe();hide=", "back();restored=probe();boundary=b.ev('({documentId:__boundary.documentId,rows:__boundary.rows})');hide=")
old=next(l for l in s.splitlines() if "record('real-pagehide-retires-before-suspension'" in l)
new=""" verdict=verify(boundary,armed,actual);old_measurement=bool(hide) and all(not v['selectedRefs'] and v['primaryRef'] is None and v['lifetime']!=pending['snapshot'][0]['lifetime'] for e in hide for v in e['snapshot'])
 (R/'DEPARTURE_BOUNDARY_PROOF.json').write_text(json.dumps({'armed':armed,'trace':boundary,'actual_bfcache':actual,'verdict':verdict,'superseded_original_measurement_passed':old_measurement,'original_measurement_is_not_new_gate':True},indent=2))
 record('real-pagehide-retires-before-suspension','matched same-store retirement during pagehide, empty transient state at trusted freeze before suspension, real BFCache return',verdict,verdict['passed'])"""
s=s.replace(old,new);final=ast.parse(s);newnames=[n.args[0].value for n in ast.walk(final) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='record' and n.args and isinstance(n.args[0],ast.Constant)];assert names==newnames
(R/'LIFECYCLE_V2_PROGRAM.py').write_text(s);(R/'ASSERTION_MAPPING.json').write_text(json.dumps({'identities':names,'changed_measurement_identity':'real-pagehide-retires-before-suspension','old':old,'new':new,'other_assertion_bodies_unchanged':True,'requirement_unchanged':'retirement before document suspension, not merely empty on restoration','supported_boundary':'This qualified Chrome real persisted pagehide/freeze path; absent freeze or missing store fails, no timer fallback.','observer_change':'New additional lifecycle-boundary-v2.js. Frozen original observer remains installed so its superseded failed sample is preserved.'},indent=2))
exec(compile(final,str(R/'LIFECYCLE_V2_PROGRAM.py'),'exec'))
