import { describe, expect, it, vi } from 'vitest'
import type { EffectiveAccessEntry, EffectiveAccessStatus } from '../../foundation/effectiveAccess'
import type { ProjectSummary } from '../../foundation/platformClient'
import {
  accessDisposition,
  contextKey,
  parseRecentProjects,
  projectStatusValues,
  selectProjects,
  sourceDisposition,
  sourcePresentationOrigin,
  unavailableProjectsSource,
  type ProjectListRequest,
  type ProjectsContext,
  type ProjectsSource,
} from './source'
import { createProjectsFixture, localhostProjectsFixture } from './fixture'

function access(status: EffectiveAccessStatus): EffectiveAccessEntry {
  return {
    key: 'project.recent.query', status, reasonCode: `TEST_${status}`, explanation: `Projected ${status}`,
    factors: { capability: 'UNKNOWN', runtime: 'UNKNOWN', entitlement: 'UNKNOWN', policy: 'UNKNOWN', quota: 'UNKNOWN' },
    source: 'SERVER',
  }
}
const scope = { principalId: 'principal-1', tenantId: 'tenant-1', sessionId: 'session-1', workspaceId: 'workspace-1' }
const context: ProjectsContext = { ...scope, access: access('AVAILABLE') }
const request: ProjectListRequest = { scope, requestId: 'request-1' }
const items: ProjectSummary[] = [
  { id: 'id-z', tenantId: 'tenant-1', name: 'Zulu', description: 'contains Launch literal', status: 'future::READY' },
  { id: 'id-b', tenantId: 'tenant-1', name: 'Alpha', description: '<b>opaque</b>', status: '未定义状态' },
  { id: 'id-a', tenantId: 'tenant-1', name: 'Alpha', description: null, status: '未定义状态' },
]
const receipt = () => ({ status: 'ok', scope, requestId: 'request-1', projects: items, boundary: { kind: 'recent', limit: 3, limited: true } })

describe('recent Project frontend consumption proposal', () => {
  it('reuses ProjectSummary, searches name and description literally, and sorts by name with an ID tie-break', () => {
    const existingViewType: ProjectSummary = items[0]
    expect(selectProjects(items, { query: 'Launch literal', status: '', order: 'name-asc' })).toEqual([existingViewType])
    expect(selectProjects(items, { query: '<b>opaque</b>', status: '', order: 'name-asc' }).map(item => item.id)).toEqual(['id-b'])
    expect(selectProjects(items, { query: '', status: '', order: 'name-asc' }).map(item => item.id)).toEqual(['id-a', 'id-b', 'id-z'])
    expect(selectProjects(items, { query: '', status: '', order: 'name-desc' }).map(item => item.id)).toEqual(['id-z', 'id-a', 'id-b'])
  })

  it('keeps projected statuses opaque and uses them only as literal local filter values', () => {
    expect(projectStatusValues(items)).toEqual(['future::READY', '未定义状态'])
    expect(selectProjects(items, { query: '', status: '未定义状态', order: 'name-asc' }).map(item => item.id)).toEqual(['id-a', 'id-b'])
    expect(selectProjects(items, { query: '', status: 'READY', order: 'name-asc' })).toEqual([])
  })

  it('accepts only an owned, bounded, recent snapshot without claiming a full inventory', () => {
    expect(parseRecentProjects(receipt(), request)).toEqual(receipt())
  })

  it.each([
    undefined,
    { error: 'NOT_FOUND' },
    { ...receipt(), requestId: 'old-request' },
    { ...receipt(), scope: { ...scope, principalId: 'other' } },
    { ...receipt(), scope: { ...scope, tenantId: 'other' } },
    { ...receipt(), scope: { ...scope, sessionId: 'other' } },
    { ...receipt(), scope: { ...scope, workspaceId: 'other' } },
    { ...receipt(), projects: [items[0], items[0]] },
    { ...receipt(), projects: [{ ...items[0], tenantId: 'other' }] },
    { ...receipt(), projects: [...items, { id: 'four', name: 'Fourth' }] },
    { ...receipt(), boundary: { kind: 'inventory', limit: 3, limited: true } },
    { ...receipt(), boundary: { kind: 'recent', limit: 0, limited: false } },
  ])('rejects malformed, duplicate, foreign, mismatched or unbounded receipts %#', input => {
    expect(() => parseRecentProjects(input, request)).toThrow()
  })

  it.each(['unavailable', 'denied', 'unknown', 'unsupported', 'error'] as const)('preserves exact %s failures with opaque explanations', status => {
    const failure = { status, scope, requestId: 'request-1', explanation: '<opaque 原因>' }
    expect(parseRecentProjects(failure, request)).toEqual(failure)
  })

  it('keys every principal, tenant, session, workspace and access projection change', () => {
    const keys = [
      context,
      { ...context, principalId: 'other' },
      { ...context, tenantId: 'other' },
      { ...context, sessionId: 'other' },
      { ...context, workspaceId: 'other' },
      { ...context, access: access('POLICY_DENIED') },
    ].map(contextKey)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('consumes established EffectiveAccess statuses without manufacturing availability', () => {
    expect(accessDisposition(context)).toBe('ready')
    expect(accessDisposition({ ...context, access: access('POLICY_DENIED') })).toBe('denied')
    expect(accessDisposition({ ...context, access: access('NOT_ENTITLED') })).toBe('denied')
    expect(accessDisposition({ ...context, access: access('UNKNOWN_FAIL_CLOSED') })).toBe('unknown')
    expect(accessDisposition({ ...context, access: access('RUNTIME_UNAVAILABLE') })).toBe('unavailable')
    expect(accessDisposition({ ...context, principalId: null })).toBe('unknown')
  })
})

describe('source boundaries', () => {
  it('requires an exact server-owned proposal projection for a real source', () => {
    const realSource = (entry: EffectiveAccessEntry): ProjectsSource => ({
      scope,
      access: entry,
      adapter: { origin: 'real', async listRecent() { throw new Error('not called') } },
    })
    expect(sourceDisposition(realSource(access('AVAILABLE')))).toBe('ready')
    expect(sourcePresentationOrigin(realSource(access('AVAILABLE')))).toBe('real')
    expect(sourceDisposition(realSource({ ...access('AVAILABLE'), key: 'fixture.project.recent.query' }))).toBe('unknown')
    expect(sourcePresentationOrigin(realSource({ ...access('AVAILABLE'), key: 'fixture.project.recent.query' }))).toBe('unavailable')
    expect(sourceDisposition(realSource({ ...access('AVAILABLE'), key: 'project.query.recent' }))).toBe('unknown')
    expect(sourceDisposition(realSource({ ...access('AVAILABLE'), source: 'DEVELOPMENT_FAIL_CLOSED' }))).toBe('unknown')
    expect(sourceDisposition(realSource({ ...access('AVAILABLE'), source: 'MISSING_SERVER_PROJECTION' }))).toBe('unknown')
  })

  it('accepts only the explicitly labelled projection for a simulated fixture', () => {
    const fixture = createProjectsFixture({ workspaceId: 'workspace-1' })
    expect(sourceDisposition(fixture)).toBe('ready')
    expect(sourcePresentationOrigin(fixture)).toBe('simulated')
    expect(sourceDisposition({ ...fixture, adapter: { ...fixture.adapter, origin: 'real' } })).toBe('unknown')
    expect(sourcePresentationOrigin({ ...fixture, adapter: { ...fixture.adapter, origin: 'real' } })).toBe('unavailable')
    expect(sourceDisposition({ ...fixture, access: { ...fixture.access, key: 'project.recent.query' } })).toBe('unknown')
    expect(sourceDisposition({ ...fixture, access: { ...fixture.access, source: 'SERVER' } })).toBe('unknown')
  })

  it('defaults unavailable without HTTP, storage-derived auth, or an adapter fallback', async () => {
    const fetch = vi.spyOn(globalThis, 'fetch')
    const source = unavailableProjectsSource('workspace-1')
    const result = await source.adapter.listRecent({ scope: source.scope, requestId: 'q' }, new AbortController().signal)
    expect(source.adapter.origin).toBe('unavailable')
    expect(result).toMatchObject({ status: 'unavailable', scope: source.scope, requestId: 'q' })
    expect(fetch).not.toHaveBeenCalled()
    fetch.mockRestore()
  })

  it('requires the exact localhost projectsFixture=1 opt-in and never touches auth, storage or transport', async () => {
    expect(localhostProjectsFixture({ hostname: 'example.com', search: '?projectsFixture=1' }, 'workspace-1')).toBeNull()
    expect(localhostProjectsFixture({ hostname: 'localhost', search: '' }, 'workspace-1')).toBeNull()
    expect(localhostProjectsFixture({ hostname: 'localhost', search: '?projectsFixture=1&projectsFixture=1' }, 'workspace-1')).toBeNull()
    const source = localhostProjectsFixture({ hostname: '127.0.0.1', search: '?projectsFixture=1' }, 'workspace-1')!
    const fetch = vi.spyOn(globalThis, 'fetch')
    const setItem = vi.spyOn(Storage.prototype, 'setItem')
    expect(source.adapter.origin).toBe('simulated')
    expect(source.scope).toMatchObject({ principalId: 'simulated-project-reader', tenantId: 'simulated-project-tenant', workspaceId: 'workspace-1' })
    await source.adapter.listRecent({ scope: source.scope, requestId: 'q' }, new AbortController().signal)
    expect(fetch).not.toHaveBeenCalled()
    expect(setItem).not.toHaveBeenCalled()
    fetch.mockRestore(); setItem.mockRestore()
  })

  it.each(['POLICY_DENIED', 'UNKNOWN_FAIL_CLOSED'] as const)('fixture cannot relax %s access', async status => {
    const source = createProjectsFixture({ workspaceId: 'workspace-1', accessStatus: status })
    expect(await source.adapter.listRecent({ scope: source.scope, requestId: 'q' }, new AbortController().signal)).toMatchObject({ status: status === 'POLICY_DENIED' ? 'denied' : 'unknown' })
  })
})
