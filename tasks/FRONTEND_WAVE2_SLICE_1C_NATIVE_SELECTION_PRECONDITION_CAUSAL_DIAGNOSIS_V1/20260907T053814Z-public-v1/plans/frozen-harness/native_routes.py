import json,time,traceback
from native_common import CanvasBrowser,R,T
b=CanvasBrowser();b.viewport(1440,1000)
b.raw('Page.addScriptToEvaluateOnNewDocument',{'source':(R/'lifecycle-observer.js').read_text()})
P='[data-canvas-node="project-node"]'
def probe():return b.ev('({snapshot:__lifecycleProbe.snapshot(),events:__lifecycleProbe.events,capture:__lifecycleProbe.captureState(),observations:__lifecycleProbe.observations,proposals:__lifecycleProbe.proposals(),path:location.pathname})')
def nav(path):
 b.ev('__lifecycleProbe.router().navigate({to:'+json.dumps(path)+'})');time.sleep(.7)
def rec(name,before,after,ok):b.record(name,'Frozen route/lifetime contract',{'before':before,'after':after},ok,assistance='CDP trusted mouse; DOM-assisted router navigation; read-only fiber/store snapshots; synthetic API fixtures')
def selected():
 (R/'fixture-workspace.txt').write_text('ux-workspace');b.reset();b.click(P);time.sleep(.2);s=probe();assert s['snapshot'][0]['selectedRefs'];return s
def empty(s):return all(not v['selectedRefs'] and v['primaryRef'] is None for v in s['snapshot'])
def torn(s):
 bad=[]
 for o in s['observations']:
  parts=o['path'].split('/');w=parts[2] if len(parts)>2 and parts[1]=='w' else None;p=parts[4] if len(parts)>4 and parts[3]=='projects' else None
  for v in o['snapshot']:
   for r in v['selectedRefs']:
    if r.get('workspaceId')!=w or r.get('projectId')!=p or r.get('surfaceId')!=v['surfaceId']:bad.append(o)
 return bad
try:
 for kind in ['query','hash']:
  s=selected();b.ev('__lifecycleProbe.router().navigate({to:location.pathname,'+('search:{view:"wide"}' if kind=='query' else 'hash:"main-content"')+'})');a=probe();rec('same-scope-'+kind,s,a,s['snapshot']==a['snapshot'])
 for kind,path in [('surface','/w/ux-workspace/projects/ux-project/workflow'),('project','/w/ux-workspace/projects/other/canvas'),('workspace','/w/other/projects/ux-project/canvas')]:
  s=selected();(R/'fixture-workspace.txt').write_text('other' if kind=='workspace' else 'ux-workspace');nav(path);a=probe();rec(kind+'-retires-owner',s,a,empty(a) and bool(a['snapshot']) and a['snapshot'][0]['lifetime']!=s['snapshot'][0]['lifetime']);rec(kind+'-torn-state',s,a,not torn(a))
 for kind in ['drag','marquee','pan']:
  s=selected();positions=b.positions();camera=b.camera()
  if kind=='pan':b.button('Pan')
  stage=b.rect('.ff-workspace-canvas');x,y=b.point(P) if kind=='drag' else (stage['x']+30,stage['y']+30)
  b.ev('window.__oldStage=document.querySelector(".ff-workspace-canvas")')
  b.mouse('mouseMoved',x,y);b.mouse('mousePressed',x,y);b.move(x+70,y+65)
  active=probe();rec(kind+'-real-capture-precondition',s,active,any(c['held'] for c in active['capture']))
  if kind=='marquee':assert b.ev('!!document.querySelector("[data-canvas-marquee]")')
  nav('/w/ux-workspace/projects/other/canvas');a=probe()
  held=b.ev('(__lifecycleProbe.capture||[]).filter(e=>e.type==="gotpointercapture").some(e=>__oldStage.hasPointerCapture(e.id))')
  rec(kind+'-real-capture-cancel',active,a,not held and empty(a) and not b.ev('!!document.querySelector("[data-canvas-marquee]")'))
  b.up(x+90,y+90);after=probe();rec(kind+'-no-partial-commit',active,after,b.positions()==[{**v,'selected':False} for v in positions] and empty(after))
 for kind,path,mode in [('unresolved','/w/pending/projects/p/canvas','loading'),('error','/w/error/projects/p/canvas','error'),('invalid','/w/ux-workspace/projects/%20/canvas','ready'),('unsupported','/w/ux-workspace/projects/ux-project/unsupported','ready')]:
  (R/'fixture-mode.txt').write_text('ready');s=selected();(R/'fixture-mode.txt').write_text(mode);nav(path);a=probe();rec(kind+'-no-old-selection',s,a,empty(a) and not b.ev('!!document.querySelector("[data-canvas-node][aria-pressed=true]")') and not torn(a))
 (R/'fixture-mode.txt').write_text('ready')
finally:
 (R/'NATIVE_ROUTE_RESULTS.json').write_text(json.dumps({'tree':T,'checks':b.checks},indent=2));(R/'NATIVE_ROUTE_COMMANDS.json').write_text(json.dumps(b.commands,indent=2));b.ws.close()
