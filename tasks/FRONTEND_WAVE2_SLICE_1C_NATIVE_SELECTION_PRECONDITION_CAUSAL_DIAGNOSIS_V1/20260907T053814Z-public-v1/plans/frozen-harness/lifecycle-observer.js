(() => {
 const ids=new WeakMap();let serial=0;
 const id=o=>{if(!ids.has(o))ids.set(o,++serial);return ids.get(o)};
 function fibers(){const el=document.getElementById('root');if(!el)return[];const key=Object.keys(el).find(k=>k.startsWith('__reactContainer$'));if(!key)return[];const f=el[key];const root=f.stateNode?.current||f;const out=[],q=[root];while(q.length){const x=q.pop();out.push(x);if(x.sibling)q.push(x.sibling);if(x.child)q.push(x.child)}return out}
 function stores(){return [...new Set(fibers().map(f=>f.memoizedProps?.value).filter(v=>v&&typeof v.getSnapshot==='function'&&typeof v.select==='function'))]}
 function snapshot(){return stores().map(s=>{const v=s.getSnapshot();return {owner:id(s),lifetime:id(v.lifetime),revision:v.revision,surfaceId:v.surfaceId,workspaceId:v.workspaceId,projectId:v.projectId,selectedRefs:v.selectedRefs,primaryRef:v.primaryRef,supported:v.supported}})}
 function router(){return fibers().map(f=>f.memoizedProps?.value).find(v=>v&&typeof v.navigate==='function'&&v.history&&v.state)}
 function proposals(){const rows=[];for(const f of fibers()){let h=f.memoizedState;let guard=0;while(h&&typeof h==='object'&&guard++<100){const p=h.memoizedState;if(p&&typeof p==='object'&&p.lifetime&&'intent' in p&&'revision' in p)rows.push({lifetime:id(p.lifetime),revision:p.revision,intent:p.intent,target:p.target});h=h.next}}return rows}
 const probe={documentId:crypto.randomUUID(),events:[],observations:[],snapshot,proposals,router};
 const record=(event,persisted)=>probe.events.push({event,persisted,path:location.pathname,at:performance.now(),snapshot:snapshot(),proposals:proposals(),selectedDom:[...document.querySelectorAll('[data-canvas-node][aria-pressed="true"]')].map(e=>e.dataset.canvasNode),capture:probe.capture||[]});
 for(const type of ['pagehide','pageshow'])addEventListener(type,event=>queueMicrotask(()=>record(type,event.persisted)));
 document.addEventListener('gotpointercapture',e=>(probe.capture ||= []).push({type:e.type,id:e.pointerId}),true);
 document.addEventListener('lostpointercapture',e=>(probe.capture ||= []).push({type:e.type,id:e.pointerId}),true);
 probe.captureState=()=>[...document.querySelectorAll('.ff-workspace-canvas')].map(e=>({connected:e.isConnected,held:(probe.capture||[]).filter(x=>x.type==='gotpointercapture').some(x=>e.hasPointerCapture(x.id))}));
 new MutationObserver(()=>{const rows=snapshot();if(rows.length)probe.observations.push({path:location.pathname,hash:location.hash,search:location.search,shell:document.querySelector('.ff-app-shell')?.dataset.surface,snapshot:rows})}).observe(document,{subtree:true,childList:true,attributes:true});
 window.__lifecycleProbe=probe;
})();