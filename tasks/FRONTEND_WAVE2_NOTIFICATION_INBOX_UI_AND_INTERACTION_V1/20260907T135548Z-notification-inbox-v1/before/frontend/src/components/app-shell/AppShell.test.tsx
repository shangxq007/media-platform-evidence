import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ProductAppShell } from './AppShell'
import type { ProjectContextValue } from '../../foundation/projectContext'
import { LocalizationProvider, createCatalog } from '../../localization'
import { commandRegistry } from '../../foundation/commandRegistry'
import { platformQueryKeys } from '../../foundation/platformClient'
import { unknownAccess, type EffectiveAccessEntry } from '../../foundation/effectiveAccess'
import { useInteractionStore } from '../../interaction/SelectionContext'

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
