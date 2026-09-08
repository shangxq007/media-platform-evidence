import type { EffectiveAccessEntry } from '../../foundation/effectiveAccess'
import type { CrossSurfaceReference } from '../../foundation/references'

export const UNAGREED_PRODUCTION_QUERY_LABEL = 'frontend.unagreed.production.scene-shot.read' as const
export const TEST_ONLY_PRODUCTION_ACCESS_KEY = 'test-only.frontend-unagreed.production.scene-shot.read' as const
export const MAX_PRODUCTION_ITEMS = 200 as const

export interface ProductionScope {
  readonly principalId: string | null
  readonly tenantId: string | null
  readonly sessionId: string
  readonly workspaceId: string
  readonly projectId: string
}

export interface ProductionContext extends ProductionScope {
  readonly access: EffectiveAccessEntry
}

export interface ProductionEntityProjection {
  readonly id: string
  readonly projectId: string
  readonly name?: string | null
  readonly description?: string | null
  readonly status?: string
  readonly version?: string
}

export interface SceneProjection extends ProductionEntityProjection {
  readonly kind: 'SCENE'
}

export type ProductionReference = CrossSurfaceReference & {
  readonly projectId: string
  readonly availability: 'SUPPORTED' | 'UNSUPPORTED'
  readonly explanation?: string
}

export interface ShotProjection extends ProductionEntityProjection {
  readonly kind: 'SHOT'
  readonly references?: readonly ProductionReference[]
}

export interface SceneShotRelation {
  readonly sceneId: string
  readonly shotId: string
}

export interface ProductionBoundary {
  readonly kind: 'project-production-snapshot'
  readonly completeness: 'complete' | 'bounded'
  readonly limit: number
  readonly version: string
}

export interface ProductionReadRequest {
  readonly scope: ProductionScope
  readonly requestId: string
}

export type ProductionFailureStatus = 'unavailable' | 'denied' | 'unknown' | 'unsupported' | 'error' | 'stale'

export interface ProductionAdapter {
  readonly origin: 'real' | 'simulated' | 'unavailable'
  readProject(request: ProductionReadRequest, signal: AbortSignal): Promise<unknown>
}

export type ProductionReadAccessBinding =
  | { readonly kind: 'HOST_AGREED'; readonly accessKey: string }
  | { readonly kind: 'TEST_ONLY_UNAGREED'; readonly accessKey: typeof TEST_ONLY_PRODUCTION_ACCESS_KEY }
  | { readonly kind: 'UNAVAILABLE'; readonly label: typeof UNAGREED_PRODUCTION_QUERY_LABEL }

export interface ProductionSource {
  readonly scope: ProductionScope
  readonly access: EffectiveAccessEntry
  readonly readAccessBinding: ProductionReadAccessBinding
  readonly adapter: ProductionAdapter
}

export type SceneOrder = 'name-asc' | 'name-desc'
export interface SceneFilters {
  readonly query: string
  readonly status: string
  readonly order: SceneOrder
}
