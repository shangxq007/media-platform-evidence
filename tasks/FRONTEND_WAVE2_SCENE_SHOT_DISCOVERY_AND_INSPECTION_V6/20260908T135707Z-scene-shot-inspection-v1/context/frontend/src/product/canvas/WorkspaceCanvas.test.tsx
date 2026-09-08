import { LocalizationProvider } from '../../localization'
import { SelectionProvider, useInteractionStore, useSelection } from '../../interaction/SelectionContext'
import { SelectionInspector } from '../../interaction/InteractionShell'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ProjectContextProvider } from '../../foundation/projectContext'
import { platformClient } from '../../foundation/platformClient'
import { CanvasContent } from './WorkspaceCanvas'
import * as canvasModel from './model'
import type { SurfaceAdapter } from '../../interaction/model'
import { readFileSync } from 'node:fs'


// Read CSS directly because Vitest stubs stylesheet imports in component tests.
const foundationStyles = readFileSync('src/styles/foundation.css', 'utf8')

let activeStore: ReturnType<typeof useInteractionStore>
let observeAdapter = false
let registeredAdapter: SurfaceAdapter
let unregisterAdapter: () => void
function SnapshotProbe() {
  activeStore = useInteractionStore()
  if (observeAdapter && !vi.isMockFunction(activeStore.register)) {
    const register = activeStore.register
    vi.spyOn(activeStore, 'register').mockImplementation(adapter => {
      registeredAdapter = adapter
      unregisterAdapter = register(adapter)
      return unregisterAdapter
    })
  }
  const snapshot = useSelection(); return <output data-testid="canvas-snapshot">{JSON.stringify(snapshot)}</output> }

function setup(locale: 'en' | 'zh-CN' = 'en') {
  vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({ workspace: { id: 'w1', name: 'Workspace' }, tenantId: 't1', recentProjects: [{ id: 'p1', name: 'First project' }, { id: 'p2', name: 'Second project' }] })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const content = (workspaceId = 'w1', projectId = 'p1') => <LocalizationProvider initialLocale={locale}><QueryClientProvider client={client}><ProjectContextProvider workspaceId={workspaceId} projectId={projectId}><SelectionProvider scope={{ surfaceId: 'canvas', workspaceId: workspaceId, projectId: projectId }}><div className="ff-app-shell" data-studio="horizontal"><CanvasContent /></div><SelectionInspector /><SnapshotProbe /></SelectionProvider></ProjectContextProvider></QueryClientProvider></LocalizationProvider>
  return { ...render(content()), content }
}

afterEach(() => { observeAdapter = false; vi.restoreAllMocks() })

describe('canvas local interactions', () => {
  it('distinguishes focus from selection, moves focused nodes, edits placement and clears to the canvas', async () => {
    setup()
    await screen.findByText('First project')
    const note = screen.getByRole('button', { name: 'Local composition note' })
    act(() => note.focus())
    expect(note.getAttribute('aria-pressed')).toBe('false')
    fireEvent.keyDown(note, { key: 'ArrowRight' })
    expect(note.style.left).toBe('454px')
    expect(note.getAttribute('aria-pressed')).toBe('true')
    expect((screen.getByLabelText('Local X') as HTMLInputElement).value).toBe('454')
    fireEvent.change(screen.getByLabelText('Local Y'), { target: { value: '-50' } })
    expect(note.style.top).toBe('-50px')
    fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Scene notes' } })
    expect(screen.getByRole('button', { name: 'Scene notes' })).toBe(note)
    fireEvent.keyDown(note, { key: 'Escape' })
    expect(note.getAttribute('aria-pressed')).toBe('false')
    expect(document.activeElement).toBe(screen.getByRole('region', { name: 'Infinite canvas workspace' }))
    expect(screen.queryByLabelText('Local title')).toBeNull()
    fireEvent.click(note)
    fireEvent.click(screen.getByRole('region', { name: 'Infinite canvas workspace' }))
    expect(note.getAttribute('aria-pressed')).toBe('false')
  })

  it('bounds zoom, resets the viewport, and leaves native controls and modified keys alone', async () => {
    setup()
    await screen.findByText('First project')
    fireEvent.click(screen.getByText('More viewport controls'))
    const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
    const node = screen.getByRole('button', { name: 'Project reference' })
    fireEvent.click(node)
    const title = screen.getByLabelText('Local title')
    expect(fireEvent.keyDown(title, { key: 'ArrowLeft' })).toBe(true)
    for (const modifier of ['ctrlKey', 'altKey', 'metaKey', 'shiftKey']) {
      expect(fireEvent.keyDown(node, { key: 'ArrowRight', [modifier]: true })).toBe(true)
      expect(fireEvent.keyDown(stage, { key: '=', [modifier]: true })).toBe(true)
    }
    expect(node.style.left).toBe('120px')
    for (let index = 0; index < 30; index++) fireEvent.keyDown(stage, { key: '=' })
    expect((screen.getByRole('button', { name: 'Zoom in' }) as HTMLButtonElement).disabled).toBe(true)
    expect(screen.getByText('200%')).toBeTruthy()
    for (let index = 0; index < 30; index++) fireEvent.click(screen.getByRole('button', { name: 'Zoom out' }))
    expect(screen.getByText('50%')).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Zoom out' }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.keyDown(stage, { key: 'ArrowRight' })
    fireEvent.click(screen.getByRole('button', { name: 'Reset viewport' }))
    expect(screen.getByText('100%')).toBeTruthy()
    expect(stage.querySelector('.ff-canvas-viewport')?.getAttribute('style')).toContain('translate(0px, 0px)')
    expect(node.getAttribute('aria-pressed')).toBe('true')
  })

  it('resets local titles, placement and selection across project and workspace navigation', async () => {
    const view = setup()
    await screen.findByText('First project')
    fireEvent.click(screen.getByRole('button', { name: 'Project reference' }))
    fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Do not leak' } })
    view.rerender(view.content('w1', 'p2'))
    expect(screen.queryByText('Do not leak')).toBeNull()
    expect(screen.queryByLabelText('Local title')).toBeNull()
    expect(await screen.findByText('Second project')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
    fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Workspace note' } })
    view.rerender(view.content('w2', 'p2'))
    expect(screen.queryByText('Workspace note')).toBeNull()
    expect(screen.getByRole('button', { name: 'Local composition note' }).getAttribute('aria-pressed')).toBe('false')
  })
})

it('fits a measured mobile stage without selecting, then reveals the selected node without moving it', async () => {
  setup()
  await screen.findByText('First project')
  const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
  vi.spyOn(stage, 'getBoundingClientRect').mockReturnValue({ width: 358, height: 340, left: 0, top: 0, right: 358, bottom: 340, x: 0, y: 0, toJSON: () => ({}) })
  fireEvent.click(screen.getByRole('button', { name: 'Fit canvas' }))
  expect(screen.queryByLabelText('Local title')).toBeNull()
  const note = screen.getByRole('button', { name: 'Local composition note' })
  fireEvent.click(note)
  fireEvent.click(screen.getByRole('button', { name: 'Reveal primary node' }))
  expect(note.style.left).toBe('430px')
  expect(note.getAttribute('aria-pressed')).toBe('true')
  expect(stage.querySelector('.ff-canvas-viewport')?.getAttribute('style')).toContain('translate(-366px, -140px)')
  fireEvent.click(screen.getByRole('button', { name: 'Clear selection' }))
  expect(screen.queryByLabelText('Local title')).toBeNull()
})

it('keeps local selection and edits when toggling the shared inspector and frees stage space', async () => {
  const view = setup()
  const styles = document.createElement('style')
  styles.textContent = foundationStyles
  view.container.append(styles)
  await screen.findByText('First project')
  const note = screen.getByRole('button', { name: 'Local composition note' })
  fireEvent.click(note)
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Scene notes' } })
  fireEvent.change(screen.getByLabelText('Local X'), { target: { value: '500' } })
  const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
  const grid = stage.parentElement!
  const expandedColumns = getComputedStyle(grid).gridTemplateColumns
  const expandedHeight = getComputedStyle(stage).height
  const toggle = screen.getByRole('button', { name: 'Hide inspector' })
  expect(toggle.tagName).toBe('BUTTON')
  expect(toggle.getAttribute('aria-expanded')).toBe('true')
  expect(document.getElementById(toggle.getAttribute('aria-controls')!)).toBeTruthy()
  act(() => toggle.focus())
  fireEvent.click(toggle)
  expect(screen.getByRole('button', { name: 'Show inspector' })).toBe(toggle)
  expect(toggle.getAttribute('aria-expanded')).toBe('false')
  expect(document.activeElement).toBe(toggle)
  expect(screen.queryByLabelText('Local title')).toBeNull()
  expect(note.getAttribute('aria-pressed')).toBe('true')
  expect(note.style.left).toBe('500px')
  expect(screen.queryByRole('complementary', { name: 'Selection inspector' })).toBeNull()
  expect(getComputedStyle(grid).gridTemplateColumns).toBe('minmax(0, 1fr)')
  // Focus alone still does not select a different node while the inspector is hidden.
  act(() => screen.getByRole('button', { name: 'Project reference' }).focus())
  expect(note.getAttribute('aria-pressed')).toBe('true')
  act(() => note.focus())
  fireEvent.keyDown(note, { key: 'ArrowRight' })
  expect(screen.queryByLabelText('Local title')).toBeNull()
  act(() => toggle.focus())
  fireEvent.click(toggle)
  expect(document.activeElement).toBe(toggle)
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Scene notes')
  expect((screen.getByLabelText('Local X') as HTMLInputElement).value).toBe('524')
  expect(note.getAttribute('aria-pressed')).toBe('true')
  expect(getComputedStyle(grid).gridTemplateColumns).toBe(expandedColumns)
  expect(getComputedStyle(stage).height).toBe(expandedHeight)
})

it('toggles ordered Canvas membership with Ctrl/Meta, preserves group on focused-node-only nudge, and supports touch mode', async () => {
  setup()
  await screen.findByText('First project')
  const project = screen.getByRole('button', { name: 'Project reference' })
  const note = screen.getByRole('button', { name: 'Local composition note' })
  fireEvent.click(project)
  fireEvent.click(note, { ctrlKey: true })
  expect(project.getAttribute('aria-pressed')).toBe('true')
  expect(note.getAttribute('aria-pressed')).toBe('true')
  expect(screen.getByRole('toolbar', { name: 'Selection actions' }).textContent).toContain('2 selected')
  act(() => project.focus())
  fireEvent.keyDown(project, { key: 'ArrowRight' })
  expect(project.style.left).toBe('144px')
  expect(note.style.left).toBe('430px')
  expect(project.getAttribute('aria-pressed')).toBe('true')
  expect(note.getAttribute('aria-pressed')).toBe('true')
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Local composition note')
  fireEvent.click(note, { metaKey: true })
  expect(note.getAttribute('aria-pressed')).toBe('false')
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Project reference')
  fireEvent.click(screen.getByRole('button', { name: 'Multi-select' }))
  fireEvent.click(note)
  expect(project.getAttribute('aria-pressed')).toBe('true')
  expect(note.getAttribute('aria-pressed')).toBe('true')
  fireEvent.click(screen.getByRole('button', { name: 'Done' }))
  fireEvent.click(project)
  expect(note.getAttribute('aria-pressed')).toBe('false')
  fireEvent.click(screen.getByRole('button', { name: 'Clear selection' }))
  expect(project.getAttribute('aria-pressed')).toBe('false')
})

it('owns modified Enter/Space only on nodes, leaves native activation intact, and excludes text and IME', async () => {
  setup()
  await screen.findByText('First project')
  const project = screen.getByRole('button', { name: 'Project reference' })
  const note = screen.getByRole('button', { name: 'Local composition note' })
  act(() => note.focus())
  expect(note.getAttribute('aria-pressed')).toBe('false')
  // Native activation is represented by click; DOM emulation does not synthesize keyboard click.
  expect(fireEvent.keyDown(project, { key: 'Enter' })).toBe(true)
  fireEvent.click(project, { detail: 0 })
  expect(fireEvent.keyDown(note, { key: ' ', ctrlKey: true })).toBe(false)
  fireEvent.keyUp(note, { key: ' ', ctrlKey: true })
  expect(project.getAttribute('aria-pressed')).toBe('true')
  expect(note.getAttribute('aria-pressed')).toBe('true')
  fireEvent.keyDown(note, { key: 'Enter', metaKey: true })
  expect(note.getAttribute('aria-pressed')).toBe('false')
  expect(fireEvent.keyDown(note, { key: 'Enter', ctrlKey: true, isComposing: true })).toBe(false)
  expect(fireEvent.keyDown(note, { key: 'ArrowRight', isComposing: true })).toBe(true)
  expect(note.style.left).toBe('430px')
  const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
  for (const tag of ['input', 'textarea', 'select', 'div']) {
    const input = document.createElement(tag)
    if (tag === 'div') input.setAttribute('contenteditable', 'true')
    stage.append(input)
    for (const key of ['Escape', 'ArrowRight', 'Enter', ' ']) expect(fireEvent.keyDown(input, { key, ctrlKey: key === ' ' })).toBe(true)
    input.remove()
  }
  expect(project.getAttribute('aria-pressed')).toBe('true')
  const edge = stage.querySelector('.ff-visual-edge')!
  expect(edge.getAttribute('aria-hidden')).toBe('true')
  expect(edge.hasAttribute('tabindex')).toBe(false)
  expect(edge.hasAttribute('data-canvas-node')).toBe(false)
  expect(foundationStyles).toMatch(/\.ff-canvas-node:focus-visible[^}]*outline: 3px/)
})

it('localizes bounded selection help, count, primary-only Inspector and touch controls in Chinese', async () => {
  setup('zh-CN')
  await screen.findByText('First project')
  fireEvent.click(screen.getByRole('button', { name: '多选' }))
  fireEvent.click(screen.getByRole('button', { name: 'Project reference' }))
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  expect(screen.getByRole('toolbar', { name: '选择操作' }).textContent).toContain('已选择 2 个')
  expect(screen.getByRole('complementary', { name: '选择检查器' }).textContent).toContain('现有操作仅影响主要对象')
  expect(screen.getByText(/已选择 2 个 · 主要对象：/).getAttribute('role')).toBe('status')
  expect(screen.getByText(/Ctrl\/Meta/).textContent).toContain('切换选择')
  expect(screen.getByRole('button', { name: '完成' })).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '清除选择' }))
  expect(screen.getByText(/已选择 0 个 · 主要对象：/).getAttribute('role')).toBe('status')
})

it('projects scoped node identity separately from explicitly mapped application references', async () => {
  setup()
  await screen.findByText('First project')
  fireEvent.click(screen.getByRole('button', { name: 'Project reference' }))
  const snapshot = JSON.parse(screen.getByTestId('canvas-snapshot').textContent!)
  expect(snapshot.selectedRefs).toEqual([{ workspaceId: 'w1', projectId: 'p1', surfaceId: 'canvas', kind: 'NODE', localId: 'project-node' }])
  expect(snapshot.selectedObjects[0].logicalRef).toEqual({ kind: 'PROJECT', referenceId: 'project-ref', entityId: 'p1' })
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Only local' } })
  const renamed = JSON.parse(screen.getByTestId('canvas-snapshot').textContent!)
  expect(renamed.selectedObjects[0].logicalRef).toEqual(snapshot.selectedObjects[0].logicalRef)
  expect(renamed.selectedRefs).toEqual(snapshot.selectedRefs)
  expect(screen.getByText('First project')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  expect(JSON.parse(screen.getByTestId('canvas-snapshot').textContent!).selectedObjects[0].logicalRef).toBeUndefined()
})


it('cancels native node activation during composition without taking over editable or unrelated keys', async () => {
  setup()
  await screen.findByText('First project')
  const project = screen.getByRole('button', { name: 'Project reference' })
  const note = screen.getByRole('button', { name: 'Local composition note' })
  const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
  fireEvent.click(project)
  const snapshot = screen.getByTestId('canvas-snapshot').textContent
  for (const composition of [{ isComposing: true }, { keyCode: 229 }]) {
    for (const key of ['Enter', ' ']) {
      expect(fireEvent.keyDown(note, { key, ...composition })).toBe(false)
      expect(fireEvent.keyDown(note, { key, ctrlKey: true, ...composition })).toBe(false)
      expect(fireEvent.keyDown(stage, { key, ...composition })).toBe(true)
    }
    for (const key of ['Escape', 'ArrowRight', 'r']) expect(fireEvent.keyDown(note, { key, ...composition })).toBe(true)
    for (const tag of ['input', 'textarea', 'select', 'div']) {
      const editable = document.createElement(tag)
      if (tag === 'div') editable.setAttribute('contenteditable', 'true')
      stage.append(editable)
      for (const key of ['Enter', ' ', 'Escape']) expect(fireEvent.keyDown(editable, { key, ...composition })).toBe(true)
      editable.remove()
    }
  }
  expect(screen.getByTestId('canvas-snapshot').textContent).toBe(snapshot)
  expect(note.style.left).toBe('430px')
  expect(fireEvent.keyDown(note, { key: 'Enter' })).toBe(true)
  expect(fireEvent.keyDown(note, { key: ' ' })).toBe(true)
})

// Simulated capture ownership only: happy-dom does not perform native pointer routing or click synthesis.
function pointerFixture() {
  const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
  const captured = new Set<number>()
  const capture = vi.fn((id: number) => { captured.add(id) })
  const release = vi.fn((id: number) => { captured.delete(id) })
  Object.defineProperties(stage, {
    setPointerCapture: { configurable: true, value: capture },
    releasePointerCapture: { configurable: true, value: release },
    hasPointerCapture: { configurable: true, value: (id: number) => captured.has(id) },
  })
  const project = screen.getByRole('button', { name: 'Project reference' })
  const note = screen.getByRole('button', { name: 'Local composition note' })
  const pointer = (type: 'pointerDown' | 'pointerMove' | 'pointerUp' | 'pointerCancel' | 'lostPointerCapture', target: Element, x = 0, y = 0, extra = {}) => fireEvent[type](target, { pointerId: 7, pointerType: 'mouse', isPrimary: true, button: 0, clientX: x, clientY: y, ...extra })
  return { stage, project, note, pointer, capture, release, captured }
}

describe('Slice1C node-origin captured click', () => {
  it.each([
    ['stage', 0, 'single'], ['viewport', 2, 'single'], ['stage', 2, 'group'], ['viewport', 0, 'group'],
  ] as const)('completes %s-targeted delta %s plain click from %s selection and permits the next background gesture', async (target, delta, membership) => {
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer } = pointerFixture()
    fireEvent.click(project)
    if (membership === 'group') fireEvent.click(note, { ctrlKey: true })
    const background = target === 'stage' ? stage : stage.querySelector('.ff-canvas-viewport')!
    pointer('pointerDown', project, 100, 100)
    expect(activeStore.getSnapshot().selectedRefs).toHaveLength(membership === 'group' ? 2 : 1)
    pointer('pointerMove', stage, 100 + delta, 100 + delta)
    pointer('pointerUp', stage, 100 + delta, 100 + delta)
    fireEvent.click(background, { detail: 1, clientX: 100 + delta, clientY: 100 + delta })
    // Existing plain node activation replaces membership; only a completed drag preserves the group.
    expect(activeStore.getSnapshot().selectedRefs.map(ref => ref.localId)).toEqual(['project-node'])
    expect(project.style.left).toBe('120px'); expect(note.style.left).toBe('430px')
    pointer('pointerDown', background, 0, 0); pointer('pointerUp', stage, 0, 0)
    fireEvent.click(background, { detail: 1 })
    expect(activeStore.getSnapshot().selectedRefs).toEqual([])
  })
  it('discards an undelivered completion on a new pointer interaction or keyboard activation', async () => {
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer } = pointerFixture()
    pointer('pointerDown', project, 100, 100); pointer('pointerUp', stage, 100, 100)
    // No click delivered for the first gesture; a later node interaction must own its own result.
    pointer('pointerDown', note, 200, 200); pointer('pointerUp', stage, 200, 200)
    fireEvent.click(stage, { detail: 1, clientX: 200, clientY: 200 })
    expect(activeStore.getSnapshot().selectedRefs.map(ref => ref.localId)).toEqual(['note-node'])
    pointer('pointerDown', note, 200, 200); pointer('pointerUp', stage, 200, 200)
    fireEvent.keyDown(project, { key: 'Enter' }); fireEvent.click(project, { detail: 0 })
    expect(activeStore.getSnapshot().selectedRefs.map(ref => ref.localId)).toEqual(['project-node'])
    fireEvent.click(stage, { detail: 1 })
    expect(activeStore.getSnapshot().selectedRefs).toEqual([])
  })
  it.each(['revision', 'pointerCancel', 'lostPointerCapture'] as const)('never revives node intent after %s and does not suppress a later node interaction', async reason => {
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer } = pointerFixture()
    pointer('pointerDown', project, 100, 100)
    if (reason === 'revision') {
      pointer('pointerUp', stage, 100, 100)
      act(() => activeStore.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [] }))
    } else {
      pointer(reason, stage, 100, 100); pointer('pointerUp', stage, 100, 100)
    }
    const before = activeStore.getSnapshot()
    fireEvent.click(stage, { detail: 1, clientX: 100, clientY: 100 })
    expect(activeStore.getSnapshot()).toBe(before)
    pointer('pointerDown', note, 200, 200); pointer('pointerUp', stage, 200, 200)
    fireEvent.click(stage, { detail: 1, clientX: 200, clientY: 200 })
    expect(activeStore.getSnapshot().selectedRefs.map(ref => ref.localId)).toEqual(['note-node'])
  })
  it('retains initial node selection when the zero-movement click targets the capturing stage', async () => {
    setup(); await screen.findByText('First project')
    const { stage, project, pointer, captured } = pointerFixture()
    pointer('pointerDown', project, 100, 100)
    expect(captured.has(7)).toBe(true)
    const selected = activeStore.getSnapshot()
    expect(selected.selectedRefs.map(ref => ref.localId)).toEqual(['project-node'])
    pointer('pointerUp', stage, 100, 100)
    fireEvent.click(stage, { detail: 1, clientX: 100, clientY: 100 })
    expect(activeStore.getSnapshot().selectedRefs).toEqual(selected.selectedRefs)
    expect(activeStore.getSnapshot().revision).toBe(selected.revision)
    expect(captured.has(7)).toBe(false)
  })
})

describe('Slice1B selection layout correction', () => {
  afterEach(() => vi.unstubAllGlobals())

  async function selectionLayoutFixture() {
    const observers = new Set<() => void>()
    vi.stubGlobal('ResizeObserver', class {
      constructor(private callback: () => void) {}
      observe() { observers.add(this.callback) }
      disconnect() { observers.delete(this.callback) }
    })
    setup(); await screen.findByText('First project')
    const fixture = pointerFixture()
    const { stage, project } = fixture
    let external = { x: 0, y: 0, width: 0, height: 0 }
    // happy-dom has no layout: geometry follows the COMMITTED shared selection UI,
    // not the synchronous store snapshot. These are the native RCA stage dimensions.
    const rect = vi.spyOn(stage, 'getBoundingClientRect').mockImplementation(() => {
      const selected = Boolean(screen.queryByRole('toolbar', { name: 'Selection actions' }))
      const x = 24 + external.x, y = (selected ? 476.59375 : 434.59375) + external.y
      const width = (selected ? 1097 : 1392) + external.width, height = 520 + external.height
      return { x, y, left: x, top: y, width, height, right: x + width, bottom: y + height, toJSON: () => ({}) }
    })
    vi.spyOn(project, 'getBoundingClientRect').mockImplementation(() => {
      const bounds = stage.getBoundingClientRect()
      return { x: 450, y: bounds.top + 110, left: 450, top: bounds.top + 110, width: 230, height: 160, right: 680, bottom: bounds.top + 270, toJSON: () => ({}) }
    })
    fireEvent.click(screen.getByRole('button', { name: 'Fit canvas' }))
    const deliverResize = () => act(() => { for (const callback of observers) callback() })
    return { ...fixture, rect, deliverResize, resize: (delta: typeof external) => { external = delta } }
  }

  it('initial unselected drag survives committed selection stage shift and ResizeObserver delivery before move', async () => {
    const { stage, project, note, pointer, capture, release, deliverResize } = await selectionLayoutFixture()
    const viewport = stage.querySelector<HTMLElement>('.ff-canvas-viewport')!
    const camera = viewport.style.transform
    expect(camera).toBe('translate(306px, 20px) scale(1)')
    expect(activeStore.getSnapshot().selectedRefs).toEqual([])
    const before = activeStore.getSnapshot()
    pointer('pointerDown', project, 566, 625.59375)
    const selected = activeStore.getSnapshot()
    expect(selected.selectedRefs.map(ref => ref.localId)).toEqual(['project-node'])
    expect(selected.revision).toBe(before.revision + 1)
    expect(stage.getBoundingClientRect().top).toBe(476.59375)
    expect(stage.getBoundingClientRect().width).toBe(1097)
    deliverResize()
    pointer('pointerMove', stage, 614, 649.59375)
    expect(project.style.left).toBe('168px'); expect(project.style.top).toBe('114px')
    expect(note.style.left).toBe('430px'); expect(note.style.top).toBe('230px')
    expect(viewport.style.transform).toBe(camera)
    expect(activeStore.getSnapshot()).toBe(selected)
    expect(selected.selectedObjects[0].x).toBe(120)
    expect(capture).toHaveBeenCalledWith(7)
    expect(release).not.toHaveBeenCalled()
    pointer('pointerUp', stage, 614, 649.59375)
    expect(project.style.left).toBe('168px'); expect(project.style.top).toBe('114px')
    expect(activeStore.getSnapshot().selectedObjects[0].x).toBe(168)
    expect(release).toHaveBeenCalledWith(7)
    // Once idle, ordinary observer-driven reveal still works.
    deliverResize()
    expect(viewport.style.transform).not.toBe(camera)
  })

  it.each(['origin', 'width', 'height', 'camera'] as const)('still cancels external %s invalidation after selection layout settles', async reason => {
    const { stage, project, pointer, release, deliverResize, resize } = await selectionLayoutFixture()
    pointer('pointerDown', project, 566, 625.59375)
    deliverResize()
    pointer('pointerMove', stage, 614, 649.59375)
    expect(project.style.left).toBe('168px')
    if (reason === 'camera') fireEvent.keyDown(stage, { key: '+' })
    else {
      resize({ x: 0, y: reason === 'origin' ? 10 : 0, width: reason === 'width' ? -100 : 0, height: reason === 'height' ? -100 : 0 })
      deliverResize()
    }
    pointer('pointerUp', stage, 614, 649.59375)
    expect(project.style.left).toBe('120px'); expect(project.style.top).toBe('90px')
    expect(activeStore.getSnapshot().selectedObjects[0].x).toBe(120)
    expect(release).toHaveBeenCalledWith(7)
  })

  it('renders the captured camera without a CSS transform transition during drag and pan', async () => {
    setup(); await screen.findByText('First project')
    const { stage, project, pointer } = pointerFixture()
    const viewport = stage.querySelector<HTMLElement>('.ff-canvas-viewport')!
    fireEvent.keyDown(stage, { key: '+' })
    pointer('pointerDown', project, 100, 100)
    expect(viewport.style.transition).toBe('none')
    pointer('pointerUp', stage, 148, 124)
    fireEvent.click(screen.getByRole('button', { name: 'Pan' }))
    pointer('pointerDown', stage, 100, 100); pointer('pointerMove', stage, 148, 124)
    expect(viewport.style.transition).toBe('none')
    pointer('pointerUp', stage, 148, 124)
  })
})

describe('Slice1B border origin correction', () => {
  afterEach(() => vi.unstubAllGlobals())

  async function borderOriginFixture(zoom = 1) {
    const observers = new Set<() => void>()
    vi.stubGlobal('ResizeObserver', class {
      constructor(private callback: () => void) {}
      observe() { observers.add(this.callback) }
      disconnect() { observers.delete(this.callback) }
    })
    setup(); await screen.findByText('First project')
    const fixture = pointerFixture()
    const geometry = { left: 24, top: 434.59375, width: 1392, height: 520, clientLeft: 1, clientTop: 1 }
    // Explicit border metrics: happy-dom's default clientLeft/clientTop are zero.
    Object.defineProperties(fixture.stage, {
      clientLeft: { configurable: true, get: () => geometry.clientLeft },
      clientTop: { configurable: true, get: () => geometry.clientTop },
    })
    vi.spyOn(fixture.stage, 'getBoundingClientRect').mockImplementation(() => ({
      ...geometry, x: geometry.left, y: geometry.top,
      right: geometry.left + geometry.width, bottom: geometry.top + geometry.height, toJSON: () => ({}),
    }))
    fireEvent.click(screen.getByRole('button', { name: 'Fit canvas' }))
    for (let step = 0; step < Math.round(Math.abs(zoom - 1) * 10); step++) fireEvent.keyDown(fixture.stage, { key: zoom < 1 ? '-' : '+' })
    const viewport = fixture.stage.querySelector<HTMLElement>('.ff-canvas-viewport')!
    expect(viewport.style.transform).toBe(`translate(306px, 20px) scale(${zoom})`)
    const client = (x: number, y: number) => [geometry.left + geometry.clientLeft + 306 + x * zoom, geometry.top + geometry.clientTop + 20 + y * zoom] as const
    vi.spyOn(fixture.project, 'getBoundingClientRect').mockImplementation(() => {
      const [left, top] = client(120, 90), width = 230 * zoom, height = 160 * zoom
      return { x: left, y: top, left, top, width, height, right: left + width, bottom: top + height, toJSON: () => ({}) }
    })
    return { ...fixture, geometry, client, deliverResize: () => act(() => { for (const callback of observers) callback() }) }
  }

  it('maps the native Project left/top vector exactly to model (120,90)', async () => {
    const { stage, pointer, client } = await borderOriginFixture()
    expect(client(120, 90)).toEqual([451, 545.59375])
    const conversion = vi.spyOn(canvasModel, 'screenToCanvas') // Call through the real component conversion.
    pointer('pointerDown', stage, 451, 545.59375)
    expect(conversion).toHaveBeenLastCalledWith({ x: 451, y: 545.59375 }, expect.objectContaining({ x: 25, y: 435.59375 }), { x: 306, y: 20 }, 1)
    expect(conversion.mock.results[conversion.mock.results.length - 1]?.value).toEqual({ x: 120, y: 90 })
    pointer('pointerUp', stage, ...client(130, 100))
    expect(activeStore.getSnapshot().selectedRefs.map(ref => ref.localId)).toEqual(['project-node'])
  })

  it.each([0.5, 1, 2])('aligns forward and reverse marquee preview to client pointers at zoom %s with border and pan', async zoom => {
    const { stage, pointer, client, geometry, deliverResize, release } = await borderOriginFixture(zoom)
    for (const reverse of [false, true]) {
      const low = client(70, 40), high = client(110, 80)
      const start = reverse ? high : low, end = reverse ? low : high
      pointer('pointerDown', stage, ...start)
      deliverResize() // Matching border and outer geometry must preserve capture.
      expect(release).not.toHaveBeenCalled()
      pointer('pointerMove', stage, ...end)
      const preview = stage.querySelector<HTMLElement>('[data-canvas-marquee]')!
      expect(preview).not.toBeNull()
      expect(Number.parseFloat(preview.style.left) + geometry.left + geometry.clientLeft).toBe(low[0])
      expect(Number.parseFloat(preview.style.top) + geometry.top + geometry.clientTop).toBe(low[1])
      expect(Number.parseFloat(preview.style.width)).toBe(high[0] - low[0])
      expect(Number.parseFloat(preview.style.height)).toBe(high[1] - low[1])
      pointer('pointerUp', stage, ...end)
      expect(stage.querySelector('[data-canvas-marquee]')).toBeNull()
      release.mockClear()
    }
  })

  describe.each([0.5, 1, 2])('absolute marquee at zoom %s with border and pan', zoom => {
    it.each(['left contact', 'left positive', 'top contact', 'top positive'])('%s respects positive-area intersection', async boundary => {
      const { stage, pointer, client } = await borderOriginFixture(zoom)
      const positive = boundary.endsWith('positive'), inset = positive ? 0.25 : 0
      const start = boundary.startsWith('left') ? client(100, 100) : client(130, 70)
      const end = boundary.startsWith('left') ? client(120 + inset, 120) : client(150, 90 + inset)
      pointer('pointerDown', stage, ...start)
      pointer('pointerMove', stage, ...end)
      pointer('pointerUp', stage, ...end)
      expect(activeStore.getSnapshot().selectedRefs.map(ref => ref.localId)).toEqual(positive ? ['project-node'] : [])
    })
  })

  describe.each(['drag', 'marquee'] as const)('%s geometry cancellation with border', kind => {
    it.each(['border left move', 'border top up', 'border left observer', 'border top observer', 'outer origin with fixed drawing origin up', 'width move', 'height observer'])('fails closed on %s', async reason => {
      const { stage, project, note, pointer, client, geometry, deliverResize, release } = await borderOriginFixture()
      if (kind === 'drag') { fireEvent.click(project); fireEvent.click(note, { ctrlKey: true }) }
      const before = activeStore.getSnapshot()
      const start = client(100, 80), end = client(160, 120)
      pointer('pointerDown', kind === 'drag' ? project : stage, ...start)
      pointer('pointerMove', stage, ...end)
      if (kind === 'drag') expect(project.style.left).toBe('180px')
      else expect(stage.querySelector('[data-canvas-marquee]')).not.toBeNull()
      if (reason.startsWith('border left')) geometry.clientLeft += 1
      else if (reason.startsWith('border top')) geometry.clientTop += 1
      else if (reason.startsWith('outer')) { geometry.left -= 1; geometry.clientLeft += 1 }
      else if (reason.startsWith('width')) geometry.width -= 10
      else geometry.height -= 10
      if (reason.endsWith('observer')) deliverResize()
      else pointer(reason.endsWith('move') ? 'pointerMove' : 'pointerUp', stage, ...end)
      expect(release).toHaveBeenCalledWith(7)
      expect(stage.querySelector('[data-canvas-marquee]')).toBeNull()
      pointer('pointerUp', stage, ...end)
      expect(project.style.left).toBe('120px'); expect(project.style.top).toBe('90px')
      expect(note.style.left).toBe('430px'); expect(note.style.top).toBe('230px')
      expect(activeStore.getSnapshot()).toBe(before)
    })
  })
})

describe('Slice1B pointer transaction', () => {
  it.each(['single', 'group', 'unselected'])('%s drag previews locally and commits atomically only on up', async mode => {
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer, capture, release } = pointerFixture()
    fireEvent.click(project)
    if (mode === 'group') fireEvent.click(note, { ctrlKey: true })
    const target = mode === 'unselected' ? note : project
    pointer('pointerDown', target, 100, 100)
    const before = activeStore.getSnapshot()
    expect(capture).toHaveBeenCalledWith(7)
    expect(before.selectedRefs.map(r => r.localId)).toEqual(mode === 'group' ? ['project-node', 'note-node'] : [mode === 'single' ? 'project-node' : 'note-node'])
    pointer('pointerMove', stage, 140, 130)
    expect(activeStore.getSnapshot()).toBe(before)
    expect(activeStore.getSnapshot().selectedObjects.map(o => [o.x, o.y])).toEqual(before.selectedObjects.map(o => [o.x, o.y]))
    expect(target.style.left).toBe(mode === 'unselected' ? '470px' : '160px')
    if (mode === 'group') expect(note.style.left).toBe('470px')
    pointer('pointerUp', stage, 140, 130)
    expect(release).toHaveBeenCalledWith(7)
    expect(activeStore.getSnapshot().revision).toBe(before.revision + 1)
    expect(activeStore.getSnapshot().selectedRefs).toEqual(before.selectedRefs)
    expect(activeStore.getSnapshot().primaryRef).toEqual(before.primaryRef)
    expect(activeStore.getSnapshot().selectedObjects.map(o => [o.x, o.y])).toEqual(before.selectedObjects.map(o => [o.x! + 40, o.y! + 30]))
    expect(activeStore.getSnapshot()).not.toHaveProperty('receipt')
    fireEvent.click(target, { detail: 1 })
    expect(activeStore.getSnapshot().selectedRefs).toEqual(before.selectedRefs)
  })

  it.each(['pointerCancel', 'lostPointerCapture', 'Escape', 'revision', 'camera', 'adapter', 'missing'])('cancels %s without any partial group move or stale continuation', async reason => {
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer, release } = pointerFixture()
    fireEvent.click(project); fireEvent.click(note, { ctrlKey: true })
    pointer('pointerDown', project, 100, 100); pointer('pointerMove', stage, 140, 150)
    expect(project.style.left).toBe('160px')
    if (reason === 'pointerCancel' || reason === 'lostPointerCapture') pointer(reason, stage)
    else if (reason === 'Escape') fireEvent.keyDown(project, { key: 'Escape' })
    else if (reason === 'revision') act(() => activeStore.setTime({ unit: 'SIMULATED_STEP_0_20', playhead: 1 }))
    else if (reason === 'camera') fireEvent.keyDown(stage, { key: '+' })
    else if (reason === 'adapter') {
      // Live adapter absence modeled at the store boundary, without adding a production test API.
      const snapshot = activeStore.getSnapshot()
      vi.spyOn(activeStore, 'getSnapshot').mockReturnValue({ ...snapshot, lifetime: {}, selectedRefs: [], selectedObjects: [], primaryRef: null, primarySelectedObject: null, supported: [] })
    } else {
      const snapshot = activeStore.getSnapshot()
      vi.spyOn(activeStore, 'getSnapshot').mockReturnValue({ ...snapshot, selectedObjects: snapshot.selectedObjects.slice(1) })
    }
    pointer('pointerMove', stage, 160, 170); pointer('pointerUp', stage, 180, 190)
    expect(project.style.left).toBe('120px'); expect(note.style.left).toBe('430px')
    expect(project.style.top).toBe('90px'); expect(note.style.top).toBe('230px')
    expect(release).toHaveBeenCalledWith(7)
  })

  it('releases on scope lifetime unmount and rejects old events in the next project', async () => {
    const view = setup(); await screen.findByText('First project')
    const { stage, project, pointer, release } = pointerFixture()
    pointer('pointerDown', project, 100, 100); pointer('pointerMove', stage, 140, 130)
    view.rerender(view.content('w1', 'p2'))
    expect(release).toHaveBeenCalledWith(7)
    pointer('pointerUp', stage, 180, 180)
    expect(screen.getByRole('button', { name: 'Project reference' }).style.left).toBe('120px')
    expect(activeStore.getSnapshot().selectedRefs).toEqual([])
  })

  it('retains modifier clicks, taps, pointer identity and capture failure behavior', async () => {
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer, capture } = pointerFixture()
    fireEvent.click(project)
    for (const modifier of ['ctrlKey', 'metaKey']) {
      pointer('pointerDown', note, 10, 10, { [modifier]: true })
      expect(project.getAttribute('aria-pressed')).toBe('true')
      pointer('pointerUp', note, 10, 10, { [modifier]: true })
      fireEvent.click(note, { [modifier]: true, detail: 1 })
    }
    expect(note.getAttribute('aria-pressed')).toBe('false')
    pointer('pointerDown', project, 100, 100)
    pointer('pointerMove', stage, 200, 200, { pointerId: 8 })
    pointer('pointerUp', stage, 200, 200, { pointerId: 8 })
    expect(project.style.left).toBe('120px')
    pointer('pointerUp', stage, 102, 101)
    fireEvent.click(project, { detail: 1 })
    expect(project.style.left).toBe('120px')
    capture.mockImplementation(() => { throw new Error('capture unavailable') })
    pointer('pointerDown', project, 100, 100); pointer('pointerMove', stage, 200, 200); pointer('pointerUp', stage, 200, 200)
    expect(project.style.left).toBe('120px')
  })
})

describe('Slice1B marquee transaction', () => {
  it.each(['replace', 'ctrlKey', 'metaKey'])('%s completion uses model order despite scrambled DOM and preserves union order', async modifier => {
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer } = pointerFixture()
    fireEvent.click(note)
    project.parentElement!.prepend(note) // DOM order is deliberately the reverse of model order.
    const snapshot = activeStore.getSnapshot()
    pointer('pointerDown', stage, 0, 0, modifier === 'replace' ? {} : { [modifier]: true })
    pointer('pointerMove', stage, 700, 500)
    expect(activeStore.getSnapshot()).toBe(snapshot)
    expect(stage.querySelector('[data-canvas-marquee]')).not.toBeNull()
    pointer('pointerUp', stage, 700, 500)
    expect(activeStore.getSnapshot().selectedRefs.map(r => r.localId)).toEqual(modifier === 'replace' ? ['project-node', 'note-node'] : ['note-node', 'project-node'])
    expect(stage.querySelector('[data-canvas-marquee]')).toBeNull()
    fireEvent.click(stage, { detail: 1 })
    expect(activeStore.getSnapshot().selectedRefs).toHaveLength(2)
  })
  it.each([[0, 0, false], [3, 1, false], [4, 0, false], [0, 100, false], [3, 3, true], [4, 1, true]])('empty click or deliberate threshold %s,%s selects %s', async (x, y, selected) => {
    setup(); await screen.findByText('First project')
    const { stage, note, pointer } = pointerFixture()
    fireEvent.click(note)
    pointer('pointerDown', stage, 130, 100)
    pointer('pointerMove', stage, 130 + x, 100 + y)
    pointer('pointerUp', stage, 130 + x, 100 + y)
    expect(activeStore.getSnapshot().selectedRefs.map(r => r.localId)).toEqual(selected ? ['project-node'] : [])
  })
  it('Select arms marquee and Pan moves the camera only; mode change cancels before continuation', async () => {
    setup(); await screen.findByText('First project')
    const { stage, project, pointer } = pointerFixture()
    expect(screen.getByRole('button', { name: 'Select' }).getAttribute('aria-pressed')).toBe('true')
    fireEvent.click(project)
    fireEvent.click(screen.getByRole('button', { name: 'Pan' }))
    pointer('pointerDown', stage, 0, 0); pointer('pointerMove', stage, 40, 30)
    expect(stage.querySelector('[data-canvas-marquee]')).toBeNull()
    expect(stage.querySelector('.ff-canvas-viewport')?.getAttribute('style')).toContain('translate(40px, 30px)')
    pointer('pointerUp', stage, 40, 30)
    expect(project.style.left).toBe('120px')
    expect(activeStore.getSnapshot().selectedRefs.map(r => r.localId)).toEqual(['project-node'])
    fireEvent.click(screen.getByRole('button', { name: 'Select' }))
    pointer('pointerDown', stage, 0, 0); pointer('pointerMove', stage, 700, 500)
    fireEvent.click(screen.getByRole('button', { name: 'Pan' }))
    pointer('pointerUp', stage, 700, 500)
    expect(activeStore.getSnapshot().selectedRefs.map(r => r.localId)).toEqual(['project-node'])
  })
  it('excludes controls, editable content, overlays, visual edges and nonprimary/touch pointers', async () => {
    setup(); await screen.findByText('First project')
    const { stage, project, pointer, capture } = pointerFixture()
    fireEvent.click(project)
    const snapshot = activeStore.getSnapshot()
    for (const tag of ['button', 'input', 'textarea', 'select', 'div']) {
      const target = document.createElement(tag)
      if (tag === 'div') target.setAttribute('contenteditable', 'true')
      stage.append(target)
      pointer('pointerDown', target); pointer('pointerMove', stage, 700, 500); pointer('pointerUp', stage, 700, 500)
      fireEvent.click(target, { detail: 1 }); target.remove()
    }
    const overlay = document.createElement('div'); stage.append(overlay)
    const inspector = screen.getByRole('complementary', { name: 'Selection inspector' })
    const toolbar = screen.getByRole('toolbar', { name: 'Selection actions' })
    for (const target of [overlay, inspector, toolbar, stage.querySelector('.ff-visual-edge')!, stage.querySelector('.ff-visual-edge span')!]) {
      pointer('pointerDown', target); pointer('pointerMove', stage, 700, 500); pointer('pointerUp', stage, 700, 500)
    }
    for (const extra of [{ pointerType: 'touch' }, { isPrimary: false }, { button: 2 }]) {
      pointer('pointerDown', stage, 0, 0, extra); pointer('pointerMove', stage, 700, 500, extra); pointer('pointerUp', stage, 700, 500, extra)
    }
    expect(capture).not.toHaveBeenCalled()
    expect(activeStore.getSnapshot()).toBe(snapshot)
  })
  it.each(['revision', 'wrong scope', 'missing adapter', 'pointerCancel', 'lostPointerCapture', 'Escape'] as const)('rejects %s at marquee continuation without transaction', async reason => {
    setup(); await screen.findByText('First project')
    const { stage, pointer, release } = pointerFixture()
    pointer('pointerDown', stage); pointer('pointerMove', stage, 700, 500)
    const select = vi.spyOn(activeStore, 'select')
    if (reason === 'revision') act(() => activeStore.setTime({ unit: 'SIMULATED_STEP_0_20', playhead: 2 }))
    else if (reason === 'wrong scope') vi.spyOn(activeStore, 'getSnapshot').mockReturnValue({ ...activeStore.getSnapshot(), projectId: 'wrong' })
    else if (reason === 'missing adapter') vi.spyOn(activeStore, 'getSnapshot').mockReturnValue({ ...activeStore.getSnapshot(), lifetime: {}, supported: [] })
    else if (reason === 'Escape') fireEvent.keyDown(stage, { key: 'Escape' })
    else pointer(reason, stage)
    pointer('pointerUp', stage, 700, 500)
    expect(select).not.toHaveBeenCalled()
    expect(activeStore.getSnapshot().selectedRefs).toEqual([])
    expect(stage.querySelector('[data-canvas-marquee]')).toBeNull()
    expect(release).toHaveBeenCalledWith(7)
  })
  it.each(['en', 'zh-CN'] as const)('localizes modes, help and preview status in %s', async locale => {
    setup(locale); await screen.findByText('First project')
    const stage = screen.getByRole('region', { name: locale === 'en' ? 'Infinite canvas workspace' : '无限画布工作区' })
    Object.defineProperties(stage, { setPointerCapture: { value: vi.fn() }, releasePointerCapture: { value: vi.fn() } })
    expect(screen.getByRole('button', { name: locale === 'en' ? 'Select' : '选择' })).toBeTruthy()
    expect(screen.getByRole('button', { name: locale === 'en' ? 'Pan' : '平移' })).toBeTruthy()
    expect(screen.getByText(locale === 'en' ? /Drag at least 4/ : /拖动至少 4/)).toBeTruthy()
    fireEvent.pointerDown(stage, { pointerId: 7, pointerType: 'mouse', isPrimary: true, button: 0, clientX: 0, clientY: 0 })
    fireEvent.pointerMove(stage, { pointerId: 7, clientX: 700, clientY: 500 })
    expect(screen.getByText(locale === 'en' ? 'Selection preview; release to select.' : '选择预览；松开以选择。')).toBeTruthy()
    expect(stage.getAttribute('role')).toBe('region')
  })
})


describe('Slice1B live adapter and release races', () => {
  it('rechecks live context after release callbacks before committing any group member', async () => {
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer, release } = pointerFixture()
    fireEvent.click(project); fireEvent.click(note, { ctrlKey: true })
    pointer('pointerDown', project, 100, 100); pointer('pointerMove', stage, 140, 130)
    release.mockImplementation(() => { activeStore.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [] }) })
    pointer('pointerUp', stage, 140, 130)
    expect(project.style.left).toBe('120px'); expect(note.style.left).toBe('430px')
  })
  it.each(['unregister', 'remove selected target', 'remove marquee hit'])('uses actual registered adapter for %s before up without a React render', async reason => {
    observeAdapter = true
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer, release } = pointerFixture()
    if (reason !== 'remove marquee hit') { fireEvent.click(project); fireEvent.click(note, { ctrlKey: true }) }
    pointer('pointerDown', reason === 'remove marquee hit' ? stage : project, 0, 0)
    pointer('pointerMove', stage, 700, 500)
    if (reason === 'unregister') act(() => unregisterAdapter())
    else {
      const objects = registeredAdapter.objects()
      vi.spyOn(registeredAdapter, 'objects').mockReturnValue(objects.filter(object => object.id !== 'note-node'))
    }
    pointer('pointerUp', stage, 700, 500)
    expect(project.style.left).toBe('120px'); expect(note.style.left).toBe('430px')
    if (reason === 'remove marquee hit') expect(activeStore.getSnapshot().selectedRefs).toEqual([])
    expect(release).toHaveBeenCalledWith(7)
  })
  it('marquee remains model ordered when a card has no mounted element', async () => {
    setup(); await screen.findByText('First project')
    const { stage, note, pointer } = pointerFixture()
    note.remove()
    pointer('pointerDown', stage); pointer('pointerMove', stage, 700, 500); pointer('pointerUp', stage, 700, 500)
    expect(activeStore.getSnapshot().selectedRefs.map(r => r.localId)).toEqual(['project-node', 'note-node'])
  })
  it('transforms drag and marquee with captured zoom, pan and nonzero viewport origin', async () => {
    setup(); await screen.findByText('First project')
    const { stage, project, pointer } = pointerFixture()
    fireEvent.keyDown(stage, { key: '-' }) // zoom .9
    fireEvent.keyDown(stage, { key: 'ArrowLeft' }) // pan x +24
    vi.spyOn(stage, 'getBoundingClientRect').mockReturnValue({ left: 10, top: 20, width: 1000, height: 700, right: 1010, bottom: 720, x: 10, y: 20, toJSON: () => ({}) })
    vi.spyOn(project, 'getBoundingClientRect').mockReturnValue({ left: 142, top: 101, width: 207, height: 144, right: 349, bottom: 245, x: 142, y: 101, toJSON: () => ({}) })
    pointer('pointerDown', project, 142, 101); pointer('pointerMove', stage, 178, 128); pointer('pointerUp', stage, 178, 128)
    expect(project.style.left).toBe('160px'); expect(project.style.top).toBe('120px')
    pointer('pointerDown', stage, 180, 130); pointer('pointerUp', stage, 190, 140)
    expect(activeStore.getSnapshot().selectedRefs.map(r => r.localId)).toEqual(['project-node'])
  })
  it('bounds group commit with one delta and leaves focused-node nudge and editable Escape ownership intact', async () => {
    setup(); await screen.findByText('First project')
    const { stage, project, note, pointer } = pointerFixture()
    fireEvent.click(project); fireEvent.click(note, { ctrlKey: true })
    pointer('pointerDown', project, 0, 0); pointer('pointerMove', stage, 9999, -9999)
    const editor = document.createElement('textarea'); stage.append(editor)
    expect(fireEvent.keyDown(editor, { key: 'Escape' })).toBe(true)
    expect(fireEvent.keyDown(project, { key: 'Escape', isComposing: true })).toBe(true)
    pointer('pointerUp', stage, 9999, -9999)
    expect(project.style.left).toBe('1690px'); expect(note.style.left).toBe('2000px')
    expect(project.style.top).toBe('-2000px'); expect(note.style.top).toBe('-1860px')
    fireEvent.keyDown(project, { key: 'ArrowLeft' })
    expect(project.style.left).toBe('1666px'); expect(note.style.left).toBe('2000px')
    expect(activeStore.getSnapshot().selectedRefs).toHaveLength(2)
    editor.remove()
  })
})

it('rejects a prepended overlay and does not announce Pan for a zero-area Select gesture', async () => {
  setup(); await screen.findByText('First project')
  const { stage, project, pointer, capture } = pointerFixture()
  fireEvent.click(project)
  const overlay = document.createElement('div'); stage.prepend(overlay)
  pointer('pointerDown', overlay); pointer('pointerMove', stage, 700, 500); pointer('pointerUp', stage, 700, 500)
  expect(capture).not.toHaveBeenCalled()
  expect(activeStore.getSnapshot().selectedRefs.map(r => r.localId)).toEqual(['project-node'])
  overlay.remove()
  pointer('pointerDown', stage); pointer('pointerMove', stage, 100, 0)
  expect(screen.queryByText('View preview; release to pan.')).toBeNull()
  expect(stage.querySelector('[data-canvas-marquee]')).toBeNull()
  pointer('pointerUp', stage, 100, 0)
  expect(activeStore.getSnapshot().selectedRefs).toEqual([])
})

it.each(['drag', 'marquee', 'pan'] as const)('Slice1C pagehide cancels %s synchronously, releases capture and never commits preview geometry', async kind => {
  setup(); await screen.findByText('First project')
  const { stage, project, note, pointer, release, captured } = pointerFixture()
  fireEvent.click(project)
  if (kind === 'pan') fireEvent.click(screen.getByRole('button', { name: 'Pan' }))
  const camera = stage.querySelector('.ff-canvas-viewport')!.getAttribute('style')
  pointer('pointerDown', kind === 'drag' ? project : stage, 100, 100)
  pointer('pointerMove', stage, 160, 170)
  expect(captured.has(7)).toBe(true)
  if (kind === 'marquee') expect(stage.querySelector('[data-canvas-marquee]')).toBeTruthy()
  const old = activeStore, before = old.getSnapshot()
  act(() => {
    window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: true }))
    expect(release).toHaveBeenCalledWith(7)
    expect(captured.has(7)).toBe(false)
    expect(old.getSnapshot().selectedRefs).toEqual([])
    expect(project.style.left).toBe('120px')
    expect(note.style.left).toBe('430px')
    expect(stage.querySelector('[data-canvas-marquee]')).toBeNull()
  })
  pointer('pointerUp', stage, 220, 240)
  expect(project.style.left).toBe('120px')
  expect(note.style.top).toBe('230px')
  expect(stage.querySelector('.ff-canvas-viewport')!.getAttribute('style')).toBe(camera)
  act(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })))
  expect(activeStore.getSnapshot().lifetime).not.toBe(before.lifetime)
  expect(activeStore.getSnapshot().selectedRefs).toEqual([])
})

it('V5 restores local title and position through the dispatcher without changing selection or camera', async () => {
  setup()
  await screen.findByText('First project')
  const note = screen.getByRole('button', { name: 'Local composition note' })
  fireEvent.click(note)
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Draft title' } })
  fireEvent.change(screen.getByLabelText('Local X'), { target: { value: '500' } })
  const before = activeStore.getSnapshot()
  const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
  fireEvent.keyDown(stage, { key: 'ArrowRight' })
  const camera = stage.querySelector('.ff-canvas-viewport')!.getAttribute('style')
  const undo = screen.getByRole('button', { name: 'Undo local edit' })
  act(() => undo.focus())
  fireEvent.click(undo)
  expect((screen.getByLabelText('Local X') as HTMLInputElement).value).toBe('430')
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Draft title')
  fireEvent.click(undo)
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Local composition note')
  expect(undo.getAttribute('aria-disabled')).toBe('true')
  expect((undo as HTMLButtonElement).disabled).toBe(false)
  expect(document.activeElement).toBe(undo)
  fireEvent.click(undo)
  const redo = screen.getByRole('button', { name: 'Redo local edit' })
  act(() => redo.focus())
  fireEvent.click(redo); fireEvent.click(redo)
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Draft title')
  expect((screen.getByLabelText('Local X') as HTMLInputElement).value).toBe('500')
  expect(redo.getAttribute('aria-disabled')).toBe('true')
  expect(document.activeElement).toBe(redo)
  expect(activeStore.getSnapshot().selectedRefs).toEqual(before.selectedRefs)
  expect(activeStore.getSnapshot().primaryRef).toEqual(before.primaryRef)
  expect(stage.querySelector('.ff-canvas-viewport')!.getAttribute('style')).toBe(camera)
})

it.each(['owner', 'document', 'adapter'] as const)('V5 clears history synchronously on %s retirement and rejects retained adapter work', async reason => {
  observeAdapter = true
  setup()
  await screen.findByText('First project')
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Retiring draft' } })
  const oldStore = activeStore
  act(() => reason === 'adapter' ? unregisterAdapter() : oldStore.retireSelectionOwner(reason))
  expect(screen.getByText('Local edits to undo: 0. To redo: 0.')).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Undo local edit' }).getAttribute('aria-disabled')).toBe('true')
  expect(oldStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'undo-local' }).ok).toBe(false)
  act(() => expect(registeredAdapter.handle({ category: 'WORKSPACE_PRESENTATION', type: 'rename', targetId: 'note-node', title: 'Stale' })).toBe(false))
  expect(screen.queryByRole('button', { name: 'Stale' })).toBeNull()
  expect(screen.getByText('Local edits to undo: 0. To redo: 0.')).toBeTruthy()
})

it('V5 bounds the session to 50 edits, preserves redo across no-ops and branches on a new edit', async () => {
  setup()
  await screen.findByText('First project')
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  const dispatchTitle = (title: string) => activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'rename', targetId: 'note-node', title }, 'INSPECTOR')
  act(() => { for (let i = 1; i <= 51; i++) expect(dispatchTitle(`Edit ${i}`).ok).toBe(true) })
  expect(screen.getByText('Local edits to undo: 50. To redo: 0.')).toBeTruthy()
  act(() => { for (let i = 0; i < 50; i++) expect(activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'undo-local' }).ok).toBe(true) })
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Edit 1')
  expect(activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'undo-local' }).ok).toBe(false)
  expect(screen.getByText('Local edits to undo: 0. To redo: 50.')).toBeTruthy()
  act(() => {
    dispatchTitle('Edit 1')
    activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'move', targetId: 'note-node', x: 430, y: 230 })
    activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'move', targetId: 'note-node', x: NaN, y: 230 })
  })
  expect(screen.getByText('Local edits to undo: 0. To redo: 50.')).toBeTruthy()
  act(() => { for (let i = 0; i < 50; i++) expect(activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'redo-local' }).ok).toBe(true) })
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Edit 51')
  act(() => activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'undo-local' }))
  act(() => dispatchTitle('New branch'))
  expect(screen.getByText('Local edits to undo: 50. To redo: 0.')).toBeTruthy()
  expect(activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'redo-local' }).ok).toBe(false)
})

it('V5 commits a whole selected drag as one edit and undo cancels a later live preview', async () => {
  setup()
  await screen.findByText('First project')
  const { stage, project, note, pointer, captured } = pointerFixture()
  act(() => activeStore.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['project-node', 'note-node'], primaryId: 'note-node' }))
  const selection = activeStore.getSnapshot()
  pointer('pointerDown', project, 100, 100); pointer('pointerMove', stage, 140, 130)
  expect(screen.getByText('Local edits to undo: 0. To redo: 0.')).toBeTruthy()
  pointer('pointerUp', stage, 140, 130)
  expect([project.style.left, note.style.left]).toEqual(['160px', '470px'])
  expect(screen.getByText('Local edits to undo: 1. To redo: 0.')).toBeTruthy()
  pointer('pointerDown', project, 100, 100); pointer('pointerMove', stage, 180, 180)
  expect(captured.size).toBe(1)
  fireEvent.click(screen.getByRole('button', { name: 'Undo local edit' }))
  expect(captured.size).toBe(0)
  expect([project.style.left, project.style.top, note.style.left, note.style.top]).toEqual(['120px', '90px', '430px', '230px'])
  pointer('pointerUp', stage, 200, 200)
  expect([project.style.left, note.style.left]).toEqual(['120px', '430px'])
  expect(screen.getByText('Local edits to undo: 0. To redo: 1.')).toBeTruthy()
  expect(activeStore.getSnapshot().selectedRefs).toEqual(selection.selectedRefs)
  expect(activeStore.getSnapshot().primaryRef).toEqual(selection.primaryRef)
  expect((screen.getByLabelText('Local X') as HTMLInputElement).value).toBe('430')
  fireEvent.click(screen.getByRole('button', { name: 'Redo local edit' }))
  expect([project.style.left, note.style.left]).toEqual(['160px', '470px'])
})

it('V5 excludes canceled/no-op gestures, selection and camera and leaves native text undo untouched', async () => {
  setup()
  await screen.findByText('First project')
  const { stage, project, pointer } = pointerFixture()
  for (const reason of ['pointerCancel', 'lostPointerCapture', 'Escape'] as const) {
    pointer('pointerDown', project, 100, 100); pointer('pointerMove', stage, 160, 160)
    if (reason === 'Escape') fireEvent.keyDown(stage, { key: reason }); else pointer(reason, stage)
    pointer('pointerUp', stage, 160, 160)
  }
  pointer('pointerDown', project, 100, 100); pointer('pointerUp', stage, 102, 102)
  pointer('pointerDown', project, 100, 100); pointer('pointerMove', stage, 150, 150); pointer('pointerUp', stage, 100, 100)
  pointer('pointerDown', stage, 0, 0); pointer('pointerMove', stage, 700, 500); pointer('pointerUp', stage, 700, 500)
  fireEvent.click(screen.getByRole('button', { name: 'Pan' }))
  pointer('pointerDown', stage, 0, 0); pointer('pointerMove', stage, 30, 30); pointer('pointerUp', stage, 30, 30)
  fireEvent.keyDown(stage, { key: '+' })
  fireEvent.click(screen.getByRole('button', { name: 'Fit canvas' }))
  fireEvent.click(project)
  const title = screen.getByLabelText('Local title')
  for (const key of ['z', 'y']) for (const modifier of ['ctrlKey', 'metaKey']) expect(fireEvent.keyDown(title, { key, [modifier]: true })).toBe(true)
  expect(screen.getByText('Local edits to undo: 0. To redo: 0.')).toBeTruthy()
  expect(project.style.left).toBe('120px')
})

it('V5 rejects an edit if releasing its live preview retires ownership synchronously', async () => {
  setup()
  await screen.findByText('First project')
  const { stage, note, pointer, release } = pointerFixture()
  fireEvent.click(note)
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Owned title' } })
  pointer('pointerDown', note, 100, 100); pointer('pointerMove', stage, 150, 150)
  release.mockImplementationOnce(() => activeStore.retireSelectionOwner('owner'))
  act(() => expect(activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'rename', targetId: 'note-node', title: 'Stale replacement' }).ok).toBe(false))
  expect(screen.getByRole('button', { name: 'Owned title' })).toBe(note)
  expect(screen.getByText('Local edits to undo: 0. To redo: 0.')).toBeTruthy()
  pointer('pointerUp', stage, 200, 200)
  expect(note.style.left).toBe('430px')
})

it.each(['project', 'workspace', 'unmount', 'pagehide'] as const)('V5 starts with empty history after %s and cannot revive old completions', async reason => {
  observeAdapter = true
  const view = setup()
  await screen.findByText('First project')
  const { stage, note, pointer } = pointerFixture()
  fireEvent.click(note)
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Old session' } })
  pointer('pointerDown', note, 100, 100); pointer('pointerMove', stage, 150, 150)
  const oldStore = activeStore
  const oldAdapter = registeredAdapter
  if (reason === 'project') view.rerender(view.content('w1', 'p2'))
  else if (reason === 'workspace') view.rerender(view.content('w2', 'p1'))
  else if (reason === 'unmount') view.unmount()
  else act(() => window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: true })))
  expect(oldStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'undo-local' }).ok).toBe(false)
  act(() => expect(oldAdapter.handle({ category: 'WORKSPACE_PRESENTATION', type: 'undo-local' })).toBe(false))
  pointer('pointerUp', stage, 200, 200)
  if (reason === 'pagehide') act(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })))
  if (reason === 'unmount') return
  expect(screen.getByText('Local edits to undo: 0. To redo: 0.')).toBeTruthy()
  expect(activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'redo-local' }).ok).toBe(false)
  const current = screen.getByRole('button', { name: reason === 'pagehide' ? 'Old session' : 'Local composition note' })
  expect(current.style.left).toBe('430px')
  fireEvent.click(current)
  fireEvent.keyDown(current, { key: 'ArrowRight' })
  expect(current.style.left).toBe('454px')
  fireEvent.click(screen.getByRole('button', { name: 'Undo local edit' }))
  expect(current.style.left).toBe('430px')
  expect(screen.getByText('Local edits to undo: 0. To redo: 1.')).toBeTruthy()
})

it('V5 rejects undo if releasing capture retires its owner and retains the committed title', async () => {
  setup()
  await screen.findByText('First project')
  const { stage, note, pointer, release } = pointerFixture()
  fireEvent.click(note)
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Committed title' } })
  pointer('pointerDown', note, 100, 100); pointer('pointerMove', stage, 150, 150)
  release.mockImplementationOnce(() => activeStore.retireSelectionOwner('owner'))
  act(() => expect(activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'undo-local' }).ok).toBe(false))
  expect(screen.getByRole('button', { name: 'Committed title' })).toBe(note)
  expect(screen.getByText('Local edits to undo: 0. To redo: 0.')).toBeTruthy()
  pointer('pointerUp', stage, 200, 200)
  expect(note.style.left).toBe('430px')
})

it('V5 restores a safe bilingual title and exposes native focusable history controls with local empty copy', async () => {
  setup('zh-CN')
  await screen.findByText('First project')
  const undo = screen.getByRole('button', { name: '撤销本地编辑' }) as HTMLButtonElement
  const redo = screen.getByRole('button', { name: '重做本地编辑' }) as HTMLButtonElement
  expect(undo.disabled).toBe(false); expect(undo.tabIndex).toBe(0)
  expect(redo.disabled).toBe(false); expect(redo.tabIndex).toBe(0)
  expect(screen.getByText('可撤销的本地编辑：0。可重做：0。')).toBeTruthy()
  const note = screen.getByRole('button', { name: 'Local composition note' })
  fireEvent.click(note)
  act(() => activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'rename', targetId: 'note-node', title: '<img src=x onerror=alert(1)> 中文标题' }))
  act(() => undo.focus())
  expect(fireEvent.keyDown(undo, { key: 'Enter' })).toBe(true)
  // Native key activation is a browser gate; happy-dom only simulates its resulting click.
  fireEvent.click(undo, { detail: 0 })
  expect(document.activeElement).toBe(undo)
  expect(undo.getAttribute('aria-disabled')).toBe('true')
  act(() => redo.focus())
  expect(fireEvent.keyDown(redo, { key: ' ' })).toBe(true)
  fireEvent.click(redo, { detail: 0 })
  expect(screen.getByRole('button', { name: '<img src=x onerror=alert(1)> 中文标题' })).toBe(note)
  expect(note.querySelector('img')).toBeNull()
  expect(document.activeElement).toBe(redo)
  expect(redo.getAttribute('aria-disabled')).toBe('true')
})

import { applyProposal, createProposal } from '../../interaction/model'

it('V5 undo and redo immediately reconcile shared projections and invalidate pre-restoration proposals', async () => {
  setup()
  await screen.findByText('First project')
  const note = screen.getByRole('button', { name: 'Local composition note' })
  fireEvent.click(note)
  fireEvent.keyDown(note, { key: 'ArrowRight' })
  const beforeUndo = activeStore.getSnapshot()
  const proposal = createProposal(beforeUndo, 'rename to Stale after undo')
  act(() => {
    expect(activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'undo-local' }, 'COMMAND').ok).toBe(true)
    expect(activeStore.getSnapshot().primarySelectedObject?.x).toBe(430)
    expect(applyProposal(activeStore, proposal).ok).toBe(false)
  })
  expect(activeStore.getSnapshot().revision).toBeGreaterThan(beforeUndo.revision)
  expect(activeStore.getSnapshot().selectedRefs).toEqual(beforeUndo.selectedRefs)
  const beforeRedo = activeStore.getSnapshot()
  const nextProposal = createProposal(beforeRedo, 'rename to Stale after redo')
  act(() => {
    expect(activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'redo-local' }, 'COMMAND').ok).toBe(true)
    expect(activeStore.getSnapshot().primarySelectedObject?.x).toBe(454)
    expect(applyProposal(activeStore, nextProposal).ok).toBe(false)
  })
  expect(activeStore.getSnapshot().revision).toBeGreaterThan(beforeRedo.revision)
  expect((screen.getByLabelText('Local X') as HTMLInputElement).value).toBe('454')
  expect(note.getAttribute('aria-label')).toBe('Local composition note')
})

it('V5 can restore an unselected edit while retaining the current primary and camera without consuming redo on view changes', async () => {
  setup()
  await screen.findByText('First project')
  const note = screen.getByRole('button', { name: 'Local composition note' })
  const project = screen.getByRole('button', { name: 'Project reference' })
  fireEvent.click(note)
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Different target' } })
  fireEvent.click(project)
  const selected = activeStore.getSnapshot()
  fireEvent.click(screen.getByRole('button', { name: 'Undo local edit' }))
  expect(note.getAttribute('aria-label')).toBe('Local composition note')
  expect(activeStore.getSnapshot().primaryRef).toEqual(selected.primaryRef)
  const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
  fireEvent.keyDown(stage, { key: 'ArrowLeft' }); fireEvent.keyDown(stage, { key: '+' })
  act(() => activeStore.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [] }))
  const camera = stage.querySelector('.ff-canvas-viewport')!.getAttribute('style')
  expect(screen.getByText('Local edits to undo: 0. To redo: 1.')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Redo local edit' }))
  expect(note.getAttribute('aria-label')).toBe('Different target')
  expect(activeStore.getSnapshot().selectedRefs).toEqual([])
  expect(stage.querySelector('.ff-canvas-viewport')!.getAttribute('style')).toBe(camera)
})
