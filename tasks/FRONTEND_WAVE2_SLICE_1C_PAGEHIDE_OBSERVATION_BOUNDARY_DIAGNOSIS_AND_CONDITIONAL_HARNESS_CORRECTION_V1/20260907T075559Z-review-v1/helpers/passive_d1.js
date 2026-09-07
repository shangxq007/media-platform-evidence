(() => {
 const ids=new WeakMap();let serial=0;const id=x=>{if(!ids.has(x))ids.set(x,++serial);return ids.get(x)};
 const rows=[],bound=[];let current=null,departure=null;const documentId=crypto.randomUUID();
 function stores(){const el=document.getElementById('root');if(!el)return[];const k=Object.keys(el).find(k=>k.startsWith('__reactContainer$'));if(!k)return[];const f=el[k],q=[f.stateNode?.current||f],found=[];while(q.length){const x=q.pop();if(x.memoizedProps?.value?.getSnapshot&&x.memoizedProps.value.select)found.push(x.memoizedProps.value);if(x.child)q.push(x.child);if(x.sibling)q.push(x.sibling)}return [...new Set(found)]}
 function snap(s){const v=s.getSnapshot();return {store:id(s),lifetime:id(v.lifetime),revision:v.revision,refs:v.selectedRefs,primary:v.primaryRef,agentOpen:v.agentOpen}}
 function dom(){return {capture:[...document.querySelectorAll('.ff-workspace-canvas')].map(e=>({held:[...new Set((window.__lifecycleProbe?.capture||[]).map(x=>x.id))].filter(n=>e.hasPointerCapture(n))})),preview:!!document.querySelector('.ff-canvas-marquee'),proposal:!!document.querySelector('[data-testid=agent-proposal]'),positions:[...document.querySelectorAll('[data-canvas-node]')].map(e=>({id:e.dataset.canvasNode,left:e.style.left,top:e.style.top}))}}
 function mark(kind,event=null,store=null){const row={seq:rows.length+1,kind,documentId,at:performance.now(),event:event?{id:id(event),type:event.type,trusted:event.isTrusted,persisted:typeof event.persisted==='boolean'?event.persisted:null,phase:event.eventPhase}:null,departure,armed:current,stores:(store?[store]:bound).map(snap),dom:dom()};rows.push(row);return row}
 function arm(reader=stores){const ss=reader();if(ss.length!==1)throw Error('expected exactly one store');const s=ss[0];if(!bound.includes(s)){bound.push(s);s.subscribe(()=>{const row=mark('notify',null,s);row.stack=new Error('same-store notification').stack})}current={documentId,...snap(s)};mark('armed');return current}
 const p={documentId,rows,arm,mark,snapshot:()=>bound.map(snap),dom};window.__boundary=p;
 for(const type of ['pagehide','pageshow'])addEventListener(type,e=>{if(type==='pagehide')departure={id:id(e),trusted:e.isTrusted,persisted:e.persisted};mark('early-'+type,e);if(type==='pagehide')rows[rows.length-1].originalSamples=JSON.parse(JSON.stringify(window.__lifecycleProbe.events));queueMicrotask(()=>mark('early-microtask-'+type,e))});
 for(const type of ['freeze','resume'])document.addEventListener(type,e=>mark(type,e),true);
 p.installLate=()=>{addEventListener('pagehide',e=>mark('capture-pagehide',e),true);addEventListener('pagehide',e=>mark('late-pagehide',e));mark('late-listeners-registered')};
 mark('installed-before-application');
})();
