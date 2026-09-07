from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];B=R.parent/'FRONTEND_WAVE2_SLICE_1C_FOUNDATIONPAGES_LINT_CORRECTION_AND_VALIDATION_CONTINUATION_V1/build/assets';out=R/'runs/R2';out.mkdir(exist_ok=True)
F='FoundationPages-hrn57YLE.js';C='WorkspaceCanvas-CJYBS6re.js'
points=[]
def point(file,name,needle,expr,source):
 text=(B/file).read_text();assert text.count(needle)==1,(name,text.count(needle));offset=text.index(needle)
 line=text[:offset].count('\n');col=len(text[text.rfind('\n',0,offset)+1:offset].encode('utf-16-le'))//2
 condition='typeof __diag!=="undefined"&&(__diag.record("logpoint",{name:'+json.dumps(name)+','+expr+',stack:new Error("diagnostic logpoint").stack}),false)'
 points.append({'name':name,'source_correspondence':source,'bundle_sha256':hashlib.sha256((B/file).read_bytes()).hexdigest(),'character_offset':offset,'excerpt':text[max(0,offset-100):offset+350],'params':{'url':'http://127.0.0.1:4196/assets/'+file,'lineNumber':line,'columnNumber':col,'condition':condition}})
model='frontend/src/interaction/model.ts:';canvas='frontend/src/product/canvas/WorkspaceCanvas.tsx:'
point(F,'update-before','Object.entries(a).every','next:a,invalidate:g,before:s,lifetime:__diag.id(s.lifetime),adapter:__diag.id(c)',model+'61-64')
point(F,'retirement','a==="document"&&(p=!0)','reason:a,retired:d,documentRetired:p,before:s,adapter:__diag.id(c)',model+'67-72')
point(F,'register','if(p)return()=>{};if(c)','nextAdapter:__diag.id(a),previousAdapter:__diag.id(c),documentRetired:p,before:s',model+'126-131')
point(F,'reconcile-inventory','V(s.selectedRefs.flatMap','inventory:a,before:s,adapter:__diag.id(c),lifetime:__diag.id(s.lifetime),projectNodeMatches:a.filter(o=>o.kind==="NODE"&&o.id==="project-node").length',model+'95-98')
point(F,'select-request','if(d)return E("Selection ownership has retired.");if(P(),a.lifetime','request:a,before:s,requestLifetime:__diag.id(a.lifetime),lifetime:__diag.id(s.lifetime),adapter:__diag.id(c)',model+'99-118')
point(F,'publish-selection','const m=Object.freeze([...a]),O=Object.freeze(a.map(i))','objects:a,primary:g,supported:u,before:s,lifetime:__diag.id(s.lifetime),adapter:__diag.id(c)',model+'84-94')
point(F,'dispatch-action','if(["CANONICAL_SEMANTIC"].includes(a.category)','action:a,invocationSource:g,before:s,lifetime:__diag.id(s.lifetime),adapter:__diag.id(c)',model+'143-158')
point(C,'cancel-gesture','const e=a.current;if(a.current=null','active:__diag.gestures(),suppression:N.current,store:__diag.id(I)',canvas+'57-66')
point(C,'pointerup-entry','const t=V(e.pointerId);if(!t)return;const s=H(t,e);if(g()','event:{type:e.type,target:__diag.desc(e.target),currentTarget:__diag.desc(e.currentTarget),clientX:e.clientX,clientY:e.clientY,buttons:e.buttons,button:e.button},active:__diag.gestures(),suppression:N.current,store:__diag.id(I)',canvas+'148-151')
point(C,'no-drag-return','if(!t.moved)return;k(d=>re(d,t.originals,s))','moved:t.moved,kind:t.kind,suppression:N.current,delta:s,store:__diag.id(I),contextRevision:t.context.revision',canvas+'155-158')
point(C,'clear-dispatch','I.dispatch({category:"LOCAL_EPHEMERAL",type:"select",ids:[]})','store:__diag.id(I),state:__diag.state(I),suppression:N.current',canvas+'183')
point(C,'click-capture','N.current&&e.detail!==0','suppression:N.current,event:{type:e.type,detail:e.detail,target:__diag.desc(e.target),currentTarget:__diag.desc(e.currentTarget),isTrusted:e.nativeEvent.isTrusted},store:__diag.id(I)',canvas+'276 onClickCapture')
point(C,'background-click','_(e.target)&&U()','event:{type:e.type,detail:e.detail,target:__diag.desc(e.target),currentTarget:__diag.desc(e.currentTarget),isTrusted:e.nativeEvent.isTrusted},isStage:e.target===b.current,isViewport:e.target===B.current,suppression:N.current,store:__diag.id(I)',canvas+'101,276 onClick')
point(C,'resize-callback','const t=a.current;if(t){if(oe(t,b.current))','active:__diag.gestures(),selected:C?.presentationId,suppression:N.current,geometry:__diag.geometry(),store:__diag.id(I)',canvas+'212-220')
point(C,'fit','const e=(t=b.current)==null?void 0:t.getBoundingClientRect();e&&k(s=>Ee','geometry:__diag.geometry(),active:__diag.gestures(),store:__diag.id(I)',canvas+'184')
point(C,'reveal','const e=(t=b.current)==null?void 0:t.getBoundingClientRect();e&&k(s=>{','geometry:__diag.geometry(),active:__diag.gestures(),store:__diag.id(I)',canvas+'185-193')
(out/'logpoints.json').write_text(json.dumps(points,indent=2))
(out/'PLAN.txt').write_text('R2 targeted confirmation of R1 clearing stack. Same original selected/input/build/fixture behavior, fresh profile. No acceptance continuation. Conditional debugger logpoints return false, no pauses, stepping, method replacements or setters. Capture exact dispatch/select/publication, all actual reconcile inventories, register/retirement, no-drag suppression reset, background event, cancellation and fit/reveal/ResizeObserver callbacks. R1 already independently reproduces without debugger; compare native sequence, geometry and ownership. Extra geometry/fiber reads and debugger execution overhead can perturb timing; do not infer original exact callback timing solely from R2. Exact prospective locations/conditions recorded in logpoints.json. Expected assertion failure is diagnostic exit1. No retry if instrumentation crashes; retain evidence and diagnose boundary.\n')
print('points',len(points));print([(x['name'],x['params']['lineNumber'],x['params']['columnNumber']) for x in points])
