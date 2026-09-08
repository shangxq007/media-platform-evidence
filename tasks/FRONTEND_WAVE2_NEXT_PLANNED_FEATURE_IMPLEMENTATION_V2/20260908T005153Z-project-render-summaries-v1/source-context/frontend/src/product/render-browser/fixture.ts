import type { RenderJobSummary } from '../../contracts/app/render-job'
import type { EffectiveAccessEntry, EffectiveAccessStatus } from '../../foundation/effectiveAccess'
import {
  SIMULATED_RENDER_SUMMARIES_QUERY_KEY,
  accessDisposition,
  scopeKey,
  type RenderListFailureStatus,
  type RendersContext,
  type RendersSource,
} from './source'

export interface RendersFixtureOptions {
  principalId?: string
  tenantId?: string
  sessionId?: string
  projectId?: string
  accessStatus?: EffectiveAccessStatus
  empty?: boolean
  limit?: number
  failure?: RenderListFailureStatus
}

function projectedAccess(status: EffectiveAccessStatus): EffectiveAccessEntry {
  return {
    key: SIMULATED_RENDER_SUMMARIES_QUERY_KEY,
    status,
    reasonCode: `SIMULATED_${status}`,
    explanation: 'Simulated Render access projection; never valid for a real resource.',
    factors: {
      capability: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      runtime: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      entitlement: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      policy: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      quota: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
    },
    source: 'DEVELOPMENT_FAIL_CLOSED',
  }
}

export function createRendersFixture(options: RendersFixtureOptions = {}): RendersSource {
  const scope = {
    principalId: options.principalId ?? 'simulated-render-reader',
    tenantId: options.tenantId ?? 'simulated-render-tenant',
    sessionId: options.sessionId ?? 'simulated-render-session',
    projectId: options.projectId ?? 'simulated-render-project',
  }
  const access = projectedAccess(options.accessStatus ?? 'AVAILABLE')
  const jobs: RenderJobSummary[] = options.empty ? [] : [
    { id: 'render-zeta', projectId: scope.projectId, timelineSnapshotId: 'timeline-snapshot-zeta', profile: 'Cinema <literal>', status: 'COMPLETED' },
    { id: 'render-beta', projectId: scope.projectId, timelineSnapshotId: 'timeline-snapshot-beta', profile: '<b>opaque profile</b>', status: 'FAILED' },
    { id: 'render-alpha', projectId: scope.projectId, timelineSnapshotId: 'timeline-snapshot-alpha', profile: 'Social 原文', status: 'QUEUED' },
  ]
  const limit = Math.min(500, Math.max(1, options.limit ?? 20))
  return {
    scope,
    access,
    adapter: {
      origin: 'simulated',
      async listProject(request, signal) {
        const envelope = { scope: request.scope, requestId: request.requestId }
        if (signal.aborted) return { ...envelope, status: 'error' }
        if (scopeKey(request.scope) !== scopeKey(scope)) return { ...envelope, status: 'denied' }
        const disposition = accessDisposition({ ...scope, access } as RendersContext)
        if (disposition !== 'ready') return { ...envelope, status: disposition }
        if (options.failure) return { ...envelope, status: options.failure, explanation: 'Simulated opaque Render source failure.' }
        return {
          ...envelope,
          status: 'ok',
          jobs: jobs.slice(0, limit).map(job => ({ ...job })),
          boundary: { kind: 'project-snapshot', limit, limited: jobs.length > limit },
        }
      },
    },
  }
}

export function localhostRendersFixture(location: Pick<Location, 'hostname' | 'search'>): RendersSource | null {
  if (!['localhost', '127.0.0.1', '[::1]'].includes(location.hostname)) return null
  const parameters = new URLSearchParams(location.search)
  if (parameters.getAll('rendersFixture').length !== 1 || parameters.get('rendersFixture') !== '1') return null
  const fixtureAccess = parameters.get('rendersFixtureAccess')
  const fixtureFailure = parameters.get('rendersFixtureFailure')
  const supportedFailures = ['unavailable', 'denied', 'unknown', 'unsupported', 'error'] as const
  return createRendersFixture({
    accessStatus: fixtureAccess === 'denied' ? 'POLICY_DENIED' : fixtureAccess === 'unknown' ? 'UNKNOWN_FAIL_CLOSED' : 'AVAILABLE',
    empty: parameters.get('rendersFixtureEmpty') === '1',
    limit: parameters.get('rendersFixtureLimited') === '1' ? 1 : undefined,
    failure: supportedFailures.find(value => value === fixtureFailure),
  })
}
