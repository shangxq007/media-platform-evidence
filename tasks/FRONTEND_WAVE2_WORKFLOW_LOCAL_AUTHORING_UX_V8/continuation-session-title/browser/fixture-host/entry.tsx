import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { routeTree } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/snapshot/frontend/src/app/routeTree'
import { LocalizationProvider } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/snapshot/frontend/src/localization'
import { platformClient, platformQueryKeys, type WorkspaceHomeProjection } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/snapshot/frontend/src/foundation/platformClient'
import { activateFixture, emitNative, sdkLog, replayRetired, settleSignout, settleGetter, deferGetter, setCurrent, emitLoaded, pendingLoaded, currentInfo } from './sdk'
import { signOutOidc, getOidcUser, subscribeOidcSessionRetirement } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/snapshot/frontend/src/auth/oidcClient'
import { unknownAccess } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/snapshot/frontend/src/foundation/effectiveAccess'
import '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/snapshot/frontend/src/styles/index.css'
if (location.hostname !== '127.0.0.1' || new URLSearchParams(location.search).get('workflowFixture') !== '1') throw Error('Explicit loopback Workflow fixture opt-in required')
activateFixture()
// Exercise the real exported cleanup in production builds (StrictMode double effects
// are development-only). This probe adds no identity or Selection authority.
let disposedProbeDeliveries = 0
const disposeProbe = subscribeOidcSessionRetirement(() => { disposedProbeDeliveries++ })
disposeProbe(); disposeProbe()
const queryClient = new QueryClient({defaultOptions:{queries:{staleTime:300000,retry:false}}})
const router = createRouter({routeTree,context:{queryClient},defaultPreload:'intent'})
let mode: 'ready' | 'error' | 'unavailable' = 'ready'
let tenant = 'simulated-workflow-tenant'
const calls: unknown[] = []
// The existing platformClient interface is the sole bootstrap seam. No node adapter,
// Workflow model import, Selection store mutation or canonical access grant is supplied.
platformClient.workspace.getHome = async (workspaceId): Promise<WorkspaceHomeProjection> => {
  calls.push({workspaceId,mode,tenant})
  if (mode !== 'ready') throw Error('EXPLICIT_SIMULATED_WORKSPACE_' + mode)
  return {workspace:{id:workspaceId,name:'EXPLICIT SIMULATED workspace'},tenantId:tenant,recentProjects:[]}
}
let accessStatus: 'POLICY_DENIED' | 'UNKNOWN_FAIL_CLOSED' = 'UNKNOWN_FAIL_CLOSED'
let accessRevision = 0
platformClient.effectiveAccess.getCatalog = async keys => Object.fromEntries(keys.map(key => [key,{...unknownAccess(key),status:accessStatus,reasonCode:'EXPLICIT_SIMULATED_'+accessRevision}]))
const synchronousRetirements: unknown[] = []
;(window as any).__WorkflowHost = {
  calls, sdkLog, synchronousRetirements, setCurrent, emitLoaded, pendingLoaded, currentInfo,
  replayRetired, settleSignout, settleGetter,
  disposedProbeDeliveries: () => disposedProbeDeliveries,
  beginGetter: () => { deferGetter(); void getOidcUser().then(()=>sdkLog.push({getterSettled:true})) },
  navigate: (workspaceId:string,projectId:string) => router.navigate({to:'/w/$workspaceId/projects/$projectId/workflow',params:{workspaceId,projectId},search:{workflowFixture:'1'} as never}),
  context: async (kind:string) => {
    if (kind === 'project' || kind === 'workspace') return router.navigate({to:'/w/$workspaceId/projects/$projectId/workflow',params:{workspaceId:kind === 'workspace'?'workflow-workspace-next':'workflow-workspace',projectId:kind === 'project'?'workflow-project-next':'workflow-project'},search:{workflowFixture:'1'} as never})
    if (kind === 'error' || kind === 'unavailable' || kind === 'recover' || kind === 'tenant') {
      mode = kind === 'error' || kind === 'unavailable' ? kind : 'ready'
      if (kind === 'tenant') {
        tenant = 'simulated-workflow-tenant-next'
        const wid = location.pathname.split('/')[2]
        queryClient.setQueryData(platformQueryKeys.workspaceHome(wid), {workspace:{id:wid,name:'EXPLICIT SIMULATED workspace'},tenantId:tenant,recentProjects:[]})
        return
      }
      const workspaceId = location.pathname.split('/')[2]
      await queryClient.resetQueries({queryKey:platformQueryKeys.workspaceHome(workspaceId)})
      return
    }
    if (kind.startsWith('sdk-')) { synchronousRetirements.push({kind,...emitNative(kind.slice(4))}); return }
    if (kind === 'signout') { void signOutOidc().then(()=>sdkLog.push({signout:'settled'}),()=>sdkLog.push({signout:'rejected'})); synchronousRetirements.push({kind,cards:document.querySelectorAll('[data-testid="workflow-sketch-node"]').length,dialogs:document.querySelectorAll('[role=dialog]').length}); return }
    if (kind === 'access-denied' || kind === 'access-unknown') {
      accessStatus=kind === 'access-denied'?'POLICY_DENIED':'UNKNOWN_FAIL_CLOSED';accessRevision++
      await queryClient.refetchQueries({queryKey:platformQueryKeys.effectiveAccess(['workflow.invoke']),exact:true});return
    }
    throw Error('Unsupported fixture context: '+kind)
  }
}
createRoot(document.getElementById('root')!).render(<StrictMode><QueryClientProvider client={queryClient}><LocalizationProvider><aside data-workflow-host style={{padding:6,background:'#462e05',color:'#fff'}}>EXPLICIT LOCAL WORKFLOW HOST — simulated workspace/identity/access only; all cards authored through UI; no backend integration</aside><RouterProvider router={router}/></LocalizationProvider></QueryClientProvider></StrictMode>)
