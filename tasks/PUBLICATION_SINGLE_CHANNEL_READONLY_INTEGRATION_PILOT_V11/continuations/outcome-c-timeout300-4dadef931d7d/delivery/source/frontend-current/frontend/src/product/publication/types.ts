import type { EffectiveAccessCatalog } from '../../foundation/effectiveAccess'

/** FRONTEND_FIXTURE_PROPOSAL; REAL_BACKEND_CONTRACT_NOT_ESTABLISHED. */
export const LIST_KEY = 'test-only.publication.list'
export const contentKey = (id: string) => `test-only.publication.content:${id}`
export const artifactKey = (id: string) => `test-only.publication.artifact:${id}`

export interface PublicationScope {
  principalId: string
  tenantId: string | null
  sessionId: string
  workspaceId: string
  projectId: string
  sourceId: string
}
export interface PublicationRequest {
  scope: PublicationScope
  requestId: string
  query: { kind: 'project-publication-snapshot'; limit: 200 }
}
export interface PublicationSource {
  scope: PublicationScope
  owner: object
  access: EffectiveAccessCatalog
  adapter: { origin: 'isolated-fixture'; read(request: PublicationRequest, signal: AbortSignal): Promise<unknown> }
}

export const publicationDisplayStatuses = ['draft', 'scheduled', 'publishing', 'published', 'failed', 'cancelled', 'unknown'] as const
export type PublicationDisplayStatus = typeof publicationDisplayStatuses[number]
export type RelationAvailability = 'supplied' | 'known-empty' | 'unavailable' | 'restricted' | 'pending-core-contract'
export interface PublicationRelations {
  artifacts: RelationAvailability
  attempts: RelationAvailability
  externalPublications: RelationAvailability
}
export interface PublicationFilters { query: string; account: string; status: string; order: 'asc' | 'desc' }
export interface PublicationAccount { id: string; name: string; platform: string }
export interface PublicationPlan {
  id: string; projectId: string; accountId: string; status: PublicationDisplayStatus
  title?: string; summary?: string; copyVersion?: string; artifactIds?: string[]
  timeField: 'scheduledAt' | 'publishedAt' | 'unscheduled' | 'unknown'
  scheduledAt?: string | null; publishedAt?: string | null
}
export interface PublicationArtifact { id: string; projectId: string; name?: string; mediaType?: string; version?: string }
export interface PublicationAttempt {
  id: string; planId: string; accountId: string; status: PublicationDisplayStatus; attemptedAt?: string | null; failureSummary?: string
}
export interface ExternalPublication {
  id: string; attemptId: string; planId: string; accountId: string; status: PublicationDisplayStatus; publishedAt?: string | null
}
export interface PublicationSnapshot {
  status: 'ok'; contract: 'fixture-only-publication-graph-v1'; version: string; completeness: 'complete' | 'bounded' | 'partial'; fetchedAt?: string | null
  relations: PublicationRelations
  accounts: PublicationAccount[]; plans: PublicationPlan[]; artifacts?: PublicationArtifact[]
  attempts?: PublicationAttempt[]; externalPublications?: ExternalPublication[]
}
export type PublicationResult = PublicationSnapshot | { status: 'unavailable' | 'restricted' | 'error' | 'invalid' }

/** Owner-local external observations are deliberately not PublicationPlan records. */
export interface ExternalObservationRequest {
  requestId: string
  binding: { scope: PublicationScope; ownerId: string }
  window: { semantics: 'half-open'; startInclusive: string; endExclusive: string }
}
export interface ScopedExternalReferences { provider: string; instance: string; account: string; post: string }
export interface ExternalObservation {
  kind: 'external-publication-observation'
  externalReferences: ScopedExternalReferences
  coreBinding: { status: 'PENDING_CORE_CONTRACT' }
  displayStatus: PublicationDisplayStatus
  statusMapping: 'bounded-display-only' | 'unmapped'
  timeField: 'scheduledAt' | 'unscheduled' | 'unknown'
  scheduledAt?: string
  summary?: string
  relationships: {
    project: { status: 'PENDING_CORE_CONTRACT' }
    artifacts: { status: 'PENDING_CORE_CONTRACT' }
    attempts: { status: 'PENDING_CORE_CONTRACT' }
    externalOutcomes: { status: 'PENDING_CORE_CONTRACT' }
  }
}
export interface ExternalObservationSnapshot {
  status: 'ok'
  contract: 'external-publication-observation-v2'
  access: { authority: 'owner-local-single-user'; scope: 'narrower-than-platform-effective-access'; list: true; content: boolean }
  window: ExternalObservationRequest['window']
  completeness: 'bounded' | 'partial'
  observedAt: string
  observations: ExternalObservation[]
}
export type ExternalObservationResult = ExternalObservationSnapshot | { status: 'restricted' | 'invalid' }
