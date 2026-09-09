import {useState} from 'react'
import {createRoot} from 'react-dom/client'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {RouterProvider,createRouter} from '@tanstack/react-router'
import {routeTree} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/snapshot/frontend/src/app/routeTree'
import {LocalizationProvider} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/snapshot/frontend/src/localization'
import {platformClient} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/snapshot/frontend/src/foundation/platformClient'
import {unknownAccess} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/snapshot/frontend/src/foundation/effectiveAccess'
import {PublicationSourceProvider} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/snapshot/frontend/src/product/publication/PublicationWorkspace'
import {source,receipt,grant} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/snapshot/frontend/src/product/publication/testing'
import {contentKey} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/snapshot/frontend/src/product/publication/types'
import {activateFixture,emitNative,setCurrent,emitLoaded,sdkLog} from './sdk'
import '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/snapshot/frontend/src/styles/index.css'
if(location.hostname!=='127.0.0.1'||!['1','project-only'].includes(new URLSearchParams(location.search).get('publicationFixture')||''))throw Error('Explicit isolated opt-in required')
activateFixture()
const queryClient=new QueryClient({defaultOptions:{queries:{staleTime:300000,retry:false}}})
const router=createRouter({routeTree,context:{queryClient},defaultPreload:'intent'})
const boundaryLog:any[]=[],reads:any[]=[],pending:any[]=[]
platformClient.workspace.getHome=async workspaceId=>{boundaryLog.push({workspaceId});return {workspace:{id:workspaceId,name:'ISOLATED publication'},tenantId:'tenant',recentProjects:[]}}
platformClient.effectiveAccess.getCatalog=async keys=>Object.fromEntries(keys.map(key=>[key,unknownAccess(key)]))
let mode='ready',serial=0
const extra=[['leap','2024-02-29T23:30:00Z'],['year','2023-12-31T23:30:00Z'],['midnight','2024-03-10T00:30:00Z'],['dst-before','2024-03-10T06:59:00Z'],['dst-after','2024-03-10T07:01:00Z'],['tie-a','2024-03-10T07:30:00Z'],['tie-z','2024-03-10T07:30:00Z'],['unscheduled',null],['invalid','2024-03-10T07:30:00']]
function data(r:any){const d:any=receipt(r);d.plans.push(...extra.map(([id,time])=>({id,projectId:'p',accountId:'a',title:id,status:'queued',artifactIds:[],timeField:id==='unscheduled'?'unscheduled':'scheduledAt',scheduledAt:time})));d.plans.push({id:'restricted',projectId:'p',accountId:'a',title:'RESTRICTED_COPY_SENTINEL',summary:'RESTRICTED_SUMMARY_SENTINEL',status:'unknown',artifactIds:[],timeField:'unknown'});if(mode==='remove')d.plans=d.plans.filter((p:any)=>p.id!=='two');if(['empty','partial'].includes(mode)){d.plans=[];d.attempts=[];d.externalPublications=[];d.completeness=mode==='partial'?'partial':'complete'}return d}
const initial=source(async(r,signal)=>{const row:any={request:r,mode,aborted:signal.aborted};reads.push(row);signal.addEventListener('abort',()=>row.aborted=true);if(mode==='error')throw Error('SIMULATED');const d=data(r);if(mode==='loading')return new Promise(resolve=>pending.push(()=>{row.settledLate=true;resolve(d)}));return d})
for(const [id] of extra)initial.access[contentKey(id!)]=grant(contentKey(id!))
function Host(){const [s,setS]=useState(initial);(window as any).__V10={reads,pending,boundaryLog,sdkLog,mode:(m:string)=>mode=m,replace:()=>setS(x=>({...x,owner:{}})),scope:()=>setS(x=>({...x,scope:{...x.scope,sessionId:'next-'+(++serial)}})),settle:()=>pending.splice(0).forEach(f=>f()),renew:async()=>{setCurrent();await emitLoaded()},event:emitNative};if(new URLSearchParams(location.search).get("publicationFixture")==="project-only")return <><aside>ISOLATED PROJECT CONTEXT — explicit auth/Project fixture; PublicationSourceProvider absent; NOT real integration</aside><RouterProvider router={router}/></>;return <PublicationSourceProvider source={s}><aside>EXPLICIT ISOLATED V10 — simulated source / SDK / access; NOT backend authority</aside><RouterProvider router={router}/></PublicationSourceProvider>}
createRoot(document.getElementById('root')!).render(<QueryClientProvider client={queryClient}><LocalizationProvider initialLocale="en"><Host/></LocalizationProvider></QueryClientProvider>)
