import { describe, expect, it, vi } from 'vitest'
import type { EffectiveAccessEntry, EffectiveAccessStatus } from '../../foundation/effectiveAccess'
import {
  parseProductionSnapshot,
  productionAccessDisposition,
  productionContextKey,
  productionPresentationOrigin,
  productionSourceDisposition,
  sceneStatusValues,
  selectScenes,
} from './model'
import { createSimulatedProductionSource, unavailableProductionSource } from './simulatedSource'
import {
  type ProductionReadRequest,
  type ProductionSource,
  type SceneProjection,
} from './types'

const TEST_HOST_ACCESS_KEY = 'test-host-agreed.production.read'
function access(status: EffectiveAccessStatus, key = TEST_HOST_ACCESS_KEY): EffectiveAccessEntry {
  return {
    key,
    status,
    reasonCode: `TEST_${status}`,
    explanation: '<server-owned opaque explanation 原文>',
    factors: { capability: 'UNKNOWN', runtime: 'UNKNOWN', entitlement: 'UNKNOWN', policy: 'UNKNOWN', quota: 'UNKNOWN' },
    source: 'SERVER',
  }
}

const scope = { principalId: 'principal-1', tenantId: 'tenant-1', sessionId: 'session-1', workspaceId: 'workspace-1', projectId: 'project-1' }
const request: ProductionReadRequest = { scope, requestId: 'request-1' }
const scenes: SceneProjection[] = [
  { kind: 'SCENE', id: 'scene-z', projectId: scope.projectId, name: 'Zulu <scene>', description: 'Exterior 原文', status: 'READY?' },
  { kind: 'SCENE', id: 'scene-b', projectId: scope.projectId, name: 'Alpha', description: null, status: 'DRAFT' },
  { kind: 'SCENE', id: 'scene-a', projectId: scope.projectId, name: 'Alpha', version: 'scene-v1' },
]
const validReceipt = () => ({
  status: 'ok', scope, requestId: request.requestId,
  scenes,
  shots: [
    { kind: 'SHOT', id: 'shot-1', projectId: scope.projectId, name: 'Opening shot', status: 'READY?', version: 'shot-v2', references: [{ kind: 'RENDER', id: 'render-1', projectId: scope.projectId, availability: 'SUPPORTED' }] },
    { kind: 'SHOT', id: 'shot-2', projectId: scope.projectId, description: '<b>literal description</b>', references: [{ kind: 'WORKFLOW', id: 'workflow-1', projectId: scope.projectId, availability: 'UNSUPPORTED', explanation: 'No safe inspection route is supplied.' }] },
  ],
  relations: [{ sceneId: 'scene-z', shotId: 'shot-1' }, { sceneId: 'scene-z', shotId: 'shot-2' }],
  boundary: { kind: 'project-production-snapshot', completeness: 'bounded', limit: 5, version: 'projection-v7' },
})

describe('bounded Scene and Shot production projection', () => {
  it('filters only supplied Scene display fields and status, then sorts stably by name and ID', () => {
    expect(selectScenes(scenes, { query: 'Exterior 原文', status: '', order: 'name-asc' }).map(scene => scene.id)).toEqual(['scene-z'])
    expect(selectScenes(scenes, { query: '', status: 'DRAFT', order: 'name-asc' }).map(scene => scene.id)).toEqual(['scene-b'])
    expect(selectScenes(scenes, { query: '', status: '', order: 'name-asc' }).map(scene => scene.id)).toEqual(['scene-a', 'scene-b', 'scene-z'])
    expect(selectScenes(scenes, { query: '', status: '', order: 'name-desc' }).map(scene => scene.id)).toEqual(['scene-z', 'scene-a', 'scene-b'])
    expect(sceneStatusValues(scenes)).toEqual(['DRAFT', 'READY?'])
  })

  it('accepts an owned bounded snapshot with explicit stable Scene-to-Shot relations and safe references', () => {
    expect(parseProductionSnapshot(validReceipt(), request)).toEqual(validReceipt())
  })

  it.each([
    undefined,
    { error: 'NOT_FOUND' },
    { ...validReceipt(), requestId: 'old-request' },
    { ...validReceipt(), scope: { ...scope, principalId: 'other' } },
    { ...validReceipt(), scope: { ...scope, tenantId: 'other' } },
    { ...validReceipt(), scope: { ...scope, sessionId: 'other' } },
    { ...validReceipt(), scope: { ...scope, workspaceId: 'other' } },
    { ...validReceipt(), scope: { ...scope, projectId: 'other' } },
    { ...validReceipt(), scenes: [scenes[0], scenes[0]] },
    { ...validReceipt(), shots: [validReceipt().shots[0], validReceipt().shots[0]] },
    { ...validReceipt(), shots: [{ ...validReceipt().shots[0], id: scenes[0].id }] },
    { ...validReceipt(), scenes: [{ ...scenes[0], projectId: 'foreign-project' }] },
    { ...validReceipt(), shots: [{ ...validReceipt().shots[0], projectId: 'foreign-project' }] },
    { ...validReceipt(), relations: [{ sceneId: 'missing', shotId: 'shot-1' }] },
    { ...validReceipt(), relations: [{ sceneId: 'scene-z', shotId: 'missing' }] },
    { ...validReceipt(), relations: [{ sceneId: 'scene-z', shotId: 'shot-1' }, { sceneId: 'scene-b', shotId: 'shot-1' }] },
    { ...validReceipt(), relations: [{ sceneId: 'scene-z', shotId: 'shot-1' }, { sceneId: 'scene-z', shotId: 'shot-1' }] },
    { ...validReceipt(), relations: [{ sceneId: 'scene-z', shotId: 'shot-1' }] },
    { ...validReceipt(), shots: [{ ...validReceipt().shots[0], references: [{ kind: 'RENDER', id: 'render-1', projectId: 'foreign-project', availability: 'SUPPORTED' }] }] },
    { ...validReceipt(), shots: [{ ...validReceipt().shots[0], references: [{ kind: 'SCENE', id: 'scene-z', projectId: scope.projectId, availability: 'SUPPORTED' }] }] },
    { ...validReceipt(), shots: [{ ...validReceipt().shots[0], references: [{ kind: 'WORKFLOW', id: 'workflow-1', projectId: scope.projectId, availability: 'UNSUPPORTED' }] }] },
    { ...validReceipt(), boundary: { ...validReceipt().boundary, version: '' } },
    { ...validReceipt(), boundary: { ...validReceipt().boundary, limit: 1 } },
    { ...validReceipt(), unexpected: 'field' },
  ])('rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results %#', input => {
    expect(() => parseProductionSnapshot(input, request)).toThrow()
  })

  it.each(['unavailable', 'denied', 'unknown', 'unsupported', 'error', 'stale'] as const)('preserves nondisclosing %s failure receipts', status => {
    const failure = { status, scope, requestId: request.requestId, explanation: '<opaque source result 原文>' }
    expect(parseProductionSnapshot(failure, request)).toEqual(failure)
  })

  it('keys all identity, scope, access, and source ownership inputs', () => {
    const base = { ...scope, access: access('AVAILABLE') }
    const keys = [
      base,
      { ...base, principalId: 'other' }, { ...base, tenantId: 'other' }, { ...base, sessionId: 'other' },
      { ...base, workspaceId: 'other' }, { ...base, projectId: 'other' }, { ...base, access: access('POLICY_DENIED') },
    ].map(productionContextKey)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('requires exact real and simulated access projections and never treats viewability as permission', () => {
    const source = (entry: EffectiveAccessEntry, bindingKey = entry.key): ProductionSource => ({ scope, access: entry, readAccessBinding: { kind: 'HOST_AGREED', accessKey: bindingKey }, adapter: { origin: 'real', async readProject() { throw new Error('not called') } } })
    expect(productionAccessDisposition({ ...scope, access: access('AVAILABLE') })).toBe('ready')
    expect(productionAccessDisposition({ ...scope, access: access('POLICY_DENIED') })).toBe('denied')
    expect(productionAccessDisposition({ ...scope, access: access('UNKNOWN_FAIL_CLOSED') })).toBe('unknown')
    expect(productionAccessDisposition({ ...scope, principalId: null, access: access('AVAILABLE') })).toBe('unknown')
    expect(productionSourceDisposition(source(access('AVAILABLE')), scope)).toBe('ready')
    expect(productionPresentationOrigin(source(access('AVAILABLE')))).toBe('real')
    expect(productionSourceDisposition(source(access('AVAILABLE'), 'different.host.binding'), scope)).toBe('unknown')
    expect(productionSourceDisposition(source(access('AVAILABLE', 'surface.production.view')), scope)).toBe('unknown')
    expect(productionSourceDisposition(source({ ...access('AVAILABLE'), source: 'DEVELOPMENT_FAIL_CLOSED' }), scope)).toBe('unknown')
    expect(productionSourceDisposition(source(access('AVAILABLE')), { workspaceId: 'workspace-2', projectId: scope.projectId })).toBe('unknown')
  })
})

describe('explicit Production source boundaries', () => {
  it('accepts an arbitrary explicitly host-agreed SERVER access binding and rejects a mismatched binding', () => {
    const accessEntry = access('AVAILABLE', 'actual.host.production.read.v7')
    const matching = {
      scope, access: accessEntry,
      readAccessBinding: { kind: 'HOST_AGREED', accessKey: accessEntry.key },
      adapter: { origin: 'real', async readProject() { throw new Error('not called') } },
    } as ProductionSource & { readAccessBinding: { kind: 'HOST_AGREED'; accessKey: string } }
    expect(productionSourceDisposition(matching, scope)).toBe('ready')
    expect(productionPresentationOrigin(matching)).toBe('real')
    expect(productionSourceDisposition({ ...matching, readAccessBinding: { ...matching.readAccessBinding, accessKey: 'different.host.binding' } }, scope)).toBe('unknown')
  })

  it.each([
    ['principalId', ''], ['tenantId', ' '], ['sessionId', '\t'], ['workspaceId', '\u0000'], ['projectId', '\n'],
  ] as const)('rejects malformed required %s before a source can be ready', (field, value) => {
    const malformedScope = { ...scope, [field]: value }
    const source = {
      scope: malformedScope, access: access('AVAILABLE'),
      readAccessBinding: { kind: 'HOST_AGREED', accessKey: TEST_HOST_ACCESS_KEY },
      adapter: { origin: 'real', async readProject() { throw new Error('must not be called') } },
    } as ProductionSource
    expect(productionAccessDisposition({ ...malformedScope, access: source.access })).toBe('unknown')
    expect(productionSourceDisposition(source, { workspaceId: malformedScope.workspaceId, projectId: malformedScope.projectId })).toBe('unknown')
  })

  it('defaults unavailable without transport and retains the supplied route scope without inventing identity', async () => {
    const fetch = vi.spyOn(globalThis, 'fetch')
    const source = unavailableProductionSource({ workspaceId: 'workspace-1', projectId: 'project-1' })
    expect(source.scope).toEqual({ principalId: null, tenantId: null, sessionId: 'unconfigured', workspaceId: 'workspace-1', projectId: 'project-1' })
    expect(await source.adapter.readProject({ scope: source.scope, requestId: 'q' }, new AbortController().signal)).toMatchObject({ status: 'unavailable', scope: source.scope, requestId: 'q' })
    expect(fetch).not.toHaveBeenCalled()
    fetch.mockRestore()
  })

  it('creates simulated data only from an explicit supplied identity and never reads URL, storage, or transport', async () => {
    const source = createSimulatedProductionSource({ scope })
    const fetch = vi.spyOn(globalThis, 'fetch')
    const getItem = vi.spyOn(Storage.prototype, 'getItem')
    expect(source.scope).toEqual(scope)
    expect(source.adapter.origin).toBe('simulated')
    await source.adapter.readProject({ scope, requestId: 'q' }, new AbortController().signal)
    expect(fetch).not.toHaveBeenCalled()
    expect(getItem).not.toHaveBeenCalled()
    fetch.mockRestore(); getItem.mockRestore()
  })
})
