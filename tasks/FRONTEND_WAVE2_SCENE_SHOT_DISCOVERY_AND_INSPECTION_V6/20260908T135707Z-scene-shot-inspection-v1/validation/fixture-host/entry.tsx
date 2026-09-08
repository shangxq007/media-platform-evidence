import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { routeTree } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/final-validation-02/snapshot/frontend/src/app/routeTree'
import { LocalizationProvider } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/final-validation-02/snapshot/frontend/src/localization'
import { ProductionSourceProvider } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/final-validation-02/snapshot/frontend/src/product/production/source'
import { createSimulatedProductionSource } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/final-validation-02/snapshot/frontend/src/product/production/simulatedSource'
import '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/final-validation-02/snapshot/frontend/src/styles/index.css'
if (!['127.0.0.1','localhost'].includes(location.hostname) || new URLSearchParams(location.search).get('v6Fixture') !== '1') throw Error('Explicit local V6 fixture opt-in required')
const scope={principalId:'simulated-production-reader',tenantId:'simulated-tenant',sessionId:'simulated-production-session',workspaceId:'workspace-1',projectId:'simulated-project'}
const fixture=createSimulatedProductionSource({scope})
let outcome='normal';let pendingResolve: (()=>void)|null=null
const calls: unknown[]=[]
const source={...fixture,adapter:{origin:'simulated' as const,async readProject(request:any,signal:AbortSignal){
 const mode=outcome;calls.push({request,mode,abortedAtStart:signal.aborted})
 if(mode==='pending') await new Promise<void>(resolve=>{pendingResolve=resolve})
 if(['error','denied','unknown','unsupported','unavailable','stale'].includes(mode))return {scope:request.scope,requestId:request.requestId,status:mode,explanation:'SIMULATED controlled source result'}
 if(mode==='invalid')return {deliberatelyInvalidFixture:true}
 if(mode==='empty')return createSimulatedProductionSource({scope,empty:true}).adapter.readProject(request,signal)
 if(mode==='bounded')return createSimulatedProductionSource({scope,limit:3}).adapter.readProject(request,signal)
 // Deliberately ignore late cancellation in the external adversarial source; the consumer must fence it.
 return fixture.adapter.readProject(request,new AbortController().signal)
}}}
;(window as any).__V6Fixture={setOutcome:(value:string)=>{outcome=value},resolvePending:()=>{pendingResolve?.();pendingResolve=null},calls,scope}
const queryClient=new QueryClient({defaultOptions:{queries:{staleTime:1000*60*5,retry:1}}})
const router=createRouter({routeTree,context:{queryClient},defaultPreload:'intent'})
createRoot(document.getElementById('root')!).render(<StrictMode><QueryClientProvider client={queryClient}><LocalizationProvider><ProductionSourceProvider source={source}><aside data-v6-host style={{padding:'6px',background:'#462e05',color:'#fff'}}>EXPLICIT LOCAL V6 FIXTURE HOST — simulated identity and Scene/Shot data; no backend integration</aside><RouterProvider router={router}/></ProductionSourceProvider></LocalizationProvider></QueryClientProvider></StrictMode>)
