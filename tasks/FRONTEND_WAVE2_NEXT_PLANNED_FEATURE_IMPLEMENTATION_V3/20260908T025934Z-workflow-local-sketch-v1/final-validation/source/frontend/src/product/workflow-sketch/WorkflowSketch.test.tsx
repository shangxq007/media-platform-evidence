import { act, createEvent, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { LocalizationProvider } from '../../localization'
import { SelectionProvider, useInteractionStore, useSelection } from '../../interaction/SelectionContext'
import { SelectionInspector } from '../../interaction/InteractionShell'
import type { InteractionStore, SelectionScope } from '../../interaction/model'
import { WorkflowSketch } from './WorkflowSketch'
import { WORKFLOW_NODE_CATEGORIES } from './model'

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

function setup(scope: SelectionScope = { workspaceId: 'workspace-1', projectId: 'project-1', surfaceId: 'workflow' }, locale: 'en' | 'zh-CN' = 'en') {
  const content = (nextScope = scope) => (
    <LocalizationProvider initialLocale={locale}>
      <SelectionProvider scope={nextScope}>
        <WorkflowSketch />
        <SelectionInspector />
        <SnapshotProbe />
      </SelectionProvider>
    </LocalizationProvider>
  )
  return { ...render(content()), content }
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

  it('does not reclaim focus after programmatic nonfocused add or remove actions', () => {
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

    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
    expect(activeStore.getSnapshot().selectedRefs).toEqual([])
    expect(document.activeElement).toBe(screen.getByRole('region', { name: 'Local workflow sketch board' }))

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
    const view = setup()
    fireEvent.click(screen.getByRole('button', { name: 'Add INTEGRATION card' }))
    view.rerender(view.content({ workspaceId: 'workspace-1', projectId: 'project-2', surfaceId: 'workflow' }))
    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
    fireEvent.click(screen.getByRole('button', { name: 'Add INTEGRATION card' }))
    act(() => window.dispatchEvent(new Event('pagehide')))
    act(() => window.dispatchEvent(new Event('pageshow')))
    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
    expect(fetch).not.toHaveBeenCalled()
    expect(storage).not.toHaveBeenCalled()
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

  it('localizes the sketch controls and empty boundary in Simplified Chinese', () => {
    setup({ workspaceId: '工作区', projectId: '项目', surfaceId: 'workflow' }, 'zh-CN')
    expect(screen.getByRole('heading', { name: '本地排列草图' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '添加 OPERATION 卡片' })).toBeTruthy()
    expect(screen.getByRole('region', { name: '本地工作流草图画板' })).toBeTruthy()
  })
})
