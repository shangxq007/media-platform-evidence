import { z } from 'zod'
import { RenderJobSummary } from '../../contracts/app/render-job'
import { isAvailable, unknownAccess, type EffectiveAccessEntry } from '../../foundation/effectiveAccess'

export const REAL_RENDER_SUMMARIES_QUERY_KEY = 'render.job.summary.query'
export const SIMULATED_RENDER_SUMMARIES_QUERY_KEY = 'fixture.render.job.summary.query'
const MAX_RENDER_SUMMARIES = 500

export interface RenderScope {
  principalId: string | null
  tenantId: string | null
  sessionId: string
  projectId: string
}
export interface RendersContext extends RenderScope { access: EffectiveAccessEntry }
export interface RenderListRequest { scope: RenderScope; requestId: string }
export interface RendersAdapter {
  origin: 'real' | 'simulated' | 'unavailable'
  listProject(request: RenderListRequest, signal: AbortSignal): Promise<unknown>
}
export interface RendersSource { scope: RenderScope; access: EffectiveAccessEntry; adapter: RendersAdapter }
export type RenderOrder = 'id-asc' | 'id-desc'
export type RenderFilters = { query: string; status: string; order: RenderOrder }
export type RenderListFailureStatus = 'unavailable' | 'denied' | 'unknown' | 'unsupported' | 'error'

const identity = z.string().min(1)
const scopeSchema = z.object({
  principalId: identity.nullable(), tenantId: identity.nullable(), sessionId: identity, projectId: identity,
}).strict()
const envelope = { scope: scopeSchema, requestId: identity }
const successSchema = z.object({
  ...envelope,
  status: z.literal('ok'),
  // Reuse the established application contract and reject any fields outside
  // its five-field safe summary instead of silently widening this surface.
  jobs: z.array(RenderJobSummary.strict()).max(MAX_RENDER_SUMMARIES),
  boundary: z.object({
    kind: z.literal('project-snapshot'),
    limit: z.number().int().positive().max(MAX_RENDER_SUMMARIES),
    limited: z.boolean(),
  }).strict(),
}).strict()
const failureSchema = z.object({
  ...envelope,
  status: z.enum(['unavailable', 'denied', 'unknown', 'unsupported', 'error']),
  explanation: z.string().optional(),
}).strict()
export type RenderSummariesSnapshot = z.infer<typeof successSchema>
export type RenderListFailure = z.infer<typeof failureSchema>

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

export function accessDisposition(context: RendersContext): 'ready' | 'unavailable' | 'denied' | 'unknown' {
  if (!context.principalId || !context.tenantId) return 'unknown'
  if (isAvailable(context.access)) return 'ready'
  if (context.access.status === 'POLICY_DENIED' || context.access.status === 'NOT_ENTITLED') return 'denied'
  if (context.access.status === 'UNKNOWN_FAIL_CLOSED') return 'unknown'
  return 'unavailable'
}

function hasExpectedProjection(source: RendersSource): boolean {
  if (source.adapter.origin === 'real') {
    // This key is a frontend consumption proposal only. A host may inject a
    // real adapter only with the exact server-owned projection.
    return source.access.key === REAL_RENDER_SUMMARIES_QUERY_KEY && source.access.source === 'SERVER'
  }
  if (source.adapter.origin === 'simulated') {
    return source.access.key === SIMULATED_RENDER_SUMMARIES_QUERY_KEY
      && source.access.source === 'DEVELOPMENT_FAIL_CLOSED'
  }
  return false
}

export function sourcePresentationOrigin(source: RendersSource): RendersAdapter['origin'] {
  return source.adapter.origin !== 'unavailable' && hasExpectedProjection(source)
    ? source.adapter.origin
    : 'unavailable'
}

export function sourceDisposition(source: RendersSource): 'ready' | 'unavailable' | 'denied' | 'unknown' {
  if (source.adapter.origin === 'unavailable') return 'unavailable'
  if (!hasExpectedProjection(source)) return 'unknown'
  return accessDisposition({ ...source.scope, access: source.access })
}

export function sourceAccessExplanation(source: RendersSource): string | null {
  return hasExpectedProjection(source) ? source.access.explanation : null
}

export function parseRenderSummaries(input: unknown, request: RenderListRequest): RenderSummariesSnapshot | RenderListFailure {
  const result = z.union([successSchema, failureSchema]).parse(input)
  if (scopeKey(result.scope) !== scopeKey(request.scope) || result.requestId !== request.requestId) {
    throw new Error('Invalid Render summary receipt ownership')
  }
  if (result.status !== 'ok') return result
  const ids = result.jobs.map(job => job.id)
  if (new Set(ids).size !== ids.length
    || result.jobs.length > result.boundary.limit
    || result.jobs.some(job => job.projectId !== request.scope.projectId)) {
    throw new Error('Invalid single-Project Render snapshot')
  }
  return result
}

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0
}

export function selectRenderJobs(jobs: readonly RenderJobSummary[], filters: RenderFilters): RenderJobSummary[] {
  const query = filters.query.toLocaleLowerCase()
  const direction = filters.order === 'id-desc' ? -1 : 1
  return jobs
    .filter(job => (!query || `${job.id}\n${job.profile}`.toLocaleLowerCase().includes(query))
      && (!filters.status || job.status === filters.status))
    .sort((left, right) => direction * compareText(left.id, right.id))
}

export function unavailableRendersSource(): RendersSource {
  const scope: RenderScope = {
    principalId: null, tenantId: null, sessionId: 'unconfigured', projectId: 'unconfigured',
  }
  return {
    scope,
    access: unknownAccess(REAL_RENDER_SUMMARIES_QUERY_KEY),
    adapter: {
      origin: 'unavailable',
      async listProject(request) {
        return { status: 'unavailable', scope: request.scope, requestId: request.requestId }
      },
    },
  }
}
