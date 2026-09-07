import { describe, expect, it, vi } from 'vitest'
import { parseList, parseMutation, resolveTarget, type InboxContext, type ListRequest, type MutationRequest } from './types'
import { unavailableSource } from './unavailable'
import { createNotificationFixture, localhostFixture } from './fixture'

const context: InboxContext = { principalId: 'p1', tenantId: 't1', sessionId: 's1', access: 'allowed' }
const query: ListRequest = { context, requestId: 'q1', filter: 'all' }
const item = { id: 'n1', content: { title: '<b>Opaque</b>', body: '原文', type: 'future.type', createdAt: 'invalid' }, read: false }
const page = () => ({ status: 'ok', context, requestId: 'q1', filter: 'all', items: [item], unread: { kind: 'known', total: 12 }, traversal: { kind: 'limited', limit: 1 } })
const mutation: MutationRequest = { context, requestId: 'm1', operation: { kind: 'single', id: 'n1' } }

describe('frontend inbox consumption contract (not a server DTO)', () => {
  it('preserves opaque content and keeps global unread independent of a bounded list', () => {
    const result = parseList(page(), query)
    expect(result).toEqual(page())
  })
  it.each([
    { error: 'NOT_FOUND' }, undefined, [], { ...page(), unread: { kind: 'known', total: -1 } },
    { ...page(), items: [item, item] }, { ...page(), context: { ...context, tenantId: 'other' } },
    { ...page(), requestId: 'old' }, { ...page(), filter: 'unread' },
    { ...page(), unread: { kind: 'unknown', total: 0 } },
    { ...page(), items: [{ ...item, read: 'false' }] },
  ])('rejects malformed or foreign list envelopes %#', input => {
    expect(() => parseList(input, query)).toThrow()
  })
  it('rejects a read item in an unread query and a global count below loaded unread', () => {
    expect(() => parseList({ ...page(), filter: 'unread', items: [{ ...item, read: true }] }, { ...query, filter: 'unread' })).toThrow()
    expect(() => parseList({ ...page(), unread: { kind: 'known', total: 0 } }, query)).toThrow()
  })
  it.each(['denied', 'unavailable', 'error', 'not-found'] as const)('preserves exact %s failures', status => {
    const failure = { status, context, requestId: 'q1', explanation: 'Opaque reason 42' }
    expect(parseList(failure, query)).toEqual(failure)
  })
  it.each([
    undefined, { error: 'NOT_FOUND' }, { id: 'n1', read: true },
    { status: 'ok', context, requestId: 'm1', operation: { kind: 'single', id: 'other' }, read: true },
    { status: 'ok', context, requestId: 'm1', operation: mutation.operation, read: false },
    { status: 'ok', context: { ...context, sessionId: 'old' }, requestId: 'm1', operation: mutation.operation, read: true },
  ])('does not accept HTTP success or wrong item/context as mutation confirmation %#', input => {
    expect(() => parseMutation(input, mutation)).toThrow()
  })
  it('accepts only exact single-read receipts and explicitly inbox-wide partial results', () => {
    const receipt = { status: 'ok', context, requestId: 'm1', operation: mutation.operation, read: true }
    expect(parseMutation(receipt, mutation)).toEqual(receipt)
    const all: MutationRequest = { ...mutation, operation: { kind: 'all', scope: 'inbox' } }
    const partial = { status: 'partial', context, requestId: 'm1', operation: all.operation, readIds: ['n1'], failures: [{ id: 'n2', reason: 'denied' }] }
    expect(parseMutation(partial, all)).toEqual(partial)
    expect(() => parseMutation({ ...partial, operation: { kind: 'all', scope: 'page' } }, all)).toThrow()
    expect(() => parseMutation({ ...partial, readIds: ['n2'] }, all)).toThrow()
  })
})

describe('typed related navigation', () => {
  const target = { kind: 'review', tenantId: 't1', workspaceId: 'w1', projectId: 'p1', availability: 'available' }
  it('maps only an explicit existing target and preserves destination authorization', () => {
    expect(resolveTarget(target, context)).toEqual({ href: '/w/w1/projects/p1/review' })
    expect(resolveTarget({ ...target, kind: 'project-overview' }, context)).toEqual({ href: '/w/w1/projects/p1/overview' })
  })
  it.each([null, 'javascript:alert(1)', 'https://example.com', { ...target, url: 'data:text/html,bad' }, { ...target, projectId: ['p1', 'p2'] }, { ...target, projectId: '../p2' }, { ...target, workspaceId: '' }, { ...target, tenantId: 'other' }, { ...target, kind: 'render' }])('rejects untyped, ambiguous or foreign targets %#', input => {
    expect(resolveTarget(input, context)).toEqual({ reason: 'unsupportedTarget' })
  })
  it('rejects explicit adapter workspace mismatches without filtering the inbox by current project', () => {
    expect(resolveTarget(target, { ...context, workspaceId: 'other' })).toEqual({ reason: 'unsupportedTarget' })
  })
  it.each(['missing', 'denied', 'unknown'] as const)('explains %s target results', availability => {
    expect(resolveTarget({ ...target, availability }, context)).toEqual({ reason: `target${availability[0].toUpperCase()}${availability.slice(1)}` })
  })
})

describe('unavailable and explicit simulation boundaries', () => {
  it('never queries HTTP or derives a real inbox from apparent local identities', async () => {
    const fetch = vi.spyOn(globalThis, 'fetch')
    expect(unavailableSource.adapter.origin).toBe('unavailable')
    expect(await unavailableSource.adapter.list({ ...query, context: { ...context, principalId: 'local-user' } }, new AbortController().signal)).toMatchObject({ status: 'unavailable' })
    expect(fetch).not.toHaveBeenCalled()
    fetch.mockRestore()
  })
  it('requires exact localhost opt-in; fixture does not touch auth, storage or transport', async () => {
    expect(localhostFixture({ hostname: 'example.com', search: '?notificationFixture=1' })).toBeNull()
    expect(localhostFixture({ hostname: 'localhost', search: '' })).toBeNull()
    const source = localhostFixture({ hostname: 'localhost', search: '?notificationFixture=1' })!
    expect(source.adapter.origin).toBe('simulated')
    expect(source.context.principalId).toBe('simulated-reader')
    const setItem = vi.spyOn(Storage.prototype, 'setItem')
    const fetch = vi.spyOn(globalThis, 'fetch')
    await source.adapter.list({ ...query, context: source.context }, new AbortController().signal)
    expect(setItem).not.toHaveBeenCalled()
    expect(fetch).not.toHaveBeenCalled()
    setItem.mockRestore(); fetch.mockRestore()
  })
  it('fixture scopes read state to its own exact session and never relaxes denied/unknown access', async () => {
    const fixture = createNotificationFixture()
    const foreign = await fixture.adapter.list(query, new AbortController().signal)
    expect(foreign).toMatchObject({ status: 'denied' })
    for (const access of ['denied', 'unknown'] as const) {
      const denied = createNotificationFixture({ access })
      expect(await denied.adapter.list({ ...query, context: denied.context }, new AbortController().signal)).toMatchObject({ status: access === 'denied' ? 'denied' : 'unavailable' })
    }
  })
})


describe('simulated related navigation isolation', () => {
  const target = { kind: 'project-overview', tenantId: 't1', workspaceId: 'simulated-workspace', projectId: 'simulated-project', availability: 'available' }
  it('links only the fixed local fixture overview with explicit simulation opt-in', () => {
    expect(resolveTarget(target, context, 'simulated')).toEqual({ href: '/w/simulated-workspace/projects/simulated-project/overview?notificationFixture=1' })
    expect(resolveTarget(target, context, 'real')).toEqual({ href: '/w/simulated-workspace/projects/simulated-project/overview' })
    expect(resolveTarget(target, context, 'unavailable')).toEqual({ reason: 'unsupportedTarget' })
  })
  it.each([{ projectId: 'real-project' }, { workspaceId: 'real-workspace' }, { kind: 'review' }])('cannot route a simulated receipt to another destination %#', overrides => {
    expect(resolveTarget({ ...target, ...overrides }, context, 'simulated')).toEqual({ reason: 'unsupportedTarget' })
  })
})
