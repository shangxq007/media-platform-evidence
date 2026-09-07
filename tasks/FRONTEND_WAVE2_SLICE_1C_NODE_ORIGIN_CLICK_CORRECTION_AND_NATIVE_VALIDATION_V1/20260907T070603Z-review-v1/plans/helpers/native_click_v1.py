import ast,sys,json,traceback,time
from pathlib import Path
R=Path(sys.argv[1]);TASK=R.parents[1];sys.path.insert(0,str(R))
tree=ast.parse((R/'native_routes.py').read_text());prefix=[]
for node in tree.body:
 if isinstance(node,ast.Try):break
 prefix.append(node)
ns={'__name__':'__focused_native_v1__','__file__':str(R/'native_routes.py')};exec(compile(ast.Module(body=prefix,type_ignores=[]),str(R/'native_routes.py'),'exec'),ns)
b=ns['b'];P=ns['P'];N='[data-canvas-node="note-node"]';b.raw('Page.addScriptToEvaluateOnNewDocument',{'source':(TASK/'helpers/passive.js').read_text()});traces=[];exit_code=0
expected=['original-selected-precondition','trusted-node-origin-capture-stage-click','already-selected-node','subthreshold-node-click','stage-background-clear','consecutive-node-clicks','ctrl-additive-node-click','plain-group-node-activation','completed-drag-trailing-click','viewport-background-clear','native-keyboard-activation']
(R/'EXPECTED_CHECKS.json').write_text(json.dumps(expected,indent=2))
def state():return ns['probe']()['snapshot'][0]
def members():return [x['localId'] for x in state()['selectedRefs']]
def record(name,ok,extra=None):
 data=b.ev('({rows:__diag.rows,snapshot:__lifecycleProbe.snapshot(),geometry:__diag.geometry()})');traces.append({'name':name,'trace':data,'extra':extra});(R/'CLICK_TRACES.json').write_text(json.dumps(traces,indent=2));b.record(name,'Accepted node/background/keyboard interaction contract; no state writes by runner',{'snapshot':data['snapshot'],'extra':extra},ok)
def no_clear_since(i):return not b.ev('__diag.rows.slice('+str(i)+').some(r=>r.kind==="store-notification" && r.state.selectedRefs.length===0)')
def mark():return b.ev('__diag.rows.length')
def pointclick(x,y,mods=0):
 for k in ['mouseMoved','mousePressed','mouseReleased']:b.mouse(k,x,y,mods)
try:
 s=ns['selected']();record(expected[0],members()==['project-node'])
 rows=b.ev('__diag.rows');events=[r for r in rows if r.get('kind')=='event' and r.get('listenerCapture')]
 downs=[r for r in events if r['type']=='pointerdown'];clicks=[r for r in events if r['type']=='click'];captures=[r for r in events if r['type']=='gotpointercapture']
 record(expected[1],bool(downs and clicks and captures) and 'canvas-node' in ' '.join(downs[-1]['pathElements']) and clicks[-1]['target']=='DIV.ff-workspace-canvas' and all(r['isTrusted'] for r in [downs[-1],clicks[-1],captures[-1]]) and downs[-1]['clientX']==clicks[-1]['clientX'] and downs[-1]['clientY']==clicks[-1]['clientY'])
 i=mark();before=state();b.click(P);record(expected[2],members()==['project-node'] and state()['revision']==before['revision'] and no_clear_since(i))
 i=mark();before=b.positions();x,y=b.down(P);b.move(x+2,y+1);b.up(x+2,y+1);record(expected[3],members()==['project-node'] and b.positions()==before and no_clear_since(i))
 r=b.rect('.ff-workspace-canvas');pointclick(r['x']+5,r['y']+5);record(expected[4],members()==[])
 i=mark();b.click(P);b.click(N);record(expected[5],members()==['note-node'] and no_clear_since(i))
 x,y=b.point(P);pointclick(x,y,2);record(expected[6],members()==['note-node','project-node'])
 i=mark();b.click(P);record(expected[7],members()==['project-node'] and no_clear_since(i))
 i=mark();before=b.positions();x,y=b.down(P);b.move(x+30,y+20);b.up(x+30,y+20);after=b.positions();record(expected[8],members()==['project-node'] and after[0]['x']==before[0]['x']+30 and after[0]['y']==before[0]['y']+20 and no_clear_since(i),{'before':before,'after':after})
 v=b.rect('.ff-canvas-viewport');x,y=v['x']+5,v['y']+5;target=b.ev('document.elementFromPoint('+str(x)+','+str(y)+').className');assert target=='ff-canvas-viewport',target;pointclick(x,y);record(expected[9],members()==[],{'origin_target':target})
 b.key('\ue004');active=b.ev('document.activeElement.dataset.canvasNode');assert active=='project-node',active;b.key('\ue007');record(expected[10],members()==['project-node'])
except BaseException:
 exit_code=1;(R/'CLICK_FAILURE.txt').write_text(traceback.format_exc());traceback.print_exc()
finally:
 try:
  (R/'FINAL_NATIVE_TRACE.json').write_text(json.dumps(b.ev('({rows:__diag.rows,snapshot:__lifecycleProbe.snapshot()})'),indent=2))
  b.shot('final-state')
 except BaseException:traceback.print_exc();exit_code=2
 (R/'CLICK_RESULTS.json').write_text(json.dumps({'checks':b.checks,'expected':expected,'exit':exit_code},indent=2));(R/'CLICK_COMMANDS.json').write_text(json.dumps(b.commands,indent=2));b.ws.close()
sys.exit(exit_code)
