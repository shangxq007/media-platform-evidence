import { describe, expect, it, vi } from 'vitest'
import type { RenderJobSummary } from '../../contracts/app/render-job'
import type { EffectiveAccessEntry, EffectiveAccessStatus } from '../../foundation/effectiveAccess'
import { createRendersFixture, localhostRendersFixture } from './fixture'
import {
  REAL_RENDER_SUMMARIES_QUERY_KEY,
  accessDisposition,
  contextKey,
  parseRenderSummaries,
  selectRenderJobs,
  sourceDisposition,
  sourcePresentationOrigin,
  unavailableRendersSource,
  type RenderListRequest,
  type RendersContext,
  type RendersSource,
} from './source'

function access(status: EffectiveAccessStatus): EffectiveAccessEntry {
  return {
    key: REAL_RENDER_SUMMARIES_QUERY_KEY,
    status,
    reasonCode: `TEST_${status}`,
    explanation: `<server-owned ${status} 原因>`,
    factors: { capability: 'UNKNOWN', runtime: 'UNKNOWN', entitlement: 'UNKNOWN', policy: 'UNKNOWN', quota: 'UNKNOWN' },
    source: 'SERVER',
  }
}

const scope = { principalId: 'principal-1', tenantId: 'tenant-1', sessionId: 'session-1', projectId: 'project-1' }
const context: RendersContext = { ...scope, access: access('AVAILABLE') }
const request: RenderListRequest = { scope, requestId: 'request-1' }
const jobs: RenderJobSummary[] = [
  { id: 'render-z', projectId: 'project-1', timelineSnapshotId: 'snapshot-z', profile: 'Cinema <literal>', status: 'COMPLETED' },
  { id: 'render-b', projectId: 'project-1', timelineSnapshotId: 'snapshot-b', profile: 'Social 原文', status: 'FAILED' },
  { id: 'render-a', projectId: 'project-1', timelineSnapshotId: 'snapshot-a', profile: 'Social 原文', status: 'QUEUED' },
]
const receipt = () => ({
  status: 'ok', scope, requestId: 'request-1', jobs,
  boundary: { kind: 'project-snapshot', limit: 3, limited: true },
})

describe('single-Project render summary consumption', () => {
  it('reuses RenderJobSummary and filters only ID/profile/status with deterministic ID sorting', () => {
    const existingContract: RenderJobSummary = jobs[0]
    expect(selectRenderJobs(jobs, { query: 'Cinema <literal>', status: '', order: 'id-asc' })).toEqual([existingContract])
    expect(selectRenderJobs(jobs, { query: 'snapshot', status: '', order: 'id-asc' })).toEqual([])
    expect(selectRenderJobs(jobs, { query: '', status: 'FAILED', order: 'id-asc' }).map(job => job.id)).toEqual(['render-b'])
    expect(selectRenderJobs(jobs, { query: '', status: '', order: 'id-asc' }).map(job => job.id)).toEqual(['render-a', 'render-b', 'render-z'])
    expect(selectRenderJobs(jobs, { query: '', status: '', order: 'id-desc' }).map(job => job.id)).toEqual(['render-z', 'render-b', 'render-a'])
  })

  it('accepts an owned, strict, bounded single-Project result without a global inventory claim', () => {
    expect(parseRenderSummaries(receipt(), request)).toEqual(receipt())
  })

  it.each([
    undefined,
    { error: 'NOT_FOUND' },
    { ...receipt(), requestId: 'old-request' },
    { ...receipt(), scope: { ...scope, principalId: 'other' } },
    { ...receipt(), scope: { ...scope, tenantId: 'other' } },
    { ...receipt(), scope: { ...scope, sessionId: 'other' } },
    { ...receipt(), scope: { ...scope, projectId: 'other' } },
    { ...receipt(), jobs: [jobs[0], jobs[0]] },
    { ...receipt(), jobs: [{ ...jobs[0], projectId: 'foreign-project' }] },
    { ...receipt(), jobs: [{ ...jobs[0], status: 'FUTURE_STATUS' }] },
    { ...receipt(), jobs: [{ ...jobs[0], providerId: 'must-not-enter-safe-summary' }] },
    { ...receipt(), jobs: [...jobs, { ...jobs[0], id: 'render-four' }] },
    { ...receipt(), boundary: { kind: 'global-inventory', limit: 3, limited: true } },
    { ...receipt(), boundary: { kind: 'project-snapshot', limit: 0, limited: false } },
    { ...receipt(), boundary: { kind: 'project-snapshot', limit: 501, limited: false } },
  ])('rejects malformed, duplicate, foreign, unknown-status, extra-field, mismatched, or unbounded results %#', input => {
    expect(() => parseRenderSummaries(input, request)).toThrow()
  })

  it.each(['unavailable', 'denied', 'unknown', 'unsupported', 'error'] as const)('preserves exact %s failures and opaque explanations', status => {
    const failure = { status, scope, requestId: 'request-1', explanation: '<opaque 原因>' }
    expect(parseRenderSummaries(failure, request)).toEqual(failure)
  })

  it('keys adapter-relevant principal, tenant, session, Project and access projection changes', () => {
    const keys = [
      context,
      { ...context, principalId: 'other' },
      { ...context, tenantId: 'other' },
      { ...context, sessionId: 'other' },
      { ...context, projectId: 'other' },
      { ...context, access: access('POLICY_DENIED') },
    ].map(contextKey)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('consumes established EffectiveAccess states without creating permission', () => {
    expect(accessDisposition(context)).toBe('ready')
    expect(accessDisposition({ ...context, access: access('POLICY_DENIED') })).toBe('denied')
    expect(accessDisposition({ ...context, access: access('NOT_ENTITLED') })).toBe('denied')
    expect(accessDisposition({ ...context, access: access('UNKNOWN_FAIL_CLOSED') })).toBe('unknown')
    expect(accessDisposition({ ...context, access: access('RUNTIME_UNAVAILABLE') })).toBe('unavailable')
    expect(accessDisposition({ ...context, principalId: null })).toBe('unknown')
  })
})

describe('Render source and fixture boundaries', () => {
  const realSource = (entry: EffectiveAccessEntry): RendersSource => ({
    scope, access: entry,
    adapter: { origin: 'real', async listProject() { throw new Error('not called') } },
  })

  it('requires the exact SERVER projection proposal for a real source', () => {
    expect(sourceDisposition(realSource(access('AVAILABLE')))).toBe('ready')
    expect(sourcePresentationOrigin(realSource(access('AVAILABLE')))).toBe('real')
    expect(sourceDisposition(realSource({ ...access('AVAILABLE'), key: 'fixture.render.job.summary.query' }))).toBe('unknown')
    expect(sourceDisposition(realSource({ ...access('AVAILABLE'), source: 'DEVELOPMENT_FAIL_CLOSED' }))).toBe('unknown')
    expect(sourcePresentationOrigin(realSource({ ...access('AVAILABLE'), source: 'DEVELOPMENT_FAIL_CLOSED' }))).toBe('unavailable')
  })

  it('accepts only the fixture-labelled fail-closed simulated projection', () => {
    const fixture = createRendersFixture()
    expect(sourceDisposition(fixture)).toBe('ready')
    expect(sourcePresentationOrigin(fixture)).toBe('simulated')
    expect(sourceDisposition({ ...fixture, adapter: { ...fixture.adapter, origin: 'real' } })).toBe('unknown')
    expect(sourceDisposition({ ...fixture, access: { ...fixture.access, key: REAL_RENDER_SUMMARIES_QUERY_KEY } })).toBe('unknown')
    expect(sourceDisposition({ ...fixture, access: { ...fixture.access, source: 'SERVER' } })).toBe('unknown')
  })

  it('defaults unavailable and performs no HTTP request', async () => {
    const fetch = vi.spyOn(globalThis, 'fetch')
    const source = unavailableRendersSource()
    const result = await source.adapter.listProject({ scope: source.scope, requestId: 'q' }, new AbortController().signal)
    expect(source.adapter.origin).toBe('unavailable')
    expect(result).toMatchObject({ status: 'unavailable', scope: source.scope, requestId: 'q' })
    expect(fetch).not.toHaveBeenCalled()
    fetch.mockRestore()
  })

  it('requires one exact localhost rendersFixture=1 opt-in and ignores URL Project claims', async () => {
    expect(localhostRendersFixture({ hostname: 'example.com', search: '?rendersFixture=1' })).toBeNull()
    expect(localhostRendersFixture({ hostname: 'localhost', search: '?projectId=project-1' })).toBeNull()
    expect(localhostRendersFixture({ hostname: 'localhost', search: '?rendersFixture=1&rendersFixture=1' })).toBeNull()
    const source = localhostRendersFixture({ hostname: '127.0.0.1', search: '?rendersFixture=1&projectId=attacker-choice' })!
    const fetch = vi.spyOn(globalThis, 'fetch')
    const setItem = vi.spyOn(Storage.prototype, 'setItem')
    expect(source.scope.projectId).toBe('simulated-render-project')
    expect(source.scope.projectId).not.toBe('attacker-choice')
    await source.adapter.listProject({ scope: source.scope, requestId: 'q' }, new AbortController().signal)
    expect(fetch).not.toHaveBeenCalled()
    expect(setItem).not.toHaveBeenCalled()
    fetch.mockRestore(); setItem.mockRestore()
  })

  it.each(['POLICY_DENIED', 'UNKNOWN_FAIL_CLOSED'] as const)('fixture cannot relax %s access', async status => {
    const source = createRendersFixture({ accessStatus: status })
    const result = await source.adapter.listProject({ scope: source.scope, requestId: 'q' }, new AbortController().signal)
    expect(result).toMatchObject({ status: status === 'POLICY_DENIED' ? 'denied' : 'unknown' })
  })
})
