import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { StrictMode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import type { EffectiveAccessEntry } from '../../foundation/effectiveAccess'
import { SelectionProvider } from '../../interaction/SelectionContext'
import { useInteractionStore } from '../../interaction/SelectionContext'
import type { InteractionStore } from '../../interaction/model'
import { LocalizationProvider } from '../../localization'
import { ProductionBrowser } from './ProductionBrowser'
import { createSimulatedProductionSource } from './simulatedSource'
import { ProductionSourceProvider } from './source'
import { type ProductionReadRequest, type ProductionSource } from './types'

const scope = { principalId: 'principal-1', tenantId: 'tenant-1', sessionId: 'session-1', workspaceId: 'workspace-1', projectId: 'project-1' }

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(value => { resolve = value })
  return { promise, resolve }
}

const TEST_HOST_ACCESS_KEY = 'test-host-agreed.production.read'
function availableAccess(): EffectiveAccessEntry {
  return {
    key: TEST_HOST_ACCESS_KEY, status: 'AVAILABLE', reasonCode: 'TEST_AVAILABLE', explanation: '<server access explanation 原文>',
    factors: { capability: 'SATISFIED', runtime: 'SATISFIED', entitlement: 'SATISFIED', policy: 'SATISFIED', quota: 'SATISFIED' }, source: 'SERVER',
  }
}

function ownedResult(request: ProductionReadRequest, sceneName = 'Connected Scene') {
  return {
    status: 'ok', scope: request.scope, requestId: request.requestId,
    scenes: [{ kind: 'SCENE', id: 'scene-connected', projectId: request.scope.projectId, name: sceneName, status: 'APPROVED', version: 'scene-v1' }],
    shots: [{ kind: 'SHOT', id: 'shot-connected', projectId: request.scope.projectId, name: 'Connected Shot', description: 'Supplied detail', status: 'READY', version: 'shot-v3', references: [{ kind: 'RENDER', id: 'render-connected', projectId: request.scope.projectId, availability: 'SUPPORTED' }] }],
    relations: [{ sceneId: 'scene-connected', shotId: 'shot-connected' }],
    boundary: { kind: 'project-production-snapshot', completeness: 'complete', limit: 2, version: 'projection-connected' },
  }
}

function realSource(overrides: Partial<typeof scope> = {}): ProductionSource {
  const sourceScope = { ...scope, ...overrides }
  return { scope: sourceScope, access: availableAccess(), readAccessBinding: { kind: 'HOST_AGREED', accessKey: TEST_HOST_ACCESS_KEY }, adapter: { origin: 'real', async readProject(request) { return ownedResult(request) } } }
}

function setup(source: ProductionSource = createSimulatedProductionSource({ scope }), locale: 'en' | 'zh-CN' = 'en') {
  return render(<LocalizationProvider initialLocale={locale}><SelectionProvider scope={{ workspaceId: scope.workspaceId, projectId: scope.projectId, surfaceId: 'production' }}><ProductionBrowser expectedScope={scope} source={source} /></SelectionProvider></LocalizationProvider>)
}

function CaptureInteractionStore({ capture }: { capture: (store: InteractionStore) => void }) {
  capture(useInteractionStore())
  return null
}

describe('ProductionBrowser Scene and Shot discovery', () => {
  it('remains initially usable under the actual StrictMode-style host lifecycle', async () => {
    const source = realSource()
    const query = vi.spyOn(source.adapter, 'readProject')
    render(<StrictMode><LocalizationProvider><SelectionProvider scope={{ workspaceId: scope.workspaceId, projectId: scope.projectId, surfaceId: 'production' }}><ProductionBrowser expectedScope={scope} source={source} /></SelectionProvider></LocalizationProvider></StrictMode>)
    expect(await screen.findByText('Connected Scene')).toBeTruthy()
    expect(screen.queryByRole('heading', { name: 'Production context retired' })).toBeNull()
    expect(query.mock.calls.length).toBeGreaterThan(0)
  })

  it('accepts the isolated fixture only through an explicit source prop or provider injection', async () => {
    const source = createSimulatedProductionSource({ scope })
    render(<LocalizationProvider><SelectionProvider scope={{ workspaceId: scope.workspaceId, projectId: scope.projectId, surfaceId: 'production' }}><ProductionSourceProvider source={source}><ProductionBrowser expectedScope={scope} /></ProductionSourceProvider></SelectionProvider></LocalizationProvider>)
    expect(await screen.findByRole('button', { name: 'Browse scene Courtyard <scene>' })).toBeTruthy()
    expect(screen.getByText(/explicitly injected fixture/i)).toBeTruthy()
  })

  it('browses only explicitly related Shots, preserves missing fields, and exposes no mutation or arbitrary URL', async () => {
    setup()
    expect(await screen.findByRole('heading', { name: 'Scenes and shots' })).toBeTruthy()
    expect(screen.getByText(/SIMULATED PRODUCTION DATA/)).toBeTruthy()
    expect(screen.getByText('workspace-1')).toBeTruthy()
    expect(screen.getByText('project-1')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Browse scene Courtyard <scene>' }))
    const shots = screen.getByRole('list', { name: 'Shots explicitly related to Courtyard <scene>' })
    expect(within(shots).getByText('Arrival shot')).toBeTruthy()
    expect(within(shots).queryByText('Studio insert')).toBeNull()
    fireEvent.click(within(shots).getByRole('button', { name: 'Inspect shot shot-courtyard-detail' }))
    const unsupported = screen.getByRole('dialog', { name: 'Shot details' })
    expect(within(unsupported).getByText('workflow-courtyard')).toBeTruthy()
    expect(within(unsupported).getByText('No safe Workflow inspection route is supplied by this fixture.')).toBeTruthy()
    expect(within(unsupported).getByText('Empty supplied value')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /create|delete|rename|assign|change status/i })).toBeNull()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('searches, filters, sorts and resets Scenes locally while retaining controls after detail close', async () => {
    setup()
    await screen.findByRole('button', { name: 'Browse scene Courtyard <scene>' })
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search scenes' }), { target: { value: 'interior 原文' } })
    expect(screen.getByRole('button', { name: 'Browse scene Studio' })).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Browse scene Courtyard <scene>' })).toBeNull()
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search scenes' }), { target: { value: '' } })
    fireEvent.change(screen.getByLabelText('Scene status'), { target: { value: 'DRAFT?' } })
    fireEvent.change(screen.getByLabelText('Sort scenes'), { target: { value: 'name-desc' } })
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search scenes' }), { target: { value: 'no match' } })
    expect(screen.getByRole('heading', { name: 'No matching scenes' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Reset filters' }))
    const launcher = screen.getByRole('button', { name: 'Browse scene Courtyard <scene>' })
    fireEvent.click(launcher)
    const shotLauncher = screen.getByRole('button', { name: 'Inspect shot Arrival shot' })
    shotLauncher.focus(); fireEvent.click(shotLauncher)
    const dialog = screen.getByRole('dialog', { name: 'Shot details' })
    expect(within(dialog).getByText('arrival-v2')).toBeTruthy()
    expect(within(dialog).getByText('render-arrival')).toBeTruthy()
    expect(within(dialog).getByText(/does not grant permission/i)).toBeTruthy()
    fireEvent.keyDown(dialog, { key: 'Escape' })
    expect(document.activeElement).toBe(shotLauncher)
    expect((screen.getByRole('searchbox', { name: 'Search scenes' }) as HTMLInputElement).value).toBe('')
    expect((screen.getByLabelText('Scene status') as HTMLSelectElement).value).toBe('')
    expect((screen.getByLabelText('Sort scenes') as HTMLSelectElement).value).toBe('name-asc')
  })

  it('keeps Reset reachable for populated filters and preserves Reset focus after restoring defaults', async () => {
    setup()
    await screen.findByRole('button', { name: 'Browse scene Courtyard <scene>' })
    fireEvent.change(screen.getByLabelText('Scene status'), { target: { value: 'DRAFT?' } })
    expect(screen.getByRole('button', { name: 'Browse scene Studio' })).toBeTruthy()
    const reset = screen.getByRole('button', { name: 'Reset filters' })
    reset.focus(); fireEvent.click(reset)
    expect((screen.getByLabelText('Scene status') as HTMLSelectElement).value).toBe('')
    expect(screen.getByRole('button', { name: 'Browse scene Courtyard <scene>' })).toBeTruthy()
    expect(document.activeElement).toBe(reset)
  })

  it('distinguishes empty snapshots, no related Shots, bounded snapshots and missing supplied values', async () => {
    const empty = setup(createSimulatedProductionSource({ scope, empty: true }))
    expect(await screen.findByRole('heading', { name: 'No scenes in this snapshot' })).toBeTruthy()
    empty.unmount()
    setup(createSimulatedProductionSource({ scope, limit: 3 }))
    expect(await screen.findByText(/bounded snapshot; more may exist/i)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Browse scene Silent scene' }))
    expect(screen.getByRole('heading', { name: 'No related shots in this snapshot' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Inspect scene Silent scene' }))
    expect(within(screen.getByRole('dialog', { name: 'Scene details' })).getAllByText('Not supplied').length).toBeGreaterThan(0)
  })

  it('uses one stable Refresh/Cancel/Retry control, drops cancelled replies, and never steals moved focus', async () => {
    const source = realSource()
    render(<LocalizationProvider><SelectionProvider scope={{ workspaceId: scope.workspaceId, projectId: scope.projectId, surfaceId: 'production' }}><button type="button">Stable focus</button><ProductionBrowser expectedScope={scope} source={source} /></SelectionProvider></LocalizationProvider>)
    await screen.findByText('Connected Scene')
    const pending = deferred<unknown>(); let request!: ProductionReadRequest
    vi.spyOn(source.adapter, 'readProject').mockImplementationOnce(value => { request = value; return pending.promise })
    const workflow = screen.getByRole('button', { name: 'Refresh production snapshot' })
    workflow.focus(); fireEvent.click(workflow)
    expect(screen.getByRole('button', { name: 'Cancel loading' })).toBe(workflow)
    const stable = screen.getByRole('button', { name: 'Stable focus' }); stable.focus()
    await act(async () => pending.resolve({ status: 'error', scope: request.scope, requestId: request.requestId, explanation: '<opaque error>' }))
    expect(screen.getByRole('button', { name: 'Retry loading' })).toBe(workflow)
    expect(document.activeElement).toBe(stable)

    const cancelled = deferred<unknown>(); let cancelledRequest!: ProductionReadRequest
    vi.spyOn(source.adapter, 'readProject').mockImplementationOnce(value => { cancelledRequest = value; return cancelled.promise })
    fireEvent.click(workflow); fireEvent.click(workflow)
    await act(async () => cancelled.resolve(ownedResult(cancelledRequest, 'Cancelled secret')))
    expect(screen.queryByText('Cancelled secret')).toBeNull()
  })

  it.each(['unavailable', 'denied', 'unknown', 'unsupported', 'error', 'stale'] as const)('clears content and renders nondisclosing %s state with opaque supplied explanation', async failure => {
    const source = realSource()
    setup(source)
    await screen.findByText('Connected Scene')
    vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => ({ status: failure, scope: request.scope, requestId: request.requestId, explanation: `<opaque ${failure} 原因>` }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh production snapshot' }))
    await waitFor(() => expect(screen.getByText(`<opaque ${failure} 原因>`)).toBeTruthy())
    expect(screen.queryByText('Connected Scene')).toBeNull()
  })

  it('fails closed on invalid relations and never retains old content', async () => {
    const source = realSource()
    setup(source)
    await screen.findByText('Connected Scene')
    vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => ({ ...ownedResult(request, 'Must stay hidden'), relations: [] }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh production snapshot' }))
    expect(await screen.findByRole('heading', { name: 'Invalid production snapshot' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Retry loading' })).toBeTruthy()
    expect(screen.queryByText('Must stay hidden')).toBeNull()
  })

  it('keeps a rejected source request retryable and distinct from invalid snapshot validation', async () => {
    const source = realSource()
    setup(source)
    await screen.findByText('Connected Scene')
    vi.spyOn(source.adapter, 'readProject').mockRejectedValueOnce(new Error('transport detail must remain hidden'))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh production snapshot' }))
    expect(await screen.findByRole('heading', { name: 'Production snapshot error' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Retry loading' })).toBeTruthy()
    expect(screen.queryByText('transport detail must remain hidden')).toBeNull()
    expect(screen.queryByRole('heading', { name: 'Invalid production snapshot' })).toBeNull()
  })

  it.each(['principalId', 'tenantId', 'sessionId', 'workspaceId', 'projectId'] as const)('retires a valid pending reply on %s change', async field => {
    const source = realSource()
    const pending = deferred<unknown>(); let oldRequest!: ProductionReadRequest
    vi.spyOn(source.adapter, 'readProject').mockImplementation(request => { oldRequest = request; return pending.promise })
    const view = setup(source)
    const nextScope = { ...scope, [field]: field === 'workspaceId' ? 'workspace-2' : field === 'projectId' ? 'project-2' : 'changed' }
    const next = realSource({ [field]: nextScope[field] })
    view.rerender(<LocalizationProvider><SelectionProvider scope={{ workspaceId: nextScope.workspaceId, projectId: nextScope.projectId, surfaceId: 'production' }}><ProductionBrowser expectedScope={nextScope} source={next} /></SelectionProvider></LocalizationProvider>)
    expect(await screen.findByText('Connected Scene')).toBeTruthy()
    await act(async () => pending.resolve(ownedResult(oldRequest, 'Retired secret')))
    expect(screen.queryByText('Retired secret')).toBeNull()
  })

  it('retires pending replies on adapter/access replacement and unmount', async () => {
    const source = realSource()
    const pending = deferred<unknown>(); let oldRequest!: ProductionReadRequest
    vi.spyOn(source.adapter, 'readProject').mockImplementation(request => { oldRequest = request; return pending.promise })
    const view = setup(source)
    const deniedBase = realSource()
    const denied = { ...deniedBase, access: { ...deniedBase.access, status: 'POLICY_DENIED' as const, explanation: '<replacement denied>' } }
    const deniedQuery = vi.spyOn(denied.adapter, 'readProject')
    view.rerender(<LocalizationProvider><SelectionProvider scope={{ workspaceId: scope.workspaceId, projectId: scope.projectId, surfaceId: 'production' }}><ProductionBrowser expectedScope={scope} source={denied} /></SelectionProvider></LocalizationProvider>)
    expect(screen.getByText('<replacement denied>')).toBeTruthy()
    expect(deniedQuery).not.toHaveBeenCalled()
    await act(async () => pending.resolve(ownedResult(oldRequest, 'Replaced adapter secret')))
    expect(screen.queryByText('Replaced adapter secret')).toBeNull()
    view.unmount()

    const unmountedSource = realSource()
    const unmounted = deferred<unknown>(); let unmountedRequest!: ProductionReadRequest
    vi.spyOn(unmountedSource.adapter, 'readProject').mockImplementation(request => { unmountedRequest = request; return unmounted.promise })
    const second = setup(unmountedSource)
    second.unmount()
    await act(async () => unmounted.resolve(ownedResult(unmountedRequest, 'Unmounted secret')))
    expect(screen.queryByText('Unmounted secret')).toBeNull()
  })

  it('clears a ready snapshot on InteractionStore owner retirement and rebinds only to a fresh pageshow store', async () => {
    const source = realSource()
    const query = vi.spyOn(source.adapter, 'readProject')
    render(<LocalizationProvider><SelectionProvider scope={{ workspaceId: scope.workspaceId, projectId: scope.projectId, surfaceId: 'production' }}><ProductionBrowser expectedScope={scope} source={source} /></SelectionProvider></LocalizationProvider>)
    expect(await screen.findByText('Connected Scene')).toBeTruthy()
    act(() => window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: true })))
    expect(screen.queryByText('Connected Scene')).toBeNull()
    expect(screen.getByRole('heading', { name: 'Production context retired' })).toBeTruthy()
    expect(query).toHaveBeenCalledTimes(1)
    act(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })))
    expect(await screen.findByText('Connected Scene')).toBeTruthy()
    expect(query).toHaveBeenCalledTimes(2)
  })

  it('rejects a pending reply after InteractionStore owner retirement', async () => {
    const source = realSource()
    const pending = deferred<unknown>(); let request!: ProductionReadRequest; let store!: InteractionStore
    vi.spyOn(source.adapter, 'readProject').mockImplementation(value => { request = value; return pending.promise })
    render(<LocalizationProvider><SelectionProvider scope={{ workspaceId: scope.workspaceId, projectId: scope.projectId, surfaceId: 'production' }}><CaptureInteractionStore capture={value => { store = value }} /><ProductionBrowser expectedScope={scope} source={source} /></SelectionProvider></LocalizationProvider>)
    expect(screen.getByRole('heading', { name: 'Loading production snapshot' })).toBeTruthy()
    act(() => store.retireSelectionOwner('owner'))
    expect(screen.getByRole('heading', { name: 'Production context retired' })).toBeTruthy()
    await act(async () => pending.resolve(ownedResult(request, 'Retired owner secret')))
    expect(screen.queryByText('Retired owner secret')).toBeNull()
  })

  it.each([
    ['principalId', ''], ['tenantId', ' '], ['sessionId', '\t'], ['workspaceId', '\u0000'], ['projectId', '\n'],
  ] as const)('does not query a malformed required %s context', (field, value) => {
    const invalid = realSource({ [field]: value })
    const query = vi.spyOn(invalid.adapter, 'readProject')
    const expected = { workspaceId: invalid.scope.workspaceId, projectId: invalid.scope.projectId }
    render(<LocalizationProvider><SelectionProvider scope={{ workspaceId: expected.workspaceId, projectId: expected.projectId, surfaceId: 'production' }}><ProductionBrowser expectedScope={expected} source={invalid} /></SelectionProvider></LocalizationProvider>)
    expect(screen.getByRole('heading', { name: 'Production snapshot access unknown' })).toBeTruthy()
    expect(query).not.toHaveBeenCalled()
  })

  it('does not query denied/unknown sources and is unavailable with no injected source', () => {
    for (const status of ['POLICY_DENIED', 'UNKNOWN_FAIL_CLOSED'] as const) {
      const base = realSource()
      const source = { ...base, access: { ...base.access, status, explanation: `<initial ${status} 原因>` } }
      const query = vi.spyOn(source.adapter, 'readProject')
      const view = setup(source)
      expect(screen.getByText(`<initial ${status} 原因>`)).toBeTruthy()
      expect(query).not.toHaveBeenCalled()
      view.unmount()
    }
    render(<LocalizationProvider><SelectionProvider scope={{ workspaceId: scope.workspaceId, projectId: scope.projectId, surfaceId: 'production' }}><ProductionBrowser expectedScope={scope} /></SelectionProvider></LocalizationProvider>)
    expect(screen.getByRole('heading', { name: 'Production snapshot unavailable' })).toBeTruthy()
  })

  it('localizes the complete bounded workflow in Chinese while preserving supplied values literally', async () => {
    setup(createSimulatedProductionSource({ scope }), 'zh-CN')
    expect(await screen.findByRole('heading', { name: '场景与镜头' })).toBeTruthy()
    expect(await screen.findByRole('searchbox', { name: '搜索场景' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '浏览场景 Courtyard <scene>' }))
    fireEvent.click(screen.getByRole('button', { name: '检查镜头 Arrival shot' }))
    const dialog = screen.getByRole('dialog', { name: '镜头详情' })
    expect(within(dialog).getByText('arrival-v2')).toBeTruthy()
    expect(within(dialog).getByText('render-arrival')).toBeTruthy()
  })
})
