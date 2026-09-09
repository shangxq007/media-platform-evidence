import { StrictMode, useLayoutEffect } from 'react'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { SelectionProvider, useInteractionStore } from '../../interaction/SelectionContext'
import { SelectionInspector } from '../../interaction/InteractionShell'
import type { InteractionStore } from '../../interaction/model'
import { LocalizationProvider } from '../../localization'
import { unknownAccess } from '../../foundation/effectiveAccess'
import { TimelineNavigation } from './TimelineNavigation'
import { clipsAtTime, compareTime, parseNavigationSnapshot, timeDifference, type NavigationRequest, type NavigationTarget, type TimelineNavigationSource } from './navigation'
import { contentHash, projectId, revisionId, timelineId } from './types'

const target: NavigationTarget = { projectId: projectId('p'), timelineId: timelineId('t'), revisionId: revisionId('r1'), contentHash: contentHash('a'.repeat(64)) }
const scope = { principalId: 'principal', tenantId: 'tenant', sessionId: 'session', workspaceId: 'w', projectId: 'p' }
const tracks = [
  { id: 'v', name: 'Picture', type: 'video', clips: [
    { id: 'opening', trackId: 'v', name: 'Opening shot', type: 'video', version: 'v1', timelineRange: { start: '0', end: '1001/30000' }, sourceRange: { start: '10', end: '300001/30000' }, source: { mediaAssetId: 'asset', mediaStreamId: 'stream', artifactId: 'artifact', contentDigest: 'b'.repeat(64) } },
    { id: 'ending', trackId: 'v', name: 'Ending shot', type: 'image', timelineRange: { start: '1001/30000', end: '2' } },
  ] },
  { id: 'a', name: 'Audio', type: 'audio', clips: [] },
]
function receipt(request: NavigationRequest, changes: Record<string, unknown> = {}) {
  return { ...request, status: 'ok', completeness: 'complete', timeBasis: 'exact-seconds', bounds: { start: '0', end: '2' }, tracks, ...changes }
}
function source(read: TimelineNavigationSource['adapter']['read'] = vi.fn(async (request: NavigationRequest) => receipt(request))): TimelineNavigationSource {
  return { scope, accessBinding: { kind: 'TEST_ONLY_UNAGREED', key: 'test-navigation' }, access: { ...unknownAccess('test-navigation'), source: 'SERVER', status: 'AVAILABLE', factors: { capability: 'SATISFIED', runtime: 'NOT_APPLICABLE', entitlement: 'SATISFIED', policy: 'SATISFIED', quota: 'NOT_APPLICABLE' } }, adapter: { origin: 'isolated-verification', read } }
}
function Probe({ onStore }: { onStore?: (store: InteractionStore) => void }) {
  const store = useInteractionStore()
  useLayoutEffect(() => { onStore?.(store) }, [store, onStore])
  return null
}
function host(value?: TimelineNavigationSource, options: { target?: NavigationTarget | null; loading?: boolean; owner?: string; zh?: boolean; onStore?: (store: InteractionStore) => void; inspector?: boolean } = {}) {
  return <StrictMode><LocalizationProvider initialLocale={options.zh ? 'zh-CN' : 'en'}><SelectionProvider scope={{ surfaceId: 'nle', workspaceId: 'w', projectId: options.owner ?? 'p' }}><Probe onStore={options.onStore} /><TimelineNavigation workspaceId="w" projectId="p" tenantId="tenant" source={value} target={options.target === undefined ? target : options.target} loading={options.loading} />{options.inspector ? <SelectionInspector /> : null}</SelectionProvider></LocalizationProvider></StrictMode>
}
function button(name: string) { return screen.getByRole('button', { name: new RegExp(name) }) }
function inputTime(value: string) {
  fireEvent.change(screen.getByLabelText('Exact time (integer or fraction)'), { target: { value } })
  fireEvent.click(screen.getByRole('button', { name: 'Locate time' }))
}
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(accept => { resolve = accept }); return { promise, resolve } }

describe('bounded Timeline navigation', () => {
  it('distinguishes unconfigured entry, loading, true empty and partial empty without fake media', async () => {
    const view = render(host())
    expect(screen.getByText('Track and clip projection unavailable')).toBeTruthy()
    expect(screen.queryByText('Empty timeline')).toBeNull()
    const read = vi.fn(async (request: NavigationRequest) => receipt(request, { tracks: [] }))
    const value = source(read)
    view.rerender(host(value, { target: null }))
    expect(screen.getByText('Track and clip projection unavailable')).toBeTruthy()
    expect(read).not.toHaveBeenCalled()
    view.rerender(host(value, { loading: true }))
    expect(screen.getByText('Loading timeline projection…')).toBeTruthy()
    expect(read).not.toHaveBeenCalled()
    view.rerender(host(value))
    await screen.findByText('Empty timeline')
    read.mockImplementation(async request => receipt(request, { tracks: [], completeness: 'bounded' }))
    fireEvent.click(button('Refresh loaded projection'))
    await screen.findByText('No tracks in this partial loaded scope')
    expect(screen.queryByText('Empty timeline')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Play' })).toBeNull()
    expect(document.querySelector('video,audio,a[href]')).toBeNull()
  })
  it('discovers multiple tracks, empty tracks and filtered no-match only within the loaded scope', async () => {
    render(host(source(vi.fn(async request => receipt(request, { completeness: 'bounded' })))))
    await screen.findByText('Opening shot')
    expect(button('Audio')).toBeTruthy()
    expect(screen.getByText('No clips loaded for this track')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Filter loaded tracks and clips'), { target: { value: 'image' } })
    expect(button('Ending shot')).toBeTruthy()
    expect(screen.queryByText('Opening shot')).toBeNull()
    fireEvent.change(screen.getByLabelText('Filter loaded tracks and clips'), { target: { value: 'absent' } })
    expect(screen.getByText('No matches in loaded scope')).toBeTruthy()
  })
  it('locates exact authored-range boundaries, end and zero without floating point or assumed FPS', async () => {
    render(host(source()))
    await screen.findByText('Opening shot')
    inputTime('0')
    expect(button('Opening shot').getAttribute('aria-pressed')).toBe('true')
    inputTime('1001/30000')
    expect(screen.getByText('Loaded clips at this position: 2')).toBeTruthy()
    expect(button('Opening shot').getAttribute('aria-pressed')).toBe('true')
    inputTime('2')
    expect(screen.getByText('Loaded clips at this position: 1')).toBeTruthy()
    for (const invalid of ['-1', '3', '0.5', '1/0', '1e3', '']) {
      inputTime(invalid)
      expect(screen.getByRole('alert')).toBeTruthy()
      expect(screen.getByLabelText('Local navigation position').textContent).toBe('2')
    }
    expect(compareTime('9007199254740993/30000', '9007199254740992/30000')).toBe(1)
    expect(timeDifference('1001/30000', '0')).toBe('1001/30000')
    const request = { scope, target, requestId: 'zero-range' }
    const point = parseNavigationSnapshot(receipt(request, { tracks: [{ id: 'v', clips: [{ id: 'point', trackId: 'v', timelineRange: { start: '1', end: '1' } }] }] }), request)
    if (point.status !== 'ok') throw new Error('Expected valid point projection')
    expect(clipsAtTime(point, '1').map(clip => clip.id)).toEqual(['point'])
    expect(clipsAtTime(point, '999/1000')).toEqual([])
    expect(timeDifference('1', '1')).toBe('0/1')
  })
  it('disables time actions for unknown basis and preserves logical metadata without inventing a duration', async () => {
    render(host(source(vi.fn(async request => receipt(request, { timeBasis: 'unknown' })))))
    await screen.findByText('Opening shot')
    fireEvent.click(button('Opening shot'))
    expect((button('Locate time') as HTMLButtonElement).disabled).toBe(true)
    expect((button('Locate selected clip') as HTMLButtonElement).disabled).toBe(true)
    fireEvent.click(button('Inspect selected metadata'))
    expect(screen.queryByText('Exact duration (seconds)')).toBeNull()
    expect(screen.getByText('asset')).toBeTruthy()
  })
  it('selects by mouse and keyboard, inspects provenance, traps focus and closes back to the launcher', async () => {
    let store!: InteractionStore
    render(host(source(), { onStore: value => { store = value } }))
    const opening = await screen.findByText('Opening shot')
    fireEvent.click(opening)
    expect(store.getSnapshot().primarySelectedObject?.id).toBe('clip:opening')
    const launcher = button('Inspect selected metadata'); launcher.focus(); fireEvent.click(launcher)
    const dialog = screen.getByRole('dialog', { name: 'Timeline object metadata' })
    expect(within(dialog).getByText('asset')).toBeTruthy()
    expect(within(dialog).getByText('1001/30000')).toBeTruthy()
    const close = button('Close timeline metadata')
    expect(document.activeElement).toBe(close)
    fireEvent.keyDown(close, { key: 'Tab' }); expect(document.activeElement).toBe(close)
    fireEvent.keyDown(dialog, { key: 'Escape' }); expect(document.activeElement).toBe(launcher)
    const clip = button('Opening shot'); clip.focus()
    expect(fireEvent.keyDown(clip, { key: ' ', ctrlKey: true })).toBe(true)
    fireEvent.keyDown(clip, { key: 'ArrowDown' })
    expect(document.activeElement).toBe(button('Ending shot'))
    expect(store.getSnapshot().primarySelectedObject?.id).toBe('clip:ending')
    fireEvent.keyDown(button('Ending shot'), { key: 'i' })
    expect(screen.getByRole('dialog')).toBeTruthy()
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(document.activeElement).toBe(button('Ending shot'))
    fireEvent.keyDown(button('Ending shot'), { key: 'End' }); expect(document.activeElement).toBe(button('Audio'))
    fireEvent.keyDown(button('Audio'), { key: 'Home' }); expect(document.activeElement).toBe(button('Picture'))
    fireEvent.keyDown(button('Picture'), { key: 'Escape' }); expect(store.getSnapshot().selectedObjects).toHaveLength(0)
  })
  it('preserves position, selection and scroll through inspector toggle, equal rerender and equal refresh', async () => {
    const value = source(); const view = render(host(value))
    await screen.findByText('Ending shot')
    inputTime('1/2')
    const list = screen.getByLabelText('Loaded tracks and clips'); list.scrollTop = 123
    const selected = button('Ending shot')
    const toggle = button('Hide inspector'); toggle.focus(); fireEvent.click(toggle)
    expect(button('Ending shot')).toBe(selected)
    expect(list.scrollTop).toBe(123)
    fireEvent.click(button('Show inspector'))
    view.rerender(host({ ...value, access: { ...value.access, observedAt: '2030-01-01' } }))
    expect(button('Ending shot')).toBe(selected)
    expect(screen.getByLabelText('Local navigation position').textContent).toBe('1/2')
    fireEvent.click(button('Refresh loaded projection'))
    await screen.findByText('Ending shot')
    expect(screen.getByLabelText('Loaded tracks and clips').scrollTop).toBe(123)
    expect(button('Ending shot').getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByLabelText('Local navigation position').textContent).toBe('1/2')
  })
  it('locates the selected clip across filters without changing overlapping explicit target identity', async () => {
    const value = source(vi.fn(async request => receipt(request, { tracks: [{ ...tracks[0], clips: tracks[0].clips.map(clip => ({ ...clip, timelineRange: { start: '0', end: '2' } })) }] })))
    render(host(value)); await screen.findByText('Ending shot'); fireEvent.click(button('Ending shot'))
    fireEvent.change(screen.getByLabelText('Filter loaded tracks and clips'), { target: { value: 'absent' } })
    fireEvent.click(button('Locate selected clip'))
    expect(button('Ending shot').getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByLabelText('Local navigation position').textContent).toBe('0')
  })
  it('clears failed refresh metadata, supports retry and distinguishes stale and restricted responses', async () => {
    const read = vi.fn< TimelineNavigationSource['adapter']['read'] >(async (request: NavigationRequest) => receipt(request))
    render(host(source(read))); await screen.findByText('Opening shot'); fireEvent.click(button('Opening shot')); fireEvent.click(button('Inspect selected metadata'))
    read.mockRejectedValueOnce(new Error('private transport detail'))
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' }); fireEvent.click(button('Refresh loaded projection'))
    await screen.findByText('Timeline projection failed. Retry the read.')
    expect(screen.queryByText('asset')).toBeNull(); expect(screen.queryByText('Opening shot')).toBeNull()
    fireEvent.click(button('Retry timeline projection')); await screen.findByText('Opening shot')
    for (const status of ['stale', 'restricted'] as const) {
      read.mockImplementationOnce(async request => ({ ...request, status }))
      fireEvent.click(button('Refresh loaded projection'))
      await screen.findByText(status === 'stale' ? 'Timeline projection is stale. Refresh required.' : 'Timeline inspection restricted or access unknown')
      expect(screen.queryByText('Opening shot')).toBeNull()
      fireEvent.click(button('Retry timeline projection')); await screen.findByText('Opening shot')
    }
  })
  it('rejects mismatched receipt scope, revision, duplicates, relationships and invalid time ranges', () => {
    const request = { scope, target, requestId: 'test' }
    const invalid = [
      { scope: { ...scope, principalId: 'other' } }, { target: { ...target, revisionId: 'other' } },
      { tracks: [tracks[0], tracks[0]] }, { tracks: [{ ...tracks[0], clips: [tracks[0].clips[0], tracks[0].clips[0]] }] },
      { tracks: [{ ...tracks[0], clips: [{ ...tracks[0].clips[0], trackId: 'other' }] }] },
      { bounds: { start: '1', end: '0' } }, { bounds: { start: '0', end: '1/0' } }, { bounds: { start: '0', end: '1' } },
    ]
    for (const changes of invalid) expect(() => parseNavigationSnapshot(receipt(request, changes), request)).toThrow()
  })
  it('retains full long names in accessible labels and details and localizes the main flow into Chinese', async () => {
    const name = '很长的片段名称'.repeat(50)
    render(host(source(vi.fn(async request => receipt(request, { tracks: [{ ...tracks[0], clips: [{ ...tracks[0].clips[0], name }] }] }))), { zh: true }))
    const clip = await screen.findByRole('button', { name: new RegExp(name) })
    expect(clip.title).toBe(name); fireEvent.click(clip)
    fireEvent.click(button('检查选中对象元数据'))
    expect(within(screen.getByRole('dialog', { name: '时间线对象元数据' })).getByText(name)).toBeTruthy()
    fireEvent.click(button('关闭时间线元数据'))
    expect(screen.getByLabelText('筛选已加载轨道和片段')).toBeTruthy()
  })
  it('removes missing selection on refresh and provides a focus fallback when its detail target disappears', async () => {
    const read = vi.fn< TimelineNavigationSource['adapter']['read'] >(async (request: NavigationRequest) => receipt(request))
    let store!: InteractionStore
    render(host(source(read), { onStore: value => { store = value } })); await screen.findByText('Opening shot')
    fireEvent.click(button('Opening shot')); fireEvent.click(button('Inspect selected metadata'))
    act(() => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [] }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(screen.getByRole('region', { name: 'Timeline navigation' }))
    fireEvent.click(button('Opening shot'))
    read.mockImplementationOnce(async request => receipt(request, { tracks: [] }))
    fireEvent.click(button('Refresh loaded projection')); await screen.findByText('Empty timeline')
    expect(store.getSnapshot().selectedObjects).toHaveLength(0)
  })
  it('aborts late reads on revision and identity/access/adapter/owner changes and rejects retained controls', async () => {
    const pending = deferred<unknown>(); let request!: NavigationRequest; let signal!: AbortSignal
    const slow = source(vi.fn((next: NavigationRequest, abort: AbortSignal) => { request = next; signal = abort; return pending.promise }))
    const view = render(host(slow))
    await waitFor(() => expect(request).toBeTruthy())
    const next = source()
    view.rerender(host(next, { target: { ...target, revisionId: revisionId('r2') } }))
    await screen.findByText('Opening shot'); expect(signal.aborted).toBe(true)
    await act(async () => pending.resolve(receipt(request, { tracks: [{ id: 'old', clips: [], name: 'Old secret' }] })))
    expect(screen.queryByText('Old secret')).toBeNull()
    for (const change of [
      { ...next, scope: { ...scope, principalId: 'other' } },
      { ...next, scope: { ...scope, sessionId: 'other-session' } },
      { ...next, scope: { ...scope, tenantId: 'other-tenant' } },
      { ...next, access: { ...next.access, status: 'POLICY_DENIED' as const } },
      { ...next, access: { ...next.access, source: 'MISSING_SERVER_PROJECTION' as const } },
      source(),
    ]) {
      view.rerender(host(next)); await screen.findByText('Opening shot'); fireEvent.click(button('Opening shot'))
      const staleInspect = button('Inspect selected metadata')
      view.rerender(host(change)); fireEvent.click(staleInspect)
      expect(screen.queryByRole('dialog')).toBeNull()
    }
    view.rerender(host(next)); await screen.findByText('Opening shot'); fireEvent.click(button('Opening shot'))
    await act(async () => view.rerender(host(next, { owner: 'replacement' })))
    expect(screen.queryByRole('dialog')).toBeNull()
  })
  it('withdraws metadata and rejects retained callbacks after explicit Selection owner retirement', async () => {
    let store!: InteractionStore
    render(host(source(), { onStore: value => { store = value } })); await screen.findByText('Opening shot')
    fireEvent.click(button('Opening shot')); const inspect = button('Inspect selected metadata'); fireEvent.click(inspect)
    act(() => store.retireSelectionOwner('document'))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.queryByText('Opening shot')).toBeNull()
    fireEvent.click(inspect)
    expect(screen.queryByRole('dialog')).toBeNull()
  })
})

it('rejects actual retained inspector and close callbacks when selection or dialog instance changes', async () => {
  function handler(element: HTMLElement): () => void {
    const key = Object.keys(element).find(key => key.startsWith('__reactProps$'))!
    return (element as unknown as Record<string, { onClick: () => void }>)[key].onClick
  }
  const value = source(), view = render(host(value))
  await screen.findByText('Opening shot'); fireEvent.click(button('Opening shot'))
  const inspectOpening = handler(button('Inspect selected metadata'))
  fireEvent.click(button('Ending shot')); act(inspectOpening)
  expect(screen.queryByRole('dialog')).toBeNull()
  fireEvent.click(button('Inspect selected metadata'))
  const closeOldDialog = handler(button('Close timeline metadata'))
  fireEvent.click(button('Close timeline metadata')); fireEvent.click(button('Inspect selected metadata'))
  act(closeOldDialog); expect(screen.getByRole('dialog')).toBeTruthy()
  const inspectOldOwner = handler(button('Inspect selected metadata'))
  await act(async () => view.rerender(host(value, { target: { ...target, timelineId: timelineId('other') } })))
  act(inspectOldOwner); expect(screen.queryByRole('dialog')).toBeNull()
})

function retainedClick(element: HTMLElement): () => void {
  const key = Object.keys(element).find(key => key.startsWith('__reactProps$'))!
  return (element as unknown as Record<string, { onClick: () => void }>)[key].onClick
}

it.each(['revision', 'source'] as const)('IR01-1 rejects actual shared toolbar callbacks after %s replacement in the same store', async change => {
  let store!: InteractionStore
  const value = source(), options = { onStore: (next: InteractionStore) => { store = next } }
  const view = render(host(value, options))
  await screen.findByText('Opening shot'); fireEvent.click(button('Opening shot'))
  const originalStore = store, lifetime = store.getSnapshot().lifetime
  const toolbar = () => within(screen.getByRole('toolbar', { name: 'Selection actions' }))
  fireEvent.click(toolbar().getByText('More'))
  const callbacks = ['Clear selection', 'Hide inspector', 'Reveal primary clip', 'Edit local properties', 'Ask Agent'].map(name => ({ name, invoke: retainedClick(toolbar().getByRole('button', { name })), inspectorOpen: !['Edit local properties'].includes(name) }))
  fireEvent.click(toolbar().getByRole('button', { name: 'Hide inspector' }))
  callbacks.push({ name: 'Show inspector', invoke: retainedClick(toolbar().getByRole('button', { name: 'Show inspector' })), inspectorOpen: false })
  view.rerender(host(change === 'source' ? source() : value, { ...options, target: change === 'revision' ? { ...target, revisionId: revisionId('r2') } : target }))
  await screen.findByText('Opening shot'); fireEvent.click(button('Opening shot'))
  expect(store).toBe(originalStore)
  expect(store.getSnapshot().lifetime).not.toBe(lifetime)
  const dispatch = vi.spyOn(store, 'dispatch')
  for (const callback of callbacks) {
    act(() => {
      store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['clip:opening'] })
      store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'agent', open: false })
    })
    act(() => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'inspect', open: callback.inspectorOpen }))
    const before = store.getSnapshot(); dispatch.mockClear()
    act(callback.invoke)
    expect.soft(dispatch, callback.name).not.toHaveBeenCalled()
    expect.soft(store.getSnapshot(), callback.name).toBe(before)
  }
})

it('IR01-2 discards shared mobile track inspection after clear before selecting a clip', async () => {
  render(host(source(), { inspector: true }))
  await screen.findByText('Opening shot'); fireEvent.click(button('Picture'))
  const launcher = button('Open selection properties'); launcher.focus(); fireEvent.click(launcher)
  const dialog = screen.getByRole('dialog', { name: 'Selection properties' })
  fireEvent.click(within(dialog).getByRole('button', { name: 'Clear track selection' }))
  expect(screen.queryByRole('dialog')).toBeNull()
  fireEvent.click(button('Ending shot'))
  expect(screen.queryByRole('dialog')).toBeNull()
  const nextLauncher = button('Open selection properties'); nextLauncher.focus(); fireEvent.click(nextLauncher)
  fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
  expect(document.activeElement).toBe(nextLauncher)
})

it.each(['clear', 'hide', 'primary'] as const)('IR01-2 discards metadata opening intent after %s instead of reviving it on selection', async change => {
  let store!: InteractionStore
  render(host(source(), { onStore: next => { store = next } }))
  await screen.findByText('Opening shot'); fireEvent.click(button('Opening shot'))
  fireEvent.click(button('Inspect selected metadata'))
  if (change === 'clear') act(() => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [] }))
  if (change === 'hide') {
    fireEvent.click(button('Hide inspector'))
    expect(screen.queryByRole('dialog')).toBeNull()
    fireEvent.click(button('Show inspector'))
  }
  fireEvent.click(button('Ending shot'))
  expect(screen.queryByRole('dialog')).toBeNull()
  fireEvent.click(button('Opening shot'))
  expect(screen.queryByRole('dialog')).toBeNull()
  const launcher = button('Inspect selected metadata'); launcher.focus(); fireEvent.click(launcher)
  expect(screen.getByRole('dialog', { name: 'Timeline object metadata' })).toBeTruthy()
  fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
  expect(document.activeElement).toBe(launcher)
})

it.each(['revision', 'source'] as const)('IR01-2 retires open shared/mobile and metadata inspectors across %s replacement', async change => {
  let store!: InteractionStore
  const value = source(), options = { inspector: true, onStore: (next: InteractionStore) => { store = next } }
  const view = render(host(value, options))
  await screen.findByText('Opening shot'); fireEvent.click(button('Opening shot'))
  const originalStore = store
  fireEvent.click(button('Inspect selected metadata'))
  fireEvent.click(button('Open selection properties'))
  expect(screen.getAllByRole('dialog')).toHaveLength(2)
  view.rerender(host(change === 'source' ? source() : value, { ...options, target: change === 'revision' ? { ...target, revisionId: revisionId('r2') } : target }))
  await screen.findByText('Opening shot')
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(store).toBe(originalStore)
  fireEvent.click(button('Opening shot'))
  expect(screen.queryByRole('dialog')).toBeNull()
  fireEvent.click(button('Open selection properties'))
  expect(screen.getByRole('dialog', { name: 'Selection properties' })).toBeTruthy()
})
