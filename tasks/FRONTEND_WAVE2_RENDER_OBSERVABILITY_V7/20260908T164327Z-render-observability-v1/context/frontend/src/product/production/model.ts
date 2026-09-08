import { z } from 'zod'
import { isAvailable } from '../../foundation/effectiveAccess'
import {
  MAX_PRODUCTION_ITEMS,
  TEST_ONLY_PRODUCTION_ACCESS_KEY,
  type ProductionContext,
  type ProductionFailureStatus,
  type ProductionReadRequest,
  type ProductionSource,
  type SceneFilters,
  type SceneProjection,
} from './types'

export function isProductionIdentity(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0 && !Array.from(value).some(character => {
    const code = character.charCodeAt(0)
    return /\s/u.test(character) || code <= 0x1f || code === 0x7f
  })
}

const identity = z.string().refine(isProductionIdentity)
const nonEmptyText = z.string().min(1)
const scopeSchema = z.object({
  principalId: identity.nullable(), tenantId: identity.nullable(), sessionId: identity,
  workspaceId: identity, projectId: identity,
}).strict()
const projectedFields = {
  id: identity, projectId: identity, name: z.string().min(1).nullable().optional(),
  description: z.string().nullable().optional(), status: nonEmptyText.optional(), version: identity.optional(),
}
const sceneSchema = z.object({ kind: z.literal('SCENE'), ...projectedFields }).strict()
const referenceBase = {
  kind: z.enum(['PROJECT', 'MEDIA_ASSET', 'ARTIFACT', 'TIMELINE', 'REVISION', 'RENDER', 'WORKFLOW']),
  id: identity, label: z.string().min(1).optional(), projectId: identity,
}
const referenceSchema = z.discriminatedUnion('availability', [
  z.object({ ...referenceBase, availability: z.literal('SUPPORTED') }).strict(),
  z.object({ ...referenceBase, availability: z.literal('UNSUPPORTED'), explanation: nonEmptyText }).strict(),
])
const shotSchema = z.object({ kind: z.literal('SHOT'), ...projectedFields, references: z.array(referenceSchema).max(MAX_PRODUCTION_ITEMS).optional() }).strict()
const relationSchema = z.object({ sceneId: identity, shotId: identity }).strict()
const envelope = { scope: scopeSchema, requestId: identity }
const successSchema = z.object({
  ...envelope, status: z.literal('ok'),
  scenes: z.array(sceneSchema).max(MAX_PRODUCTION_ITEMS),
  shots: z.array(shotSchema).max(MAX_PRODUCTION_ITEMS),
  relations: z.array(relationSchema).max(MAX_PRODUCTION_ITEMS),
  boundary: z.object({
    kind: z.literal('project-production-snapshot'), completeness: z.enum(['complete', 'bounded']),
    limit: z.number().int().positive().max(MAX_PRODUCTION_ITEMS), version: identity,
  }).strict(),
}).strict()
const failureSchema = z.object({
  ...envelope, status: z.enum(['unavailable', 'denied', 'unknown', 'unsupported', 'error', 'stale']),
  explanation: z.string().optional(),
}).strict()

export type ProductionSnapshot = z.infer<typeof successSchema>
export type ProductionFailure = z.infer<typeof failureSchema>

export function productionScopeKey(scope: ProductionContext | ProductionSource['scope']): string {
  return JSON.stringify([scope.principalId, scope.tenantId, scope.sessionId, scope.workspaceId, scope.projectId])
}

export function productionContextKey(context: ProductionContext): string {
  return JSON.stringify([
    productionScopeKey(context), context.access.key, context.access.status, context.access.reasonCode,
    context.access.explanation, context.access.source, context.access.observedAt ?? null,
    context.access.factors.capability, context.access.factors.runtime, context.access.factors.entitlement,
    context.access.factors.policy, context.access.factors.quota,
  ])
}

export function productionAccessDisposition(context: ProductionContext): 'ready' | 'unavailable' | 'denied' | 'unknown' {
  if (!productionScopeIsValid(context)) return 'unknown'
  if (isAvailable(context.access)) return 'ready'
  if (context.access.status === 'POLICY_DENIED' || context.access.status === 'NOT_ENTITLED') return 'denied'
  if (context.access.status === 'UNKNOWN_FAIL_CLOSED') return 'unknown'
  return 'unavailable'
}

export function productionScopeIsValid(scope: ProductionSource['scope']): boolean {
  return isProductionIdentity(scope.principalId) && isProductionIdentity(scope.tenantId)
    && isProductionIdentity(scope.sessionId) && isProductionIdentity(scope.workspaceId)
    && isProductionIdentity(scope.projectId)
}

function hasExpectedProjection(source: ProductionSource): boolean {
  if (source.adapter.origin === 'real') {
    return source.readAccessBinding.kind === 'HOST_AGREED'
      && isProductionIdentity(source.readAccessBinding.accessKey)
      && source.readAccessBinding.accessKey !== 'surface.production.view'
      && source.access.key === source.readAccessBinding.accessKey
      && source.access.source === 'SERVER'
  }
  if (source.adapter.origin === 'simulated') {
    return source.readAccessBinding.kind === 'TEST_ONLY_UNAGREED'
      && source.readAccessBinding.accessKey === TEST_ONLY_PRODUCTION_ACCESS_KEY
      && source.access.key === TEST_ONLY_PRODUCTION_ACCESS_KEY
      && source.access.source === 'DEVELOPMENT_FAIL_CLOSED'
  }
  return false
}

export function productionSourceDisposition(source: ProductionSource, expected: Pick<ProductionSource['scope'], 'workspaceId' | 'projectId'>): 'ready' | 'unavailable' | 'denied' | 'unknown' {
  if (source.adapter.origin === 'unavailable') return 'unavailable'
  if (!productionScopeIsValid(source.scope) || !isProductionIdentity(expected.workspaceId) || !isProductionIdentity(expected.projectId)) return 'unknown'
  if (source.scope.workspaceId !== expected.workspaceId || source.scope.projectId !== expected.projectId) return 'unknown'
  if (!hasExpectedProjection(source)) return 'unknown'
  return productionAccessDisposition({ ...source.scope, access: source.access })
}

export function productionPresentationOrigin(source: ProductionSource): ProductionSource['adapter']['origin'] {
  return source.adapter.origin !== 'unavailable' && hasExpectedProjection(source) ? source.adapter.origin : 'unavailable'
}

export function productionAccessExplanation(source: ProductionSource): string | null {
  return hasExpectedProjection(source) && productionScopeIsValid(source.scope) ? source.access.explanation : null
}

export function parseProductionSnapshot(input: unknown, request: ProductionReadRequest): ProductionSnapshot | ProductionFailure {
  const result = z.union([successSchema, failureSchema]).parse(input)
  if (productionScopeKey(result.scope) !== productionScopeKey(request.scope) || result.requestId !== request.requestId) throw new Error('Invalid Production snapshot receipt ownership')
  if (result.status !== 'ok') return result
  const sceneIds = result.scenes.map(scene => scene.id)
  const shotIds = result.shots.map(shot => shot.id)
  const allIds = [...sceneIds, ...shotIds]
  const relationKeys = result.relations.map(relation => JSON.stringify([relation.sceneId, relation.shotId]))
  const relationCountByShot = new Map<string, number>()
  for (const relation of result.relations) relationCountByShot.set(relation.shotId, (relationCountByShot.get(relation.shotId) ?? 0) + 1)
  const invalidReferences = result.shots.some(shot => {
    const references = shot.references ?? []
    const keys = references.map(reference => JSON.stringify([reference.kind, reference.id]))
    return new Set(keys).size !== keys.length || references.some(reference => reference.projectId !== request.scope.projectId)
  })
  if (new Set(allIds).size !== allIds.length
    || new Set(relationKeys).size !== relationKeys.length
    || result.scenes.length > result.boundary.limit || result.shots.length > result.boundary.limit
    || result.scenes.some(scene => scene.projectId !== request.scope.projectId)
    || result.shots.some(shot => shot.projectId !== request.scope.projectId)
    || result.relations.some(relation => !sceneIds.includes(relation.sceneId) || !shotIds.includes(relation.shotId))
    || shotIds.some(shotId => relationCountByShot.get(shotId) !== 1) || invalidReferences) {
    throw new Error('Invalid single-Project Scene and Shot snapshot')
  }
  return result
}

function compareText(left: string, right: string): number { return left < right ? -1 : left > right ? 1 : 0 }
function sceneSortName(scene: SceneProjection): string { return scene.name ?? scene.id }

export function selectScenes(scenes: readonly SceneProjection[], filters: SceneFilters): SceneProjection[] {
  const query = filters.query.toLocaleLowerCase()
  const direction = filters.order === 'name-desc' ? -1 : 1
  return scenes
    .filter(scene => (!query || `${scene.id}\n${scene.name ?? ''}\n${scene.description ?? ''}`.toLocaleLowerCase().includes(query)) && (!filters.status || scene.status === filters.status))
    .sort((left, right) => direction * compareText(sceneSortName(left), sceneSortName(right)) || compareText(left.id, right.id))
}

export function sceneStatusValues(scenes: readonly SceneProjection[]): string[] {
  return [...new Set(scenes.flatMap(scene => scene.status === undefined ? [] : [scene.status]))].sort(compareText)
}

export function productionFailureStatuses(): readonly ProductionFailureStatus[] {
  return ['unavailable', 'denied', 'unknown', 'unsupported', 'error', 'stale']
}
