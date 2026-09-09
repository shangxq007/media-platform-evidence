import { StrictMode } from 'react'
import { act, createEvent, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { LocalizationProvider } from '../../localization'
import { SelectionProvider, useInteractionStore, useSelection } from '../../interaction/SelectionContext'
import { SelectionInspector } from '../../interaction/InteractionShell'
import type { InteractionStore, SelectionScope, SurfaceAdapter } from '../../interaction/model'
import { WorkflowSketch } from './WorkflowSketch'
import { WORKFLOW_NODE_CATEGORIES } from './model'

let capturedAdapter: SurfaceAdapter
vi.mock('../../interaction/SelectionContext', async importOriginal => {
  const actual = await importOriginal<typeof import('../../interaction/SelectionContext')>()
  return { ...actual, useSurfaceAdapter: (adapter: SurfaceAdapter) => { capturedAdapter = adapter; actual.useSurfaceAdapter(adapter) } }
})
let activeStore: InteractionStore
function SnapshotProbe() {
  activeStore = useInteractionStore()
  const selection = useSelection()
  return <output data-testid="workflow-selection">{JSON.stringify({
    selectedRefs: selection.selectedRefs,
    selectedObjects: selection.selectedObjects,
    supported: selection.supported,
  })}</output>
}

function setup(scope: SelectionScope = { workspaceId: 'workspace-1', projectId: 'project-1', surfaceId: 'workflow' }, locale: 'en' | 'zh-CN' = 'en', strict = false) {
  const content = (nextScope = scope) => (
    <LocalizationProvider initialLocale={locale}>
      <SelectionProvider scope={nextScope}>
        <WorkflowSketch />
        <SelectionInspector />
        <SnapshotProbe />
      </SelectionProvider>
    </LocalizationProvider>
  )
  const wrapped = (nextScope = scope) => strict ? <StrictMode>{content(nextScope)}</StrictMode> : content(nextScope)
  return { ...render(wrapped()), content: wrapped }
}

afterEach(() => vi.restoreAllMocks())

describe('workflow local node-arrangement sketch', () => {
  it('starts empty with a truthful boundary and all seven category entry points', () => {
    setup()

    expect(screen.getByRole('heading', { name: 'Local arrangement sketch' })).toBeTruthy()
    expect(screen.getByText('This sketch is local, unsaved, and cannot run. Cards do not define workflow steps, parameters, or connections.')).toBeTruthy()
    expect(screen.getByText('No local cards yet')).toBeTruthy()
    for (const category of WORKFLOW_NODE_CATEGORIES) {
      expect(screen.getByRole('button', { name: `Add ${category} card` })).toBeTruthy()
    }
    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
  })

  it('adds every category and converges keyboard and Inspector actions on the shared adapter', () => {
    setup()
    for (const category of WORKFLOW_NODE_CATEGORIES) fireEvent.click(screen.getByRole('button', { name: `Add ${category} card` }))
    const cards = screen.getAllByTestId('workflow-sketch-node')
    expect(cards).toHaveLength(7)
    expect(cards.map(card => card.querySelector('.ff-badge')?.textContent)).toEqual(WORKFLOW_NODE_CATEGORIES)

    const operation = cards[0]
    act(() => operation.focus())
    expect(operation.getAttribute('aria-pressed')).toBe('false')
    expect(JSON.parse(screen.getByTestId('workflow-selection').textContent!).selectedRefs).toEqual([])
    fireEvent.keyDown(operation, { key: 'Enter' })
    expect(operation.getAttribute('aria-pressed')).toBe('true')
    let snapshot = JSON.parse(screen.getByTestId('workflow-selection').textContent!)
    expect(snapshot.supported).toEqual(['rename', 'move', 'reveal'])
    expect(snapshot.selectedRefs).toEqual([{ workspaceId: 'workspace-1', projectId: 'project-1', surfaceId: 'workflow', kind: 'NODE', localId: 'workflow-node-1' }])
    expect(snapshot.selectedObjects[0]).toMatchObject({ id: 'workflow-node-1', kind: 'NODE', title: 'OPERATION', x: 32, y: 32, reference: 'OPERATION' })
    expect(snapshot.selectedObjects[0]).not.toHaveProperty('synthetic')
    expect(screen.getByText('Local board range: X 16–896; Y 16–560.')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Local title'), { target: { value: '<img src=x onerror=alert(1)> review' } })
    expect(operation.getAttribute('aria-label')).toBe('<img src=x onerror=alert(1)> review')
    expect(operation.querySelector('img')).toBeNull()
    fireEvent.keyDown(operation, { key: 'ArrowRight' })
    expect((screen.getByLabelText('Local X') as HTMLInputElement).value).toBe('56')
    fireEvent.change(screen.getByLabelText('Local Y'), { target: { value: '9999' } })
    expect((screen.getByLabelText('Local Y') as HTMLInputElement).value).toBe('560')

    const reveal = vi.fn()
    Object.defineProperty(operation, 'scrollIntoView', { configurable: true, value: reveal })
    fireEvent.click(screen.getByRole('button', { name: 'Show primary node' }))
    expect(reveal).toHaveBeenCalledWith({ block: 'nearest', inline: 'nearest' })

    const renderCard = cards[1]
    act(() => renderCard.focus())
    expect(operation.getAttribute('aria-pressed')).toBe('true')
    expect(renderCard.getAttribute('aria-pressed')).toBe('false')
    fireEvent.keyDown(renderCard, { key: ' ' })
    expect(operation.getAttribute('aria-pressed')).toBe('false')
    expect(renderCard.getAttribute('aria-pressed')).toBe('true')
    snapshot = JSON.parse(screen.getByTestId('workflow-selection').textContent!)
    expect(snapshot.selectedObjects[0].reference).toBe('RENDER')
  })

  it.each(['en', 'zh-CN'] as const)('keeps invalid titles correctable in %s and rejects dispatcher bypasses', locale => {
    setup(undefined, locale)
    const addName = locale === 'en' ? 'Add OPERATION card' : '添加 OPERATION 卡片'
    fireEvent.click(screen.getByRole('button', { name: addName }))
    fireEvent.click(screen.getByRole('button', { name: addName }))
    const [first, second] = screen.getAllByTestId('workflow-sketch-node')
    fireEvent.click(first)
    const input = screen.getByLabelText(locale === 'en' ? 'Local title' : '本地标题') as HTMLInputElement
    for (const value of ['', '   ', 'x'.repeat(121)]) {
      fireEvent.change(input, { target: { value } })
      expect(input.value).toBe(value)
      expect(input.getAttribute('aria-invalid')).toBe('true')
      expect(screen.getByRole('alert').textContent).toBe(locale === 'en' ? 'Enter a title of 1–120 characters, including at least one non-space character.' : '请输入 1–120 个字符的标题，且至少包含一个非空白字符。')
      expect(first.getAttribute('aria-label')).toBe('OPERATION')
      let accepted = true
      act(() => { accepted = activeStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'rename', targetId: 'workflow-node-1', title: value }, 'COMMAND').ok })
      expect(accepted).toBe(false)
    }
    fireEvent.change(input, { target: { value: 'Repaired title' } })
    expect(first.getAttribute('aria-label')).toBe('Repaired title')
    expect(second.getAttribute('aria-label')).toBe('OPERATION')
    expect(screen.queryByRole('alert')).toBeNull()
    fireEvent.change(input, { target: { value: ' ' } })
    fireEvent.click(second)
    expect((screen.getByLabelText(locale === 'en' ? 'Local title' : '本地标题') as HTMLInputElement).value).toBe('OPERATION')
  })

  it('cancels native activation without selecting while text composition is in progress', () => {
    setup()
    fireEvent.click(screen.getByRole('button', { name: 'Add OPERATION card' }))
    const card = screen.getByTestId('workflow-sketch-node')
    act(() => card.focus())

    const composingEnter = createEvent.keyDown(card, { key: 'Enter', isComposing: true })
    const composingSpace = createEvent.keyDown(card, { key: ' ', keyCode: 229 })
    fireEvent(card, composingEnter)
    fireEvent(card, composingSpace)

    expect(composingEnter.defaultPrevented).toBe(true)
    expect(composingSpace.defaultPrevented).toBe(true)
    expect(card.getAttribute('aria-pressed')).toBe('false')
    expect(activeStore.getSnapshot().selectedRefs).toEqual([])
  })

  it('enforces capacity and transfers focus from the newly disabled add control to the stable board', () => {
    setup()
    const add = screen.getByRole('button', { name: 'Add WAIT card' })
    for (let index = 0; index < 12; index += 1) {
      act(() => add.focus())
      fireEvent.click(add)
    }

    expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(12)
    expect(screen.getByRole('alert').textContent).toContain('12-card limit reached')
    expect((add as HTMLButtonElement).disabled).toBe(true)
    expect(document.activeElement).toBe(screen.getByRole('region', { name: 'Local workflow sketch board' }))
  })

  it('restores prior focus after programmatic nonfocused add and cancelled removal', () => {
    setup()
    const addWait = screen.getByRole('button', { name: 'Add WAIT card' })
    const board = screen.getByRole('region', { name: 'Local workflow sketch board' })
    act(() => board.focus())
    for (let index = 0; index < 12; index += 1) fireEvent.click(addWait)
    expect(document.activeElement).toBe(board)

    const cards = screen.getAllByTestId('workflow-sketch-node')
    const selected = cards[0]
    fireEvent.click(selected)
    act(() => cards[1].focus())
    fireEvent.click(screen.getByRole('button', { name: 'Remove selected card' }))
    fireEvent.click(screen.getByRole('button', { name: 'Keep card' }))
    expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(12)
    expect(document.activeElement).toBe(cards[1])
  })

  it('removes the selected card, reconciles shared selection, and retains nonreused IDs', () => {
    setup()
    const add = screen.getByRole('button', { name: 'Add AGENT card' })
    fireEvent.click(add)
    const first = screen.getByTestId('workflow-sketch-node')
    fireEvent.keyDown(first, { key: 'Enter' })
    const remove = screen.getByRole('button', { name: 'Remove selected card' })
    act(() => remove.focus())
    fireEvent.click(remove)
    expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(1)
    fireEvent.click(screen.getByRole('button', { name: 'Remove card' }))

    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
    expect(activeStore.getSnapshot().selectedRefs).toEqual([])
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Add OPERATION card' }))

    fireEvent.click(add)
    fireEvent.keyDown(screen.getByTestId('workflow-sketch-node'), { key: 'Enter' })
    expect(activeStore.getSnapshot().primaryRef?.localId).toBe('workflow-node-2')
  })

  it('cancels or confirms discard through the shared dialog with deterministic focus', async () => {
    setup()
    fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add CONDITION card' }))
    const reset = screen.getByRole('button', { name: 'Reset sketch' })
    act(() => reset.focus())
    fireEvent.click(reset)
    expect(screen.getByRole('dialog', { name: 'Discard local sketch?' })).toBeTruthy()
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Keep sketch' })))
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(reset)
    expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(2)

    fireEvent.click(reset)
    const discard = screen.getByRole('button', { name: 'Discard sketch' })
    act(() => discard.focus())
    fireEvent.click(discard)
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
    expect(document.activeElement).toBe(screen.getByRole('region', { name: 'Local workflow sketch board' }))
  })

  it('clears cards on exact scope and owner-lifetime changes without persistence or requests', () => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    const storage = vi.spyOn(Storage.prototype, 'setItem')
    const xhr = vi.spyOn(XMLHttpRequest.prototype, 'open')
    const view = setup()
    fireEvent.click(screen.getByRole('button', { name: 'Add INTEGRATION card' }))
    fireEvent.click(screen.getByTestId('workflow-sketch-node'))
    fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Local only' } })
    fireEvent.click(screen.getByRole('button', { name: 'Move right' }))
    fireEvent.click(screen.getByRole('button', { name: 'Check selected card' }))
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    fireEvent.click(screen.getByRole('button', { name: 'Remove selected card' }))
    fireEvent.click(screen.getByRole('button', { name: 'Remove card' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add INTEGRATION card' }))
    fireEvent.click(screen.getByRole('button', { name: 'Reset sketch' }))
    fireEvent.click(screen.getByRole('button', { name: 'Discard sketch' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add INTEGRATION card' }))
    view.rerender(view.content({ workspaceId: 'workspace-1', projectId: 'project-2', surfaceId: 'workflow' }))
    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
    fireEvent.click(screen.getByRole('button', { name: 'Add INTEGRATION card' }))
    act(() => window.dispatchEvent(new Event('pagehide')))
    act(() => window.dispatchEvent(new Event('pageshow')))
    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
    expect(fetch).not.toHaveBeenCalled()
    expect(storage).not.toHaveBeenCalled()
    expect(xhr).not.toHaveBeenCalled()
    vi.unstubAllGlobals()
  })

  it('retires an open reset confirmation on owner change without clearing the new owner sketch', () => {
    const view = setup()
    fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
    fireEvent.click(screen.getByRole('button', { name: 'Reset sketch' }))
    const retiredDiscard = screen.getByRole('button', { name: 'Discard sketch' })

    view.rerender(view.content({ workspaceId: 'workspace-1', projectId: 'project-2', surfaceId: 'workflow' }))
    expect(screen.queryByRole('dialog', { name: 'Discard local sketch?' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Add CONDITION card' }))
    fireEvent.click(retiredDiscard)

    expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(1)
    expect(screen.getByTestId('workflow-sketch-node').textContent).toContain('CONDITION')
  })

  it('checks selected properties in the shared dialog, moves by pointer and keyboard, and restores close focus', () => {
    setup()
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    const card = screen.getByTestId('workflow-sketch-node')
    fireEvent.click(card)
    const check = screen.getByRole('button', { name: 'Check selected card' })
    act(() => check.focus())
    fireEvent.click(check)
    const dialog = screen.getByRole('dialog', { name: 'Selection properties' })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Move right' }))
    expect(card.textContent).toContain('X 56 · Y 32')
    fireEvent.change(within(dialog).getByLabelText('Local X'), { target: { value: '896' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Move right' }))
    expect(card.textContent).toContain('X 896 · Y 32')
    expect(within(dialog).getByText('At the board edge. Movement stays within the local board range.')).toBeTruthy()
    fireEvent.keyDown(dialog, { key: 'Escape' })
    expect(document.activeElement).toBe(check)
    fireEvent.keyDown(card, { key: 'ArrowLeft' })
    expect(card.textContent).toContain('X 872 · Y 32')
    expect(activeStore.getSnapshot().primaryRef?.localId).toBe('workflow-node-1')
  })

  it('confirms only the captured card, preserves remaining content, and returns focus to a surviving card', () => {
    setup()
    fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    const [first, second] = screen.getAllByTestId('workflow-sketch-node')
    fireEvent.click(first)
    const remove = screen.getByRole('button', { name: 'Remove selected card' })
    act(() => remove.focus())
    fireEvent.click(remove)
    const dialog = screen.getByRole('dialog', { name: 'Remove local card?' })
    expect(within(dialog).getByText('Remove “REVIEW” from this unsaved sketch? Other cards will stay.')).toBeTruthy()
    fireEvent.keyDown(dialog, { key: 'Escape' })
    expect(document.activeElement).toBe(remove)
    expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(2)
    fireEvent.click(remove)
    fireEvent.click(screen.getByRole('button', { name: 'Remove card' }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.getAllByTestId('workflow-sketch-node')).toEqual([second])
    expect(second.textContent).toContain('WAIT')
    expect(activeStore.getSnapshot().selectedRefs).toEqual([])
    expect(screen.queryByLabelText('Local title')).toBeNull()
    expect(document.activeElement).toBe(second)
  })

  it.each(['owner', 'document', 'adapter'] as const)('retires edits and confirmations under StrictMode on %s retirement and rejects actual retained adapters', reason => {
    const view = setup(undefined, 'en', true)
    fireEvent.click(screen.getByRole('button', { name: 'Add OPERATION card' }))
    fireEvent.click(screen.getByTestId('workflow-sketch-node'))
    fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Private draft' } })
    fireEvent.click(screen.getByRole('button', { name: 'Remove selected card' }))
    expect(screen.getByRole('dialog', { name: 'Remove local card?' })).toBeTruthy()
    const retained = capturedAdapter.handle
    const oldStore = activeStore
    act(() => oldStore.retireSelectionOwner(reason))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
    act(() => expect(retained({ category: 'WORKSPACE_PRESENTATION', type: 'rename', targetId: 'workflow-node-1', title: 'Stale' })).toBe(false))
    view.rerender(view.content({ workspaceId: 'workspace-1', projectId: 'new-project', surfaceId: 'workflow' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    fireEvent.click(screen.getByTestId('workflow-sketch-node'))
    expect(activeStore.getSnapshot().primaryRef?.localId).toBe('workflow-node-1')
    act(() => expect(retained({ category: 'WORKSPACE_PRESENTATION', type: 'rename', targetId: 'workflow-node-1', title: 'Stale' })).toBe(false))
    expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('WAIT')
    expect(oldStore.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'rename', targetId: 'workflow-node-1', title: 'Stale' }).ok).toBe(false)
  })

  it('localizes the sketch controls and empty boundary in Simplified Chinese', () => {
    setup({ workspaceId: '工作区', projectId: '项目', surfaceId: 'workflow' }, 'zh-CN')
    expect(screen.getByRole('heading', { name: '本地排列草图' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '添加 OPERATION 卡片' })).toBeTruthy()
    expect(screen.getByRole('region', { name: '本地工作流草图画板' })).toBeTruthy()
  })
})

// Retain React's actual rendered callback, not a detached DOM click that React ignores.
function retainedClick(element: HTMLElement): () => void {
  const key = Object.keys(element).find(key => key.startsWith('__reactProps$'))!
  return (element as unknown as Record<string, { onClick: () => void }>)[key].onClick
}

it('rejects an actual retained deletion confirmation after cancel, selection change, and new owner with a colliding ID', () => {
  const view = setup(undefined, 'en', true)
  fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
  fireEvent.click(screen.getByTestId('workflow-sketch-node'))
  fireEvent.click(screen.getByRole('button', { name: 'Remove selected card' }))
  const confirm = retainedClick(screen.getByRole('button', { name: 'Remove card' }))
  fireEvent.click(screen.getByRole('button', { name: 'Keep card' }))
  act(confirm)
  expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(1)
  fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
  fireEvent.click(screen.getAllByTestId('workflow-sketch-node')[1])
  act(confirm)
  expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(2)
  view.rerender(view.content({ workspaceId: 'workspace-1', projectId: 'next', surfaceId: 'workflow' }))
  fireEvent.click(screen.getByRole('button', { name: 'Add OPERATION card' }))
  fireEvent.click(screen.getByTestId('workflow-sketch-node'))
  act(confirm)
  expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('OPERATION')
})

it('rejects actual retained title and reset callbacks after owner retirement or cancellation', () => {
  const view = setup(undefined, 'en', true)
  fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
  fireEvent.click(screen.getByTestId('workflow-sketch-node'))
  const title = screen.getByLabelText('Local title')
  const key = Object.keys(title).find(key => key.startsWith('__reactProps$'))!
  const edit = (title as unknown as Record<string, { onChange: (event: { target: { value: string } }) => void }>)[key].onChange
  fireEvent.click(screen.getByRole('button', { name: 'Reset sketch' }))
  const discardButton = screen.getByRole('button', { name: 'Discard sketch' })
  const discardKey = Object.keys(discardButton).find(key => key.startsWith('__reactProps$'))!
  const discard = (discardButton as unknown as Record<string, { onClick: (event: { currentTarget: HTMLElement }) => void }>)[discardKey].onClick
  fireEvent.click(screen.getByRole('button', { name: 'Keep sketch' }))
  act(() => discard({ currentTarget: discardButton }))
  expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(1)
  view.rerender(view.content({ workspaceId: 'workspace-2', projectId: 'project-1', surfaceId: 'workflow' }))
  fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
  fireEvent.click(screen.getByTestId('workflow-sketch-node'))
  act(() => edit({ target: { value: 'Old edit' } }))
  act(() => discard({ currentTarget: discardButton }))
  expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('WAIT')
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('WAIT')
})

// Layout bounds themselves are browser-verified by Hermes; DOM tests prove that
// clamping never truncates the model, accessible button name or editable inspector.
it.each(['中'.repeat(120), 'x'.repeat(120), '剪辑Workflow_'.repeat(12)])('retains a maximum-length title in the card and keyboard-accessible inspector: %s', title => {
  const maxTitle = title.padEnd(120, '文').slice(0, 120)
  setup()
  for (let index = 0; index < 5; index += 1) fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
  const cards = screen.getAllByTestId('workflow-sketch-node')
  act(() => cards[0].focus())
  fireEvent.keyDown(cards[0], { key: 'Enter' })
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: maxTitle } })
  expect(cards[0].querySelector('strong')?.textContent).toBe(maxTitle)
  expect(screen.getByRole('button', { name: maxTitle })).toBe(cards[0])
  expect(cards[0].getAttribute('aria-pressed')).toBe('true')
  expect(cards[0].querySelector('.ff-badge')?.textContent).toBe('REVIEW')
  expect(cards[0].textContent).toContain('X 32 · Y 32')
  expect(cards[4].textContent).toContain('X 32 · Y 168')
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe(maxTitle)
  fireEvent.click(cards[1])
  act(() => cards[0].focus())
  fireEvent.keyDown(cards[0], { key: 'Enter' })
  expect(document.activeElement).toBe(cards[0])
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe(maxTitle)
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Edited full title' } })
  expect(cards[0].getAttribute('aria-label')).toBe('Edited full title')
})
