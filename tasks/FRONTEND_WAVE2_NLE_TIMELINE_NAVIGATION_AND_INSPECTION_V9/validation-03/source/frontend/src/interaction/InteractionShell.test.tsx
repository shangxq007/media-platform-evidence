import { StrictMode, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import { createMemoryHistory, createRouter, RouterProvider, useLocation, useParams } from '@tanstack/react-router'
import { routeTree } from '../app/routeTree'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, createEvent, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { ProductAppShell } from '../components/app-shell/AppShell'
import { ProjectContextProvider } from '../foundation/projectContext'
import { platformClient } from '../foundation/platformClient'
import { WorkflowSketch } from '../product/workflow-sketch/WorkflowSketch'
import { CanvasContent } from '../product/canvas/WorkspaceCanvas'
import { SelectionProvider, useInteractionStore, useSelection, useSurfaceAdapter } from './SelectionContext'
import { AgentLauncher, AgentShell, SelectionInspector, SelectionActionBar, useSelectionCommands } from './InteractionShell'
import { applyProposal, createProposal, type InteractionStore, type SelectionScope, type SelectionState } from './model'
import { LocalizationProvider } from '../localization'
import { CommandPalette, type PaletteAction } from '../components/design-system'

// Explicit test-only host preserves shared synthetic proposal coverage after V9
// removes synthetic clips and simulation from ordinary NLE product entry.
function SyntheticClipHost() {
  const store = useInteractionStore(), selection = useSelection()
  const [enabled, setEnabled] = useState(false)
  const [titles, setTitles] = useState(['Synthetic opening clip', 'Synthetic closing clip'])
  const current = useRef(titles)
  useSurfaceAdapter({
    objects: () => enabled ? titles.map((title, index) => ({ id: `fixture-${index}`, kind: 'CLIP', title, synthetic: true })) : [],
    supports: ['rename'], handle: action => {
      if (action.type !== 'rename') return false
      const index = Number(action.targetId.slice(-1))
      current.current = current.current.map((title, item) => item === index ? action.title : title)
      setTitles(current.current); return true
    },
  })
  useLayoutEffect(() => { store.setTime({ unit: 'SIMULATED_STEP_0_20', playhead: 0, range: [4, 9] }) }, [store])
  return <><SelectionActionBar /><label><input type="checkbox" checked={enabled} onChange={event => setEnabled(event.target.checked)} />Enable synthetic clip presentation fixture</label>{enabled ? titles.map((title, index) => <button key={index} onClick={event => {
    const id = `fixture-${index}`
    const ids = event.ctrlKey || event.metaKey ? [...selection.selectedObjects.map(object => object.id), id] : [id]
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids, primaryId: id })
  }}>{title}</button>) : null}</>
}

function setup(surface: 'canvas' | 'nle' = 'canvas') {
  vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({ workspace: { id: 'w', name: 'Workspace' }, tenantId: null, recentProjects: [{ id: 'p', name: 'Project' }] })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><ProjectContextProvider workspaceId="w" projectId="p"><ProductAppShell surfaceId={surface} workspaceId="w" project={{ workspaceId: 'w', projectId: 'p', project: { kind: 'PROJECT', id: 'p' }, tenantId: null, status: 'BLOCKED', reason: 'Not resolved' }}>{surface === 'canvas' ? <CanvasContent /> : <SyntheticClipHost />}</ProductAppShell></ProjectContextProvider></QueryClientProvider>)
}
afterEach(() => { routeObservations = null; vi.restoreAllMocks() })
it('converges direct keyboard, toolbar, inspector, command and Agent reveal on the same selection', async () => {
  setup()
  const note = await screen.findByRole('button', { name: 'Local composition note' })
  const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
  vi.spyOn(stage, 'getBoundingClientRect').mockReturnValue({ width: 600, height: 400 } as DOMRect)
  fireEvent.click(note)
  const camera = () => stage.querySelector('.ff-canvas-viewport')?.getAttribute('style')
  fireEvent.keyDown(note, { key: 'r' })
  const revealed = camera()
  expect(revealed).toContain('translate')
  fireEvent.click(screen.getByRole('button', { name: 'Reveal primary node' }))
  expect(camera()).toBe(revealed)
  fireEvent.click(screen.getByRole('button', { name: 'Show primary node' }))
  expect(camera()).toBe(revealed)
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
  fireEvent.click(screen.getByRole('button', { name: 'Reveal node: Local composition note' }))
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(camera()).toBe(revealed)
  fireEvent.click(within(screen.getByRole('toolbar', { name: 'Selection actions' })).getByRole('button', { name: 'Ask Agent' }))
  const dialog = screen.getByRole('dialog', { name: 'Agent conversation' })
  expect(within(dialog).getByTestId('agent-context').textContent).toContain('NODE · Local composition note')
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: 'reveal' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  expect((within(dialog).getByRole('button', { name: 'Apply' }) as HTMLButtonElement).disabled).toBe(true)
  expect((within(dialog).getByRole('button', { name: 'Apply canonical change' }) as HTMLButtonElement).disabled).toBe(true)
})
it('modifies a synthetic rename, applies only local presentation, and updates palette discovery', async () => {
  setup()
  fireEvent.click(await screen.findByRole('button', { name: 'Local composition note' }))
  fireEvent.click(screen.getAllByRole('button', { name: 'Ask Agent' })[0])
  const input = screen.getByLabelText('User intent')
  expect(document.activeElement).toBe(input)
  fireEvent.change(input, { target: { value: 'rename to Draft title' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  expect(screen.getByLabelText('Synthetic proposal').textContent).toContain('Draft title')
  fireEvent.click(screen.getByRole('button', { name: 'Modify' }))
  expect(screen.queryByLabelText('Synthetic proposal')).toBeNull()
  expect(document.activeElement).toBe(input)
  fireEvent.change(input, { target: { value: 'rename to Opening' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  expect((screen.getByRole('button', { name: 'Apply local presentation' }) as HTMLButtonElement).disabled).toBe(false)
  expect(screen.getByLabelText('Synthetic proposal').textContent).toContain('not saved')
  fireEvent.click(screen.getByRole('button', { name: 'Apply local presentation' }))
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Opening')
  expect((screen.getByRole('button', { name: 'Apply' }) as HTMLButtonElement).disabled).toBe(true)
  fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
  expect(screen.getByRole('button', { name: 'Opening' }).getAttribute('aria-pressed')).toBe('true')
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Opening')
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
  expect(screen.getByRole('button', { name: 'Inspect node: Opening' })).toBeTruthy()
})
it('offers two explicit synthetic clips whose modifier selection drives shared shell contexts', async () => {
  setup('nle')
  const toggle = await screen.findByLabelText('Enable synthetic clip presentation fixture')
  expect(screen.queryByRole('button', { name: 'Synthetic opening clip' })).toBeNull()
  fireEvent.click(toggle)
  fireEvent.click(screen.getByRole('button', { name: 'Synthetic opening clip' }))
  fireEvent.click(screen.getByRole('button', { name: /Synthetic closing clip/ }), { ctrlKey: true })
  expect(screen.getByRole('toolbar', { name: 'Selection actions' }).textContent).toContain('CLIP')
  expect(screen.getByRole('toolbar', { name: 'Selection actions' }).textContent).toContain('2 selected')
  expect(screen.getByRole('complementary', { name: 'Selection inspector' }).textContent).toContain('no canonical clip geometry')
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
  expect(screen.getByRole('button', { name: 'Inspect 2 selected clips' })).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Ask Agent about 2 selected clips' }))
  expect(screen.getByTestId('agent-context').textContent).toContain('Synthetic opening clip')
  expect(screen.getByTestId('agent-context').textContent).toContain('Synthetic closing clip')
  expect(screen.getByTestId('agent-context').textContent).toContain('simulated steps · range 4–9')
  expect(screen.getByText('AGENT_PROPOSAL_UI_IS_SYNTHETIC=YES')).toBeTruthy()
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: '把这两段的音量都降低一点' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  expect(screen.getByLabelText('Synthetic proposal').textContent).toContain('Lower the volume of 2 selected clips')
  expect(screen.getByLabelText('Synthetic proposal').textContent).toContain('Synthetic demo')
  expect(screen.getByLabelText('Synthetic proposal').textContent).toContain('Apply is unavailable for this proposal')
  expect((screen.getByRole('button', { name: 'Apply' }) as HTMLButtonElement).disabled).toBe(true)
  expect((within(screen.getByRole('dialog')).getByRole('button', { name: 'Apply canonical change' }) as HTMLButtonElement).disabled).toBe(true)
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: 'rename to Primary only' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  expect(screen.getByLabelText('Synthetic proposal').textContent).toContain('Rename only the primary clip')
  expect(screen.getByLabelText('Synthetic proposal').textContent).toContain('Other selected objects remain unchanged')
  fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
  fireEvent.click(toggle)
  expect(screen.queryByRole('toolbar', { name: 'Selection actions' })).toBeNull()
})
function ContextProbe() {
  const store = useInteractionStore(), selection = useSelection()
  useSurfaceAdapter({ objects: () => [{ id: 'one', kind: 'NODE', title: 'One' }, { id: 'two', kind: 'NODE', title: 'Two' }], supports: ['rename'], handle: () => true })
  return <><button onClick={() => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['one'] })}>Select one</button><button onClick={() => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['two'] })}>Select two</button><output data-testid="selection-count">{selection.selectedObjects.length}</output><AgentLauncher /><AgentShell /></>
}
it('keeps Product UI locale independent from generated Agent conversation language', () => {
  render(<LocalizationProvider initialLocale="zh-CN"><SelectionProvider scope={{ surfaceId: 'workspace' }}><ContextProbe /></SelectionProvider></LocalizationProvider>)
  fireEvent.click(screen.getByText('Select one'))
  fireEvent.click(screen.getByRole('button', { name: '询问 Agent' }))
  fireEvent.click(screen.getByRole('button', { name: '预览' }))
  expect(screen.getByTestId('agent-proposal').textContent).toContain('Open Inspector for the selected presentation object.')
  expect(screen.getByTestId('agent-proposal').textContent).toContain('已理解的请求')
})
it('rejects stale UI proposals and resets context synchronously across project and surface changes', () => {
  const content = (projectId: string, surfaceId: 'canvas' | 'nle' = 'canvas') => <SelectionProvider scope={{ projectId, surfaceId }}><ContextProbe /></SelectionProvider>
  const view = render(content('p'))
  fireEvent.click(screen.getByText('Select one'))
  fireEvent.click(screen.getAllByRole('button', { name: 'Ask Agent' })[0])
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: 'rename to Updated' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  // A concurrent product selection change invalidates a captured proposal.
  fireEvent.click(screen.getByText('Select two'))
  expect(screen.getByRole('alert').textContent).toContain('Context changed')
  expect((screen.getByRole('button', { name: 'Apply local presentation' }) as HTMLButtonElement).disabled).toBe(true)
  view.rerender(content('other'))
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(screen.getByTestId('selection-count').textContent).toBe('0')
  fireEvent.click(screen.getByText('Select one'))
  view.rerender(content('other', 'nle'))
  expect(screen.getByTestId('selection-count').textContent).toBe('0')
})
it('opens Inspector through the local Agent action, closes the dialog, and restores launcher focus', async () => {
  setup()
  fireEvent.click(await screen.findByRole('button', { name: 'Local composition note' }))
  const launcher = screen.getAllByRole('button', { name: 'Ask Agent' })[0]
  act(() => launcher.focus())
  fireEvent.click(launcher)
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: 'inspect' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  fireEvent.click(screen.getByRole('button', { name: 'Open Inspector' }))
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(screen.getByRole('complementary', { name: 'Selection inspector' })).toBeTruthy()
  expect(document.activeElement).toBe(launcher)
})
it('keeps technical proposal evidence closed until diagnostics are explicitly opened', async () => {
  setup('nle')
  fireEvent.click(await screen.findByLabelText('Enable synthetic clip presentation fixture'))
  fireEvent.click(screen.getByRole('button', { name: 'Synthetic opening clip' }))
  fireEvent.click(screen.getByRole('button', { name: /Synthetic closing clip/ }), { metaKey: true })
  fireEvent.click(screen.getAllByRole('button', { name: 'Ask Agent' })[0])
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: '把这两段的音量都降低一点' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  const proposal = screen.getByLabelText('Synthetic proposal')
  const diagnostics = within(proposal).getByText('Proposal diagnostics').closest('details')!
  expect((diagnostics as HTMLDetailsElement).open).toBe(false)
  fireEvent.click(within(proposal).getByText('Proposal diagnostics'))
  expect((diagnostics as HTMLDetailsElement).open).toBe(true)
  expect(proposal.textContent).toContain('SYNTHETIC_EFFECTIVE_ACTION_PROJECTION')
})
it('traps Agent focus and restores its launcher after Escape and backdrop dismissal', () => {
  render(<SelectionProvider scope={{ surfaceId: 'workspace' }}><AgentLauncher /><AgentShell /></SelectionProvider>)
  const launcher = screen.getByRole('button', { name: 'Ask Agent' })
  act(() => launcher.focus())
  fireEvent.click(launcher)
  const dialog = screen.getByRole('dialog')
  expect(document.activeElement).toBe(screen.getByLabelText('User intent'))
  const last = within(dialog).getByLabelText('User intent')
  act(() => last.focus())
  fireEvent.keyDown(last, { key: 'Tab' })
  expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Close Agent conversation' }))
  fireEvent.keyDown(document.activeElement!, { key: 'Tab', shiftKey: true })
  expect(document.activeElement).toBe(last)
  fireEvent.keyDown(dialog, { key: 'Escape' })
  expect(document.activeElement).toBe(launcher)
  fireEvent.click(launcher)
  const backdrop = screen.getByRole('dialog').parentElement!
  const mouseDown = createEvent.mouseDown(backdrop)
  expect(fireEvent(backdrop, mouseDown)).toBe(false)
  expect(mouseDown.defaultPrevented).toBe(true)
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(document.activeElement).toBe(launcher)
  expect(document.body.style.overflow).toBe('')
})
it('keeps Agent header, conversation body, and composer in independent regions', () => {
  render(<SelectionProvider scope={{ surfaceId: 'workspace' }}><AgentLauncher /><AgentShell /></SelectionProvider>)
  const launcher = screen.getByRole('button', { name: 'Ask Agent' })
  act(() => launcher.focus())
  fireEvent.click(launcher)
  const dialog = screen.getByRole('dialog', { name: 'Agent conversation' })
  const body = within(dialog).getByRole('region', { name: 'Agent conversation body' })
  const composer = within(dialog).getByRole('form', { name: 'Agent composer' })

  expect(dialog.classList.contains('ff-interaction-dialog--agent')).toBe(true)
  expect(body.classList.contains('ff-agent-scroll-region')).toBe(true)
  expect(composer.classList.contains('ff-agent-composer')).toBe(true)
  expect(body.contains(composer)).toBe(false)
  expect(composer.contains(within(dialog).getByLabelText('User intent'))).toBe(true)
  expect(document.body.style.overflow).toBe('hidden')

  fireEvent.change(within(dialog).getByLabelText('User intent'), { target: { value: 'inspect' } })
  fireEvent.click(within(dialog).getByRole('button', { name: 'Preview' }))
  fireEvent.click(within(dialog).getByRole('button', { name: 'Modify' }))
  expect(document.activeElement).toBe(within(composer).getByLabelText('User intent'))

  fireEvent.keyDown(dialog, { key: 'Escape' })
  expect(document.body.style.overflow).toBe('')
})
it('preserves internal dialog mousedown defaults, text entry and button clicks', () => {
  render(<SelectionProvider scope={{ surfaceId: 'workspace' }}><AgentLauncher /><AgentShell /></SelectionProvider>)
  fireEvent.click(screen.getByRole('button', { name: 'Ask Agent' }))
  const dialog = screen.getByRole('dialog')
  const input = within(dialog).getByLabelText('User intent')
  const preview = within(dialog).getByRole('button', { name: 'Preview' })
  for (const target of [dialog, input, preview]) {
    const mouseDown = createEvent.mouseDown(target)
    expect(fireEvent(target, mouseDown)).toBe(true)
    expect(mouseDown.defaultPrevented).toBe(false)
    expect(screen.getByRole('dialog')).toBe(dialog)
  }
  fireEvent.change(input, { target: { value: 'inspect' } })
  expect((input as HTMLTextAreaElement).value).toBe('inspect')
  fireEvent.click(preview)
  expect(within(dialog).getByLabelText('Synthetic proposal')).toBeTruthy()
  expect(screen.getByRole('dialog')).toBe(dialog)
})

function RefreshProbe({ title, present = true, reveal = false }: { title: string; present?: boolean; reveal?: boolean }) {
  const store = useInteractionStore(), selection = useSelection()
  useSurfaceAdapter({ objects: () => present ? [{ id: 'one', kind: 'NODE', title }] : [], supports: reveal ? ['rename', 'reveal'] : ['rename'], handle: () => true })
  return <><button onClick={() => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['one'] })}>Choose</button><output data-testid="refresh">{selection.primarySelectedObject?.title}:{selection.revision}:{selection.supported.join(',')}</output><AgentLauncher /><AgentShell /></>
}
it('refreshes adapter projections after render, invalidates old proposals, and prunes without a render loop', () => {
  const content = (title: string, present = true, reveal = false) => <SelectionProvider scope={{ surfaceId: 'canvas' }}><RefreshProbe title={title} present={present} reveal={reveal} /></SelectionProvider>
  const view = render(content('Before'))
  fireEvent.click(screen.getByText('Choose'))
  fireEvent.click(screen.getByRole('button', { name: 'Ask Agent' }))
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  view.rerender(content('After', true, true))
  expect(screen.getByTestId('refresh').textContent).toContain('After:3:rename,reveal')
  expect(screen.getByRole('alert').textContent).toContain('Context changed')
  view.rerender(content('After', true, true))
  expect(screen.getByTestId('refresh').textContent).toBe('After:3:rename,reveal')
  view.rerender(content('After', false, true))
  expect(screen.getByTestId('refresh').textContent).toBe(':4:rename,reveal')
})

function SharedProbe() {
  const store = useInteractionStore()
  useSurfaceAdapter({ objects: () => [{ id: 'one', kind: 'CLIP', title: 'One', synthetic: true }, { id: 'two', kind: 'CLIP', title: 'Two', synthetic: true }], supports: ['rename', 'reveal'], handle: () => true })
  const commands = useSelectionCommands()
  return <><button onClick={() => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['one', 'two'], primaryId: 'two' })}>Choose two</button><SelectionActionBar /><SelectionInspector /><AgentShell /><output data-testid="commands">{JSON.stringify(commands.map(({ id, label, disabledReason }) => ({ id, label, disabledReason })))}</output></>
}
it('localizes shared multi-selection and unavailable commands with stable action IDs', () => {
  const view = render(<LocalizationProvider initialLocale="zh-CN"><SelectionProvider scope={{ surfaceId: 'nle' }}><SharedProbe /></SelectionProvider></LocalizationProvider>)
  fireEvent.click(screen.getByText('Choose two'))
  expect(screen.getByRole('complementary').textContent).toContain('现有操作仅影响主要对象')
  expect(screen.getByRole('toolbar').textContent).toContain('已选择 2 个')
  const commands = JSON.parse(screen.getByTestId('commands').textContent!)
  expect(commands.find((c: { id: string }) => c.id === 'selection.adjust-audio')).toMatchObject({ label: '调整音频（演示）', disabledReason: '仅模拟夹具；未连接获授权的操作。' })
  expect(commands.find((c: { id: string }) => c.id === 'selection.inspect').label).toBe('检查已选择的 2 个片段')
  fireEvent.click(screen.getByRole('button', { name: '询问 Agent' }))
  expect(screen.getByTestId('agent-context').textContent).toContain('已选择 2 个 · 主要 片段 · Two')
  expect(screen.getByTestId('agent-context').textContent).toContain('One, Two')
  expect(within(screen.getByRole('dialog')).getByText('此处尚无法应用此更改。需要已连接的服务器预览和确认流程。')).toBeTruthy()
  expect((within(screen.getByRole('dialog')).getByRole('button', { name: '应用规范更改' }) as HTMLButtonElement).disabled).toBe(true)
  view.unmount()
  render(<SelectionProvider scope={{ surfaceId: 'nle' }}><SharedProbe /></SelectionProvider>)
  fireEvent.click(screen.getByText('Choose two'))
  expect(JSON.parse(screen.getByTestId('commands').textContent!).map((c: { id: string }) => c.id)).toEqual(commands.map((c: { id: string }) => c.id))
})

it('binds Canvas multi-selection to Inspector, toolbar, Command and Agent and invalidates a primary-only proposal', async () => {
  setup()
  const note = await screen.findByRole('button', { name: 'Local composition note' })
  const project = screen.getByRole('button', { name: 'Project reference' })
  fireEvent.click(project)
  fireEvent.click(note, { metaKey: true })
  expect(screen.getByRole('toolbar', { name: 'Selection actions' }).textContent).toContain('2 selected · primary NODE · Local composition note')
  expect(screen.getByRole('complementary', { name: 'Selection inspector' }).textContent).toContain('Existing operations affect only the primary object.')
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Primary note' } })
  expect(project.getAttribute('aria-label')).toBe('Project reference')
  expect(note.getAttribute('aria-label')).toBe('Primary note')
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
  expect(screen.getByRole('button', { name: 'Inspect 2 selected objects' })).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Ask Agent about 2 selected objects' }))
  expect(screen.getByTestId('agent-context').textContent).toContain('2 selected · primary NODE · Primary note')
  expect(screen.getByTestId('agent-context').textContent).toContain('Project reference, Primary note')
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: 'rename to Stale' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  expect(screen.getByTestId('agent-proposal').textContent).toContain('Rename only the primary node')
  // Concurrent surface selection changes invalidate the proposal even when initiated outside the dialog.
  fireEvent.click(project, { ctrlKey: true })
  expect(screen.getByRole('alert').textContent).toContain('Context changed')
  expect((screen.getByRole('button', { name: 'Apply local presentation' }) as HTMLButtonElement).disabled).toBe(true)
  expect((screen.getByRole('button', { name: 'Apply' }) as HTMLButtonElement).disabled).toBe(true)
  expect(note.getAttribute('aria-pressed')).toBe('true')
  expect(project.getAttribute('aria-pressed')).toBe('false')
})


it('increases mounted provider revision across workspace, project and surface scopes with fresh empty lifetimes', () => {
  let active!: InteractionStore
  const handle = vi.fn(() => true)
  function Probe() {
    active = useInteractionStore()
    useSurfaceAdapter({ objects: () => [{ id: 'one', kind: 'NODE', title: 'One' }, { id: 'two', kind: 'NODE', title: 'Two' }], supports: ['rename'], handle })
    const selection = useSelection()
    return <output data-testid="scope-revision">{selection.revision}</output>
  }
  const content = (scope: SelectionScope) => <SelectionProvider scope={scope}><Probe /></SelectionProvider>
  let scope: SelectionScope = { workspaceId: 'w', projectId: 'p', surfaceId: 'canvas' }
  const view = render(content(scope))
  for (const nextScope of [{ ...scope, workspaceId: 'w2' }, { workspaceId: 'w2', projectId: 'p2', surfaceId: 'canvas' as const }, { workspaceId: 'w2', projectId: 'p2', surfaceId: 'nle' as const }, scope]) {
    act(() => {
      for (const ids of [['one'], ['two'], ['one', 'two']]) active.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids })
    })
    const previousStore = active
    const before = active.getSnapshot()
    expect(before.revision).toBeGreaterThan(2)
    const proposal = createProposal(before, 'rename to Stale')
    expect(proposal.action?.type).toBe('rename')
    view.rerender(content({ ...scope }))
    expect(active).toBe(previousStore)
    expect(active.getSnapshot()).toBe(before)
    view.rerender(content(nextScope))
    const after = active.getSnapshot()
    expect(after).toMatchObject({ ...nextScope, selectedRefs: [], primaryRef: null, selectedObjects: [], primarySelectedObject: null })
    expect(after.lifetime).not.toBe(before.lifetime)
    expect(after.revision).toBeGreaterThan(before.revision)
    expect(screen.getByTestId('scope-revision').textContent).toBe(String(after.revision))
    expect(previousStore.getSnapshot().selectedRefs).toEqual([])
    expect(previousStore.getSnapshot().lifetime).not.toBe(before.lifetime)
    expect(applyProposal(active, proposal).ok).toBe(false)
    expect(applyProposal(previousStore, proposal).ok).toBe(false)
    expect(handle).not.toHaveBeenCalled()
    view.rerender(content({ ...nextScope }))
    expect(active.getSnapshot()).toBe(after)
    scope = nextScope
  }
})

it.each([false, true])('Slice1C pagehide persisted=%s retires synchronously and pageshow starts fresh without restoring proposals', persisted => {
  let active!: InteractionStore
  function Probe() { active = useInteractionStore(); return <ContextProbe /> }
  const view = render(<SelectionProvider scope={{ workspaceId: 'w', projectId: 'p', surfaceId: 'canvas' }}><Probe /></SelectionProvider>)
  fireEvent.click(screen.getByText('Select one'))
  fireEvent.click(screen.getByRole('button', { name: 'Ask Agent' }))
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  const old = active, before = old.getSnapshot(), proposal = createProposal(before, 'rename to Stale')
  act(() => {
    window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted }))
    // These assertions run in the event turn, before act can flush queued React effects.
    expect(old.getSnapshot().selectedRefs).toEqual([])
    expect(old.getSnapshot().primaryRef).toBeNull()
    expect(old.getSnapshot().supported).toEqual([])
    expect(old.getSnapshot().lifetime).not.toBe(before.lifetime)
  })
  expect(screen.queryByRole('dialog')).toBeNull()
  act(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted })))
  expect(active.getSnapshot().selectedRefs).toEqual([])
  expect(active.getSnapshot().lifetime).not.toBe(before.lifetime)
  expect(applyProposal(active, proposal).ok).toBe(false)
  expect(applyProposal(old, proposal).ok).toBe(false)
  fireEvent.click(screen.getByText('Select two'))
  expect(active.getSnapshot().primaryRef?.localId).toBe('two')
  expect(old.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['one'] }).ok).toBe(false)
  expect(active.getSnapshot().primaryRef?.localId).toBe('two')
  view.unmount()
})


// Instrument the actual provider with a committed consumer. All application routing, shell,
// ProjectFrame readiness, Canvas adapter and Selection implementation remain real.
let routeObservations: { pathname: string; params: { workspaceId?: string; projectId?: string }; selection: SelectionState; live: SelectionState; store: InteractionStore }[] | null = null
vi.mock('./SelectionContext', async importOriginal => {
  const actual = await importOriginal<typeof import('./SelectionContext')>()
  return { ...actual, SelectionProvider: function ObservedProvider(props: { scope: SelectionScope; children: ReactNode }) {
    return <actual.SelectionProvider {...props}>{props.children}{routeObservations ? <RouteSelectionObserver /> : null}</actual.SelectionProvider>
  } }
})
function RouteSelectionObserver() {
  const selection = useSelection(), store = useInteractionStore()
  const location = useLocation(), params = useParams({ strict: false }) as { workspaceId?: string; projectId?: string }
  useLayoutEffect(() => { routeObservations?.push({ pathname: location.pathname, params, selection, live: store.getSnapshot(), store }) })
  return null
}
async function routeSetup() {
  vi.spyOn(platformClient.workspace, 'getHome').mockImplementation(async workspaceId => ({ workspace: { id: workspaceId, name: 'Workspace' }, tenantId: null, recentProjects: [] }))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } })
  const history = createMemoryHistory({ initialEntries: ['/w/w/projects/p/canvas'] })
  const router = createRouter({ routeTree, history, context: { queryClient: client } })
  routeObservations = []
  const view = render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>)
  await screen.findByRole('button', { name: 'Local composition note' })
  const current = () => routeObservations![routeObservations!.length - 1].store
  const navigate = async (to: string) => { await act(async () => { await router.navigate({ to }) }) }
  return { ...view, router, client, history, current, navigate }
}
function assertRouteObservations() {
  expect(routeObservations!.length).toBeGreaterThan(0)
  for (const observation of routeObservations!) {
    for (const snapshot of [observation.selection, observation.live]) {
      expect(snapshot.workspaceId).toBe(observation.params.workspaceId)
      expect(snapshot.projectId).toBe(observation.params.projectId)
      for (const ref of snapshot.selectedRefs) {
        expect(ref.workspaceId).toBe(observation.params.workspaceId)
        expect(ref.projectId).toBe(observation.params.projectId)
        expect(ref.surfaceId).toBe(snapshot.surfaceId)
      }
      if (observation.pathname.endsWith('/canvas')) expect(snapshot.surfaceId).toBe('canvas')
      if (observation.pathname.endsWith('/workflow')) expect(snapshot.surfaceId).toBe('workflow')
    }
  }
}
it('Slice1C actual route query and hash preserve the same live exact owner and proposal; focus is independent', async () => {
  const app = await routeSetup()
  const note = screen.getByRole('button', { name: 'Local composition note' })
  fireEvent.click(note)
  const owner = app.current(), before = owner.getSnapshot(), proposal = createProposal(before, 'inspect')
  await app.navigate('/w/w/projects/p/canvas?view=wide#main-content')
  expect(app.current()).toBe(owner)
  expect(owner.getSnapshot()).toBe(before)
  act(() => screen.getByRole('button', { name: 'Project reference' }).focus())
  expect(owner.getSnapshot()).toBe(before)
  act(() => expect(applyProposal(owner, proposal).ok).toBe(true))
  assertRouteObservations()
})
it.each([
  ['surface', '/w/w/projects/p/workflow'],
  ['project', '/w/w/projects/p2/canvas'],
  ['workspace', '/w/w2/projects/p/canvas'],
])('Slice1C actual route %s change is empty and fresh with no colliding localId carry and atomic observations', async (_kind, target) => {
  const app = await routeSetup()
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  const old = app.current(), before = old.getSnapshot(), proposal = createProposal(before, 'rename to Stale')
  await app.navigate(target)
  if (target.endsWith('/canvas')) await screen.findByRole('button', { name: 'Local composition note' })
  else await screen.findByRole('heading', { name: 'Workflow planning' })
  const current = app.current()
  expect(current.getSnapshot().selectedRefs).toEqual([])
  expect(current.getSnapshot().primaryRef).toBeNull()
  expect(current.getSnapshot().lifetime).not.toBe(before.lifetime)
  expect(old.getSnapshot().selectedRefs).toEqual([])
  expect(applyProposal(old, proposal).ok).toBe(false)
  expect(applyProposal(current, proposal).ok).toBe(false)
  assertRouteObservations()
})
it('Slice1C actual Back and Forward recreate owners without historical membership', async () => {
  const app = await routeSetup()
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  const first = app.current().getSnapshot()
  await app.navigate('/w/w/projects/p2/canvas')
  await screen.findByRole('button', { name: 'Local composition note' })
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  const second = app.current().getSnapshot()
  await act(async () => app.history.back())
  await waitFor(() => expect(app.current().getSnapshot().projectId).toBe('p'))
  expect(app.current().getSnapshot().selectedRefs).toEqual([])
  expect(app.current().getSnapshot().lifetime).not.toBe(first.lifetime)
  await act(async () => app.history.forward())
  await waitFor(() => expect(app.current().getSnapshot().projectId).toBe('p2'))
  expect(app.current().getSnapshot().selectedRefs).toEqual([])
  expect(app.current().getSnapshot().lifetime).not.toBe(second.lifetime)
  assertRouteObservations()
})
it('Slice1C aborted precommit navigation retains the actual old owner and exact valid proposal', async () => {
  const app = await routeSetup()
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  const owner = app.current(), before = owner.getSnapshot(), proposal = createProposal(before, 'inspect')
  const unblock = app.history.block({ blockerFn: () => true })
  await act(async () => { app.history.push('/w/w/projects/p2/canvas'); await Promise.resolve() })
  expect(app.router.state.location.pathname).toBe('/w/w/projects/p/canvas')
  expect(app.current()).toBe(owner)
  expect(owner.getSnapshot()).toBe(before)
  act(() => expect(applyProposal(owner, proposal).ok).toBe(true))
  unblock()
  assertRouteObservations()
})
it('Slice1C committed unresolved and ERROR targets expose no old selection or adapter and late responses cannot reactivate them', async () => {
  const app = await routeSetup()
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  const old = app.current(), before = old.getSnapshot()
  let resolvePending!: (value: Awaited<ReturnType<typeof platformClient.workspace.getHome>>) => void
  vi.mocked(platformClient.workspace.getHome).mockImplementation(workspaceId => {
    if (workspaceId === 'pending') return new Promise(resolve => { resolvePending = resolve })
    return Promise.reject(Object.assign(new Error('Unavailable'), { name: 'WORKSPACE_SCOPE_NOT_AVAILABLE' }))
  })
  await app.navigate('/w/pending/projects/p/canvas')
  expect(app.router.state.location.pathname).toBe('/w/pending/projects/p/canvas')
  expect(screen.queryByRole('button', { name: 'Local composition note' })).toBeNull()
  expect(screen.queryByRole('complementary', { name: 'Selection inspector' })).toBeNull()
  expect(old.getSnapshot().selectedRefs).toEqual([])
  expect(old.getSnapshot().supported).toEqual([])
  expect(old.getSnapshot().lifetime).not.toBe(before.lifetime)
  await app.navigate('/w/unavailable/projects/p/canvas')
  await screen.findByText('Workspace context unavailable')
  expect(screen.queryByRole('button', { name: 'Local composition note' })).toBeNull()
  await act(async () => resolvePending({ workspace: { id: 'pending', name: 'Late' }, tenantId: null, recentProjects: [] }))
  expect(screen.queryByRole('button', { name: 'Local composition note' })).toBeNull()
  assertRouteObservations()
})
it.each(['/w/w/projects/%20/canvas', '/w/%20/projects/p/canvas', '/w/w/projects/p/unsupported', '/w/w/projects/canvas'])('Slice1C malformed or missing route IDs and unsupported surface %s expose no old owner', async target => {
  const app = await routeSetup()
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  const old = app.current()
  await app.navigate(target)
  expect(screen.queryByRole('button', { name: 'Local composition note' })).toBeNull()
  expect(old.getSnapshot().selectedRefs).toEqual([])
  expect(old.getSnapshot().supported).toEqual([])
  assertRouteObservations()
})
it('Slice1C BLOCKED unknown project is explicitly provisional and confers no canonical authorization', async () => {
  const app = await routeSetup() // Empty recentProjects intentionally does not establish existence.
  expect(screen.getByText(/Provisional presentation/)).toBeTruthy()
  expect(screen.getByText('BLOCKED')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
  expect(app.current().getSnapshot().selectedRefs).toHaveLength(1)
  expect((screen.getByRole('button', { name: 'Create semantic relationship' }) as HTMLButtonElement).disabled).toBe(true)
  expect(app.current().dispatch({ category: 'CANONICAL_SEMANTIC', type: 'semantic', commandId: 'test' }).ok).toBe(false)
  assertRouteObservations()
})
it('Slice1C StrictMode adapter and owner recreation stays usable but never resurrects a retired proposal', () => {
  let active!: InteractionStore
  function Probe() { active = useInteractionStore(); return <ContextProbe /> }
  const content = (show: boolean) => <StrictMode>{show ? <SelectionProvider scope={{ surfaceId: 'canvas' }}><Probe /></SelectionProvider> : null}</StrictMode>
  const view = render(content(true))
  fireEvent.click(screen.getByText('Select one'))
  const old = active, before = old.getSnapshot(), proposal = createProposal(before, 'inspect')
  view.rerender(content(false))
  expect(old.getSnapshot().selectedRefs).toEqual([])
  view.rerender(content(true))
  expect(active.getSnapshot().selectedRefs).toEqual([])
  expect(active.getSnapshot().lifetime).not.toBe(before.lifetime)
  expect(applyProposal(active, proposal).ok).toBe(false)
  fireEvent.click(screen.getByText('Select two'))
  expect(active.getSnapshot().selectedRefs).toHaveLength(1)
})

it.each(['drag', 'marquee', 'pan'] as const)('Slice1C actual route commit cancels %s before old DOM retirement without partial geometry commit', async kind => {
  const app = await routeSetup()
  const stage = screen.getByRole('region', { name: 'Infinite canvas workspace' })
  const note = screen.getByRole('button', { name: 'Local composition note' })
  fireEvent.click(note)
  if (kind === 'pan') fireEvent.click(screen.getByRole('button', { name: 'Pan' }))
  const release = vi.fn(() => expect(stage.isConnected).toBe(true))
  Object.defineProperties(stage, {
    setPointerCapture: { configurable: true, value: vi.fn() },
    releasePointerCapture: { configurable: true, value: release },
  })
  vi.spyOn(stage, 'getBoundingClientRect').mockReturnValue({ left: 0, top: 0, width: 900, height: 700 } as DOMRect)
  const event = { pointerId: 17, pointerType: 'mouse', isPrimary: true, button: 0, clientX: 100, clientY: 100 }
  fireEvent.pointerDown(kind === 'drag' ? note : stage, event)
  fireEvent.pointerMove(stage, { ...event, clientX: 160, clientY: 170 })
  if (kind === 'drag') expect(note.style.left).toBe('490px')
  if (kind === 'marquee') expect(stage.querySelector('[data-canvas-marquee]')).toBeTruthy()
  const old = app.current()
  await app.navigate('/w/w/projects/p2/canvas')
  const next = await screen.findByRole('button', { name: 'Local composition note' })
  expect(release).toHaveBeenCalledWith(17)
  expect(old.getSnapshot().selectedRefs).toEqual([])
  fireEvent.pointerUp(stage, { ...event, clientX: 240, clientY: 250 })
  expect(next.style.left).toBe('430px')
  expect(next.style.top).toBe('230px')
  expect(app.current().getSnapshot().selectedRefs).toEqual([])
  assertRouteObservations()
})


// DOM event simulation verifies handler/default ownership, not native browser key synthesis or OS IME.
function paletteFixture() {
  const first = vi.fn(), last = vi.fn(), unavailable = vi.fn(), close = vi.fn()
  const actions: PaletteAction[] = [
    { id: 'first', label: 'First target', onSelect: first },
    { id: 'blocked', label: 'Blocked target', disabledReason: 'Unavailable fixture reason', onSelect: unavailable },
    { id: 'last', label: 'Last target', onSelect: last },
  ]
  const content = (next = actions) => <CommandPalette open actions={next} onClose={close} />
  const view = render(content())
  return { ...view, actions, content, first, last, unavailable, close, input: screen.getByRole('searchbox') }
}
it('palette enters search, clamps enabled arrows, owns result Home/End and scrolls focused buttons', () => {
  const p = paletteFixture()
  const first = screen.getByRole('button', { name: 'First target' }), last = screen.getByRole('button', { name: 'Last target' })
  const scroll = vi.fn()
  Object.defineProperty(first, 'scrollIntoView', { configurable: true, value: scroll })
  expect(document.activeElement).toBe(p.input)
  fireEvent.keyDown(p.input, { key: 'ArrowDown' })
  expect(document.activeElement).toBe(first)
  expect(scroll).toHaveBeenCalledWith({ block: 'nearest' })
  fireEvent.keyDown(first, { key: 'ArrowUp' })
  expect(document.activeElement).toBe(first)
  fireEvent.keyDown(first, { key: 'ArrowDown' })
  expect(document.activeElement).toBe(last)
  fireEvent.keyDown(last, { key: 'ArrowDown' })
  expect(document.activeElement).toBe(last)
  fireEvent.keyDown(last, { key: 'Home' })
  expect(document.activeElement).toBe(first)
  fireEvent.keyDown(first, { key: 'End' })
  expect(document.activeElement).toBe(last)
  act(() => p.input.focus())
  fireEvent.keyDown(p.input, { key: 'ArrowUp' })
  expect(document.activeElement).toBe(last)
  expect(p.first).not.toHaveBeenCalled()
  expect(p.last).not.toHaveBeenCalled()
})
it('palette preserves editing and modified keys; input Enter is inert and native result click executes once', () => {
  const p = paletteFixture()
  for (const key of ['Home', 'End', ' ', 'a', 'ArrowLeft', 'ArrowRight', 'Tab']) expect(fireEvent.keyDown(p.input, { key })).toBe(true)
  for (const modifier of ['ctrlKey', 'metaKey', 'altKey', 'shiftKey']) {
    for (const key of ['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', ' ']) expect(fireEvent.keyDown(p.input, { key, [modifier]: true })).toBe(true)
  }
  fireEvent.keyDown(p.input, { key: 'Enter' })
  expect(p.first).not.toHaveBeenCalled()
  const first = screen.getByRole('button', { name: 'First target' })
  for (const key of ['Enter', ' ']) {
    expect(fireEvent.keyDown(first, { key })).toBe(true)
    expect(fireEvent.keyUp(first, { key })).toBe(true)
    expect(p.first).toHaveBeenCalledTimes(key === 'Enter' ? 0 : 1)
    fireEvent.click(first, { detail: 0 }) // Explicit simulated native click, no browser proof.
  }
  expect(p.first).toHaveBeenCalledTimes(2)
  fireEvent.click(first, { detail: 1 })
  expect(p.first).toHaveBeenCalledTimes(3)
  fireEvent.click(screen.getByRole('button', { name: 'Blocked target' }))
  expect(p.unavailable).not.toHaveBeenCalled()
})
it('palette reconciles filter, no-match, all-unavailable and removed or disabled active results', () => {
  const p = paletteFixture()
  fireEvent.keyDown(p.input, { key: 'ArrowDown' })
  const removed = screen.getByRole('button', { name: 'First target' })
  p.rerender(p.content(p.actions.slice(1)))
  expect(document.activeElement).toBe(p.input)
  fireEvent.click(removed)
  expect(p.first).not.toHaveBeenCalled()
  fireEvent.keyDown(p.input, { key: 'ArrowDown' })
  p.rerender(p.content(p.actions.slice(1).map(action => ({ ...action, disabledReason: 'Now unavailable' }))))
  expect(document.activeElement).toBe(p.input)
  fireEvent.keyDown(p.input, { key: 'ArrowDown' })
  fireEvent.keyDown(p.input, { key: 'Enter' })
  expect(p.last).not.toHaveBeenCalled()
  expect(screen.getByRole('status').textContent).toBe('2 commands found; 0 available.')
  fireEvent.change(p.input, { target: { value: 'no such target' } })
  expect(screen.getByRole('status').textContent).toBe('No matching commands.')
  fireEvent.keyDown(p.input, { key: 'ArrowUp' })
  fireEvent.keyDown(p.input, { key: 'Enter' })
  expect(document.activeElement).toBe(p.input)
  expect(p.last).not.toHaveBeenCalled()
})
it('palette resolves replacement by stable ID despite label and order changes', () => {
  const p = paletteFixture(), replacement = vi.fn()
  fireEvent.keyDown(p.input, { key: 'ArrowDown' })
  const button = screen.getByRole('button', { name: 'First target' })
  p.rerender(p.content([p.actions[2], { id: 'first', label: '当前目标', onSelect: replacement }]))
  expect(document.activeElement).toBe(button)
  expect(button.textContent).toBe('当前目标')
  fireEvent.click(button)
  expect(replacement).toHaveBeenCalledTimes(1)
  expect(p.first).not.toHaveBeenCalled()
  fireEvent.change(p.input, { target: { value: 'Last' } })
  expect(document.activeElement).toBe(p.input)
  fireEvent.click(button)
  expect(replacement).toHaveBeenCalledTimes(1)
  fireEvent.keyDown(p.input, { key: 'ArrowDown' })
  expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Last target' }))
})
it.each(['events', 'native', 'legacy'])('palette blocks simulated IME navigation, activation and Escape (%s)', mode => {
  const p = paletteFixture(), first = screen.getByRole('button', { name: 'First target' })
  const extra = mode === 'native' ? { isComposing: true } : mode === 'legacy' ? { keyCode: 229 } : {}
  if (mode === 'events') fireEvent.compositionStart(p.input)
  for (const key of ['ArrowDown', 'ArrowUp', 'Home', 'End', 'Escape', 'Enter']) fireEvent.keyDown(p.input, { key, ...extra })
  expect(document.activeElement).toBe(p.input)
  expect(p.close).not.toHaveBeenCalled()
  expect(fireEvent.keyDown(p.input, { key: ' ', ...extra })).toBe(true)
  fireEvent.change(p.input, { target: { value: 'target' } })
  expect((p.input as HTMLInputElement).value).toBe('target')
  act(() => first.focus())
  for (const key of ['Enter', ' ']) {
    expect(fireEvent.keyDown(first, { key, ...extra })).toBe(false)
    expect(fireEvent.keyUp(first, { key, ...extra })).toBe(false)
  }
  if (mode === 'events') {
    fireEvent.click(first, { detail: 0 })
    expect(p.first).not.toHaveBeenCalled()
    fireEvent.compositionEnd(p.input)
  }
  expect(p.first).not.toHaveBeenCalled()
  fireEvent.keyDown(first, { key: 'ArrowDown' })
  expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Last target' }))
})
it.each([
  ['en', 'Search commands', 'Close command palette', '3 commands found; 2 available.', 'No matching commands.', 'Use Up and Down'],
  ['zh-CN', '搜索命令', '关闭命令面板', '找到 3 个命令；2 个可用。', '没有匹配的命令。', '使用上、下方向键'],
] as const)('palette has localized purpose, one live status and external unavailable descriptions in %s', (locale, search, close, count, empty, help) => {
  render(<LocalizationProvider initialLocale={locale}><CommandPalette open onClose={() => {}} actions={[
    { id: 'a', label: 'Same', onSelect: vi.fn() }, { id: 'b', label: 'Same', onSelect: vi.fn() },
    { id: 'blocked', label: 'Unavailable', disabledReason: 'Specific reason', onSelect: vi.fn() },
  ]} /></LocalizationProvider>)
  const dialog = screen.getByRole('dialog'), input = screen.getByRole('searchbox', { name: search })
  expect(screen.getByRole('button', { name: close })).toBeTruthy()
  expect(screen.getByRole('status').textContent).toBe(count)
  expect(dialog.querySelectorAll('[role="status"], [aria-live]')).toHaveLength(1)
  const description = document.getElementById(input.getAttribute('aria-describedby')!)!
  expect(description.textContent).toContain(help)
  const disabled = screen.getByRole('button', { name: 'Unavailable' })
  const reason = document.getElementById(disabled.getAttribute('aria-describedby')!)!
  expect(reason.textContent).toContain('Specific reason')
  expect(disabled.contains(reason)).toBe(false)
  expect(reason.closest('details')).toBeNull()
  expect(dialog.querySelector('[role="combobox"], [role="listbox"], [role="application"]')).toBeNull()
  fireEvent.change(input, { target: { value: 'missing' } })
  expect(screen.getByRole('status').textContent).toBe(empty)
})
it('palette retains dialog Tab boundary trap, Escape and launcher restoration', async () => {
  setup()
  await screen.findByRole('button', { name: 'Local composition note' })
  const launcher = screen.getByRole('button', { name: /Commands/ })
  act(() => launcher.focus())
  fireEvent.click(launcher)
  expect(document.activeElement).toBe(screen.getByRole('searchbox'))
  const close = screen.getByRole('button', { name: 'Close command palette' })
  act(() => close.focus())
  fireEvent.keyDown(close, { key: 'Tab', shiftKey: true })
  const last = document.activeElement!
  expect(last.tagName).toBe('SUMMARY')
  fireEvent.keyDown(last, { key: 'Tab' })
  expect(document.activeElement).toBe(close)
  fireEvent.keyDown(close, { key: 'Escape' })
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(document.activeElement).toBe(launcher)
})
it('palette selection projections reject retained closures and dispatch current primary/query without focus selection changes', () => {
  let store!: InteractionStore, commands!: PaletteAction[]
  const handle = vi.fn(() => true)
  function Probe() {
    store = useInteractionStore()
    useSurfaceAdapter({ objects: () => [{ id: 'one', title: 'One', kind: 'NODE' }, { id: 'two', title: 'Two', kind: 'NODE' }], supports: ['reveal', 'compare-revisions'], handle })
    commands = useSelectionCommands()
    return <CommandPalette open actions={commands} onClose={() => {}} />
  }
  const content = (projectId: string) => <SelectionProvider scope={{ projectId, surfaceId: 'canvas' }}><Probe /></SelectionProvider>
  const view = render(content('p'))
  act(() => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['one'] }))
  const old = commands.find(action => action.id === 'selection.reveal')!
  act(() => {
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['two'] })
    old.onSelect() // Before React reprojects: stale captured primary must not reach the adapter.
  })
  expect(handle).not.toHaveBeenCalled()
  const snapshot = store.getSnapshot(), dispatch = vi.spyOn(store, 'dispatch')
  fireEvent.keyDown(screen.getByRole('searchbox'), { key: 'ArrowDown' })
  fireEvent.keyDown(document.activeElement!, { key: 'ArrowDown' })
  expect(store.getSnapshot()).toBe(snapshot)
  expect(dispatch).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Reveal node: Two' }))
  expect(dispatch).toHaveBeenCalledWith({ category: 'WORKSPACE_PRESENTATION', type: 'reveal', targetId: 'two' }, 'COMMAND')
  act(() => store.setRevisionPair({ from: 'r1', to: 'r2' }))
  const compare = commands.find(action => action.id === 'review.compare')!
  fireEvent.click(screen.getByRole('button', { name: compare.label }))
  expect(dispatch).toHaveBeenCalledWith({ category: 'READ_ONLY_QUERY', type: 'compare-revisions', pair: { from: 'r1', to: 'r2' } }, 'COMMAND')
  const staleAsk = commands.find(action => action.id === 'agent.open')!
  view.rerender(content('p2'))
  act(() => staleAsk.onSelect())
  expect(store.getSnapshot().agentOpen).toBe(false)
  fireEvent.click(screen.getByRole('button', { name: /Ask Agent about/ }))
  expect(store.getSnapshot().agentOpen).toBe(true)
  expect(store.dispatch({ category: 'CANONICAL_SEMANTIC', type: 'semantic', commandId: 'apply' }).ok).toBe(false)
})

it('palette suppresses a simulated composing Space release after composition ends', () => {
  const p = paletteFixture()
  const first = screen.getByRole('button', { name: 'First target' })
  act(() => first.focus())
  fireEvent.compositionStart(p.input)
  expect(fireEvent.keyDown(first, { key: ' ' })).toBe(false)
  fireEvent.compositionEnd(p.input)
  expect(fireEvent.keyUp(first, { key: ' ' })).toBe(false)
  expect(p.first).not.toHaveBeenCalled()
  expect(fireEvent.keyDown(first, { key: ' ' })).toBe(true)
  expect(fireEvent.keyUp(first, { key: ' ' })).toBe(true)
  fireEvent.click(first, { detail: 0 }) // Simulated click only; browser default synthesis is external.
  expect(p.first).toHaveBeenCalledTimes(1)
})
it('retained Selection commands reject changed revisions before dispatch, including untargeted actions', () => {
  let store!: InteractionStore, commands!: PaletteAction[]
  function Probe() {
    store = useInteractionStore()
    useSurfaceAdapter({ objects: () => [{ id: 'one', title: 'One', kind: 'NODE' }, { id: 'two', title: 'Two', kind: 'NODE' }], supports: ['reveal', 'compare-revisions'], handle: () => true })
    commands = useSelectionCommands()
    return <CommandPalette open actions={commands} onClose={() => {}} />
  }
  render(<SelectionProvider scope={{ projectId: 'p', surfaceId: 'canvas' }}><Probe /></SelectionProvider>)
  act(() => {
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['one', 'two'], primaryId: 'one' })
    store.setRevisionPair({ from: 'r1', to: 'r2' })
  })
  const retained = commands
  const dispatch = vi.spyOn(store, 'dispatch')
  act(() => {
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['one', 'two'], primaryId: 'two' })
    store.setRevisionPair({ from: 'r2', to: 'r3' })
    dispatch.mockClear()
    retained.forEach(command => command.onSelect())
  })
  expect(dispatch).not.toHaveBeenCalled()
  expect(store.getSnapshot().primarySelectedObject?.id).toBe('two')
  expect(store.getSnapshot().selectedObjects).toHaveLength(2)
  expect(store.getSnapshot().agentOpen).toBe(false)
  fireEvent.click(screen.getByRole('button', { name: 'Reveal node: Two' }))
  expect(dispatch).toHaveBeenCalledWith({ category: 'WORKSPACE_PRESENTATION', type: 'reveal', targetId: 'two' }, 'COMMAND')
})

it('V5 discovers Canvas history in the shared palette, reconciles Inspector and keeps canonical actions disabled', async () => {
  setup()
  fireEvent.click(await screen.findByRole('button', { name: 'Local composition note' }))
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Palette draft' } })
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
  const palette = screen.getByRole('dialog', { name: 'Command palette' })
  fireEvent.click(within(palette).getByRole('button', { name: 'Undo local edit' }))
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Local composition note')
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
  fireEvent.click(within(screen.getByRole('dialog', { name: 'Command palette' })).getByRole('button', { name: 'Redo local edit' }))
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Palette draft')
  fireEvent.click(screen.getAllByRole('button', { name: 'Ask Agent' })[0])
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: 'rename to Agent draft' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  fireEvent.click(screen.getByRole('button', { name: 'Apply local presentation' }))
  fireEvent.click(screen.getByRole('button', { name: 'Close Agent conversation' }))
  fireEvent.click(screen.getByRole('button', { name: 'Undo local edit' }))
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('Palette draft')
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
  const canonical = within(screen.getByRole('dialog', { name: 'Command palette' })).getAllByRole('button').filter(button => /canonical/i.test(button.textContent ?? ''))
  expect(canonical.length).toBeGreaterThan(0)
  canonical.forEach(button => expect((button as HTMLButtonElement).disabled).toBe(true))
})

it('V5 retained contextual history checks live adapter availability even before a new render', () => {
  let store!: InteractionStore, commands!: PaletteAction[]
  let available = true
  const handle = vi.fn(() => true)
  function Probe() {
    store = useInteractionStore()
    useSurfaceAdapter({ objects: () => [], get supports() { return available ? ['undo-local'] as const : [] }, handle })
    commands = useSelectionCommands()
    return null
  }
  render(<SelectionProvider scope={{ surfaceId: 'canvas' }}><Probe /></SelectionProvider>)
  const retained = commands.find(command => command.id === 'canvas.undo-local')!
  expect(retained).toBeTruthy()
  const before = store.getSnapshot()
  available = false // No reconciliation or render has happened yet.
  expect(store.getSnapshot()).toBe(before)
  act(() => retained.onSelect())
  expect(handle).not.toHaveBeenCalled()
  expect(commands.some(command => command.id === 'canvas.undo-local')).toBe(false)
})

it('Workflow Agent preview rejects overlong titles before shared proposal truncation can bypass validation', () => {
  render(<SelectionProvider scope={{ surfaceId: 'workflow' }}><WorkflowSketch /><SelectionInspector /><AgentLauncher /><AgentShell /></SelectionProvider>)
  fireEvent.click(screen.getByRole('button', { name: 'Add OPERATION card' }))
  fireEvent.click(screen.getByTestId('workflow-sketch-node'))
  fireEvent.click(screen.getByRole('button', { name: 'Ask Agent' }))
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: 'rename to ' + 'x'.repeat(121) } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  expect(screen.queryByRole('button', { name: 'Apply local presentation' })).toBeNull()
  expect(screen.getByLabelText('Synthetic proposal').textContent).toContain('Enter a title of 1–120 characters')
  expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('OPERATION')
  fireEvent.click(screen.getByRole('button', { name: 'Modify' }))
  fireEvent.change(screen.getByLabelText('User intent'), { target: { value: 'rename to Repaired' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  fireEvent.click(screen.getByRole('button', { name: 'Apply local presentation' }))
  expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('Repaired')
})


it('IR01-1 shared toolbar rejects retained selection revisions and still dispatches current local actions', () => {
  let store!: InteractionStore
  const handle = vi.fn(() => true)
  function Probe() {
    store = useInteractionStore()
    useSurfaceAdapter({ objects: () => [{ id: 'one', title: 'One', kind: 'NODE' }, { id: 'two', title: 'Two', kind: 'NODE' }], supports: ['reveal'], handle })
    return <SelectionActionBar />
  }
  render(<SelectionProvider scope={{ projectId: 'p', surfaceId: 'canvas' }}><Probe /></SelectionProvider>)
  act(() => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['one', 'two'], primaryId: 'one' }))
  fireEvent.click(screen.getByText('More'))
  const callbacks = screen.getAllByRole('button').filter(button => !(button as HTMLButtonElement).disabled).map(element => {
    const key = Object.keys(element).find(key => key.startsWith('__reactProps$'))!
    return (element as unknown as Record<string, { onClick: () => void }>)[key].onClick
  })
  const dispatch = vi.spyOn(store, 'dispatch')
  act(() => {
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['one', 'two'], primaryId: 'two' })
    dispatch.mockClear()
    callbacks.forEach(invoke => invoke()) // Invoke before React renders the new primary.
  })
  expect(dispatch).not.toHaveBeenCalled()
  expect(handle).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Reveal primary node' }))
  expect(handle).toHaveBeenCalledWith({ category: 'WORKSPACE_PRESENTATION', type: 'reveal', targetId: 'two' })
  fireEvent.click(screen.getByRole('button', { name: 'Hide inspector' }))
  expect(store.getSnapshot().inspectorOpen).toBe(false)
  fireEvent.click(screen.getByRole('button', { name: 'Show inspector' }))
  expect(store.getSnapshot().inspectorOpen).toBe(true)
  fireEvent.click(screen.getByRole('button', { name: 'Hide inspector' }))
  fireEvent.click(screen.getByRole('button', { name: 'Edit local properties' }))
  expect(store.getSnapshot().inspectorOpen).toBe(true)
  fireEvent.click(screen.getByRole('button', { name: 'Ask Agent' }))
  expect(store.getSnapshot().agentOpen).toBe(true)
  expect(store.dispatch({ category: 'CANONICAL_SEMANTIC', type: 'semantic', commandId: 'apply' }).ok).toBe(false)
  fireEvent.click(screen.getByRole('button', { name: 'Clear selection' }))
  expect(store.getSnapshot().selectedObjects).toHaveLength(0)
})


it('IR01-2 current Canvas mobile properties keep title editing live and require a new opening for a new primary', async () => {
  setup()
  fireEvent.click(await screen.findByRole('button', { name: 'Local composition note' }))
  const launcher = screen.getByRole('button', { name: 'Open selection properties' })
  launcher.focus(); fireEvent.click(launcher)
  const dialog = screen.getByRole('dialog', { name: 'Selection properties' })
  fireEvent.change(within(dialog).getByLabelText('Local title'), { target: { value: 'Still editing' } })
  expect(screen.getByRole('dialog')).toBe(dialog)
  expect((within(dialog).getByLabelText('Local title') as HTMLInputElement).value).toBe('Still editing')
  fireEvent.keyDown(dialog, { key: 'Escape' })
  expect(document.activeElement).toBe(launcher)
  fireEvent.click(launcher)
  fireEvent.click(screen.getByRole('button', { name: 'Project reference' }))
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(screen.getByRole('complementary', { name: 'Selection inspector' }).textContent).toContain('Project reference')
})
