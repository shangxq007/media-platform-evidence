import type { EffectiveAccessCatalog } from '../../foundation/effectiveAccess'

/** FRONTEND_CONSUMPTION_PROPOSAL; REAL_BACKEND_CONTRACT_NOT_ESTABLISHED. */
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
  adapter: { origin: 'isolated-verification'; read(request: PublicationRequest, signal: AbortSignal): Promise<unknown> }
}
export interface PublicationFilters { query: string; account: string; status: string; order: 'asc' | 'desc' }
export interface PublicationAccount { id: string; name: string; platform: string }
export interface PublicationPlan {
  id: string; projectId: string; accountId: string; status: string
  title?: string; summary?: string; copyVersion?: string; artifactIds: string[]
  timeField: 'scheduledAt' | 'publishedAt' | 'unscheduled' | 'unknown'
  scheduledAt?: string | null; publishedAt?: string | null
}
export interface PublicationArtifact { id: string; projectId: string; name?: string; mediaType?: string; version?: string }
export interface PublicationAttempt {
  id: string; planId: string; accountId: string; status: string; attemptedAt?: string | null; failureSummary?: string
}
export interface ExternalPublication {
  id: string; attemptId: string; planId: string; accountId: string; status: string; publishedAt?: string | null
}
export interface PublicationSnapshot {
  status: 'ok'; version: string; completeness: 'complete' | 'bounded' | 'partial'; fetchedAt?: string | null
  accounts: PublicationAccount[]; plans: PublicationPlan[]; artifacts: PublicationArtifact[]
  attempts: PublicationAttempt[]; externalPublications: ExternalPublication[]
}
export type PublicationResult = PublicationSnapshot | { status: 'unavailable' | 'restricted' | 'error' | 'invalid' }
