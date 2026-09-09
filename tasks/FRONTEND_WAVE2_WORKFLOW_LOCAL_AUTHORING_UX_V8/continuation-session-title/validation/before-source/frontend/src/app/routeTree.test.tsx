import { StrictMode } from 'react'
import type { User } from 'oidc-client-ts'
import * as oidcClient from '../auth/oidcClient'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createMemoryHistory, createRouter } from '@tanstack/react-router'
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { LocalizationProvider } from '../localization'
import { unknownAccess } from '../foundation/effectiveAccess'
import { platformQueryKeys, platformClient } from '../foundation/platformClient'
import api, { platformClient as exportedPlatformClient } from '../api'
import { surfaceRegistry } from '../foundation/surfaceRegistry'
import { implementedRouteInventory, legacyRouteInventory, routeTree } from './routeTree'
import { timelineQueryGateway } from '../api/app/timeline-query.gateway'
import { contentHash, projectId, revisionId, timelineId } from '../product/timeline/types'

// Await test-runner transformation of the shared lazy module before UI timing assertions.
// The registered routes still render through their real Suspense/lazy boundary.
beforeAll(async () => { await import('../surfaces/FoundationPages') })

describe('runtime route registration and deep-link restoration', () => {
  afterEach(() => vi.restoreAllMocks())

  it('registers every implemented page and preserved legacy link exactly once', () => {
    expect(new Set(implementedRouteInventory).size).toBe(implementedRouteInventory.length)
    expect(new Set(legacyRouteInventory).size).toBe(legacyRouteInventory.length)
    for (const surface of surfaceRegistry) expect(implementedRouteInventory).toContain(surface.routeTemplate as typeof implementedRouteInventory[number])
    const registered = (routeTree.children ?? []).map(child => (child.options as { path?: string }).path)
    for (const path of [...implementedRouteInventory, ...legacyRouteInventory]) expect(registered).toContain(path)
  })

  it('restores Workspace, Project, and surface identity from a creative deep link and fails unauthorized commands closed', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({
      workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1',
      recentProjects: [{ id: 'project-1', name: 'Launch film' }],
    })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/canvas'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Infinite canvas' })).toBeTruthy())
    expect(await within(screen.getByRole('navigation', { name: 'Breadcrumb' })).findByText('Launch film')).toBeTruthy()
    expect(screen.getByText(/server cannot yet verify the Workspace-to-Project relationship/i)).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Create semantic relationship' }) as HTMLButtonElement).disabled).toBe(true)
    const canvas = screen.getByRole('region', { name: 'Infinite canvas workspace' })
    fireEvent.keyDown(canvas, { key: 'ArrowLeft' })
    const canvasStatus = screen.getByText((_content, element) => element?.classList.contains('ff-canvas-status') ?? false)
    expect(canvasStatus.textContent).toContain('Viewport: 24, 0')
  })

  it('remounts the ProjectFrame subtree when same-route Workspace or Project parameters change', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({
      workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1',
      recentProjects: [{ id: 'project-1', name: 'First film' }, { id: 'project-2', name: 'Second film' }],
    })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/canvas'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)
    const canvas = await screen.findByRole('region', { name: 'Infinite canvas workspace' })
    fireEvent.keyDown(canvas, { key: 'ArrowLeft' })
    expect(screen.getByText((_content, element) => element?.classList.contains('ff-canvas-status') ?? false).textContent).toContain('Viewport: 24, 0')

    fireEvent.click(screen.getByRole('button', { name: 'Local composition note' }))
    fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Private local title' } })

    await act(async () => {
      await router.navigate({
        to: '/w/$workspaceId/projects/$projectId/canvas',
        params: { workspaceId: 'workspace-1', projectId: 'project-2' },
      })
    })
    expect((await screen.findAllByText('Second film')).length).toBeGreaterThan(0)
    expect(screen.getByText((_content, element) => element?.classList.contains('ff-canvas-status') ?? false).textContent).toContain('Viewport: 0, 0')
    expect(screen.getByText('project-2')).toBeTruthy()
    expect(screen.queryByText('Private local title')).toBeNull()
    expect(screen.queryByLabelText('Local title')).toBeNull()
  })

  it('integrates the disposable sketch on the Workflow route while invoke remains unavailable', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({
      workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1',
      recentProjects: [{ id: 'project-1', name: 'Launch film' }],
    })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/workflow'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)

    expect(await screen.findByRole('heading', { name: 'Local arrangement sketch' })).toBeTruthy()
    const invoke = screen.getByRole('button', { name: 'Invoke workflow' }) as HTMLButtonElement
    expect(invoke.disabled).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Add CONDITION card' }))
    expect(screen.getByTestId('workflow-sketch-node').textContent).toContain('CONDITION')
  })

  it('retires Workflow drafts and confirmations when host tenant or effective access changes without granting invocation', async () => {
    const home = { workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1', recentProjects: [] }
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue(home)
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/workflow'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)
    await screen.findByRole('heading', { name: 'Local arrangement sketch' })
    const addDraft = () => {
      fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
      fireEvent.click(screen.getByTestId('workflow-sketch-node'))
      fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Private draft' } })
      fireEvent.click(screen.getByRole('button', { name: 'Remove selected card' }))
    }
    addDraft()
    act(() => queryClient.setQueryData(platformQueryKeys.workspaceHome('workspace-1'), { ...home, tenantId: 'tenant-2' }))
    await waitFor(() => expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0))
    expect(screen.queryByRole('dialog')).toBeNull()
    addDraft()
    act(() => queryClient.setQueryData(platformQueryKeys.effectiveAccess(['workflow.invoke']), { 'workflow.invoke': { ...unknownAccess('workflow.invoke'), source: 'SERVER', status: 'POLICY_DENIED' } }))
    await waitFor(() => expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect((screen.getByRole('button', { name: 'Invoke workflow' }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    expect(screen.getAllByTestId('workflow-sketch-node')).toHaveLength(1)
    act(() => queryClient.setQueryData(platformQueryKeys.effectiveAccess(['workflow.invoke']), { 'workflow.invoke': { ...unknownAccess('workflow.invoke'), source: 'SERVER', status: 'AVAILABLE' } }))
    await waitFor(() => expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0))
    expect((screen.getByRole('button', { name: 'Invoke workflow' }) as HTMLButtonElement).disabled).toBe(true)
    addDraft()
    act(() => queryClient.getQueryCache().find({ queryKey: platformQueryKeys.workspaceHome('workspace-1') })!.setState({ status: 'error', error: new Error('Workspace unavailable') }))
    await screen.findByRole('heading', { name: 'Workspace context unavailable' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
  })

  it('presents bilingual Workflow page guidance and category explanations on the existing route', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({ workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: null, recentProjects: [] })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const router = createRouter({ routeTree, history: createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/workflow'] }), context: { queryClient } })
    render(<LocalizationProvider><QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider></LocalizationProvider>)
    await screen.findByRole('heading', { name: 'Local arrangement sketch' })
    expect(screen.getByText('Operation — note work you want to do.')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Product UI language'), { target: { value: 'zh-CN' } })
    expect(screen.getByRole('heading', { name: '工作流规划' })).toBeTruthy()
    expect(screen.getByText('操作 — 记录想完成的工作。')).toBeTruthy()
    expect(screen.getByText('此页面不会保存或运行工作流。')).toBeTruthy()
    expect((screen.getByRole('button', { name: '调用工作流' }) as HTMLButtonElement).disabled).toBe(true)
  })

  it('reaches the post-H7 edit route and loads explicit canonical HEAD authority', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({
      workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1',
      recentProjects: [{ id: 'project-1', name: 'Launch film' }],
    })
    vi.spyOn(timelineQueryGateway, 'getHead').mockResolvedValue({ ok: true, value: {
      projectId: projectId('project-1'), timelineId: timelineId('project-1'),
      revisionId: revisionId('revision-R0'), contentHash: contentHash('a'.repeat(64)),
    } })
    vi.spyOn(timelineQueryGateway, 'listRevisions').mockResolvedValue({ ok: true, value: [] })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/edit'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Timeline editor' })).toBeTruthy())
    expect(await screen.findByText('revision-R0')).toBeTruthy()
    expect(screen.getByText('ASSET GATEWAY · UNAVAILABLE')).toBeTruthy()
  })

  it('renders the Workspace to Projects entry without synthesizing a Project selection', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({
      workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1',
      recentProjects: [{ id: 'project-1', name: 'Launch film' }],
    })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/w/workspace-1/home'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Editorial' })).toBeTruthy())
    expect(screen.getByText('Launch film')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'View project list' }).getAttribute('href')).toBe('/w/workspace-1/projects')
    expect((screen.getByRole('button', { name: 'Open' }) as HTMLButtonElement).disabled).toBe(true)
  })

  it('routes the existing Projects destination to the fail-closed recent-project browser without using Workspace home as its source', async () => {
    const home = vi.spyOn(platformClient.workspace, 'getHome')
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/w/workspace-1/projects'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)
    expect(await screen.findByRole('heading', { name: 'Recent projects unavailable' })).toBeTruthy()
    expect(screen.getByText(/no authenticated, session-bound recent-project source/i)).toBeTruthy()
    expect(home).not.toHaveBeenCalled()
  })

  it('routes Operations renders to the fail-closed source browser and leaves Storage behavior unchanged', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/operations/renders'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    const view = render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)
    expect(await screen.findByRole('heading', { name: 'Render observability unavailable' })).toBeTruthy()
    expect(screen.getByText(/no authenticated, session-bound, single-Project Render source/i)).toBeTruthy()
    expect(screen.getByText('unconfigured')).toBeTruthy()

    view.unmount()
    const storageHistory = createMemoryHistory({ initialEntries: ['/operations/storage'] })
    const storageRouter = createRouter({ routeTree, history: storageHistory, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={storageRouter} /></QueryClientProvider>)
    expect(await screen.findByRole('heading', { name: 'Storage' })).toBeTruthy()
    expect(screen.getByRole('searchbox', { name: 'Search Storage' })).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Filter' }) as HTMLButtonElement).disabled).toBe(true)
    expect(screen.getByText(/existing storage health diagnostic/i)).toBeTruthy()
  })

  it('registers the Project Production consumer with exact route scope and no implicit fixture or request', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({
      workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1',
      recentProjects: [{ id: 'project-1', name: 'Launch film' }],
    })
    const fetch = vi.spyOn(globalThis, 'fetch')
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/production'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)
    expect(await screen.findByRole('heading', { name: 'Production snapshot unavailable' })).toBeTruthy()
    expect(screen.getAllByText('workspace-1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('project-1').length).toBeGreaterThan(0)
    expect(screen.getByText(/no authenticated, session-bound, single-Project Scene and Shot source/i)).toBeTruthy()
    expect(screen.queryByText(/SIMULATED PRODUCTION DATA/)).toBeNull()
    expect(fetch).not.toHaveBeenCalled()
  })

  it('handles Workspace API errors without inventing an empty state', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockRejectedValue(new Error('offline'))
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const history = createMemoryHistory({ initialEntries: ['/w/workspace-1/home'] })
    const router = createRouter({ routeTree, history, context: { queryClient } })
    render(<QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider>)
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Workspace unavailable' })).toBeTruthy())
  })

  it('preserves the historical default API export alongside the additive platform client', () => {
    expect(api.defaults.baseURL).toBe('/api/v1')
    expect(exportedPlatformClient).toBe(platformClient)
  })
})

// Real oidcClient export, mocked native SDK boundary: no real config, credentials or transport.
const oidcFixture = vi.hoisted(() => {
  const names = ['UserLoaded', 'UserUnloaded', 'AccessTokenExpired', 'UserSignedIn', 'UserSignedOut', 'UserSessionChanged'] as const
  const listeners = Object.fromEntries(names.map(name => [name, new Set<() => void>()])) as Record<typeof names[number], Set<() => void>>
  const events = Object.fromEntries(names.flatMap(name => [
    [`add${name}`, (callback: () => void) => { listeners[name].add(callback); return () => { listeners[name].delete(callback) } }],
    [`remove${name}`, (callback: () => void) => { listeners[name].delete(callback) }],
  ]))
  return { names, listeners, events, enabled: false, constructed: vi.fn(), getUser: vi.fn(), signoutRedirect: vi.fn() }
})
vi.mock('../auth/oidcConfig', () => ({
  isOidcEnabled: () => oidcFixture.enabled,
  getOidcSettings: () => ({ issuer: 'https://oidc.invalid', clientId: 'native-sdk-test', redirectUri: 'https://app.invalid/callback', scope: 'openid' }),
}))
vi.mock('oidc-client-ts', () => ({
  UserManager: class {
    constructor() { oidcFixture.constructed() }
    events = oidcFixture.events
    getUser = oidcFixture.getUser
    signoutRedirect = oidcFixture.signoutRedirect
  },
  WebStorageStateStore: class {},
}))

function renderedHandler<T>(element: HTMLElement, name: string): T {
  const key = Object.keys(element).find(key => key.startsWith('__reactProps$'))!
  return (element as unknown as Record<string, Record<string, T>>)[key][name]
}

async function workflowIdentityHost() {
  oidcFixture.enabled = true
  vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({ workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1', recentProjects: [] })
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const router = createRouter({ routeTree, history: createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/workflow'] }), context: { queryClient } })
  const view = render(<StrictMode><QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider></StrictMode>)
  await screen.findByRole('heading', { name: 'Local arrangement sketch' })
  return view
}

function privateWorkflowDraft() {
  fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
  fireEvent.click(screen.getByTestId('workflow-sketch-node'))
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Private previous session' } })
  const edit = renderedHandler<(event: { target: { value: string } }) => void>(screen.getByLabelText('Local title'), 'onChange')
  fireEvent.click(screen.getByRole('button', { name: 'Remove selected card' }))
  const confirm = renderedHandler<() => void>(screen.getByRole('button', { name: 'Remove card' }), 'onClick')
  return { edit, confirm }
}

function expectRetiredImmediately() {
  expect(screen.queryAllByTestId('workflow-sketch-node')).toHaveLength(0)
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(screen.queryByLabelText('Local title')).toBeNull()
  expect(document.body.textContent).not.toContain('Private previous session')
}

function expectStaleHandlersRejected(retained: ReturnType<typeof privateWorkflowDraft>) {
  fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
  fireEvent.click(screen.getByTestId('workflow-sketch-node'))
  // IDs intentionally collide across remounts; old closures must reject ownership.
  act(() => { retained.edit({ target: { value: 'Retired edit' } }); retained.confirm() })
  expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('WAIT')
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('WAIT')
  expect((screen.getByRole('button', { name: 'Invoke workflow' }) as HTMLButtonElement).disabled).toBe(true)
}

describe('Workflow native OIDC identity/session retirement', () => {
  afterEach(() => {
    cleanup()
    oidcFixture.enabled = false
    vi.restoreAllMocks()
    oidcFixture.getUser.mockReset()
    oidcFixture.signoutRedirect.mockReset()
  })

  it('provides an unconfigured no-op subscription without constructing a manager', () => {
    oidcFixture.enabled = false
    const before = oidcFixture.constructed.mock.calls.length
    const callback = vi.fn()
    const unsubscribe = oidcClient.subscribeOidcSessionRetirement(callback)
    for (const listeners of Object.values(oidcFixture.listeners)) for (const listener of listeners) listener()
    unsubscribe()
    unsubscribe()
    expect(callback).not.toHaveBeenCalled()
    expect(oidcFixture.constructed.mock.calls.length).toBe(before)
  })

  it('subscribes through the real export and symmetrically removes native and signout listeners', async () => {
    oidcFixture.enabled = true
    const callback = vi.fn()
    const unsubscribe = oidcClient.subscribeOidcSessionRetirement(callback)
    const retained = [...oidcFixture.listeners.UserLoaded][0]
    for (const name of oidcFixture.names) {
      expect(oidcFixture.listeners[name].size).toBe(1)
      for (const listener of oidcFixture.listeners[name]) listener()
    }
    expect(callback).toHaveBeenCalledTimes(oidcFixture.names.length)
    unsubscribe()
    unsubscribe()
    for (const listeners of Object.values(oidcFixture.listeners)) expect(listeners.size).toBe(0)
    retained()
    await oidcClient.signOutOidc()
    expect(callback).toHaveBeenCalledTimes(oidcFixture.names.length)
    expect(oidcFixture.getUser).not.toHaveBeenCalled()
  })

  it.each(oidcFixture.names)('withdraws old Workflow content synchronously on SDK %s and rejects retained editor/confirmation callbacks', async name => {
    const view = await workflowIdentityHost()
    const retained = privateWorkflowDraft()
    act(() => {
      for (const listener of oidcFixture.listeners[name]) listener()
      // Checked during SDK delivery, before act flushes batched React work.
      expectRetiredImmediately()
    })
    expectStaleHandlersRejected(retained)
    expect(oidcFixture.getUser).not.toHaveBeenCalled()
    view.unmount()
    for (const listeners of Object.values(oidcFixture.listeners)) expect(listeners.size).toBe(0)
  })

  it.each(['resolve', 'reject'] as const)('retires at signout initiation before redirect settles (%s), with no draft restoration', async outcome => {
    let resolve!: () => void
    let reject!: (error: Error) => void
    oidcFixture.signoutRedirect.mockReturnValue(new Promise<void>((yes, no) => { resolve = yes; reject = no }))
    await workflowIdentityHost()
    const retained = privateWorkflowDraft()
    let completion!: Promise<string>
    act(() => {
      completion = oidcClient.signOutOidc().then(() => 'resolved', () => 'rejected')
      expectRetiredImmediately()
    })
    expectStaleHandlersRejected(retained)
    await act(async () => {
      if (outcome === 'resolve') resolve()
      else reject(new Error('Mock redirect failed'))
      expect(await completion).toBe(outcome === 'resolve' ? 'resolved' : 'rejected')
    })
    expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('WAIT')
  })

  it('does not hydrate from a late async getter, and treats late UserLoaded as retirement rather than restoration', async () => {
    let resolve!: (user: User | null) => void
    oidcFixture.getUser.mockReturnValue(new Promise<User | null>(yes => { resolve = yes }))
    await workflowIdentityHost()
    const late = oidcClient.getOidcUser()
    const retained = privateWorkflowDraft()
    act(() => {
      for (const listener of oidcFixture.listeners.UserUnloaded) listener()
      expectRetiredImmediately()
    })
    expectStaleHandlersRejected(retained)
    await act(async () => { resolve(null); await late })
    expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('WAIT')
    act(() => {
      for (const listener of oidcFixture.listeners.UserLoaded) listener()
      expectRetiredImmediately()
    })
  })
})
