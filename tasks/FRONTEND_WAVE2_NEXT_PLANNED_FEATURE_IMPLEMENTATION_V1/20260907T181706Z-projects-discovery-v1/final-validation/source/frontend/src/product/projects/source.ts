import { z } from 'zod'
import { isAvailable, unknownAccess, type EffectiveAccessEntry } from '../../foundation/effectiveAccess'
import type { ProjectSummary } from '../../foundation/platformClient'

export interface ProjectScope { principalId: string | null; tenantId: string | null; sessionId: string; workspaceId: string }
export interface ProjectsContext extends ProjectScope { access: EffectiveAccessEntry }
export interface ProjectListRequest { scope: ProjectScope; requestId: string }
export interface ProjectsAdapter { origin: 'real' | 'simulated' | 'unavailable'; listRecent(request: ProjectListRequest, signal: AbortSignal): Promise<unknown> }
export interface ProjectsSource { scope: ProjectScope; access: EffectiveAccessEntry; adapter: ProjectsAdapter }
export type ProjectOrder = 'name-asc' | 'name-desc'
export type ProjectFilters = { query: string; status: string; order: ProjectOrder }
export type ProjectListFailureStatus = 'unavailable' | 'denied' | 'unknown' | 'unsupported' | 'error'

const RECENT_PROJECTS_QUERY_KEY = 'project.recent.query'
const SIMULATED_RECENT_PROJECTS_QUERY_KEY = 'fixture.project.recent.query'

const identity = z.string().min(1)
const scopeSchema = z.object({
  principalId: identity.nullable(), tenantId: identity.nullable(), sessionId: identity, workspaceId: identity,
}).strict()
const projectSchema = z.object({
  id: identity,
  tenantId: identity.nullable().optional(),
  name: identity,
  description: z.string().nullish(),
  status: z.string().optional(),
  createdAt: z.string().optional(),
}).strict()
const envelope = { scope: scopeSchema, requestId: identity }
const successSchema = z.object({
  ...envelope,
  status: z.literal('ok'),
  projects: z.array(projectSchema),
  // The only supported collection is a capped recent-work snapshot. This is
  // intentionally not a cursor, total, or claim about complete inventory.
  boundary: z.object({ kind: z.literal('recent'), limit: z.number().int().positive(), limited: z.boolean() }).strict(),
}).strict()
const failureSchema = z.object({
  ...envelope,
  status: z.enum(['unavailable', 'denied', 'unknown', 'unsupported', 'error']),
  explanation: z.string().optional(),
}).strict()
export type RecentProjectsSnapshot = z.infer<typeof successSchema>
export type ProjectListFailure = z.infer<typeof failureSchema>

export function scopeKey(scope: ProjectScope): string {
  return JSON.stringify([scope.principalId, scope.tenantId, scope.sessionId, scope.workspaceId])
}

export function contextKey(context: ProjectsContext): string {
  return JSON.stringify([
    scopeKey(context), context.access.key, context.access.status, context.access.reasonCode,
    context.access.explanation, context.access.source, context.access.observedAt ?? null,
    context.access.factors.capability, context.access.factors.runtime, context.access.factors.entitlement,
    context.access.factors.policy, context.access.factors.quota,
  ])
}

export function accessDisposition(context: ProjectsContext): 'ready' | 'unavailable' | 'denied' | 'unknown' {
  if (!context.principalId || !context.tenantId) return 'unknown'
  if (isAvailable(context.access)) return 'ready'
  if (context.access.status === 'POLICY_DENIED' || context.access.status === 'NOT_ENTITLED') return 'denied'
  if (context.access.status === 'UNKNOWN_FAIL_CLOSED') return 'unknown'
  return 'unavailable'
}

function hasExpectedProjection(source: ProjectsSource): boolean {
  if (source.adapter.origin === 'real') {
    // This key remains a frontend consumption proposal. A real adapter may
    // consume it only when the host supplies the matching server projection.
    return source.access.key === RECENT_PROJECTS_QUERY_KEY && source.access.source === 'SERVER'
  }
  if (source.adapter.origin === 'simulated') {
    return source.access.key === SIMULATED_RECENT_PROJECTS_QUERY_KEY
      && source.access.source === 'DEVELOPMENT_FAIL_CLOSED'
  }
  return false
}

export function sourcePresentationOrigin(source: ProjectsSource): ProjectsAdapter['origin'] {
  return source.adapter.origin !== 'unavailable' && hasExpectedProjection(source)
    ? source.adapter.origin
    : 'unavailable'
}

export function sourceDisposition(source: ProjectsSource, expectedWorkspaceId = source.scope.workspaceId): 'ready' | 'unavailable' | 'denied' | 'unknown' {
  if (source.adapter.origin === 'unavailable') return 'unavailable'
  if (source.scope.workspaceId !== expectedWorkspaceId) return 'unknown'
  if (!hasExpectedProjection(source)) return 'unknown'
  return accessDisposition({ ...source.scope, access: source.access })
}

export function sourceAccessExplanation(source: ProjectsSource): string | null {
  return hasExpectedProjection(source) ? source.access.explanation : null
}

export function parseRecentProjects(input: unknown, request: ProjectListRequest): RecentProjectsSnapshot | ProjectListFailure {
  const result = z.union([successSchema, failureSchema]).parse(input)
  if (scopeKey(result.scope) !== scopeKey(request.scope) || result.requestId !== request.requestId) {
    throw new Error('Invalid recent Projects receipt ownership')
  }
  if (result.status !== 'ok') return result
  const ids = result.projects.map(project => project.id)
  if (new Set(ids).size !== ids.length || result.projects.length > result.boundary.limit
    || result.projects.some(project => project.tenantId !== undefined && project.tenantId !== request.scope.tenantId)) {
    throw new Error('Invalid recent Projects snapshot')
  }
  return result
}

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0
}

export function selectProjects(projects: readonly ProjectSummary[], filters: ProjectFilters): ProjectSummary[] {
  const query = filters.query.toLocaleLowerCase()
  const direction = filters.order === 'name-desc' ? -1 : 1
  return projects
    .filter(project => (!query || `${project.name}\n${project.description ?? ''}`.toLocaleLowerCase().includes(query))
      && (!filters.status || project.status === filters.status))
    .sort((left, right) => direction * compareText(left.name, right.name) || compareText(left.id, right.id))
}

export function projectStatusValues(projects: readonly ProjectSummary[]): string[] {
  return [...new Set(projects.flatMap(project => project.status === undefined ? [] : [project.status]))].sort(compareText)
}

export function unavailableProjectsSource(workspaceId: string): ProjectsSource {
  const scope = { principalId: null, tenantId: null, sessionId: 'unconfigured', workspaceId }
  return {
    scope,
    access: unknownAccess(RECENT_PROJECTS_QUERY_KEY),
    adapter: { origin: 'unavailable', async listRecent(request) { return { status: 'unavailable', scope: request.scope, requestId: request.requestId } } },
  }
}
