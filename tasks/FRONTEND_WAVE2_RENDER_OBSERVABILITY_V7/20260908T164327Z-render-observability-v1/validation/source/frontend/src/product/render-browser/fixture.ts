import type { EffectiveAccessEntry, EffectiveAccessStatus } from '../../foundation/effectiveAccess'
import {
  MAX_RENDER_ITEMS,
  TEST_ONLY_RENDER_ACCESS_KEY,
  accessDisposition,
  renderScopeIsValid,
  scopeKey,
  type RenderFailureStatus,
  type RenderProjection,
  type RenderScope,
  type RenderSource,
  type RendersContext,
} from './source'

export interface RendersFixtureOptions {
  readonly scope: RenderScope
  readonly accessStatus?: EffectiveAccessStatus
  readonly empty?: boolean
  readonly limit?: number
  readonly failure?: RenderFailureStatus
  readonly freshness?: 'current' | 'stale'
}

function assertExplicitScope(scope: RenderScope): void {
  if (!renderScopeIsValid(scope)) throw new Error('The simulated Render source requires an explicitly supplied complete, well-formed identity and Project scope')
}
function projectedAccess(status: EffectiveAccessStatus): EffectiveAccessEntry {
  return {
    key: TEST_ONLY_RENDER_ACCESS_KEY, status, reasonCode: `SIMULATED_${status}`,
    explanation: 'Simulated Render access projection; never valid for a real resource.',
    factors: {
      capability: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN', runtime: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      entitlement: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN', policy: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      quota: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
    }, source: 'DEVELOPMENT_FAIL_CLOSED',
  }
}

export function createRendersFixture(options: RendersFixtureOptions): RenderSource {
  assertExplicitScope(options.scope)
  const scope = { ...options.scope }
  const access = projectedAccess(options.accessStatus ?? 'AVAILABLE')
  const jobs: RenderProjection[] = options.empty ? [] : [
    {
      id: 'render-courtyard-final', projectId: scope.projectId, name: 'Courtyard <final>', status: 'VENDOR_WARMING', version: 'render-v7',
      source: { id: 'revision-courtyard', kind: 'TIMELINE_REVISION', version: 'revision-v4' },
      createdAt: '2026-09-08T01:00:00Z', updatedAt: '2026-09-08T01:04:00Z', startedAt: '2026-09-08T01:01:00Z',
      progress: { value: 3, unit: 'shots', total: 8, totalUnit: 'shots', stage: 'Composite <literal>' },
      task: { id: 'task-courtyard', status: 'TASK_RUNNING', version: 'task-v3' },
      attempts: { completeness: 'complete', limit: 2, items: [{ id: 'attempt-courtyard-1', ordinal: 1, taskId: 'task-courtyard', status: 'ATTEMPT_RUNNING' }] },
      artifacts: { state: 'available', completeness: 'bounded', limit: 2, items: [{ id: 'artifact-courtyard-preview', name: 'Preview 原文', type: 'video/mp4', availability: 'PROCESSING?', version: 'artifact-v1', taskId: 'task-courtyard', metadataAccess: 'inspectable' }] },
    },
    {
      id: 'render-social-failed', projectId: scope.projectId, name: 'Social 原文', status: 'FAILED', version: 'render-v3',
      source: { id: 'revision-social', kind: 'TIMELINE_REVISION' },
      createdAt: '2026-09-08T02:00:00Z', updatedAt: '2026-09-08T02:02:00Z', startedAt: '2026-09-08T02:01:00Z', endedAt: '2026-09-08T02:02:00Z',
      progress: { value: 140, unit: 'frames', total: 100, totalUnit: 'frames', stage: 'Encode' },
      task: { id: 'task-social', status: 'TASK_FAILED' },
      failure: { summary: 'Encoder rejected supplied media', code: 'MEDIA_REJECTED', occurredAt: '2026-09-08T02:02:00Z' },
      attempts: { completeness: 'complete', limit: 1, items: [{ id: 'attempt-social-1', ordinal: 1, taskId: 'task-social', status: 'ATTEMPT_FAILED', failure: { summary: 'Encoder rejected supplied media', code: 'MEDIA_REJECTED', occurredAt: '2026-09-08T02:02:00Z' } }] },
      artifacts: { state: 'empty' },
    },
    { id: 'render-queued', projectId: scope.projectId, status: 'QUEUED?', source: { id: 'request-queued', kind: 'RENDER_REQUEST' } },
  ]
  const limit = Math.min(MAX_RENDER_ITEMS, Math.max(1, options.limit ?? MAX_RENDER_ITEMS))
  return {
    scope, access, readAccessBinding: { kind: 'TEST_ONLY_UNAGREED', accessKey: TEST_ONLY_RENDER_ACCESS_KEY },
    adapter: {
      origin: 'simulated',
      async readProject(request, signal) {
        const envelope = { scope: request.scope, requestId: request.requestId }
        if (signal.aborted) return { ...envelope, status: 'error' }
        if (scopeKey(request.scope) !== scopeKey(scope)) return { ...envelope, status: 'denied' }
        const disposition = accessDisposition({ ...scope, access } as RendersContext)
        if (disposition !== 'ready') return { ...envelope, status: disposition }
        if (options.failure) return { ...envelope, status: options.failure, explanation: 'Simulated opaque Render source result.' }
        return {
          ...envelope, status: 'ok', jobs: jobs.slice(0, limit).map(job => structuredClone(job)),
          boundary: {
            kind: 'project-render-observability-snapshot', completeness: options.limit === undefined ? 'complete' : 'bounded', limit,
            version: 'simulated-render-observability-v1', freshness: options.freshness ?? 'current',
            sourceUpdatedAt: '2026-09-08T02:02:00Z', supportedStatusFilters: ['VENDOR_WARMING', 'FAILED', 'QUEUED?'],
          },
        }
      },
    },
  }
}
