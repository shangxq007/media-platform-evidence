import { contextKey, type InboxAdapter, type InboxContext, type InboxItem, type InboxSource, type ListRequest, type MutationRequest } from './types'

export interface FixtureOptions {
  access?: InboxContext['access']; principalId?: string; tenantId?: string; sessionId?: string
  empty?: boolean; limit?: number; failReadIds?: readonly string[]; failList?: boolean
}
export type NotificationFixture = InboxSource & { adapter: InboxAdapter & Required<Pick<InboxAdapter, 'markRead' | 'markAllRead'>> }
export function createNotificationFixture(options: FixtureOptions = {}): NotificationFixture {
  // All identities here are simulated and isolated from the application's auth.
  const context: InboxContext = {
    principalId: options.principalId ?? 'simulated-reader', tenantId: options.tenantId ?? 'simulated-tenant',
    sessionId: options.sessionId ?? 'simulated-session', access: options.access ?? 'allowed',
  }
  let items: InboxItem[] = options.empty ? [] : [
    { id: 'simulated-1', content: { title: 'Preview is ready', body: 'A simulated preview is ready.\nNo media was rendered.', type: 'render.completed', createdAt: '2026-09-07T10:00:00Z' }, read: false,
      target: { kind: 'project-overview', tenantId: context.tenantId, workspaceId: 'simulated-workspace', projectId: 'simulated-project', availability: 'available' } },
    { id: 'simulated-2', content: { title: '<img src=x onerror=alert(1)>', body: 'Original opaque text 原文', type: 'future.event', createdAt: 'invalid' }, read: false, target: { kind: 'unknown' } },
    { id: 'simulated-3', content: { title: 'Earlier update', body: 'This in-memory notification was already read.', type: 'system.announcement', createdAt: null }, read: true },
  ]
  function failure(request: ListRequest | MutationRequest, signal: AbortSignal) {
    const envelope = { context: request.context, requestId: request.requestId }
    if (signal.aborted) return { ...envelope, status: 'error' }
    if (contextKey(request.context) !== contextKey(context) || context.access === 'denied') return { ...envelope, status: 'denied' }
    if (context.access !== 'allowed') return { ...envelope, status: 'unavailable' }
    return null
  }
  return { context, adapter: {
    origin: 'simulated', capabilities: { singleRead: true, readAll: 'inbox' },
    async list(request, signal) {
      const rejected = failure(request, signal)
      if (rejected) return rejected
      if (options.failList) return { status: 'error', context, requestId: request.requestId }
      const filtered = items.filter(item => request.filter === 'all' || !item.read)
      const limit = Math.max(1, options.limit ?? 50)
      return { status: 'ok', context, requestId: request.requestId, filter: request.filter,
        items: filtered.slice(0, limit).map(item => ({ ...item, content: { ...item.content } })),
        unread: { kind: 'known', total: items.filter(item => !item.read).length },
        traversal: filtered.length > limit ? { kind: 'limited', limit } : { kind: 'complete' },
      }
    },
    async markRead(request, signal) {
      const rejected = failure(request, signal)
      if (rejected) return rejected
      const envelope = { context, requestId: request.requestId }
      if (request.operation.kind !== 'single') return { ...envelope, status: 'error' }
      const id = request.operation.id
      if (!items.some(item => item.id === id)) return { ...envelope, status: 'not-found' }
      if (options.failReadIds?.includes(id)) return { ...envelope, status: 'denied' }
      items = items.map(item => item.id === id ? { ...item, read: true } : item)
      return { ...envelope, status: 'ok', operation: request.operation, read: true }
    },
    async markAllRead(request, signal) {
      const rejected = failure(request, signal)
      if (rejected) return rejected
      if (request.operation.kind !== 'all' || request.operation.scope !== 'inbox') return { status: 'error', context, requestId: request.requestId }
      const readIds = items.filter(item => !item.read && !options.failReadIds?.includes(item.id)).map(item => item.id)
      const failures = items.filter(item => !item.read && options.failReadIds?.includes(item.id)).map(item => ({ id: item.id, reason: 'denied' }))
      items = items.map(item => readIds.includes(item.id) ? { ...item, read: true } : item)
      return { status: failures.length ? 'partial' : 'ok', context, requestId: request.requestId, operation: request.operation, readIds, failures }
    },
  } }
}

export function localhostFixture(location: Pick<Location, 'hostname' | 'search'>): InboxSource | null {
  if (!['localhost', '127.0.0.1', '[::1]'].includes(location.hostname)) return null
  const params = new URLSearchParams(location.search)
  if (params.getAll('notificationFixture').length !== 1 || params.get('notificationFixture') !== '1') return null
  const access = params.get('notificationFixtureAccess')
  return createNotificationFixture({
    access: access === 'denied' ? 'denied' : access === 'unknown' ? 'unknown' : 'allowed',
    failList: params.get('notificationFixtureFailure') === 'list',
    failReadIds: params.get('notificationFixtureFailure') === 'read' ? ['simulated-1', 'simulated-2'] : [],
  })
}
