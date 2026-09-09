import { z } from 'zod'
import type { EffectiveAccessCatalog } from '../../foundation/effectiveAccess'
import { LIST_KEY, contentKey, artifactKey, type PublicationFilters, type PublicationPlan, type PublicationRequest, type PublicationResult, type PublicationSnapshot, type PublicationSource } from './types'

const id = z.string().min(1).max(180).regex(/^[a-zA-Z0-9][a-zA-Z0-9_.:-]*$/)
const text = z.string().max(4000)
const optionalTime = z.string().max(100).nullable().optional()
const scopeSchema = z.object({ principalId: id, tenantId: id.nullable(), sessionId: id, workspaceId: id, projectId: id, sourceId: id })
const envelope = z.object({ scope: scopeSchema, requestId: id, query: z.object({ kind: z.literal('project-publication-snapshot'), limit: z.literal(200) }), status: z.enum(['ok', 'unavailable', 'restricted', 'error']) })
const planSchema = z.object({ id, projectId: id, accountId: id, status: z.string().min(1).max(120), title: text.optional(), summary: text.optional(), copyVersion: text.optional(), artifactIds: z.array(id).max(200), timeField: z.enum(['scheduledAt', 'publishedAt', 'unscheduled', 'unknown']), scheduledAt: optionalTime, publishedAt: optionalTime })
const snapshotSchema = envelope.extend({ status: z.literal('ok'), version: id, completeness: z.enum(['complete', 'bounded', 'partial']), fetchedAt: optionalTime,
  accounts: z.array(z.object({ id, name: text, platform: text })).max(200),
  plans: z.array(planSchema).max(200),
  artifacts: z.array(z.object({ id, projectId: id, name: text.optional(), mediaType: text.optional(), version: text.optional() })).max(200),
  attempts: z.array(z.object({ id, planId: id, accountId: id, status: text, attemptedAt: optionalTime, failureSummary: text.optional() })).max(1000),
  externalPublications: z.array(z.object({ id, attemptId: id, planId: id, accountId: id, status: text, publishedAt: optionalTime })).max(1000),
})
export const scopeKey = (scope: PublicationRequest['scope']) => JSON.stringify([scope.principalId, scope.tenantId, scope.sessionId, scope.workspaceId, scope.projectId, scope.sourceId])
export function accessFingerprint(access: EffectiveAccessCatalog): string {
  return JSON.stringify(Object.keys(access).sort().map(key => { const e = access[key]; return [key, e.key, e.status, e.source, e.reasonCode, e.factors.capability, e.factors.runtime, e.factors.entitlement, e.factors.policy, e.factors.quota] }))
}
function allowed(access: EffectiveAccessCatalog, key: string): boolean {
  const e = access[key]
  return Boolean(e && e.key === key && e.source === 'SERVER' && e.status === 'AVAILABLE' && ['capability', 'runtime', 'entitlement', 'policy', 'quota'].every(f => ['SATISFIED', 'NOT_APPLICABLE'].includes(e.factors[f as keyof typeof e.factors])))
}
export function publicationAccess(source: PublicationSource): boolean {
  return scopeSchema.safeParse(source.scope).success && source.adapter.origin === 'isolated-verification' && Boolean(source.owner) && allowed(source.access, LIST_KEY)
}
export function parsePublication(input: unknown, request: PublicationRequest, access: EffectiveAccessCatalog): PublicationResult {
  if (!allowed(access, LIST_KEY)) return { status: 'restricted' }
  const e = envelope.safeParse(input)
  if (!e.success || e.data.requestId !== request.requestId || scopeKey(e.data.scope) !== scopeKey(request.scope) || JSON.stringify(e.data.query) !== JSON.stringify(request.query)) return { status: 'invalid' }
  if (e.data.status !== 'ok') return { status: e.data.status }
  const parsed = snapshotSchema.safeParse(input)
  if (!parsed.success) return { status: 'invalid' }
  const s = parsed.data
  const unique = (rows: { id: string }[]) => new Set(rows.map(row => row.id)).size === rows.length
  const accountIds = new Set(s.accounts.map(a => a.id)), artifactIds = new Set(s.artifacts.map(a => a.id))
  if (![s.accounts, s.plans, s.artifacts, s.attempts, s.externalPublications].every(unique)
    || s.artifacts.some(a => a.projectId !== request.scope.projectId)
    || s.plans.some(p => p.projectId !== request.scope.projectId || !accountIds.has(p.accountId) || new Set(p.artifactIds).size !== p.artifactIds.length || p.artifactIds.some(a => !artifactIds.has(a)))
    || s.attempts.some(a => !s.plans.some(p => p.id === a.planId && p.accountId === a.accountId))
    || s.externalPublications.some(e => !s.attempts.some(a => a.id === e.attemptId && a.planId === e.planId && a.accountId === e.accountId))) return { status: 'invalid' }
  // Explicit field projection occurs before rendering/Selection. The backend still must trim responses.
  const artifacts = s.artifacts.filter(a => allowed(access, artifactKey(a.id)))
  const permittedArtifacts = new Set(artifacts.map(a => a.id))
  const plans = s.plans.map(p => ({ id: p.id, projectId: p.projectId, accountId: p.accountId, status: p.status, timeField: p.timeField, scheduledAt: p.scheduledAt, publishedAt: p.publishedAt,
    artifactIds: p.artifactIds.filter(a => permittedArtifacts.has(a)),
    ...(allowed(access, contentKey(p.id)) ? { title: p.title, summary: p.summary, copyVersion: p.copyVersion } : {}),
  }))
  const attempts = s.attempts.map(a => ({ id: a.id, planId: a.planId, accountId: a.accountId, status: a.status, attemptedAt: a.attemptedAt, ...(allowed(access, contentKey(a.planId)) ? { failureSummary: a.failureSummary } : {}) }))
  return { status: 'ok', version: s.version, completeness: s.completeness, fetchedAt: s.fetchedAt, accounts: s.accounts, plans, artifacts, attempts, externalPublications: s.externalPublications }
}
const pad = (n: number) => String(n).padStart(2, '0')
const daysInMonth = (year: number, month: number) => [31, year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1] ?? 0
export function monthDays(month: string): string[] {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) return []
  const [y, m] = month.split('-').map(Number)
  if (y < 1) return []
  return Array.from({ length: daysInMonth(y, m) }, (_, i) => `${month}-${pad(i + 1)}`)
}
export function shiftMonth(month: string, delta: number): string {
  if (!monthDays(month).length || !Number.isInteger(delta)) return month
  const [y, m] = month.split('-').map(Number), n = y * 12 + m - 1 + delta
  if (n < 12 || n >= 120000) return month
  return `${String(Math.floor(n / 12)).padStart(4, '0')}-${pad(n % 12 + 1)}`
}
/** Dates without an explicit offset are deliberately never parsed. */
export function absoluteInstant(value: unknown): number | null {
  if (typeof value !== 'string') return null
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,3})?(Z|[+-](\d{2}):(\d{2}))$/.exec(value)
  if (!match) return null
  const [, y, m, d, h, min, sec, zone, oh, om] = match
  if (+y < 1 || +m < 1 || +m > 12 || +d < 1 || +d > daysInMonth(+y, +m) || +h > 23 || +min > 59 || +sec > 59 || (zone !== 'Z' && (+oh > 23 || +om > 59 || zone === '-00:00'))) return null
  const instant = Date.parse(value)
  return Number.isFinite(instant) ? instant : null
}
export function calendarDay(value: unknown, zone: string): string | null {
  const instant = absoluteInstant(value)
  if (instant === null) return null
  try {
    const parts = new Intl.DateTimeFormat('en-US', { timeZone: zone, calendar: 'gregory', numberingSystem: 'latn', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(instant)
    const part = (name: string) => parts.find(p => p.type === name)?.value
    return `${part('year')?.padStart(4, '0')}-${part('month')}-${part('day')}`
  } catch { return null }
}
export function planInstant(plan: PublicationPlan): number | null {
  return plan.timeField === 'scheduledAt' || plan.timeField === 'publishedAt' ? absoluteInstant(plan[plan.timeField]) : null
}
export function planDay(plan: PublicationPlan, zone: string): string | null {
  return plan.timeField === 'scheduledAt' || plan.timeField === 'publishedAt' ? calendarDay(plan[plan.timeField], zone) : null
}
export function filterPlans(snapshot: PublicationSnapshot, filters: PublicationFilters): PublicationPlan[] {
  const query = filters.query.trim().toLowerCase()
  return snapshot.plans.filter(p => (!filters.account || p.accountId === filters.account) && (!filters.status || p.status === filters.status) && (!query || [p.id, p.title, p.summary].some(v => v?.toLowerCase().includes(query))))
    .sort((a, b) => {
      const left = planInstant(a), right = planInstant(b)
      if (left === null && right !== null) return 1
      if (right === null && left !== null) return -1
      const difference = left !== null && right !== null ? (left - right) * (filters.order === 'asc' ? 1 : -1) : 0
      return difference || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)
    })
}
