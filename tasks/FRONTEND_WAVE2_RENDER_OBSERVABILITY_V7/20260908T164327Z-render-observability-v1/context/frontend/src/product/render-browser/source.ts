import { z } from 'zod'
import { isAvailable, type EffectiveAccessEntry } from '../../foundation/effectiveAccess'

// FRONTEND UNAGREED consumer proposal only. These labels are not an endpoint,
// backend permission, canonical schema, or assertion of integration.
export const UNAGREED_RENDER_QUERY_LABEL = 'frontend.unagreed.render.observability.read' as const
export const TEST_ONLY_RENDER_ACCESS_KEY = 'test-only.frontend-unagreed.render.observability.read' as const
export const MAX_RENDER_ITEMS = 500 as const

export interface RenderScope {
  readonly principalId: string | null
  readonly tenantId: string | null
  readonly sessionId: string
  readonly projectId: string
}
export interface RendersContext extends RenderScope { readonly access: EffectiveAccessEntry }
export interface RenderReadRequest { readonly scope: RenderScope; readonly requestId: string }
export interface RendersAdapter {
  readonly origin: 'real' | 'simulated' | 'unavailable'
  readProject(request: RenderReadRequest, signal: AbortSignal): Promise<unknown>
}
export type RenderReadAccessBinding =
  | { readonly kind: 'HOST_AGREED'; readonly accessKey: string }
  | { readonly kind: 'TEST_ONLY_UNAGREED'; readonly accessKey: typeof TEST_ONLY_RENDER_ACCESS_KEY }
  | { readonly kind: 'UNAVAILABLE'; readonly label: typeof UNAGREED_RENDER_QUERY_LABEL }
export interface RenderSource {
  readonly scope: RenderScope
  readonly access: EffectiveAccessEntry
  readonly readAccessBinding: RenderReadAccessBinding
  readonly adapter: RendersAdapter
}
// Compatibility name retained for the existing bounded consumer module.
export type RendersSource = RenderSource
export type RenderOrder = 'name-asc' | 'name-desc'
export interface RenderFilters { readonly query: string; readonly status: string; readonly order: RenderOrder }
export type RenderFailureStatus = 'unavailable' | 'denied' | 'unknown' | 'unsupported' | 'error' | 'stale'

export function isRenderIdentity(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0 && value.length <= 256 && !Array.from(value).some(character => {
    const code = character.charCodeAt(0)
    return /\s/u.test(character) || code <= 0x1f || code === 0x7f
  })
}

const privateOrSecret = /(?:authorization\s*:|bearer\s+|password\s*[:=]|api[_-]?key\s*[:=]|(?:access|refresh|session)?token\s*[:=]|(?:^|\s)(?:\/home\/|\/users\/|[a-z]:\\)|traceback|stack\s*trace|\bat\s+\S+\s+\([^)]*:\d+(?::\d+)?\))/iu
export function isSafeDisclosure(value: string): boolean {
  return value.length <= 1_000 && !privateOrSecret.test(value) && !Array.from(value).some(character => {
    const code = character.charCodeAt(0)
    return (code <= 0x08 || (code >= 0x0b && code <= 0x1f) || code === 0x7f)
  })
}

const identity = z.string().refine(isRenderIdentity)
const literal = z.string().max(500).refine(value => isSafeDisclosure(value))
const statusLiteral = z.string().min(1).max(120).refine(value => isSafeDisclosure(value))
const safeDisclosure = z.string().min(1).max(1_000).refine(isSafeDisclosure)
const sourceTime = z.iso.datetime({ offset: true })
const optionalTime = sourceTime.nullable().optional()
const scopeSchema = z.object({ principalId: identity.nullable(), tenantId: identity.nullable(), sessionId: identity, projectId: identity }).strict()
const failureDetailSchema = z.object({
  summary: safeDisclosure,
  code: z.string().min(1).max(120).regex(/^[A-Za-z0-9_.:-]+$/u).optional(),
  occurredAt: sourceTime.optional(),
}).strict()
const progressSchema = z.object({
  value: z.number().finite(), unit: statusLiteral,
  total: z.number().finite().optional(), totalUnit: statusLiteral.optional(), stage: literal.optional(),
}).strict().superRefine((value, context) => {
  if ((value.total === undefined) !== (value.totalUnit === undefined)) context.addIssue({ code: 'custom', message: 'Progress total and unit must be supplied together' })
})
const taskSchema = z.object({ id: identity, status: statusLiteral.optional(), version: identity.optional() }).strict()
const attemptSchema = z.object({
  id: identity, ordinal: z.number().int().positive().max(1_000_000), taskId: identity, status: statusLiteral,
  parentAttemptId: identity.optional(), retryOfAttemptId: identity.optional(), startedAt: optionalTime, endedAt: optionalTime,
  failure: failureDetailSchema.optional(),
}).strict()
const attemptsSchema = z.object({
  completeness: z.enum(['complete', 'bounded']), limit: z.number().int().positive().max(MAX_RENDER_ITEMS),
  items: z.array(attemptSchema).max(MAX_RENDER_ITEMS),
}).strict()
const artifactSchema = z.object({
  id: identity, name: literal.nullable().optional(), type: statusLiteral, availability: statusLiteral,
  version: identity.optional(), taskId: identity, metadataAccess: z.enum(['inspectable', 'denied', 'unavailable', 'unknown', 'stale']),
}).strict()
const artifactUnavailable = z.object({ state: z.enum(['denied', 'unavailable', 'unknown', 'stale']), explanation: safeDisclosure.optional() }).strict()
const artifactsSchema = z.discriminatedUnion('state', [
  z.object({ state: z.literal('empty') }).strict(),
  artifactUnavailable,
  z.object({
    state: z.literal('available'), completeness: z.enum(['complete', 'bounded']), limit: z.number().int().positive().max(MAX_RENDER_ITEMS),
    items: z.array(artifactSchema).max(MAX_RENDER_ITEMS),
  }).strict(),
])
const renderSchema = z.object({
  id: identity, projectId: identity, name: literal.nullable().optional(), status: statusLiteral, version: identity.optional(),
  source: z.object({ id: identity, kind: statusLiteral, version: identity.optional() }).strict(),
  createdAt: optionalTime, updatedAt: optionalTime, startedAt: optionalTime, endedAt: optionalTime,
  progress: progressSchema.optional(), task: taskSchema.optional(), failure: failureDetailSchema.optional(),
  attempts: attemptsSchema.optional(), artifacts: artifactsSchema.optional(),
}).strict()
const boundarySchema = z.object({
  kind: z.literal('project-render-observability-snapshot'), completeness: z.enum(['complete', 'bounded']),
  limit: z.number().int().positive().max(MAX_RENDER_ITEMS), version: identity,
  freshness: z.enum(['current', 'stale']), sourceUpdatedAt: sourceTime.optional(),
  supportedStatusFilters: z.array(statusLiteral).max(100),
}).strict()
const envelope = { scope: scopeSchema, requestId: identity }
const successSchema = z.object({ ...envelope, status: z.literal('ok'), jobs: z.array(renderSchema).max(MAX_RENDER_ITEMS), boundary: boundarySchema }).strict()
const failureSchema = z.object({ ...envelope, status: z.enum(['unavailable', 'denied', 'unknown', 'unsupported', 'error', 'stale']), explanation: safeDisclosure.optional() }).strict()

export type RenderProgress = z.infer<typeof progressSchema>
export type RenderAttempt = z.infer<typeof attemptSchema>
export type RenderArtifact = z.infer<typeof artifactSchema>
export type RenderProjection = z.infer<typeof renderSchema>
export type RenderSnapshotBoundary = z.infer<typeof boundarySchema>
export type RenderSnapshot = z.infer<typeof successSchema>
export type RenderReadFailure = z.infer<typeof failureSchema>

export class RenderProjectionError extends Error {
  constructor(readonly kind: 'invalid' | 'invalid-relationship', message: string) { super(message); this.name = 'RenderProjectionError' }
}

export function scopeKey(scope: RenderScope): string {
  return JSON.stringify([scope.principalId, scope.tenantId, scope.sessionId, scope.projectId])
}
export function contextKey(context: RendersContext): string {
  return JSON.stringify([
    scopeKey(context), context.access.key, context.access.status, context.access.reasonCode,
    context.access.explanation, context.access.source, context.access.observedAt ?? null,
    context.access.factors.capability, context.access.factors.runtime, context.access.factors.entitlement,
    context.access.factors.policy, context.access.factors.quota,
  ])
}
export function renderScopeIsValid(scope: RenderScope): boolean {
  return isRenderIdentity(scope.principalId) && isRenderIdentity(scope.tenantId)
    && isRenderIdentity(scope.sessionId) && isRenderIdentity(scope.projectId)
}
export function accessDisposition(context: RendersContext): 'ready' | 'unavailable' | 'denied' | 'unknown' {
  if (!renderScopeIsValid(context)) return 'unknown'
  if (isAvailable(context.access)) return 'ready'
  if (context.access.status === 'POLICY_DENIED' || context.access.status === 'NOT_ENTITLED') return 'denied'
  if (context.access.status === 'UNKNOWN_FAIL_CLOSED') return 'unknown'
  return 'unavailable'
}

function hasExpectedProjection(source: RenderSource): boolean {
  if (source.adapter.origin === 'real') {
    return source.readAccessBinding.kind === 'HOST_AGREED'
      && isRenderIdentity(source.readAccessBinding.accessKey)
      && source.readAccessBinding.accessKey !== 'surface.operations.view'
      && source.readAccessBinding.accessKey !== UNAGREED_RENDER_QUERY_LABEL
      && source.readAccessBinding.accessKey !== TEST_ONLY_RENDER_ACCESS_KEY
      && source.access.key === source.readAccessBinding.accessKey
      && source.access.source === 'SERVER'
  }
  if (source.adapter.origin === 'simulated') {
    return source.readAccessBinding.kind === 'TEST_ONLY_UNAGREED'
      && source.readAccessBinding.accessKey === TEST_ONLY_RENDER_ACCESS_KEY
      && source.access.key === TEST_ONLY_RENDER_ACCESS_KEY
      && source.access.source === 'DEVELOPMENT_FAIL_CLOSED'
  }
  return false
}
export function sourceDisposition(source: RenderSource): 'ready' | 'unavailable' | 'denied' | 'unknown' {
  if (source.adapter.origin === 'unavailable') return 'unavailable'
  if (!hasExpectedProjection(source) || !renderScopeIsValid(source.scope)) return 'unknown'
  return accessDisposition({ ...source.scope, access: source.access })
}
export function sourcePresentationOrigin(source: RenderSource): RenderSource['adapter']['origin'] {
  return source.adapter.origin !== 'unavailable' && hasExpectedProjection(source) && renderScopeIsValid(source.scope) ? source.adapter.origin : 'unavailable'
}
export function sourceAccessExplanation(source: RenderSource): string | null {
  return hasExpectedProjection(source) && renderScopeIsValid(source.scope) && isSafeDisclosure(source.access.explanation) ? source.access.explanation : null
}

function timeValue(value: string | null | undefined): number | null { return value == null ? null : Date.parse(value) }
function validTimeOrder(start: string | null | undefined, end: string | null | undefined): boolean {
  const left = timeValue(start), right = timeValue(end)
  return left === null || right === null || left <= right
}
function validateRelationships(job: RenderProjection): void {
  const attempts = job.attempts?.items ?? []
  if (job.attempts && attempts.length > job.attempts.limit) throw new RenderProjectionError('invalid', 'Attempt boundary exceeded')
  if (new Set(attempts.map(attempt => attempt.id)).size !== attempts.length || new Set(attempts.map(attempt => attempt.ordinal)).size !== attempts.length) {
    throw new RenderProjectionError('invalid-relationship', 'Duplicate Render attempt identity or ordinal')
  }
  const byId = new Map(attempts.map(attempt => [attempt.id, attempt]))
  for (const attempt of attempts) {
    if (!job.task || attempt.taskId !== job.task.id) throw new RenderProjectionError('invalid-relationship', 'Attempt task link is invalid')
    for (const linkedId of [attempt.parentAttemptId, attempt.retryOfAttemptId]) {
      if (!linkedId) continue
      const linked = byId.get(linkedId)
      if (!linked || linked.id === attempt.id || linked.ordinal >= attempt.ordinal) throw new RenderProjectionError('invalid-relationship', 'Attempt parent or retry link is invalid')
    }
    if (!validTimeOrder(attempt.startedAt, attempt.endedAt)) throw new RenderProjectionError('invalid', 'Attempt times are invalid')
  }
  if (job.artifacts?.state === 'available') {
    if (job.artifacts.items.length > job.artifacts.limit || new Set(job.artifacts.items.map(artifact => artifact.id)).size !== job.artifacts.items.length) {
      throw new RenderProjectionError('invalid', 'Artifact boundary or identity is invalid')
    }
    if (!job.task || job.artifacts.items.some(artifact => artifact.taskId !== job.task!.id)) {
      throw new RenderProjectionError('invalid-relationship', 'Artifact task link is invalid')
    }
  }
  if (!validTimeOrder(job.createdAt, job.updatedAt) || !validTimeOrder(job.startedAt, job.endedAt)) throw new RenderProjectionError('invalid', 'Render source times are invalid')
}

export function parseRenderSnapshot(input: unknown, request: RenderReadRequest): RenderSnapshot | RenderReadFailure {
  let result: RenderSnapshot | RenderReadFailure
  try { result = z.union([successSchema, failureSchema]).parse(input) }
  catch { throw new RenderProjectionError('invalid', 'Invalid Render observability receipt') }
  if (scopeKey(result.scope) !== scopeKey(request.scope) || result.requestId !== request.requestId) throw new RenderProjectionError('invalid', 'Invalid Render receipt ownership')
  if (result.status !== 'ok') return result
  if (result.jobs.length > result.boundary.limit
    || new Set(result.jobs.map(job => job.id)).size !== result.jobs.length
    || result.jobs.some(job => job.projectId !== request.scope.projectId)
    || new Set(result.boundary.supportedStatusFilters).size !== result.boundary.supportedStatusFilters.length) {
    throw new RenderProjectionError('invalid', 'Invalid single-Project Render snapshot')
  }
  for (const job of result.jobs) validateRelationships(job)
  return result
}

export function deriveProgressPercent(progress: RenderProgress | undefined): number | null {
  if (!progress || progress.total === undefined || progress.totalUnit === undefined
    || !Number.isFinite(progress.value) || !Number.isFinite(progress.total)
    || progress.unit !== progress.totalUnit || progress.total <= 0 || progress.value < 0 || progress.value > progress.total) return null
  return progress.value / progress.total * 100
}
function compareText(left: string, right: string): number { return left < right ? -1 : left > right ? 1 : 0 }
function sortName(job: RenderProjection): string { return (job.name || job.id).toLocaleLowerCase() }
export function selectRenderJobs(jobs: readonly RenderProjection[], filters: RenderFilters): RenderProjection[] {
  const query = filters.query.toLocaleLowerCase()
  const direction = filters.order === 'name-desc' ? -1 : 1
  return jobs.filter(job => (!query || `${job.id}\n${job.name ?? ''}`.toLocaleLowerCase().includes(query)) && (!filters.status || job.status === filters.status))
    .sort((left, right) => direction * compareText(sortName(left), sortName(right)) || compareText(left.id, right.id))
}
export function renderStatusValues(boundary: Pick<RenderSnapshotBoundary, 'supportedStatusFilters'>): string[] {
  return [...boundary.supportedStatusFilters]
}

export function unavailableRendersSource(): RenderSource {
  const scope: RenderScope = { principalId: null, tenantId: null, sessionId: 'unconfigured', projectId: 'unconfigured' }
  return {
    scope,
    access: {
      key: UNAGREED_RENDER_QUERY_LABEL, status: 'UNKNOWN_FAIL_CLOSED', reasonCode: 'EFFECTIVE_ACCESS_PROJECTION_MISSING',
      explanation: 'Effective access is not available from a connected Render source.',
      factors: { capability: 'UNKNOWN', runtime: 'UNKNOWN', entitlement: 'UNKNOWN', policy: 'UNKNOWN', quota: 'UNKNOWN' },
      source: 'MISSING_SERVER_PROJECTION',
    },
    readAccessBinding: { kind: 'UNAVAILABLE', label: UNAGREED_RENDER_QUERY_LABEL },
    adapter: { origin: 'unavailable', async readProject(request) { return { status: 'unavailable', scope: request.scope, requestId: request.requestId } } },
  }
}
