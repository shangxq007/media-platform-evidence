import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ProductAppShell } from './AppShell'
import { NotificationInboxProvider } from '../../product/notifications/NotificationInbox'
import { createNotificationFixture } from '../../product/notifications/fixture'
import { surfaceRegistry } from '../../foundation/surfaceRegistry'
import type { ProjectContextValue } from '../../foundation/projectContext'
import { LocalizationProvider, createCatalog } from '../../localization'
import { commandRegistry, type ShortcutOverrides } from '../../foundation/commandRegistry'
import { platformQueryKeys } from '../../foundation/platformClient'
import { unknownAccess, type EffectiveAccessEntry } from '../../foundation/effectiveAccess'
import { useInteractionStore, useSurfaceAdapter } from '../../interaction/SelectionContext'

const project: ProjectContextValue = {
  workspaceId: 'workspace-1', tenantId: null, projectId: 'project-1', project: { kind: 'PROJECT', id: 'project-1' },
  status: 'BLOCKED', reason: 'Scoped relationship unavailable.',
}

function renderShell() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}><ProductAppShell surfaceId="nle" workspaceId="workspace-1" project={project}><h1>Editor center</h1><input aria-label="Unsaved local edit" defaultValue="" /></ProductAppShell></QueryClientProvider>)
}

describe('shared application shell', () => {
  it('switches Product UI locale from the shell selector', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<LocalizationProvider><QueryClientProvider client={queryClient}><ProductAppShell surfaceId="nle" workspaceId="workspace-1" project={project}><h1>Editor center</h1></ProductAppShell></QueryClientProvider></LocalizationProvider>)
    expect(screen.getByRole('button', { name: /Commands/ })).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Product UI language'), { target: { value: 'zh-CN' } })
    expect(screen.getByRole('button', { name: /命令/ })).toBeTruthy()
    expect(screen.getByLabelText('产品界面语言')).toBeTruthy()
  })

  it('allows remote copy replacement without changing protected command availability', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const remote = createCatalog('en', { shell: { 'command.timeline.operation.apply': { message: 'Remote timeline wording', params: [] } } })
    render(<LocalizationProvider remoteProvider={{ loadCatalog: async () => remote }}><QueryClientProvider client={queryClient}><ProductAppShell surfaceId="nle" workspaceId="workspace-1" project={project}><h1>Editor center</h1></ProductAppShell></QueryClientProvider></LocalizationProvider>)
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    const action = await screen.findByRole('button', { name: 'Remote timeline wording' }) as HTMLButtonElement
    expect(action.disabled).toBe(true)
  })

  it('exposes keyboard-reachable navigation and named panel controls', () => {
    renderShell()
    fireEvent.click(screen.getByText('Navigation'))
    expect(screen.getByRole('navigation', { name: 'Global navigation' })).toBeTruthy()
    expect(screen.getByRole('navigation', { name: 'Project surface switcher' })).toBeTruthy()
    const toggle = screen.getByRole('button', { name: 'Toggle asset browser' })
    expect(toggle.getAttribute('aria-pressed')).toBe('false')
    fireEvent.click(toggle)
    expect(toggle.getAttribute('aria-pressed')).toBe('true')
    expect(within(screen.getByRole('navigation', { name: 'Project surface switcher' })).getByRole('link', { name: /Canvas/ }).getAttribute('href'))
      .toBe('/w/workspace-1/projects/project-1/canvas')
    expect(within(screen.getByRole('navigation', { name: 'Project surface switcher' })).getByRole('link', { name: /Workflow/ }).getAttribute('href'))
      .toBe('/w/workspace-1/projects/project-1/workflow')
  })

  it('opens a palette whose protected commands remain disabled', () => {
    renderShell()
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    expect(screen.getByRole('dialog', { name: 'Command palette' })).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Apply timeline operation' }) as HTMLButtonElement).disabled).toBe(true)
  })
})

it('uses only horizontal Studio and leaves text-entry shortcuts alone', () => {
  window.history.replaceState(null, '', '?layout=B')
  const view = renderShell()
  expect(view.container.querySelector('.ff-app-shell')?.getAttribute('data-studio')).toBe('horizontal')
  expect(screen.queryByRole('button', { name: /Layout/ })).toBeNull()
  const input = screen.getByLabelText('Unsaved local edit')
  fireEvent.change(input, { target: { value: 'Keep this' } })
  fireEvent.keyDown(input, { key: 'k', ctrlKey: true })
  expect(screen.queryByRole('dialog')).toBeNull()
  expect((input as HTMLInputElement).value).toBe('Keep this')
  window.history.replaceState(null, '', '/')
})


describe.each([
  { locale: 'en' as const, create: 'Create project', apply: 'Apply timeline operation', canonical: 'This change cannot be applied here yet. A connected server preview and confirmation flow is required; use the existing timeline advanced controls for supported operations.', hidden: 'This surface is not discoverable at its current maturity.', unresolved: 'A server-resolved Project context is required.', missing: 'Effective access is not available from the server. This action is disabled.' },
  { locale: 'zh-CN' as const, create: '创建项目', apply: '应用时间线操作', canonical: '此处尚无法应用此更改。需要已连接的服务器预览和确认流程。', hidden: '此界面在当前成熟度下尚未开放。', unresolved: '需要服务器已解析的项目上下文。', missing: '服务器尚未提供有效访问权限信息。此操作已禁用。' },
])('real AppShell unavailable descriptions in $locale', copy => {
  function setup(surfaceId: 'nle' | 'storyboard', resolved: boolean, entry?: EffectiveAccessEntry) {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnMount: false } } })
    const accessKey = platformQueryKeys.effectiveAccess(commandRegistry.flatMap(command => command.requiredAccessKey ? [command.requiredAccessKey] : []))
    if (entry) queryClient.setQueryData(accessKey, { [entry.key]: entry })
    let store!: ReturnType<typeof useInteractionStore>
    function Probe() { store = useInteractionStore(); return null }
    render(<LocalizationProvider initialLocale={copy.locale}><QueryClientProvider client={queryClient}><ProductAppShell surfaceId={surfaceId} workspaceId="workspace-1" project={{ ...project, status: resolved ? 'RESOLVED' : 'BLOCKED' }}><Probe /></ProductAppShell></QueryClientProvider></LocalizationProvider>)
    const dispatch = vi.spyOn(store, 'dispatch')
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    return { queryClient, accessKey, dispatch }
  }

  function expectDisabledDescription(label: string, reason: string) {
    const button = screen.getByRole('button', { name: name => name === label || name.startsWith(`${label} `) }) as HTMLButtonElement
    expect(button.disabled).toBe(true)
    const description = document.getElementById(button.getAttribute('aria-describedby')!)!
    expect(description).not.toBeNull()
    expect(description.textContent).toBe(reason)
    expect(button.contains(description)).toBe(false)
    expect(description.closest('details')).toBeNull()
    fireEvent.click(button)
    fireEvent.keyDown(button, { key: 'Enter' })
    fireEvent.keyUp(button, { key: 'Enter' })
    fireEvent.keyDown(button, { key: ' ' })
    fireEvent.keyUp(button, { key: ' ' })
    expect(screen.getByRole('dialog')).toBeTruthy()
  }

  it('localizes real missing access before and after the fail-closed adapter resolves', async () => {
    const { queryClient, accessKey, dispatch } = setup('nle', true)
    expectDisabledDescription(copy.create, `${copy.canonical} ${copy.missing}`)
    await waitFor(() => expect(queryClient.getQueryState(accessKey)?.status).toBe('success'))
    expectDisabledDescription(copy.apply, `${copy.canonical} ${copy.missing}`)
    expect(dispatch).not.toHaveBeenCalled()
  })

  it('localizes the unresolved project explanation', () => {
    const { dispatch } = setup('nle', false)
    expectDisabledDescription(copy.apply, `${copy.canonical} ${copy.unresolved}`)
    expect(dispatch).not.toHaveBeenCalled()
  })

  it('localizes the hidden surface explanation ahead of unresolved project and access reasons', () => {
    const { dispatch } = setup('storyboard', false)
    expectDisabledDescription(copy.apply, `${copy.canonical} ${copy.hidden}`)
    expect(dispatch).not.toHaveBeenCalled()
  })

  it.each([
    'Denied by workspace policy P-42.',
    'This surface is not discoverable at its current maturity.',
    'A server-resolved Project context is required.',
    'Effective access is not available from the server. This action is disabled.',
  ])('preserves opaque server explanation verbatim: %s', explanation => {
    const { dispatch } = setup('nle', true, { ...unknownAccess('timeline.operation.apply'), source: 'SERVER', status: 'POLICY_DENIED', explanation })
    expectDisabledDescription(copy.apply, `${copy.canonical} ${explanation}`)
    expect(dispatch).not.toHaveBeenCalled()
  })

  it('keeps canonical actions disabled with localized copy even for available access', () => {
    const { dispatch } = setup('nle', true, { ...unknownAccess('timeline.operation.apply'), source: 'SERVER', status: 'AVAILABLE', explanation: 'Server allows invocation.' })
    expectDisabledDescription(copy.apply, copy.canonical)
    expect(dispatch).not.toHaveBeenCalled()
  })
})


describe('shared notification entry', () => {
  it.each(surfaceRegistry.map(surface => surface.id))('has exactly one fail-closed entry on %s', surfaceId => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<QueryClientProvider client={client}><ProductAppShell surfaceId={surfaceId}><h1>Surface</h1></ProductAppShell></QueryClientProvider>)
    expect(screen.getAllByRole('button', { name: 'Notifications · unread count unknown' })).toHaveLength(1)
    fireEvent.click(screen.getByRole('button', { name: /Notifications/ }))
    expect(screen.getByRole('dialog', { name: 'Notifications' })).toBeTruthy()
  })

  it('keeps inbox identity independent of project and preserves Selection on opening, detail and read', async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const source = createNotificationFixture()
    const list = vi.spyOn(source.adapter, 'list')
    let store!: ReturnType<typeof useInteractionStore>
    function Probe() {
      store = useInteractionStore()
      useSurfaceAdapter({ objects: () => [{ id: 'selected-a', title: 'Selected A', kind: 'NODE' }, { id: 'selected-b', title: 'Selected B', kind: 'NODE' }], supports: [], handle: () => false })
      return null
    }
    const content = (projectId: string) => <NotificationInboxProvider source={source}><QueryClientProvider client={client}><ProductAppShell surfaceId="canvas" workspaceId="workspace-1" project={{ ...project, projectId }}><Probe /></ProductAppShell></QueryClientProvider></NotificationInboxProvider>
    const view = render(content('project-1'))
    act(() => { store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['selected-a', 'selected-b'], primaryId: 'selected-b' }) })
    expect(store.getSnapshot().selectedObjects).toHaveLength(2)
    const dispatch = vi.spyOn(store, 'dispatch')
    const before = store.getSnapshot()
    fireEvent.click(screen.getByRole('button', { name: /Notifications/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Read notification: Preview is ready' }))
    fireEvent.click(within(screen.getByRole('listitem', { name: 'Preview is ready' })).getByRole('button', { name: 'Mark as read' }))
    await waitFor(() => expect(within(screen.getByRole('listitem', { name: 'Preview is ready' })).getByText('Read')).toBeTruthy())
    expect(store.getSnapshot()).toBe(before)
    expect(dispatch).not.toHaveBeenCalled()
    view.rerender(content('project-2'))
    expect(screen.getByRole('dialog', { name: 'Notifications' })).toBeTruthy()
    expect(within(screen.getByRole('listitem', { name: 'Preview is ready' })).getByText('Read')).toBeTruthy()
    expect(list).toHaveBeenCalledTimes(2)
    for (const [request] of list.mock.calls) {
      expect(request.context).toEqual(source.context)
      expect(request.context).not.toHaveProperty('workspaceId')
      expect(request.context).not.toHaveProperty('projectId')
    }
  })
})


describe('session-local command palette shortcut', () => {
  function keyDown(target: Window | HTMLElement, init: KeyboardEventInit) {
    const event = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, ...init })
    // Happy DOM aliases AltGraph to any Alt key. Model the independent, unpressed
    // AltGraph state for ordinary chords; the AltGraph rejection case sets it true.
    const nativeModifierState = event.getModifierState.bind(event)
    Object.defineProperty(event, 'getModifierState', { value: (key: string) => key === 'AltGraph' ? false : nativeModifierState(key) })
    return fireEvent(target, event)
  }

  function setup(shortcutOverrides: ShortcutOverrides = {}) {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    return render(<QueryClientProvider client={client}><ProductAppShell surfaceId="canvas" workspaceId="workspace-1" project={project} shortcutOverrides={shortcutOverrides}><input aria-label="Local draft" defaultValue="Keep this draft" /></ProductAppShell></QueryClientProvider>)
  }

  it('applies, cancels and resets the shortcut while preserving focus, drafts and shared selection actions', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    let store!: ReturnType<typeof useInteractionStore>
    function Probe() {
      store = useInteractionStore()
      useSurfaceAdapter({ objects: () => [{ id: 'a', title: 'Selected A', kind: 'NODE' }, { id: 'b', title: 'Selected B', kind: 'NODE' }], supports: ['reveal'], handle: () => true })
      return <input aria-label="Local draft" defaultValue="Keep this draft" />
    }
    render(<QueryClientProvider client={client}><ProductAppShell surfaceId="canvas" shortcutOverrides={{ 'project.create': 'Mod+Alt+N' }}><Probe /></ProductAppShell></QueryClientProvider>)
    act(() => { store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['a', 'b'], primaryId: 'b' }) })
    const before = store.getSnapshot()
    const dispatch = vi.spyOn(store, 'dispatch')
    const launcher = screen.getByRole('button', { name: 'Keyboard shortcut' })
    const commands = screen.getByRole('button', { name: /Commands/ })
    launcher.focus()
    fireEvent.click(launcher)
    const dialog = screen.getByRole('dialog', { name: 'Keyboard shortcut' })
    const choice = within(dialog).getByRole('combobox', { name: 'Command palette shortcut' })
    expect(document.activeElement).toBe(choice)
    expect((choice as HTMLSelectElement).value).toBe('Mod+K')
    fireEvent.change(choice, { target: { value: 'Mod+Alt+K' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }))
    expect(document.activeElement).toBe(launcher)
    expect(commands.textContent).toContain('Mod+K')
    fireEvent.click(launcher)
    fireEvent.change(screen.getByRole('combobox', { name: 'Command palette shortcut' }), { target: { value: 'Mod+Alt+P' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply shortcut' }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(launcher)
    expect(commands.textContent).toContain('Mod+Alt+P')
    expect(keyDown(window, { key: 'k', ctrlKey: true })).toBe(true)
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(keyDown(window, { key: 'p', ctrlKey: true, altKey: true })).toBe(false)
    expect(screen.getByRole('dialog', { name: 'Command palette' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Create project Mod+Alt+N' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Inspect 2 selected objects' }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(launcher)
    expect(dispatch).toHaveBeenCalledWith({ category: 'LOCAL_EPHEMERAL', type: 'inspect', open: true }, 'COMMAND')
    expect(store.getSnapshot().selectedRefs).toEqual(before.selectedRefs)
    expect(store.getSnapshot().primaryRef).toEqual(before.primaryRef)
    dispatch.mockClear()
    fireEvent.click(launcher)
    fireEvent.click(screen.getByRole('button', { name: 'Restore default' }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(launcher)
    expect(commands.textContent).toContain('Mod+K')
    expect(keyDown(window, { key: 'p', ctrlKey: true, altKey: true })).toBe(true)
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(dispatch).not.toHaveBeenCalled()
    expect((screen.getByLabelText('Local draft') as HTMLInputElement).value).toBe('Keep this draft')
    expect(store.getSnapshot().selectedRefs).toEqual(before.selectedRefs)
    keyDown(window, { key: 'k', ctrlKey: true })
    expect(screen.getByRole('dialog', { name: 'Command palette' })).toBeTruthy()
  })

  it('leaves native editing and handled gestures alone, including an active composition without a key flag', () => {
    setup({ 'navigation.command-palette.open': 'Mod+Alt+K' })
    const launcher = screen.getByRole('button', { name: 'Keyboard shortcut' })
    for (const extra of [{ repeat: true }, { shiftKey: true }, { metaKey: true }, { isComposing: true }, { keyCode: 229 }, { ctrlKey: false }]) {
      expect(keyDown(launcher, { key: 'k', ctrlKey: true, altKey: true, ...extra })).toBe(true)
      expect(screen.queryByRole('dialog')).toBeNull()
    }
    const altGraph = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, altKey: true, bubbles: true, cancelable: true })
    Object.defineProperty(altGraph, 'getModifierState', { value: (key: string) => key === 'AltGraph' })
    expect(fireEvent(launcher, altGraph)).toBe(true)
    expect(screen.queryByRole('dialog')).toBeNull()
    const handled = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, altKey: true, bubbles: true, cancelable: true })
    handled.preventDefault()
    fireEvent(launcher, handled)
    expect(screen.queryByRole('dialog')).toBeNull()
    for (const tag of ['input', 'textarea', 'select', 'div']) {
      const field = document.createElement(tag)
      if (tag === 'div') field.setAttribute('contenteditable', 'true')
      const target = tag === 'div' ? field.appendChild(document.createElement('span')) : field
      document.body.appendChild(field)
      expect(keyDown(target, { key: 'k', ctrlKey: true, altKey: true })).toBe(true)
      expect(screen.queryByRole('dialog')).toBeNull()
      field.remove()
    }
    launcher.focus()
    fireEvent.compositionStart(launcher)
    expect(keyDown(launcher, { key: 'k', ctrlKey: true, altKey: true })).toBe(true)
    expect(screen.queryByRole('dialog')).toBeNull()
    fireEvent.compositionEnd(launcher)
    expect(keyDown(launcher, { key: 'K', ctrlKey: true, altKey: true })).toBe(false)
    expect(screen.getByRole('dialog', { name: 'Command palette' })).toBeTruthy()
  })

  it('keeps modal ownership for shortcuts and behind-modal activation and hands focus to a shared Agent action', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    let store!: ReturnType<typeof useInteractionStore>
    function Probe() { store = useInteractionStore(); return null }
    render(<QueryClientProvider client={client}><ProductAppShell surfaceId="canvas"><Probe /></ProductAppShell></QueryClientProvider>)
    const launcher = screen.getByRole('button', { name: 'Keyboard shortcut' })
    const commands = screen.getByRole('button', { name: /Commands/ })
    const notifications = screen.getByRole('button', { name: /Notifications/ })
    launcher.focus()
    fireEvent.click(launcher)
    const editor = screen.getByRole('dialog', { name: 'Keyboard shortcut' })
    const entry = document.activeElement
    expect(keyDown(window, { key: 'k', ctrlKey: true })).toBe(true)
    fireEvent.click(commands)
    fireEvent.click(notifications)
    expect(screen.getAllByRole('dialog')).toEqual([editor])
    expect(document.activeElement).toBe(entry)
    // A shared store action can open the existing Agent without a DOM click.
    act(() => { store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'agent', open: true }) })
    expect(screen.queryByRole('dialog', { name: 'Keyboard shortcut' })).toBeNull()
    const agent = screen.getByRole('dialog', { name: 'Agent conversation' })
    expect(agent.contains(document.activeElement)).toBe(true)
    fireEvent.click(commands)
    fireEvent.click(launcher)
    expect(screen.getAllByRole('dialog')).toEqual([agent])
    keyDown(agent, { key: 'Escape' })
    commands.focus()
    fireEvent.click(commands)
    fireEvent.click(launcher)
    expect(screen.getAllByRole('dialog')).toHaveLength(1)
    fireEvent.click(screen.getByRole('button', { name: /Ask Agent about/ }))
    const sharedAgent = screen.getByRole('dialog', { name: 'Agent conversation' })
    expect(screen.getAllByRole('dialog')).toEqual([sharedAgent])
    expect(sharedAgent.contains(document.activeElement)).toBe(true)
    keyDown(sharedAgent, { key: 'Escape' })
    expect(document.activeElement).toBe(commands)
    notifications.focus()
    fireEvent.click(notifications)
    const inbox = screen.getByRole('dialog', { name: 'Notifications' })
    const inboxEntry = document.activeElement
    fireEvent.click(commands)
    fireEvent.click(launcher)
    expect(keyDown(window, { key: 'k', ctrlKey: true })).toBe(true)
    expect(screen.getAllByRole('dialog')).toEqual([inbox])
    expect(document.activeElement).toBe(inboxEntry)
  })

  it.each([
    { locale: 'en' as const, launcher: 'Keyboard shortcut', commands: /Commands/, choice: 'Command palette shortcut', unavailable: 'Shortcut unavailable', unsupported: 'This shortcut is not supported. Choose a listed shortcut or restore the default.', reset: 'Restore default', apply: 'Apply shortcut', cancel: 'Cancel' },
    { locale: 'zh-CN' as const, launcher: '键盘快捷键', commands: /命令/, choice: '命令面板快捷键', unavailable: '快捷键不可用', unsupported: '不支持此快捷键。请选择列表中的快捷键或恢复默认设置。', reset: '恢复默认', apply: '应用快捷键', cancel: '取消' },
  ])('repairs an unsupported initial shortcut and retains native dialog focus in $locale', copy => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<LocalizationProvider initialLocale={copy.locale}><QueryClientProvider client={client}><ProductAppShell surfaceId="canvas" shortcutOverrides={{ 'navigation.command-palette.open': '<img src=x onerror=alert(1)>' }}>Draft</ProductAppShell></QueryClientProvider></LocalizationProvider>)
    const commands = screen.getByRole('button', { name: copy.commands })
    const launcher = screen.getByRole('button', { name: copy.launcher })
    expect(commands.textContent).toContain(copy.unavailable)
    expect(keyDown(window, { key: 'k', ctrlKey: true })).toBe(true)
    expect(screen.queryByRole('dialog')).toBeNull()
    commands.focus()
    fireEvent.click(commands)
    keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(document.activeElement).toBe(commands)
    launcher.focus()
    fireEvent.click(launcher)
    const dialog = screen.getByRole('dialog', { name: copy.launcher })
    expect(within(dialog).getByRole('alert').textContent).toBe(copy.unsupported)
    expect(dialog.querySelector('img')).toBeNull()
    expect((screen.getByRole('button', { name: copy.apply }) as HTMLButtonElement).disabled).toBe(true)
    const choice = screen.getByRole('combobox', { name: copy.choice })
    expect(document.activeElement).toBe(choice)
    const cancel = screen.getByRole('button', { name: copy.cancel })
    cancel.focus()
    keyDown(cancel, { key: 'Tab' })
    const close = within(dialog).getAllByRole('button')[0]
    expect(document.activeElement).toBe(close)
    keyDown(close, { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(cancel)
    fireEvent.mouseDown(dialog.parentElement!)
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(launcher)
    expect(commands.textContent).toContain(copy.unavailable)
    fireEvent.click(launcher)
    fireEvent.click(screen.getByRole('button', { name: copy.reset }))
    expect(document.activeElement).toBe(launcher)
    expect(commands.textContent).toContain('Mod+K')
    keyDown(window, { key: 'k', metaKey: true })
    expect(screen.getByRole('dialog')).toBeTruthy()
  })

  it('rejects initial and edited collisions without replacing other commands or silently resetting', () => {
    setup({ 'navigation.command-palette.open': 'Mod+Alt+P', 'project.create': 'mod+alt+p', 'render.open': 'Mod+K' })
    const commands = screen.getByRole('button', { name: /Commands/ })
    const launcher = screen.getByRole('button', { name: 'Keyboard shortcut' })
    expect(commands.textContent).toContain('Shortcut unavailable')
    for (const event of [{ key: 'p', altKey: true }, { key: 'k' }]) {
      expect(keyDown(window, { ctrlKey: true, ...event })).toBe(true)
      expect(screen.queryByRole('dialog')).toBeNull()
    }
    fireEvent.click(launcher)
    expect(screen.getByText('This shortcut is assigned to another command. Choose a different shortcut.')).toBeTruthy()
    const apply = screen.getByRole('button', { name: 'Apply shortcut' }) as HTMLButtonElement
    const reset = screen.getByRole('button', { name: 'Restore default' }) as HTMLButtonElement
    expect(apply.disabled).toBe(true)
    expect(reset.disabled).toBe(true)
    expect(screen.getByText('The default shortcut is assigned to another command and cannot be restored.')).toBeTruthy()
    fireEvent.click(reset)
    expect(commands.textContent).toContain('Shortcut unavailable')
    fireEvent.change(screen.getByRole('combobox', { name: 'Command palette shortcut' }), { target: { value: 'Mod+Alt+K' } })
    expect(apply.disabled).toBe(false)
    fireEvent.click(apply)
    fireEvent.click(launcher)
    fireEvent.change(screen.getByRole('combobox', { name: 'Command palette shortcut' }), { target: { value: 'Mod+Alt+P' } })
    expect((screen.getByRole('button', { name: 'Apply shortcut' }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(commands.textContent).toContain('Mod+Alt+K')
    keyDown(window, { key: 'k', ctrlKey: true, altKey: true })
    expect(screen.getByRole('dialog', { name: 'Command palette' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Create project mod+alt+p' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Open render entry Mod+K' })).toBeTruthy()
  })

  it('retires only local remapping and editor state across scope, owner and mount lifetimes', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    let store!: ReturnType<typeof useInteractionStore>
    function Probe() {
      store = useInteractionStore()
      useSurfaceAdapter({ objects: () => [], supports: [], handle: () => false })
      return <input aria-label="Surviving shell consumer" defaultValue="Keep local work" />
    }
    const content = (workspaceId: string, projectId: string, surfaceId: 'canvas' | 'nle') => <QueryClientProvider client={client}><ProductAppShell surfaceId={surfaceId} workspaceId={workspaceId} project={{ ...project, workspaceId, projectId }} shortcutOverrides={{ 'navigation.command-palette.open': 'Mod+Alt+K', 'project.create': 'Mod+Alt+N' }}><Probe /></ProductAppShell></QueryClientProvider>
    const view = render(content('workspace-1', 'project-1', 'canvas'))
    const consumer = screen.getByLabelText('Surviving shell consumer')
    fireEvent.change(consumer, { target: { value: 'Edited local work' } })
    fireEvent.click(screen.getByRole('button', { name: 'Toggle asset browser' }))
    const remapAndOpenEditor = () => {
      const launcher = screen.getByRole('button', { name: 'Keyboard shortcut' })
      launcher.focus()
      fireEvent.click(launcher)
      fireEvent.change(screen.getByRole('combobox', { name: 'Command palette shortcut' }), { target: { value: 'Mod+Alt+P' } })
      fireEvent.click(screen.getByRole('button', { name: 'Apply shortcut' }))
      fireEvent.click(launcher)
      return launcher
    }
    for (const scope of [['workspace-2', 'project-1', 'canvas'], ['workspace-2', 'project-2', 'canvas'], ['workspace-2', 'project-2', 'nle'], ['workspace-1', 'project-1', 'canvas']] as const) {
      const launcher = remapAndOpenEditor()
      view.rerender(content(scope[0], scope[1], scope[2]))
      expect(screen.queryByRole('dialog')).toBeNull()
      expect(document.activeElement).toBe(launcher)
      expect(screen.getByRole('button', { name: /Commands/ }).textContent).toContain('Mod+Alt+K')
      expect(keyDown(window, { key: 'p', ctrlKey: true, altKey: true })).toBe(true)
      expect(screen.queryByRole('dialog')).toBeNull()
      expect(screen.getByLabelText('Surviving shell consumer')).toBe(consumer)
      expect((consumer as HTMLInputElement).value).toBe('Edited local work')
      expect(screen.getByRole('button', { name: 'Toggle asset browser' }).getAttribute('aria-pressed')).toBe('true')
    }
    const launcher = remapAndOpenEditor()
    const owner = store
    const lifetime = store.getSnapshot().lifetime
    act(() => { store.retireSelectionOwner('adapter') })
    expect(store).toBe(owner)
    expect(store.getSnapshot().lifetime).not.toBe(lifetime)
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(launcher)
    expect(screen.getByRole('button', { name: /Commands/ }).textContent).toContain('Mod+Alt+K')
    remapAndOpenEditor()
    keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    keyDown(window, { key: 'p', ctrlKey: true, altKey: true })
    expect(screen.getByRole('dialog', { name: 'Command palette' })).toBeTruthy()
    view.rerender(content('workspace-3', 'project-3', 'nle'))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.getByRole('button', { name: /Commands/ }).textContent).toContain('Mod+Alt+K')
    view.unmount()
    setup()
    expect(screen.getByRole('button', { name: /Commands/ }).textContent).toContain('Mod+K')
    expect(keyDown(window, { key: 'p', ctrlKey: true, altKey: true })).toBe(true)
    expect(screen.queryByRole('dialog')).toBeNull()
    keyDown(window, { key: 'k', ctrlKey: true })
    expect(screen.getByRole('dialog', { name: 'Command palette' })).toBeTruthy()
  })

  it('uses the supported caller binding for both discovery and exact keyboard activation', () => {
    setup({ 'navigation.command-palette.open': 'Mod+Alt+P' })
    expect(screen.getByRole('button', { name: /Commands/ }).textContent).toContain('Mod+Alt+P')
    expect(keyDown(window, { key: 'k', ctrlKey: true })).toBe(true)
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(keyDown(window, { key: 'p', ctrlKey: true, metaKey: true, altKey: true })).toBe(true)
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(keyDown(window, { key: 'p', metaKey: true, altKey: true })).toBe(false)
    expect(screen.getByRole('dialog', { name: 'Command palette' })).toBeTruthy()
  })
})
