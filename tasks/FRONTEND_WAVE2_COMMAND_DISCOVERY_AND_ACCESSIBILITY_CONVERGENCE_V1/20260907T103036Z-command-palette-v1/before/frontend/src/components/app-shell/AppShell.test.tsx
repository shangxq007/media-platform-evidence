import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ProductAppShell } from './AppShell'
import type { ProjectContextValue } from '../../foundation/projectContext'
import { LocalizationProvider, createCatalog } from '../../localization'

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
