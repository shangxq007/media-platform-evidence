import type { EffectiveAccessEntry, EffectiveAccessStatus } from '../../foundation/effectiveAccess'
import { productionAccessDisposition, productionScopeIsValid, productionScopeKey } from './model'
import {
  MAX_PRODUCTION_ITEMS, TEST_ONLY_PRODUCTION_ACCESS_KEY, UNAGREED_PRODUCTION_QUERY_LABEL,
  type ProductionContext, type ProductionFailureStatus, type ProductionScope, type ProductionSource,
  type SceneProjection, type SceneShotRelation, type ShotProjection,
} from './types'

export interface SimulatedProductionOptions {
  readonly scope: ProductionScope
  readonly accessStatus?: EffectiveAccessStatus
  readonly empty?: boolean
  readonly limit?: number
  readonly failure?: ProductionFailureStatus
}

function assertExplicitScope(scope: ProductionScope): void {
  if (!productionScopeIsValid(scope)) throw new Error('The simulated Production source requires an explicitly supplied complete, well-formed identity and scope')
}

function simulatedAccess(status: EffectiveAccessStatus): EffectiveAccessEntry {
  return {
    key: TEST_ONLY_PRODUCTION_ACCESS_KEY, status, reasonCode: `SIMULATED_${status}`,
    explanation: 'Simulated Production access projection; never valid for a real resource.',
    factors: {
      capability: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN', runtime: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      entitlement: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN', policy: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
      quota: status === 'AVAILABLE' ? 'SATISFIED' : 'UNKNOWN',
    }, source: 'DEVELOPMENT_FAIL_CLOSED',
  }
}

export function createSimulatedProductionSource(options: SimulatedProductionOptions): ProductionSource {
  assertExplicitScope(options.scope)
  const scope = { ...options.scope }
  const access = simulatedAccess(options.accessStatus ?? 'AVAILABLE')
  const scenes: SceneProjection[] = options.empty ? [] : [
    { kind: 'SCENE', id: 'scene-courtyard', projectId: scope.projectId, name: 'Courtyard <scene>', description: 'Exterior gathering', status: 'APPROVED', version: 'courtyard-v4' },
    { kind: 'SCENE', id: 'scene-studio', projectId: scope.projectId, name: 'Studio', description: 'Interior 原文', status: 'DRAFT?', version: 'studio-v1' },
    { kind: 'SCENE', id: 'scene-silent', projectId: scope.projectId, name: 'Silent scene' },
  ]
  const shots: ShotProjection[] = options.empty ? [] : [
    { kind: 'SHOT', id: 'shot-arrival', projectId: scope.projectId, name: 'Arrival shot', description: 'Wide arrival', status: 'READY?', version: 'arrival-v2', references: [{ kind: 'RENDER', id: 'render-arrival', label: 'Arrival render', projectId: scope.projectId, availability: 'SUPPORTED' }] },
    { kind: 'SHOT', id: 'shot-courtyard-detail', projectId: scope.projectId, description: '', status: 'DRAFT?', references: [{ kind: 'WORKFLOW', id: 'workflow-courtyard', projectId: scope.projectId, availability: 'UNSUPPORTED', explanation: 'No safe Workflow inspection route is supplied by this fixture.' }] },
    { kind: 'SHOT', id: 'shot-studio-insert', projectId: scope.projectId, name: 'Studio insert', description: '<b>literal supplied detail</b>' },
  ]
  const relations: SceneShotRelation[] = options.empty ? [] : [
    { sceneId: 'scene-courtyard', shotId: 'shot-arrival' },
    { sceneId: 'scene-courtyard', shotId: 'shot-courtyard-detail' },
    { sceneId: 'scene-studio', shotId: 'shot-studio-insert' },
  ]
  const limit = Math.min(MAX_PRODUCTION_ITEMS, Math.max(1, options.limit ?? MAX_PRODUCTION_ITEMS))
  const visibleScenes = scenes.slice(0, limit)
  const visibleSceneIds = new Set(visibleScenes.map(scene => scene.id))
  const visibleShots = shots.filter(shot => relations.some(relation => relation.shotId === shot.id && visibleSceneIds.has(relation.sceneId))).slice(0, limit)
  const visibleShotIds = new Set(visibleShots.map(shot => shot.id))
  const visibleRelations = relations.filter(relation => visibleSceneIds.has(relation.sceneId) && visibleShotIds.has(relation.shotId))
  return {
    scope, access, readAccessBinding: { kind: 'TEST_ONLY_UNAGREED', accessKey: TEST_ONLY_PRODUCTION_ACCESS_KEY },
    adapter: {
      origin: 'simulated',
      async readProject(request, signal) {
        const envelope = { scope: request.scope, requestId: request.requestId }
        if (signal.aborted) return { ...envelope, status: 'error' }
        if (productionScopeKey(request.scope) !== productionScopeKey(scope)) return { ...envelope, status: 'denied' }
        const disposition = productionAccessDisposition({ ...scope, access } as ProductionContext)
        if (disposition !== 'ready') return { ...envelope, status: disposition }
        if (options.failure) return { ...envelope, status: options.failure, explanation: 'Simulated opaque Production source result.' }
        return {
          ...envelope, status: 'ok', scenes: visibleScenes.map(scene => ({ ...scene })),
          shots: visibleShots.map(shot => ({ ...shot, references: shot.references?.map(reference => ({ ...reference })) })),
          relations: visibleRelations.map(relation => ({ ...relation })),
          boundary: { kind: 'project-production-snapshot', completeness: options.limit === undefined ? 'complete' : 'bounded', limit, version: 'simulated-production-projection-v1' },
        }
      },
    },
  }
}

export function unavailableProductionSource(expected: { workspaceId: string; projectId: string }): ProductionSource {
  const scope: ProductionScope = { principalId: null, tenantId: null, sessionId: 'unconfigured', workspaceId: expected.workspaceId, projectId: expected.projectId }
  return {
    scope,
    access: {
      key: UNAGREED_PRODUCTION_QUERY_LABEL, status: 'UNKNOWN_FAIL_CLOSED', reasonCode: 'EFFECTIVE_ACCESS_PROJECTION_MISSING',
      explanation: 'Effective access is not available from a connected Production source.',
      factors: { capability: 'UNKNOWN', runtime: 'UNKNOWN', entitlement: 'UNKNOWN', policy: 'UNKNOWN', quota: 'UNKNOWN' },
      source: 'MISSING_SERVER_PROJECTION',
    },
    readAccessBinding: { kind: 'UNAVAILABLE', label: UNAGREED_PRODUCTION_QUERY_LABEL },
    adapter: { origin: 'unavailable', async readProject(request) { return { status: 'unavailable', scope: request.scope, requestId: request.requestId } } },
  }
}
