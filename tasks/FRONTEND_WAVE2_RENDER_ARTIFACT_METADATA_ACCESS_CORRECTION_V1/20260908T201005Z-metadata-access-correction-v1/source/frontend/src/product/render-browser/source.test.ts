import { describe, expect, it, vi } from 'vitest'
import type { EffectiveAccessEntry, EffectiveAccessStatus } from '../../foundation/effectiveAccess'
import { createRendersFixture } from './fixture'
import {
  TEST_ONLY_RENDER_ACCESS_KEY,
  RenderProjectionError,
  accessDisposition,
  contextKey,
  deriveProgressPercent,
  parseRenderSnapshot,
  renderStatusValues,
  selectRenderJobs,
  sourceDisposition,
  sourcePresentationOrigin,
  unavailableRendersSource,
  type RenderReadRequest,
  type RenderProjection,
  type RenderSource,
} from './source'

const HOST_ACCESS_KEY = 'host-agreed.render-observability.read'
const scope = { principalId: 'principal-1', tenantId: 'tenant-1', sessionId: 'session-1', projectId: 'project-1' }

function access(status: EffectiveAccessStatus, key = HOST_ACCESS_KEY): EffectiveAccessEntry {
  return {
    key, status, reasonCode: `TEST_${status}`, explanation: '<server-owned opaque explanation 原文>',
    factors: { capability: 'UNKNOWN', runtime: 'UNKNOWN', entitlement: 'UNKNOWN', policy: 'UNKNOWN', quota: 'UNKNOWN' },
    source: 'SERVER', observedAt: '2026-09-08T01:00:00Z',
  }
}

const request: RenderReadRequest = { scope, requestId: 'request-1' }
const jobs: RenderProjection[] = [
  {
    id: 'render-z', projectId: scope.projectId, name: 'Zulu <literal>', status: 'VENDOR_WARMING', version: 'render-v2',
    source: { id: 'timeline-z', kind: 'TIMELINE_REVISION', version: 'revision-z' },
    createdAt: '2026-09-08T01:00:00Z', updatedAt: '2026-09-08T01:02:00Z',
    progress: { value: 48, unit: 'frames', total: 96, totalUnit: 'frames', stage: 'Encode 原文' },
    task: { id: 'task-z', status: 'RUNNING', version: 'task-v3' },
    attempts: { completeness: 'bounded', limit: 2, items: [
      { id: 'attempt-1', ordinal: 1, taskId: 'task-z', status: 'FAILED', failure: { summary: 'Worker exited safely', code: 'WORKER_EXIT', occurredAt: '2026-09-08T01:01:00Z' } },
      { id: 'attempt-2', ordinal: 2, taskId: 'task-z', status: 'RUNNING', parentAttemptId: 'attempt-1', retryOfAttemptId: 'attempt-1' },
    ] },
    artifacts: { state: 'available', completeness: 'bounded', limit: 2, items: [
      { id: 'artifact-z', name: 'Preview <literal>', type: 'video/mp4', availability: 'AVAILABLE', version: 'artifact-v1', taskId: 'task-z', metadataAccess: 'inspectable' },
    ] },
  },
  { id: 'render-a', projectId: scope.projectId, name: null, status: 'QUEUED', source: { id: 'timeline-a', kind: 'TIMELINE_REVISION' } },
]

const receipt = () => ({
  status: 'ok' as const, scope, requestId: request.requestId, jobs,
  boundary: {
    kind: 'project-render-observability-snapshot' as const, completeness: 'bounded' as const, limit: 5,
    version: 'projection-v7', freshness: 'current' as const, sourceUpdatedAt: '2026-09-08T01:03:00Z',
    supportedStatusFilters: ['QUEUED', 'VENDOR_WARMING'],
  },
})

function realSource(entry = access('AVAILABLE'), bindingKey = entry.key): RenderSource {
  return {
    scope, access: entry, readAccessBinding: { kind: 'HOST_AGREED', accessKey: bindingKey },
    adapter: { origin: 'real', async readProject() { throw new Error('not called') } },
  }
}

describe('bounded Render observability projection', () => {
  it('searches only supplied ID/name, uses source-supported statuses, and sorts stably by name then ID', () => {
    expect(selectRenderJobs(jobs, { query: 'Zulu <literal>', status: '', order: 'name-asc' }).map(job => job.id)).toEqual(['render-z'])
    expect(selectRenderJobs(jobs, { query: 'timeline-z', status: '', order: 'name-asc' })).toEqual([])
    expect(selectRenderJobs(jobs, { query: '', status: 'VENDOR_WARMING', order: 'name-asc' }).map(job => job.id)).toEqual(['render-z'])
    expect(selectRenderJobs([...jobs, { ...jobs[1], id: 'render-b' }], { query: '', status: '', order: 'name-asc' }).map(job => job.id)).toEqual(['render-a', 'render-b', 'render-z'])
    expect(renderStatusValues(receipt().boundary)).toEqual(['QUEUED', 'VENDOR_WARMING'])
  })

  it('derives percent only for matching finite units and valid ranges without clamping invalid values', () => {
    expect(deriveProgressPercent({ value: 48, unit: 'frames', total: 96, totalUnit: 'frames' })).toBe(50)
    expect(deriveProgressPercent({ value: 140, unit: 'frames', total: 100, totalUnit: 'frames' })).toBeNull()
    expect(deriveProgressPercent({ value: 1, unit: 'shot', total: 2, totalUnit: 'frames' })).toBeNull()
    expect(deriveProgressPercent({ value: 1, unit: 'frames' })).toBeNull()
    expect(deriveProgressPercent(undefined)).toBeNull()
  })

  it('accepts safe task, attempt, failure, progress and bounded Artifact metadata as one owned snapshot', () => {
    expect(parseRenderSnapshot(receipt(), request)).toEqual(receipt())
  })

  it.each(['inspectable', 'denied', 'unknown', 'unavailable', 'stale'] as const)('preserves item metadataAccess %s in an available collection and still validates its relationship', metadataAccess => {
    const artifact = { id: 'artifact-permission', name: 'Ordinary preview', type: 'video/mp4', availability: 'AVAILABLE', taskId: 'task-z', metadataAccess }
    const input = { ...receipt(), jobs: [{ ...jobs[0], artifacts: { state: 'available', completeness: 'complete', limit: 1, items: [artifact] } }] }
    expect(parseRenderSnapshot(input, request)).toEqual(input)
    artifact.taskId = 'unrelated-task'
    expect(() => parseRenderSnapshot(input, request)).toThrow('Artifact task link is invalid')
    expect(artifact.metadataAccess).toBe(metadataAccess)
  })

  it.each([undefined, null, '', 'allow', 'INSPECTABLE', true])('rejects missing or invalid item metadataAccess %s without defaulting to inspectable', metadataAccess => {
    const artifact = { id: 'artifact-permission', name: 'Ordinary preview', type: 'video/mp4', availability: 'AVAILABLE', taskId: 'task-z', ...(metadataAccess === undefined ? {} : { metadataAccess }) }
    const input = { ...receipt(), jobs: [{ ...jobs[0], artifacts: { state: 'available', completeness: 'complete', limit: 1, items: [artifact] } }] }
    expect(() => parseRenderSnapshot(input, request)).toThrow('Invalid Render observability receipt')
    expect('metadataAccess' in artifact ? artifact.metadataAccess : undefined).toBe(metadataAccess)
  })

  it('preserves missing, empty, bounded, denied, unavailable, unknown and stale Artifact states without inventing history', () => {
    for (const artifacts of [undefined, { state: 'empty' }, { state: 'denied' }, { state: 'unavailable' }, { state: 'unknown' }, { state: 'stale' }] as const) {
      const input: ReturnType<typeof receipt> = receipt()
      input.jobs = [{ ...jobs[1], ...(artifacts === undefined ? {} : { artifacts }) }]
      expect(parseRenderSnapshot(input, request).status).toBe('ok')
    }
  })

  it('classifies broken attempt and Artifact task links as invalid relationships', () => {
    for (const changed of [
      { ...jobs[0], attempts: { completeness: 'complete', limit: 2, items: [{ id: 'attempt-2', ordinal: 2, taskId: 'task-z', status: 'RUNNING', parentAttemptId: 'missing' }] } },
      { ...jobs[0], artifacts: { state: 'available', completeness: 'complete', limit: 1, items: [{ id: 'artifact-z', type: 'video/mp4', availability: 'AVAILABLE', taskId: 'wrong-task', metadataAccess: 'inspectable' }] } },
    ]) {
      const input: ReturnType<typeof receipt> = receipt(); input.jobs = [changed as RenderProjection]
      try { parseRenderSnapshot(input, request); throw new Error('expected rejection') }
      catch (error) { expect(error).toBeInstanceOf(RenderProjectionError); expect((error as RenderProjectionError).kind).toBe('invalid-relationship') }
    }
  })

  it('rejects malformed ownership, duplicate identities, foreign Projects, invalid source times, unsafe failures and excess bounds', () => {
    const variants: unknown[] = [
      { ...receipt(), requestId: 'old-request' },
      { ...receipt(), scope: { ...scope, sessionId: 'other' } },
      { ...receipt(), jobs: [jobs[0], jobs[0]] },
      { ...receipt(), jobs: [{ ...jobs[0], projectId: 'foreign-project' }] },
      { ...receipt(), jobs: [{ ...jobs[0], startedAt: 'not-a-time' }] },
      { ...receipt(), jobs: [{ ...jobs[0], failure: { summary: 'Bearer secret-token' } }] },
      { ...receipt(), boundary: { ...receipt().boundary, limit: 1 } },
      { ...receipt(), boundary: { ...receipt().boundary, supportedStatusFilters: ['QUEUED', 'QUEUED'] } },
      { ...receipt(), unexpected: true },
    ]
    for (const input of variants) expect(() => parseRenderSnapshot(input, request)).toThrow()
  })

  it.each(['unavailable', 'denied', 'unknown', 'unsupported', 'error', 'stale'] as const)('preserves safe nondisclosing %s receipts', status => {
    const failure = { status, scope, requestId: request.requestId, explanation: '<opaque source result 原文>' }
    expect(parseRenderSnapshot(failure, request)).toEqual(failure)
  })
})

describe('Render source, identity and access boundaries', () => {
  it('accepts only an exact host-agreed SERVER binding and never treats Operations visibility as query permission', () => {
    expect(sourceDisposition(realSource())).toBe('ready')
    expect(sourcePresentationOrigin(realSource())).toBe('real')
    expect(sourceDisposition(realSource(access('AVAILABLE'), 'other.host.binding'))).toBe('unknown')
    expect(sourceDisposition(realSource(access('AVAILABLE', 'surface.operations.view')))).toBe('unknown')
    const relabelledTestSource = realSource(access('AVAILABLE', TEST_ONLY_RENDER_ACCESS_KEY))
    expect(sourceDisposition(relabelledTestSource)).toBe('unknown')
    expect(sourcePresentationOrigin(relabelledTestSource)).toBe('unavailable')
    expect(sourceDisposition(realSource({ ...access('AVAILABLE'), source: 'DEVELOPMENT_FAIL_CLOSED' }))).toBe('unknown')
    expect(sourceDisposition(realSource(access('POLICY_DENIED')))).toBe('denied')
    expect(sourceDisposition(realSource(access('UNKNOWN_FAIL_CLOSED')))).toBe('unknown')
    expect(accessDisposition({ ...scope, access: access('RUNTIME_UNAVAILABLE') })).toBe('unavailable')
  })

  it('keys principal, tenant, session, Project and complete access projection ownership', () => {
    const context = { ...scope, access: access('AVAILABLE') }
    const keys = [context, { ...context, principalId: 'other' }, { ...context, tenantId: 'other' }, { ...context, sessionId: 'other' }, { ...context, projectId: 'other' }, { ...context, access: access('POLICY_DENIED') }].map(contextKey)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('requires explicit fixture identity, performs no transport or storage access, and has a distinct test-only binding', async () => {
    expect(() => createRendersFixture({ scope: { ...scope, principalId: null } })).toThrow()
    const source = createRendersFixture({ scope })
    const fetch = vi.spyOn(globalThis, 'fetch')
    const getItem = vi.spyOn(Storage.prototype, 'getItem')
    expect(source.access.key).toBe(TEST_ONLY_RENDER_ACCESS_KEY)
    expect(sourceDisposition(source)).toBe('ready')
    await source.adapter.readProject({ scope, requestId: 'q' }, new AbortController().signal)
    expect(fetch).not.toHaveBeenCalled(); expect(getItem).not.toHaveBeenCalled()
    fetch.mockRestore(); getItem.mockRestore()
  })

  it('defaults unavailable without transport and does not invent a Project or identity', async () => {
    const fetch = vi.spyOn(globalThis, 'fetch')
    const source = unavailableRendersSource()
    expect(source.scope).toEqual({ principalId: null, tenantId: null, sessionId: 'unconfigured', projectId: 'unconfigured' })
    expect(await source.adapter.readProject({ scope: source.scope, requestId: 'q' }, new AbortController().signal)).toMatchObject({ status: 'unavailable' })
    expect(fetch).not.toHaveBeenCalled(); fetch.mockRestore()
  })
})
