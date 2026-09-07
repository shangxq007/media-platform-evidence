import ast,sys,json,traceback
from pathlib import Path
R=Path(sys.argv[1]);TASK=R.parents[1];sys.path.insert(0,str(R));tree=ast.parse((R/'native_routes.py').read_text());prefix=[]
for node in tree.body:
 if isinstance(node,ast.Try):break
 prefix.append(node)
ns={'__name__':'__supplement_v1__','__file__':str(R/'native_routes.py')};exec(compile(ast.Module(body=prefix,type_ignores=[]),str(R/'native_routes.py'),'exec'),ns);b=ns['b'];rc=0
expected=['T17-no-role-application','T17-native-delete-no-route-selection-layer','T17-native-editable-arrow-escape-ownership','positive-area-native-marquee','T14-positive-preview-precondition','T14-preview-residue-after-navigation']
(R/'EXPECTED_CHECKS.json').write_text(json.dumps(expected,indent=2))
def snap():return ns['probe']()['snapshot']
def rec(name,ok,actual):b.record(name,'Frozen T17 keyboard ownership / T14 preview and accepted marquee behavior',actual,ok)
try:
 b.raw('Page.addScriptToEvaluateOnNewDocument',{'source':(TASK/'helpers/passive.js').read_text()})
 ns['selected']();b.ev('window.__nativeKeys=[];window.addEventListener("keydown",e=>__nativeKeys.push({key:e.key,isTrusted:e.isTrusted,target:e.target.tagName,isComposing:e.isComposing}),{capture:true,passive:true});void 0')
 rec(expected[0],not b.ev('!!document.querySelector("[role=application]")'),{'role_application_present':False})
 before=snap();positions=b.positions()
 for kind in ['keyDown','keyUp']:b.raw('Input.dispatchKeyEvent',{'type':kind,'key':'Delete','code':'Delete','windowsVirtualKeyCode':46})
 rec(expected[1],snap()==before and b.positions()==positions,{'before':before,'after':snap(),'keys':b.ev('__nativeKeys')})
 b.click('#selection-inspector input');before=snap();positions=b.positions();b.key('\ue012');b.key('\ue00c')
 rec(expected[2],snap()==before and b.positions()==positions and b.ev('document.activeElement.tagName')=='INPUT',{'before':before,'after':snap(),'keys':b.ev('__nativeKeys'),'physical_OS_IME':'NOT_RUN; synthetic exclusions covered in fresh unit suite'})
 r=b.rect('.ff-workspace-canvas');x,y=r['x']+5,r['y']+5;b.mouse('mouseMoved',x,y);b.mouse('mousePressed',x,y);b.move(r['x']+r['w']-5,r['y']+r['h']-5);assert b.ev('!!document.querySelector("[data-canvas-marquee]")');b.up(r['x']+r['w']-5,r['y']+r['h']-5)
 rec(expected[3],[v['localId'] for v in snap()[0]['selectedRefs']]==['project-node','note-node'],snap())
 r=b.rect('.ff-workspace-canvas');x,y=r['x']+5,r['y']+5;b.mouse('mouseMoved',x,y);b.mouse('mousePressed',x,y);b.move(x+90,y+80)
 before=ns['probe']();rec(expected[4],b.ev('!!document.querySelector("[data-canvas-marquee]")') and any(v['held'] for v in before['capture']),before)
 ns['nav']('/w/ux-workspace/projects/other/canvas');b.up(x+90,y+80);after=ns['probe']()
 rec(expected[5],ns['empty'](after) and not b.ev('!!document.querySelector("[data-canvas-marquee]")') and not b.ev('document.querySelector(".ff-canvas-status").textContent.includes("preview")'),after)
except BaseException:
 rc=1;(R/'SUPPLEMENT_FAILURE.txt').write_text(traceback.format_exc());traceback.print_exc()
finally:
 try:(R/'SUPPLEMENT_TRACE.json').write_text(json.dumps(b.ev('({rows:__diag.rows,snapshot:__lifecycleProbe.snapshot(),keys:__nativeKeys})'),indent=2))
 except BaseException:traceback.print_exc();rc=2
 (R/'SUPPLEMENT_RESULTS.json').write_text(json.dumps({'checks':b.checks,'expected':expected,'exit':rc},indent=2));(R/'SUPPLEMENT_COMMANDS.json').write_text(json.dumps(b.commands,indent=2));b.ws.close()
sys.exit(rc)
