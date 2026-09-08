from pathlib import Path
import sys,json
V=Path(sys.argv[1]).resolve();S=V/'snapshot/frontend';H=V/'fixture-host';H.mkdir(exist_ok=False)
(H/'node_modules').symlink_to(S/'node_modules',target_is_directory=True)
text='''import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { routeTree } from 'SOURCE/app/routeTree'
import { LocalizationProvider } from 'SOURCE/localization'
import { RenderBrowserProvider } from 'SOURCE/product/render-browser/RenderBrowser'
import { createRendersFixture } from 'SOURCE/product/render-browser/fixture'
import 'SOURCE/styles/index.css'
if (!['127.0.0.1','localhost'].includes(location.hostname) || new URLSearchParams(location.search).get('v7Fixture') !== '1') throw Error('Explicit local V7 fixture opt-in required')
const scope={principalId:'simulated-render-reader',tenantId:'simulated-tenant',sessionId:'simulated-render-session',projectId:'simulated-project'}
const fixture=createRendersFixture({scope})
let outcome='normal';let pendingResolve: (()=>void)|null=null
const calls: unknown[]=[]
const source={...fixture,adapter:{origin:'simulated' as const,async readProject(request:any,signal:AbortSignal){
 const mode=outcome;calls.push({request,mode,abortedAtStart:signal.aborted})
 if(mode==='pending') await new Promise<void>(resolve=>{pendingResolve=resolve})
 if(['error','denied','unknown','unsupported','unavailable','stale'].includes(mode))return {scope:request.scope,requestId:request.requestId,status:mode,explanation:'SIMULATED controlled source result'}
 if(mode==='invalid')return {deliberatelyInvalidFixture:true}
 if(mode==='empty')return createRendersFixture({scope,empty:true}).adapter.readProject(request,signal)
 if(mode==='bounded')return createRendersFixture({scope,limit:2}).adapter.readProject(request,signal)
 // Deliberately ignore late cancellation in this external adversarial source.
 const result:any=await fixture.adapter.readProject(request,new AbortController().signal)
 if(mode==='invalid-relationship')result.jobs[0].attempts.items[0].taskId='foreign-task'
 if(mode==='unknown-progress')delete result.jobs[0].progress.total,delete result.jobs[0].progress.totalUnit
 if(mode==='artifact-denied')result.jobs[0].artifacts={state:'denied'}
 if(mode==='artifact-stale')result.jobs[0].artifacts={state:'stale'}
 if(mode==='missing-detail')result.jobs=result.jobs.filter((job:any)=>job.id!=='render-courtyard-final')
 return result
}}}
;(window as any).__V7Fixture={setOutcome:(value:string)=>{outcome=value},resolvePending:()=>{pendingResolve?.();pendingResolve=null},calls,scope}
const queryClient=new QueryClient({defaultOptions:{queries:{staleTime:1000*60*5,retry:1}}})
const router=createRouter({routeTree,context:{queryClient},defaultPreload:'intent'})
createRoot(document.getElementById('root')!).render(<StrictMode><QueryClientProvider client={queryClient}><LocalizationProvider><RenderBrowserProvider source={source}><aside data-v7-host style={{padding:'6px',background:'#462e05',color:'#fff'}}>EXPLICIT LOCAL V7 FIXTURE HOST — simulated identity and Render data; no backend integration</aside><RouterProvider router={router}/></RenderBrowserProvider></LocalizationProvider></QueryClientProvider></StrictMode>)
'''.replace('SOURCE',str(S/'src'))
(H/'entry.tsx').write_text(text)
(V/'FIXTURE_HOST_INPUTS.json').write_text(json.dumps({'implementation_tree':(V/'FINAL_TREE.txt').read_text().strip(),'host':str(H/'entry.tsx'),'scope':'External opt-in RenderBrowserProvider around exact final registered route tree; simulated identity/data and controlled adversarial outcomes. Ordinary entry unavailable.','ordinary_entry':str(S/'src/main.tsx'),'fixture_scope':{'principalId':'simulated-render-reader','tenantId':'simulated-tenant','sessionId':'simulated-render-session','projectId':'simulated-project'}},indent=2))
