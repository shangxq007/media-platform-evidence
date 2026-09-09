import {useState} from 'react'
import {createRoot} from 'react-dom/client'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {RouterProvider,createRouter} from '@tanstack/react-router'
import {routeTree} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NLE_TIMELINE_NAVIGATION_AND_INSPECTION_V9/validation-03/snapshot/frontend/src/app/routeTree'
import {LocalizationProvider} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NLE_TIMELINE_NAVIGATION_AND_INSPECTION_V9/validation-03/snapshot/frontend/src/localization'
import {platformClient} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NLE_TIMELINE_NAVIGATION_AND_INSPECTION_V9/validation-03/snapshot/frontend/src/foundation/platformClient'
import {unknownAccess} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NLE_TIMELINE_NAVIGATION_AND_INSPECTION_V9/validation-03/snapshot/frontend/src/foundation/effectiveAccess'
import {TimelineNavigationProvider} from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NLE_TIMELINE_NAVIGATION_AND_INSPECTION_V9/validation-03/snapshot/frontend/src/product/timeline/TimelineNavigation'
import {activateFixture,emitNative,setCurrent,emitLoaded,sdkLog} from './sdk'
import '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NLE_TIMELINE_NAVIGATION_AND_INSPECTION_V9/validation-03/snapshot/frontend/src/styles/index.css'
if(location.hostname!=='127.0.0.1'||new URLSearchParams(location.search).get('nleFixture')!=='1')throw Error('Explicit isolated NLE opt-in required')
activateFixture()
const queryClient=new QueryClient({defaultOptions:{queries:{staleTime:300000,retry:false}}})
const router=createRouter({routeTree,context:{queryClient},defaultPreload:'intent'})
const boundaryLog:any[]=[]
platformClient.workspace.getHome=async(workspaceId)=>{boundaryLog.push({kind:'workspace',workspaceId});return {workspace:{id:workspaceId,name:'ISOLATED NLE workspace'},tenantId:'tenant-1',recentProjects:[]}}
platformClient.effectiveAccess.getCatalog=async keys=>{boundaryLog.push({kind:'effectiveAccess',keys});return Object.fromEntries(keys.map(key=>[key,unknownAccess(key)]))}
const reads:any[]=[],pending:any[]=[]
let mode='ready', serial=0
const longName='Opening 超长片段名称 '+ 'Long logical metadata name 中文 '.repeat(15)
function adapter(){const id=++serial;return {origin:'isolated-verification',async read(request:any,signal:AbortSignal){const row:any={id,request,mode,aborted:signal.aborted};reads.push(row);signal.addEventListener('abort',()=>row.aborted=true);const result={...request,status:'ok',completeness:'bounded',timeBasis:mode==='unknown'?'unknown':'exact-seconds',bounds:{start:'0',end:'2'},tracks:mode==='empty'?[]:[{id:'video-1',name:'Picture 视频 '+ 'Track long name '.repeat(12),type:'video',clips:[{id:'clip-1',trackId:'video-1',name:longName,type:'video',version:'v1',timelineRange:{start:'0',end:'1001/30000'},sourceRange:{start:'10',end:'11'},source:{mediaAssetId:'asset-1',mediaStreamId:'stream-1'}},{id:'clip-2',trackId:'video-1',name:'Continuation 后续',type:'video',timelineRange:{start:'1001/30000',end:'2'}}]},{id:'audio-1',name:'Audio 音频',type:'audio',clips:[]}]};if(mode==='error')throw Error('SIMULATED_READ_ERROR');if(mode==='loading')return new Promise(resolve=>pending.push(()=>{row.settledLate=true;resolve(result)}));return result}}}
const initial:any={scope:{principalId:'principal-1',tenantId:'tenant-1',sessionId:'session-1',workspaceId:'workspace-1',projectId:'project-1'},accessBinding:{kind:'TEST_ONLY_UNAGREED',key:'v9-read'},access:{key:'v9-read',source:'SERVER',status:'AVAILABLE',reasonCode:'ISOLATED_ONLY',explanation:'Simulated not authorization',factors:{capability:'SATISFIED',runtime:'NOT_APPLICABLE',entitlement:'SATISFIED',policy:'SATISFIED',quota:'NOT_APPLICABLE'}},adapter:adapter()}
function Host(){const [source,setSource]=useState(initial);(window as any).__V9={reads,pending,sdkLog,boundaryLog,longName,mode:(next:string)=>{mode=next},replace:()=>setSource((s:any)=>({...s,adapter:adapter()})),access:(status:string)=>setSource((s:any)=>({...s,access:{...s.access,status}})),scope:()=>setSource((s:any)=>({...s,scope:{...s.scope,sessionId:'session-'+(++serial)}})),settle:()=>{pending.splice(0).forEach(fn=>fn())},identity:async()=>{setCurrent({sub:'principal-next',sid:'session-next'});await emitLoaded()},event:emitNative};return <TimelineNavigationProvider source={source}><aside style={{padding:6,background:'#462e05',color:'white'}}>EXPLICIT ISOLATED V9 — simulated projection / SDK / access; NOT backend integration</aside><RouterProvider router={router}/></TimelineNavigationProvider>}
createRoot(document.getElementById('root')!).render(<QueryClientProvider client={queryClient}><LocalizationProvider><Host/></LocalizationProvider></QueryClientProvider>)
