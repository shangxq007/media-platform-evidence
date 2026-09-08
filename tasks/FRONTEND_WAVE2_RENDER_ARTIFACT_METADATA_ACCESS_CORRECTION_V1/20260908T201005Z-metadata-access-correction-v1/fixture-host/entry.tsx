import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { routeTree } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend/src/app/routeTree'
import { LocalizationProvider } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend/src/localization'
import { RenderBrowserProvider } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend/src/product/render-browser/RenderBrowser'
import { createRendersFixture } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend/src/product/render-browser/fixture'
import '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/final-validation-01/snapshot/frontend/src/styles/index.css'
if (location.hostname !== '127.0.0.1' || new URLSearchParams(location.search).get('metadataFixture') !== '1') throw Error('Explicit loopback metadata fixture opt-in required')
const initialScope={principalId:'simulated-render-reader',tenantId:'simulated-tenant',sessionId:'simulated-render-session',projectId:'simulated-project'}
let mode='mixed'
const calls:any[]=[]
const pending=new Map<number,()=>void>()
let next=0
let changeContext:(kind:string)=>void=()=>{throw Error('host not mounted')}
const states=['inspectable','denied','unknown','stale','unavailable'] as const
const items=states.map((state,index)=>({id:`ordinary-artifact-${index}`,name:`Ordinary preview ${index} 原文`,type:`video/ordinary-${index}`,availability:`ORDINARY_AVAILABILITY_${index}`,version:`ordinary-version-${index}`,taskId:'task-courtyard',metadataAccess:state}))
function sourceFor(scope:any,accessStatus:any='AVAILABLE') {
 const fixture=createRendersFixture({scope,accessStatus})
 return {...fixture,adapter:{origin:'simulated' as const,async readProject(request:any,signal:AbortSignal){
  const selected=mode;const id=++next
  const call:any={id,request:structuredClone(request),mode:selected,abortedAtStart:signal.aborted,returned:false};calls.push(call)
  // Capture the old request and outcome before waiting; deliberately ignore cancellation.
  const result:any=await fixture.adapter.readProject(request,new AbortController().signal)
  if(result.status==='ok') {
   const access=selected==='visible'?'inspectable':selected.startsWith('all-')?selected.slice(4):null
   result.jobs[0].artifacts={state:'available',completeness:'complete',limit:5,items:items.map(item=>({...item,metadataAccess:access??item.metadataAccess}))}
   if(scope.sessionId!==initialScope.sessionId) result.jobs[0].name='New session render'
  }
  if(selected==='pending') await new Promise<void>(resolve=>pending.set(id,resolve))
  call.abortedAtReturn=signal.aborted;call.returned=true;pending.delete(id)
  return result
 }}}
}
;(window as any).__MetadataFixture={setMode:(value:string)=>{if(!['mixed','visible','all-denied','all-unknown','all-stale','all-unavailable','pending'].includes(value))throw Error('unsupported mode');mode=value},resolvePending:()=>{for(const resolve of pending.values())resolve()},pendingIds:()=>[...pending.keys()],calls,items,changeContext:(kind:string)=>changeContext(kind)}
const queryClient=new QueryClient({defaultOptions:{queries:{staleTime:300000,retry:1}}})
const router=createRouter({routeTree,context:{queryClient},defaultPreload:'intent'})
function Host(){
 const [source,setSource]=useState(()=>sourceFor(initialScope))
 changeContext=(kind)=>{
  if(kind==='session')setSource(sourceFor({...initialScope,sessionId:'simulated-session-next'}))
  else if(kind==='denied')setSource(sourceFor(initialScope,'POLICY_DENIED'))
  else if(kind==='unknown')setSource(sourceFor(initialScope,'UNKNOWN_FAIL_CLOSED'))
  else if(kind==='reset')setSource(sourceFor(initialScope))
  else throw Error('unsupported context')
 }
 return <RenderBrowserProvider source={source}><aside data-metadata-host style={{padding:6,background:'#462e05',color:'#fff'}}>EXPLICIT LOCAL METADATA FIXTURE — simulated Render identity/data; no backend integration</aside><RouterProvider router={router}/></RenderBrowserProvider>
}
createRoot(document.getElementById('root')!).render(<StrictMode><QueryClientProvider client={queryClient}><LocalizationProvider><Host/></LocalizationProvider></QueryClientProvider></StrictMode>)
