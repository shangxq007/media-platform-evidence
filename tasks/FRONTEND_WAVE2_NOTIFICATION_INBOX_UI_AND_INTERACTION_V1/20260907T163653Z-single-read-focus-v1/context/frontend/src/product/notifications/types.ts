import { z } from 'zod'

// Frontend consumption proposal only. No endpoint, backend DTO, or authorization claim.
const identity = z.string().min(1)
const contextSchema = z.object({
  principalId: identity.nullable(), tenantId: identity.nullable(), sessionId: identity,
  access: z.enum(['allowed', 'denied', 'unknown']), workspaceId: identity.optional(),
}).strict()
export type InboxContext = z.infer<typeof contextSchema>
export type InboxFilter = 'all' | 'unread'
export interface ListRequest { context: InboxContext; requestId: string; filter: InboxFilter }
export interface MutationRequest {
  context: InboxContext; requestId: string
  operation: { kind: 'single'; id: string } | { kind: 'all'; scope: 'inbox' }
}
const itemSchema = z.object({
  id: identity,
  content: z.object({ title: z.string(), body: z.string(), type: z.string(), createdAt: z.string().nullable() }).strict(),
  read: z.boolean(), target: z.unknown().optional(),
}).strict()
export type InboxItem = z.infer<typeof itemSchema>
const envelope = { context: contextSchema, requestId: identity }
const failureSchema = z.object({ ...envelope, status: z.enum(['unavailable', 'denied', 'not-found', 'error']), explanation: z.string().optional() }).strict()
const pageSchema = z.object({
  ...envelope, status: z.literal('ok'), filter: z.enum(['all', 'unread']), items: z.array(itemSchema),
  unread: z.discriminatedUnion('kind', [z.object({ kind: z.literal('known'), total: z.number().int().nonnegative() }).strict(), z.object({ kind: z.literal('unknown') }).strict()]),
  // A bounded snapshot has no inferred cursor or fabricated total. A future adapter
  // must explicitly extend this boundary before offering traversal controls.
  traversal: z.discriminatedUnion('kind', [z.object({ kind: z.literal('complete') }).strict(), z.object({ kind: z.literal('limited'), limit: z.number().int().positive() }).strict()]),
}).strict()
export type InboxPage = z.infer<typeof pageSchema>
export type InboxFailure = z.infer<typeof failureSchema>
const allOperation = z.object({ kind: z.literal('all'), scope: z.literal('inbox') }).strict()
const singleSchema = z.object({ ...envelope, status: z.literal('ok'), operation: z.object({ kind: z.literal('single'), id: identity }).strict(), read: z.literal(true) }).strict()
const allSchema = z.object({ ...envelope, status: z.enum(['ok', 'partial']), operation: allOperation,
  readIds: z.array(identity), failures: z.array(z.object({ id: identity, reason: z.enum(['denied', 'not-found', 'error']) }).strict()),
}).strict()

export interface InboxAdapter {
  origin: 'real' | 'simulated' | 'unavailable'
  capabilities: { singleRead: boolean; readAll: 'inbox' | 'unsupported' }
  list(request: ListRequest, signal: AbortSignal): Promise<unknown>
  markRead?(request: MutationRequest, signal: AbortSignal): Promise<unknown>
  markAllRead?(request: MutationRequest, signal: AbortSignal): Promise<unknown>
}
export interface InboxSource { context: InboxContext; adapter: InboxAdapter }
export function contextKey(context: InboxContext): string {
  return JSON.stringify([context.principalId, context.tenantId, context.sessionId, context.access, context.workspaceId ?? null])
}
export function canQuery(source: InboxSource): boolean {
  return source.adapter.origin !== 'unavailable' && source.context.access === 'allowed' && !!source.context.principalId && !!source.context.tenantId
}
function requireOwnership(result: { context: InboxContext; requestId: string }, request: ListRequest | MutationRequest) {
  if (contextKey(result.context) !== contextKey(request.context) || result.requestId !== request.requestId) throw new Error('Invalid inbox receipt ownership')
}
export function parseList(input: unknown, request: ListRequest): InboxPage | InboxFailure {
  const result = z.union([pageSchema, failureSchema]).parse(input)
  requireOwnership(result, request)
  if (result.status !== 'ok') return result
  const unread = result.items.filter(item => !item.read).length
  if (result.filter !== request.filter || new Set(result.items.map(item => item.id)).size !== result.items.length
    || (request.filter === 'unread' && unread !== result.items.length)
    || (result.unread.kind === 'known' && (result.unread.total < unread || (result.traversal.kind === 'complete' && result.unread.total !== unread)))
    || (result.traversal.kind === 'limited' && result.items.length > result.traversal.limit)) throw new Error('Invalid inbox snapshot')
  return result
}
export function parseMutation(input: unknown, request: MutationRequest) {
  const result = z.union([singleSchema, allSchema, failureSchema]).parse(input)
  requireOwnership(result, request)
  if (result.status !== 'ok' && result.status !== 'partial') return result
  if (result.operation.kind !== request.operation.kind
    || (result.operation.kind === 'single' && request.operation.kind === 'single' && result.operation.id !== request.operation.id)) throw new Error('Invalid inbox operation receipt')
  if ('readIds' in result) {
    const ids = [...result.readIds, ...result.failures.map(failure => failure.id)]
    if (new Set(ids).size !== ids.length || (result.status === 'ok' && result.failures.length !== 0) || (result.status === 'partial' && result.failures.length === 0)) throw new Error('Invalid inbox partial receipt')
  }
  return result
}

// These are the only supported existing destinations. Unknown payloads remain
// opaque and are never interpreted as a URL or inferred from a notification type.
const routeId = z.string().regex(/^[A-Za-z0-9_-]+$/)
const targetSchema = z.object({
  kind: z.enum(['project-overview', 'review']), tenantId: identity,
  workspaceId: routeId, projectId: routeId,
  availability: z.enum(['available', 'missing', 'denied', 'unknown']),
}).strict()
export type InboxTarget = z.infer<typeof targetSchema>
export type TargetResult = { href: string } | { reason: 'unsupportedTarget' | 'targetMissing' | 'targetDenied' | 'targetUnknown' }
export function resolveTarget(input: unknown, context: InboxContext, origin: InboxAdapter['origin'] = 'real'): TargetResult {
  const parsed = targetSchema.safeParse(input)
  if (!parsed.success || origin === 'unavailable' || context.access !== 'allowed' || !context.principalId || parsed.data.tenantId !== context.tenantId
    || (context.workspaceId !== undefined && parsed.data.workspaceId !== context.workspaceId)) return { reason: 'unsupportedTarget' }
  const target = parsed.data
  if (target.availability === 'missing') return { reason: 'targetMissing' }
  if (target.availability === 'denied') return { reason: 'targetDenied' }
  if (target.availability === 'unknown') return { reason: 'targetUnknown' }
  // Simulation can open exactly the existing provisional overview. No fixture
  // payload can route to a real identity or turn the destination's checks off.
  if (origin === 'simulated') {
    if (target.kind !== 'project-overview' || target.workspaceId !== 'simulated-workspace' || target.projectId !== 'simulated-project') return { reason: 'unsupportedTarget' }
    return { href: '/w/simulated-workspace/projects/simulated-project/overview?notificationFixture=1' }
  }
  return { href: `/w/${encodeURIComponent(target.workspaceId)}/projects/${encodeURIComponent(target.projectId)}/${target.kind === 'review' ? 'review' : 'overview'}` }
}


export function notificationDate(value: string | null): Date | null {
  if (!z.iso.datetime({ offset: true }).safeParse(value).success) return null
  const date = new Date(value!)
  return Number.isFinite(date.getTime()) ? date : null
}
