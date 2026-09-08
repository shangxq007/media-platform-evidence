import type { EffectiveAccessEntry, EffectiveAccessStatus } from '../../foundation/effectiveAccess'
import type { ProjectSummary } from '../../foundation/platformClient'
import { accessDisposition, scopeKey, type ProjectListFailureStatus, type ProjectsContext, type ProjectsSource } from './source'

export interface ProjectsFixtureOptions {
  workspaceId: string
  principalId?: string
  tenantId?: string
  sessionId?: string
  accessStatus?: EffectiveAccessStatus
  empty?: boolean
  limit?: number
  failure?: ProjectListFailureStatus
}

function projectedAccess(status: EffectiveAccessStatus): EffectiveAccessEntry {
  return {
    key: 'fixture.project.recent.query', status,
    reasonCode: `SIMULATED_${status}`, explanation: 'Simulated access projection; never valid for a real resource.',
    factors: {
      capability: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN', runtime: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      entitlement: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN', policy: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      quota: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
    },
    source: 'DEVELOPMENT_FAIL_CLOSED',
  }
}

export function createProjectsFixture(options: ProjectsFixtureOptions = { workspaceId: 'simulated-workspace' }): ProjectsSource {
  const scope = {
    principalId: options.principalId ?? 'simulated-project-reader', tenantId: options.tenantId ?? 'simulated-project-tenant',
    sessionId: options.sessionId ?? 'simulated-project-session', workspaceId: options.workspaceId,
  }
  const access = projectedAccess(options.accessStatus ?? 'AVAILABLE')
  const projects: ProjectSummary[] = options.empty ? [] : [
    { id: 'project-zeta', tenantId: scope.tenantId, name: 'Zeta <project>', description: 'description literal 原文', status: 'future::READY<script>', createdAt: '2026-08-31T08:00:00Z' },
    { id: 'project-alpha-b', tenantId: scope.tenantId, name: 'Alpha project', description: '<b>opaque description</b>', status: 'IN_REVIEW?', createdAt: 'not-a-protocol-time' },
    { id: 'project-alpha-a', tenantId: scope.tenantId, name: 'Alpha project', description: null, status: 'IN_REVIEW?' },
  ]
  const limit = Math.max(1, options.limit ?? 20)
  return {
    scope, access,
    adapter: {
      origin: 'simulated',
      async listRecent(request, signal) {
        const envelope = { scope: request.scope, requestId: request.requestId }
        if (signal.aborted) return { ...envelope, status: 'error' }
        if (scopeKey(request.scope) !== scopeKey(scope)) return { ...envelope, status: 'denied' }
        const disposition = accessDisposition({ ...scope, access } as ProjectsContext)
        if (disposition !== 'ready') return { ...envelope, status: disposition }
        if (options.failure) return { ...envelope, status: options.failure, explanation: 'Simulated opaque source failure.' }
        return {
          ...envelope, status: 'ok', projects: projects.slice(0, limit).map(project => ({ ...project })),
          boundary: { kind: 'recent', limit, limited: projects.length > limit },
        }
      },
    },
  }
}

export function localhostProjectsFixture(location: Pick<Location, 'hostname' | 'search'>, workspaceId: string): ProjectsSource | null {
  if (!['localhost', '127.0.0.1', '[::1]'].includes(location.hostname)) return null
  const parameters = new URLSearchParams(location.search)
  if (parameters.getAll('projectsFixture').length !== 1 || parameters.get('projectsFixture') !== '1') return null
  const access = parameters.get('projectsFixtureAccess')
  const failure = parameters.get('projectsFixtureFailure')
  const supportedFailures = ['unavailable', 'denied', 'unknown', 'unsupported', 'error'] as const
  return createProjectsFixture({
    workspaceId,
    accessStatus: access === 'denied' ? 'POLICY_DENIED' : access === 'unknown' ? 'UNKNOWN_FAIL_CLOSED' : 'AVAILABLE',
    empty: parameters.get('projectsFixtureEmpty') === '1',
    limit: parameters.get('projectsFixtureLimited') === '1' ? 1 : undefined,
    failure: supportedFailures.find(value => value === failure),
  })
}
