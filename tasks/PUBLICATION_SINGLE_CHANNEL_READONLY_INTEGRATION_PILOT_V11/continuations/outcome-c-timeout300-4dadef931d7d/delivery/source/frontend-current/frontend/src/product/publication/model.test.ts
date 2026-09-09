import { describe, expect, it } from 'vitest'
import { absoluteInstant, calendarDay, monthDays, shiftMonth, parsePublication, parseExternalObservations, filterPlans, publicationAccess, accessFingerprint } from './model'
import { LIST_KEY, type ExternalObservationRequest, type PublicationRequest, type PublicationSource } from './types'

import { grant, scope, request, receipt, source } from './testing'

describe('publication time and scoped consumption proposal', () => {
  it('accepts strict offset instants and rejects invalid, missing, date-only and offsetless values', () => {
    expect(absoluteInstant('2024-02-29T23:59:59.125+05:30')).toBe(Date.parse('2024-02-29T18:29:59.125Z'))
    for (const value of [undefined, null, '', '2024-02-30T12:00:00Z', '2023-02-29T00:00:00Z', '2024-03-10', '2024-03-10T12:00:00', '2024-03-10T24:00:00Z', '2024-03-10T12:00:00+25:00']) expect(absoluteInstant(value)).toBeNull()
  })
  it('calculates Gregorian month ends, leap years and year navigation without 24h stepping', () => {
    expect(monthDays('2024-02')).toHaveLength(29)
    expect(monthDays('2100-02')).toHaveLength(28)
    expect(monthDays('2000-02')[28]).toBe('2000-02-29')
    expect(shiftMonth('2024-12', 1)).toBe('2025-01')
    expect(shiftMonth('2024-01', -1)).toBe('2023-12')
    expect(monthDays('2024-13')).toEqual([])
  })
  it('groups instants across midnight and both DST changes using the selected display timezone', () => {
    expect(calendarDay('2024-03-01T00:30:00Z', 'America/Los_Angeles')).toBe('2024-02-29')
    expect(calendarDay('2024-03-10T06:59:00Z', 'America/New_York')).toBe('2024-03-10')
    expect(calendarDay('2024-03-10T07:01:00Z', 'America/New_York')).toBe('2024-03-10')
    expect(calendarDay('2024-11-03T05:30:00Z', 'America/New_York')).toBe(calendarDay('2024-11-03T06:30:00Z', 'America/New_York'))
    expect(calendarDay('2024-03-10', 'UTC')).toBeNull()
    expect(calendarDay('2024-03-10T00:00:00Z', 'bad-zone')).toBeNull()
  })
  it('requires host bound access and does not authorize a source allowed boolean', () => {
    const s = source(); expect(publicationAccess(s)).toBe(true)
    expect(publicationAccess({ ...s, access: {} })).toBe(false)
    expect(publicationAccess({ ...s, access: { [LIST_KEY]: { ...grant('wrong'), allowed: true } } } as PublicationSource)).toBe(false)
    expect(publicationAccess({ ...s, scope: { ...scope, sessionId: '' } })).toBe(false)
    expect(accessFingerprint(s.access)).toBe(accessFingerprint({ ...s.access, [LIST_KEY]: { ...grant(LIST_KEY), observedAt: 'later', explanation: 'new text' } }))
  })
  it('preserves distinct fixture relationships while normalizing unknown statuses for display', () => {
    const parsed = parsePublication(receipt(), request, source().access)
    expect(parsed.status).toBe('ok')
    if (parsed.status !== 'ok') throw Error('missing snapshot')
    expect(parsed.accounts.map(a => a.id)).toEqual(['a', 'b'])
    expect(parsed.attempts?.map(a => a.id)).toEqual(['try1', 'try2'])
    expect(parsed.externalPublications?.[0]).toMatchObject({ id: 'external1', attemptId: 'try2' })
    expect(parsed.plans.map(plan => plan.status)).toEqual(['scheduled', 'unknown'])
    expect(JSON.stringify(parsed)).not.toMatch(/SECRET_URL|alien-state/)
  })
  it('rejects mismatched receipts, duplicate identities and inferred or cross-account relationships', () => {
    const bad = [receipt({ ...request, requestId: 'old' }), receipt({ ...request, scope: { ...scope, projectId: 'other' } }), receipt({ ...request, query: { ...request.query, limit: 100 } } as unknown as PublicationRequest), receipt(request, { completeness: 'unknown' }), receipt(request, { accounts: [{ id: 'a', name: 'A', platform: 'X' }, { id: 'a', name: 'B', platform: 'X' }] }), receipt(request, { attempts: [{ id: 't', planId: 'one', accountId: 'b', status: 'ok' }] }), receipt(request, { externalPublications: [{ id: 'e', attemptId: 'absent', planId: 'one', accountId: 'a', status: 'ok' }] })]
    for (const input of bad) expect(parsePublication(input, request, source().access).status).toBe('invalid')
  })
  it('strips protected copy, artifact metadata and failure summaries before Selection or DOM consumption', () => {
    const raw = receipt(); raw.plans[0].title = 'SECRET_COPY'; raw.artifacts[0].id = 'SECRET_ARTIFACT'; raw.plans[0].artifactIds = ['SECRET_ARTIFACT']; raw.attempts[0].failureSummary = 'SECRET_FAILURE'
    const parsed = parsePublication(raw, request, { [LIST_KEY]: grant(LIST_KEY) })
    expect(parsed.status).toBe('ok')
    expect(JSON.stringify(parsed)).not.toMatch(/SECRET_|copy-v1|Permitted summary|Master/)
    if (parsed.status !== 'ok') throw Error('missing snapshot')
    expect(parsed.relations.artifacts).toBe('restricted')
    expect(parsed.artifacts).toBeUndefined()
    expect(parsed.plans.every(plan => plan.artifactIds === undefined)).toBe(true)
  })
  it('distinguishes unavailable relationships from authoritative empty fixture relations', () => {
    const raw = receipt()
    const plans = raw.plans.map(({ artifactIds: _artifactIds, ...plan }) => plan)
    const pending = parsePublication(receipt(request, { relations: { artifacts: 'pending-core-contract', attempts: 'unavailable', externalPublications: 'restricted' }, artifacts: undefined, attempts: undefined, externalPublications: undefined, plans }), request, source().access)
    expect(pending.status).toBe('ok')
    if (pending.status !== 'ok') throw Error('missing snapshot')
    expect(pending.relations).toEqual({ artifacts: 'pending-core-contract', attempts: 'unavailable', externalPublications: 'restricted' })
    expect(pending.artifacts).toBeUndefined()
    expect(parsePublication(receipt(request, { relations: { ...raw.relations, artifacts: 'unavailable' } }), request, source().access).status).toBe('invalid')
    expect(parsePublication(receipt(request, { relations: { artifacts: 'known-empty', attempts: 'supplied', externalPublications: 'supplied' }, artifacts: [], plans }), request, source().access).status).toBe('ok')
  })
  it('filters supplied permitted content by stable account ID and sorts explicit time with ID ties', () => {
    const parsed = parsePublication(receipt(), request, source().access)
    if (parsed.status !== 'ok') throw Error('missing snapshot')
    expect(filterPlans(parsed, { query: 'story', account: 'b', status: '', order: 'asc' }).map(p => p.id)).toEqual(['two'])
    expect(filterPlans(parsed, { query: '', account: '', status: '', order: 'desc' }).map(p => p.id)).toEqual(['one', 'two'])
    expect(filterPlans(parsed, { query: '', account: '', status: 'unknown', order: 'asc' }).map(p => p.id)).toEqual(['two'])
  })
})

describe('unbound external observation preparation', () => {
  const externalRequest: ExternalObservationRequest = {
    requestId: 'request1', binding: { scope, ownerId: 'host1' },
    window: { semantics: 'half-open', startInclusive: '2026-09-01T00:00:00Z', endExclusive: '2026-10-01T00:00:00Z' },
  }
  function externalReceipt(changes: Record<string, unknown> = {}) {
    return {
      contract: 'external-publication-observation-v2', status: 'ok', requestId: 'request1', binding: externalRequest.binding,
      access: { authority: 'owner-local-single-user', scope: 'narrower-than-platform-effective-access', list: true, content: false },
      providerVersion: 'v2.23.0', providerSourceCommit: '1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9', evidence: 'pure-synthetic-projection',
      window: { ...externalRequest.window, upstreamEndInclusive: '2026-09-30T23:59:59.999Z' }, observedAt: '2026-09-09T13:00:00Z', completeness: 'bounded', omissions: {},
      externalAccount: { externalReferences: { provider: 'postiz', instance: 'instance1', account: 'account1' }, label: 'Synthetic account', providerLabel: 'synthetic', coreBinding: { status: 'PENDING_CORE_CONTRACT' } },
      observations: [{
        kind: 'external-publication-observation', externalReferences: { provider: 'postiz', instance: 'instance1', account: 'account1', post: 'post1' },
        coreBinding: { status: 'PENDING_CORE_CONTRACT' }, displayStatus: 'unknown', statusMapping: 'unmapped', timeField: 'unknown',
        relationships: { project: { status: 'PENDING_CORE_CONTRACT' }, artifacts: { status: 'PENDING_CORE_CONTRACT' }, attempts: { status: 'PENDING_CORE_CONTRACT' }, externalOutcomes: { status: 'PENDING_CORE_CONTRACT' } },
      }], ...changes,
    }
  }
  it('keeps provider/instance/account/post refs scoped and never promotes observations to plans', () => {
    const parsed = parseExternalObservations(externalReceipt(), externalRequest)
    expect(parsed.status).toBe('ok')
    if (parsed.status !== 'ok') throw Error('missing observations')
    expect(parsed.access.scope).toBe('narrower-than-platform-effective-access')
    expect(parsed.observations[0].externalReferences).toEqual({ provider: 'postiz', instance: 'instance1', account: 'account1', post: 'post1' })
    expect(parsed.observations[0].coreBinding.status).toBe('PENDING_CORE_CONTRACT')
    expect(JSON.stringify(parsed)).not.toMatch(/projectId|planId|attemptId|publishedAt|rawStatus/)
  })
  it('rejects unscoped, duplicated, injected raw-status or mismatched-window observations', () => {
    const raw = externalReceipt()
    const observations = raw.observations
    expect(parseExternalObservations(externalReceipt({ observations: [...observations, observations[0]] }), externalRequest).status).toBe('invalid')
    expect(parseExternalObservations(externalReceipt({ observations: [{ ...observations[0], rawStatus: 'PRIVATE_PROVIDER_VALUE' }] }), externalRequest).status).toBe('invalid')
    expect(parseExternalObservations(externalReceipt({ window: { ...raw.window, endExclusive: '2026-10-02T00:00:00Z' } }), externalRequest).status).toBe('invalid')
  })
})
