// Explicit test-only data; never imported by the ordinary product route.
import { unknownAccess } from '../../foundation/effectiveAccess'
import { LIST_KEY, contentKey, artifactKey, type PublicationRequest, type PublicationSource } from './types'
export function grant(key: string) {
  return { ...unknownAccess(key), source: 'SERVER' as const, status: 'AVAILABLE' as const, factors: { capability: 'SATISFIED' as const, runtime: 'NOT_APPLICABLE' as const, entitlement: 'SATISFIED' as const, policy: 'SATISFIED' as const, quota: 'NOT_APPLICABLE' as const } }
}
export const scope = { principalId: 'person', tenantId: 'tenant', sessionId: 'session', workspaceId: 'w', projectId: 'p', sourceId: 'source' }
export const request: PublicationRequest = { scope, requestId: 'r', query: { kind: 'project-publication-snapshot', limit: 200 } }
export function receipt(r: PublicationRequest = request, changes: Record<string, unknown> = {}) {
  return { ...r, status: 'ok', version: 'v1', completeness: 'complete', fetchedAt: '2024-03-10T08:00:00Z',
    accounts: [{ id: 'a', name: 'Studio North', platform: 'Example' }, { id: 'b', name: 'Studio South', platform: 'Example' }],
    plans: [
      { id: 'one', projectId: 'p', accountId: 'a', status: 'queued', title: 'Opening story', summary: 'Permitted summary', copyVersion: 'copy-v1', artifactIds: ['output'], timeField: 'scheduledAt', scheduledAt: '2024-03-10T07:30:00Z' },
      { id: 'two', projectId: 'p', accountId: 'b', status: 'alien-state', title: 'Second story', artifactIds: [], timeField: 'publishedAt', publishedAt: '2024-03-10T07:30:00Z' },
    ], artifacts: [{ id: 'output', projectId: 'p', name: 'Master', mediaType: 'video', version: 'v2' }],
    attempts: [{ id: 'try1', planId: 'one', accountId: 'a', status: 'failed', failureSummary: 'Delivery rejected', attemptedAt: '2024-03-09T23:00:00Z' }, { id: 'try2', planId: 'one', accountId: 'a', status: 'unknown' }],
    externalPublications: [{ id: 'external1', attemptId: 'try2', planId: 'one', accountId: 'a', status: 'unknown', url: 'javascript:SECRET_URL' }], ...changes }
}
export function source(read: PublicationSource['adapter']['read'] = async r => receipt(r)): PublicationSource {
  return { scope, owner: {}, adapter: { origin: 'isolated-verification', read }, access: { [LIST_KEY]: grant(LIST_KEY), [contentKey('one')]: grant(contentKey('one')), [contentKey('two')]: grant(contentKey('two')), [artifactKey('output')]: grant(artifactKey('output')) } }
}

