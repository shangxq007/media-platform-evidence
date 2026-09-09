import { StrictMode } from 'react'
import { User } from 'oidc-client-ts'
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
    expect(await screen.findByText('revision-R0', { selector: 'code' })).toBeTruthy()
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
  const listeners = Object.fromEntries(names.map(name => [name, new Set<(user?: User) => void | Promise<void>>()])) as Record<typeof names[number], Set<(user?: User) => void | Promise<void>>>
  const events = Object.fromEntries(names.flatMap(name => [
    [`add${name}`, (callback: (user?: User) => void | Promise<void>) => { listeners[name].add(callback); return () => { listeners[name].delete(callback) } }],
    [`remove${name}`, (callback: (user?: User) => void | Promise<void>) => { listeners[name].delete(callback) }],
  ]))
  return { names, listeners, events, enabled: false, constructed: vi.fn(), getUser: vi.fn().mockResolvedValue(null), signoutRedirect: vi.fn() }
})
vi.mock('../auth/oidcConfig', () => ({
  isOidcEnabled: () => oidcFixture.enabled,
  getOidcSettings: () => ({ issuer: 'https://oidc.invalid', clientId: 'native-sdk-test', redirectUri: 'https://app.invalid/callback', scope: 'openid' }),
}))
vi.mock('oidc-client-ts', async importOriginal => ({
  ...await importOriginal<typeof import('oidc-client-ts')>(),
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
  return { ...view, queryClient, router }
}

function privateWorkflowDraft() {
  fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
  fireEvent.click(screen.getByTestId('workflow-sketch-node'))
  fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Private previous session' } })
  const arrange = renderedHandler<() => void>(screen.getByRole('button', { name: 'Move right' }), 'onClick')
  const edit = renderedHandler<(event: { target: { value: string } }) => void>(screen.getByLabelText('Local title'), 'onChange')
  fireEvent.click(screen.getByRole('button', { name: 'Remove selected card' }))
  const confirm = renderedHandler<() => void>(screen.getByRole('button', { name: 'Remove card' }), 'onClick')
  return { edit, confirm, arrange }
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
  act(() => { retained.edit({ target: { value: 'Retired edit' } }); retained.confirm(); retained.arrange() })
  expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('WAIT')
  expect((screen.getByLabelText('Local title') as HTMLInputElement).value).toBe('WAIT')
  expect(screen.getByTestId('workflow-sketch-node').textContent).toContain('X 32 · Y 32')
  expect((screen.getByRole('button', { name: 'Invoke workflow' }) as HTMLButtonElement).disabled).toBe(true)
}

function sdkUser(overrides: Partial<ConstructorParameters<typeof User>[0]> = {}) {
  return new User({
    access_token: 'test-access-original', token_type: 'Bearer', scope: 'openid profile',
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    profile: { iss: 'https://oidc.invalid', aud: 'native-sdk-test', sub: 'principal-1', sid: 'session-1', tenant_id: 'tenant-1', iat: 100, exp: 9999999999 },
    ...overrides,
  })
}

async function emitLoaded(user: User) {
  oidcFixture.getUser.mockResolvedValue(user)
  await act(async () => { for (const listener of oidcFixture.listeners.UserLoaded) await listener(user) })
}

describe('Workflow native OIDC identity/session retirement', () => {
  it('preserves the complete draft and unfinished inspector input through two ordinary SDK renewals and a render', async () => {
    const initial = sdkUser()
    oidcFixture.getUser.mockResolvedValue(initial)
    const view = await workflowIdentityHost()
    await act(async () => {})
    fireEvent.click(screen.getByRole('button', { name: 'Add REVIEW card' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    const cards = screen.getAllByTestId('workflow-sketch-node')
    fireEvent.click(cards[0])
    fireEvent.change(screen.getByLabelText('Local title'), { target: { value: 'Keep this title' } })
    fireEvent.click(screen.getByRole('button', { name: 'Move right' }))
    fireEvent.change(screen.getByLabelText('Local title'), { target: { value: '   ' } })
    const input = screen.getByLabelText('Local title') as HTMLInputElement
    act(() => input.focus())
    for (let renewal = 1; renewal <= 2; renewal += 1) {
      await emitLoaded(sdkUser({ access_token: `test-renewed-${renewal}`, expires_at: initial.expires_at! + renewal * 3600,
        profile: { ...initial.profile, iat: 100 + renewal, exp: initial.profile.exp + renewal * 3600 } }))
      expect(screen.getAllByTestId('workflow-sketch-node')).toEqual(cards)
      expect(cards[0].getAttribute('aria-label')).toBe('Keep this title')
      expect(cards[0].getAttribute('aria-pressed')).toBe('true')
      expect(cards[0].textContent).toContain('X 56 · Y 32')
      expect(screen.getByLabelText('Local title')).toBe(input)
      expect(input.value).toBe('   ')
      expect(document.activeElement).toBe(input)
    }
    act(() => view.queryClient.setQueryData(platformQueryKeys.workspaceHome('workspace-1'), { workspace: { id: 'workspace-1', name: 'Editorial rerender' }, tenantId: 'tenant-1', recentProjects: [] }))
    await act(async () => {})
    expect(screen.getAllByTestId('workflow-sketch-node')).toEqual(cards)
    expect(input.value).toBe('   ')
  })

  it.each(['principal', 'tenant', 'session', 'scope', 'expired', 'unknown expiry', 'invalid expiry', 'missing sid', 'ambiguous tenant'] as const)('retires on actual %s change and rejects old title, arrange and delete callbacks', async change => {
    const initial = sdkUser()
    oidcFixture.getUser.mockResolvedValue(initial)
    await workflowIdentityHost()
    const retained = privateWorkflowDraft()
    const next = sdkUser()
    if (change === 'principal') next.profile.sub = 'principal-2'
    if (change === 'tenant') next.profile.tenant_id = 'tenant-2'
    if (change === 'session') next.profile.sid = 'session-2'
    if (change === 'scope') next.scope = 'openid'
    if (change === 'expired') next.expires_at = 0
    if (change === 'unknown expiry') next.expires_at = undefined
    if (change === 'invalid expiry') next.expires_at = Number.NaN
    if (change === 'missing sid') delete next.profile.sid
    if (change === 'ambiguous tenant') next.profile.tenantId = 'different-tenant'
    await emitLoaded(next)
    expectRetiredImmediately()
    expectStaleHandlersRejected(retained)
  })

  it('preserves edits for a fresh observation of equal access but retires a changed factor or access error', async () => {
    oidcFixture.getUser.mockResolvedValue(sdkUser())
    const view = await workflowIdentityHost()
    const key = platformQueryKeys.effectiveAccess(['workflow.invoke'])
    const entry = { ...unknownAccess('workflow.invoke'), observedAt: '2026-09-09T01:00:00Z' }
    act(() => view.queryClient.setQueryData(key, { 'workflow.invoke': entry }))
    await act(async () => {})
    privateWorkflowDraft()
    const card = screen.getByTestId('workflow-sketch-node')
    act(() => view.queryClient.setQueryData(key, { 'workflow.invoke': { ...entry, observedAt: '2026-09-09T01:01:00Z', explanation: 'Same effective decision, newer explanation.' } }))
    await act(async () => {})
    expect(screen.getByTestId('workflow-sketch-node')).toBe(card)
    act(() => view.queryClient.setQueryData(key, { 'workflow.invoke': { ...entry, factors: { ...entry.factors, policy: 'UNSATISFIED' } } }))
    await waitFor(() => expectRetiredImmediately())
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    act(() => view.queryClient.getQueryCache().find({ queryKey: key })!.setState({ status: 'error', error: new Error('Access expired') }))
    await waitFor(() => expectRetiredImmediately())
  })

  it('establishes trustworthy delayed initial hydration without a fake identity switch', async () => {
    let resolve!: (user: User) => void
    oidcFixture.getUser.mockReturnValue(new Promise<User>(yes => { resolve = yes }))
    await workflowIdentityHost()
    privateWorkflowDraft()
    const card = screen.getByTestId('workflow-sketch-node')
    await act(async () => resolve(sdkUser()))
    expect(screen.getByTestId('workflow-sketch-node')).toBe(card)
    expect(screen.getByRole('dialog')).toBeTruthy()
    await emitLoaded(sdkUser({ scope: 'profile openid openid' }))
    expect(screen.getByTestId('workflow-sketch-node')).toBe(card)
  })

  it('lets UserLoaded supersede initial hydration and ignores a late different initial user', async () => {
    let resolve!: (user: User) => void
    oidcFixture.getUser.mockReturnValue(new Promise<User>(yes => { resolve = yes }))
    await workflowIdentityHost()
    privateWorkflowDraft()
    await emitLoaded(sdkUser())
    const card = screen.getByTestId('workflow-sketch-node')
    await act(async () => resolve(sdkUser({ profile: { ...sdkUser().profile, sid: 'old-initial-session' } })))
    expect(screen.getByTestId('workflow-sketch-node')).toBe(card)
    await emitLoaded(sdkUser({ access_token: 'test-renewal' }))
    expect(screen.getByTestId('workflow-sketch-node')).toBe(card)
  })

  it('rejects an older loaded read after a newer stored context, including an old event delivered afterwards', async () => {
    oidcFixture.getUser.mockResolvedValue(sdkUser())
    await workflowIdentityHost()
    privateWorkflowDraft()
    let resolve!: (user: User) => void
    oidcFixture.getUser.mockReturnValue(new Promise<User>(yes => { resolve = yes }))
    let pending!: Promise<void>
    act(() => { pending = Promise.resolve([...oidcFixture.listeners.UserLoaded][0](sdkUser())) })
    const next = sdkUser({ profile: { ...sdkUser().profile, sid: 'new-session' } })
    await emitLoaded(next)
    expectRetiredImmediately()
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    const card = screen.getByTestId('workflow-sketch-node')
    await act(async () => { resolve(sdkUser()); await pending })
    await act(async () => { for (const listener of oidcFixture.listeners.UserLoaded) await listener(sdkUser()) })
    expect(screen.getByTestId('workflow-sketch-node')).toBe(card)
    await emitLoaded(sdkUser({ ...next, access_token: 'test-next-renewal' }))
    expect(screen.getByTestId('workflow-sketch-node')).toBe(card)
  })

  it('does not let an old loaded notification hide a pending genuine identity change', async () => {
    const initial = sdkUser()
    oidcFixture.getUser.mockResolvedValue(initial)
    await workflowIdentityHost()
    privateWorkflowDraft()
    const next = sdkUser({ profile: { ...initial.profile, sid: 'new-session' } })
    let resolve!: (user: User) => void
    oidcFixture.getUser.mockReturnValue(new Promise<User>(yes => { resolve = yes }))
    let pending!: Promise<void>
    act(() => { pending = Promise.resolve([...oidcFixture.listeners.UserLoaded][0](next)) })
    oidcFixture.getUser.mockResolvedValue(next)
    await act(async () => { for (const listener of oidcFixture.listeners.UserLoaded) await listener(initial) })
    expectRetiredImmediately()
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    await act(async () => { resolve(next); await pending })
    expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('WAIT')
  })

  it('retires on SDK read failure and missing current user instead of preserving uncertain access', async () => {
    oidcFixture.getUser.mockResolvedValue(sdkUser())
    await workflowIdentityHost()
    privateWorkflowDraft()
    oidcFixture.getUser.mockRejectedValue(new Error('SDK read failed'))
    await act(async () => { for (const listener of oidcFixture.listeners.UserLoaded) await listener(sdkUser()) })
    expectRetiredImmediately()
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    oidcFixture.getUser.mockResolvedValue(null)
    await act(async () => { for (const listener of oidcFixture.listeners.UserLoaded) await listener(sdkUser()) })
    expectRetiredImmediately()
  })

  it('ignores pending SDK reads after signout initiation and StrictMode unmount', async () => {
    let resolve!: (user: User) => void
    oidcFixture.getUser.mockReturnValue(new Promise<User>(yes => { resolve = yes }))
    const view = await workflowIdentityHost()
    privateWorkflowDraft()
    await act(async () => oidcClient.signOutOidc())
    expectRetiredImmediately()
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    await act(async () => resolve(sdkUser()))
    const card = screen.getByTestId('workflow-sketch-node')
    let finish!: (user: User) => void
    oidcFixture.getUser.mockReturnValue(new Promise<User>(yes => { finish = yes }))
    let pending!: Promise<void>
    act(() => { pending = Promise.resolve([...oidcFixture.listeners.UserLoaded][0](sdkUser())) })
    view.unmount()
    for (const listeners of Object.values(oidcFixture.listeners)) expect(listeners.size).toBe(0)
    await act(async () => { finish(sdkUser()); await pending })
    expect(card.isConnected).toBe(false)
    expect(screen.queryByTestId('workflow-sketch-node')).toBeNull()
  })

  it.each(['workspace', 'project'] as const)('retires the Workflow owner on a %s route change', async target => {
    oidcFixture.getUser.mockResolvedValue(sdkUser())
    const view = await workflowIdentityHost()
    const retained = privateWorkflowDraft()
    await act(async () => view.router.navigate({ to: '/w/$workspaceId/projects/$projectId/workflow', params: {
      workspaceId: target === 'workspace' ? 'workspace-2' : 'workspace-1',
      projectId: target === 'project' ? 'project-2' : 'project-1',
    } }))
    await screen.findByRole('heading', { name: 'Local arrangement sketch' })
    expectRetiredImmediately()
    expectStaleHandlersRejected(retained)
  })

  afterEach(() => {
    cleanup()
    oidcFixture.enabled = false
    vi.restoreAllMocks()
    oidcFixture.getUser.mockReset().mockResolvedValue(null)
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
    oidcFixture.getUser.mockResolvedValue(sdkUser())
    const unsubscribe = oidcClient.subscribeOidcSessionRetirement(callback)
    await Promise.resolve()
    const retained = [...oidcFixture.listeners.UserLoaded][0]
    for (const name of oidcFixture.names) {
      expect(oidcFixture.listeners[name].size).toBe(1)
      for (const listener of oidcFixture.listeners[name]) await listener(name === 'UserLoaded' ? sdkUser({ expires_at: 0 }) : undefined)
    }
    expect(callback).toHaveBeenCalledTimes(oidcFixture.names.length - 1)
    unsubscribe()
    unsubscribe()
    for (const listeners of Object.values(oidcFixture.listeners)) expect(listeners.size).toBe(0)
    await retained(sdkUser())
    await oidcClient.signOutOidc()
    expect(callback).toHaveBeenCalledTimes(oidcFixture.names.length - 1)
    expect(oidcFixture.getUser).toHaveBeenCalled()
  })

  it.each(oidcFixture.names.filter(name => name !== 'UserLoaded'))('withdraws old Workflow content synchronously on SDK %s and rejects retained editor/confirmation callbacks', async name => {
    const view = await workflowIdentityHost()
    const retained = privateWorkflowDraft()
    act(() => {
      for (const listener of oidcFixture.listeners[name]) listener()
      // Checked during SDK delivery, before act flushes batched React work.
      expectRetiredImmediately()
    })
    expectStaleHandlersRejected(retained)
    expect(oidcFixture.getUser).toHaveBeenCalled()
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

  it('ignores hydration after unload and ignores an old loaded event after a new stored session', async () => {
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
    const current = sdkUser({ profile: { ...sdkUser().profile, sid: 'new-session' } })
    await emitLoaded(current)
    expectRetiredImmediately()
    fireEvent.click(screen.getByRole('button', { name: 'Add WAIT card' }))
    await act(async () => { for (const listener of oidcFixture.listeners.UserLoaded) await listener(sdkUser()) })
    expect(screen.getByTestId('workflow-sketch-node').getAttribute('aria-label')).toBe('WAIT')
  })
})

it('V9 NLE route preserves navigation through native renewal and equal access, then retires on true session or access change', async () => {
  oidcFixture.enabled = true
  oidcFixture.getUser.mockResolvedValue(sdkUser())
  const { TimelineNavigationProvider } = await import('../product/timeline/TimelineNavigation')
  const access = { ...unknownAccess('timeline.operation.apply'), source: 'SERVER' as const, status: 'AVAILABLE' as const }
  const source: import('../product/timeline/navigation').TimelineNavigationSource = {
    scope: { principalId: 'principal-1', sessionId: 'session-1', tenantId: 'tenant-1', workspaceId: 'workspace-1', projectId: 'project-1' },
    accessBinding: { kind: 'TEST_ONLY_UNAGREED', key: 'test-navigation' },
    access: { ...unknownAccess('test-navigation'), source: 'SERVER', status: 'AVAILABLE', factors: { capability: 'SATISFIED', runtime: 'NOT_APPLICABLE', entitlement: 'SATISFIED', policy: 'SATISFIED', quota: 'NOT_APPLICABLE' } },
    adapter: { origin: 'isolated-verification', read: async request => ({ ...request, status: 'ok', completeness: 'complete', timeBasis: 'exact-seconds', tracks: [{ id: 'v', name: 'Video', clips: [{ id: 'clip', trackId: 'v', name: 'Verification clip', timelineRange: { start: '0', end: '2' } }] }] }) },
  }
  vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({ workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1', recentProjects: [] })
  vi.spyOn(platformClient.effectiveAccess, 'getCatalog').mockResolvedValue({ 'timeline.operation.apply': access })
  vi.spyOn(timelineQueryGateway, 'getHead').mockResolvedValue({ ok: true, value: { projectId: projectId('project-1'), timelineId: timelineId('project-1'), revisionId: revisionId('revision-R0'), contentHash: contentHash('a'.repeat(64)) } })
  vi.spyOn(timelineQueryGateway, 'listRevisions').mockResolvedValue({ ok: true, value: [] })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } })
  const router = createRouter({ routeTree, history: createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/edit'] }), context: { queryClient: client } })
  try {
    render(<StrictMode><QueryClientProvider client={client}><TimelineNavigationProvider source={source}><RouterProvider router={router} /></TimelineNavigationProvider></QueryClientProvider></StrictMode>)
    await screen.findByRole('button', { name: /Verification clip/ }); await act(async () => {})
    const clip = screen.getByRole('button', { name: /Verification clip/ }); fireEvent.click(clip)
    fireEvent.change(screen.getByLabelText('Exact time (integer or fraction)'), { target: { value: '1/3' } })
    fireEvent.click(screen.getByRole('button', { name: 'Locate time' }))
    await emitLoaded(sdkUser({ access_token: 'test-renewed-navigation' }))
    expect(screen.getByRole('button', { name: /Verification clip/ })).toBe(clip)
    expect(clip.getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByLabelText('Local navigation position').textContent).toBe('1/3')
    act(() => client.setQueryData(platformQueryKeys.effectiveAccess(['timeline.operation.apply']), { 'timeline.operation.apply': { ...access, observedAt: '2030-01-01' } }))
    expect(screen.getByRole('button', { name: /Verification clip/ })).toBe(clip)
    const staleInspect = renderedHandler<() => void>(screen.getByRole('button', { name: 'Inspect selected metadata' }), 'onClick')
    fireEvent.click(screen.getByRole('button', { name: 'Inspect selected metadata' }))
    await emitLoaded(sdkUser({ profile: { ...sdkUser().profile, sid: 'session-new' } }))
    expect(clip.isConnected).toBe(false); expect(screen.queryByRole('dialog')).toBeNull()
    const next = await screen.findByRole('button', { name: /Verification clip/ })
    expect(next.getAttribute('aria-pressed')).toBe('false')
    act(staleInspect); expect(screen.queryByRole('dialog')).toBeNull()
    fireEvent.click(next)
    act(() => client.setQueryData(platformQueryKeys.effectiveAccess(['timeline.operation.apply']), { 'timeline.operation.apply': { ...access, status: 'POLICY_DENIED' } }))
    await waitFor(() => expect(next.isConnected).toBe(false))
    expect(screen.queryByRole('dialog')).toBeNull()
  } finally {
    cleanup(); oidcFixture.enabled = false; vi.restoreAllMocks(); oidcFixture.getUser.mockReset().mockResolvedValue(null)
  }
})

it('V10 publication route has an ordinary unavailable entry and an explicit host with native renewal continuity and retirement', async () => {
  oidcFixture.enabled = true
  oidcFixture.getUser.mockResolvedValue(sdkUser())
  const { PublicationSourceProvider } = await import('../product/publication/PublicationWorkspace')
  const { source, receipt } = await import('../product/publication/testing')
  const read = vi.fn(async (r: import('../product/publication/types').PublicationRequest) => {
    const raw = receipt(r)
    return { ...raw, plans: raw.plans.map(p => ({ ...p, projectId: r.scope.projectId })), artifacts: raw.artifacts.map(a => ({ ...a, projectId: r.scope.projectId })) }
  })
  const supplied = source(read)
  supplied.scope = { ...supplied.scope, workspaceId: 'workspace-1', projectId: 'project-1', tenantId: 'tenant-1' }
  vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({ workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1', recentProjects: [] })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } })
  const router = createRouter({ routeTree, history: createMemoryHistory({ initialEntries: ['/w/workspace-1/projects/project-1/publication'] }), context: { queryClient: client } })
  try {
    const renderHost = (injected: boolean) => <StrictMode><QueryClientProvider client={client}>{injected ? <PublicationSourceProvider source={supplied}><RouterProvider router={router} /></PublicationSourceProvider> : <RouterProvider router={router} />}</QueryClientProvider></StrictMode>
    const view = render(renderHost(false))
    await screen.findByText('Publication source not connected')
    expect(read).not.toHaveBeenCalled()
    expect(screen.getByRole('navigation', { name: 'Project surface switcher' }).querySelector('[aria-current="page"]')?.getAttribute('href')).toBe('/w/workspace-1/projects/project-1/publication')
    view.rerender(renderHost(true)); await screen.findByRole('button', { name: 'Opening story' }); await act(async () => {})
    fireEvent.change(screen.getByLabelText('Search supplied publications'), { target: { value: 'Opening' } })
    const row = screen.getByRole('button', { name: 'Opening story' }); fireEvent.click(row)
    const dialog = screen.getByRole('dialog')
    await emitLoaded(sdkUser({ access_token: 'test-renewal-publication' }))
    expect(screen.getByRole('dialog')).toBe(dialog)
    expect(screen.getByRole('button', { name: 'Opening story' })).toBe(row)
    const dismiss = renderedHandler<() => void>(screen.getByRole('button', { name: 'Close publication details' }), 'onClick')
    const readsBeforeRetirement = read.mock.calls.length
    await emitLoaded(sdkUser({ profile: { ...sdkUser().profile, sid: 'new-publication-session' } }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Opening story' })).toBeNull()
    expect(read.mock.calls.length).toBe(readsBeforeRetirement)
    act(dismiss); expect(screen.queryByRole('dialog')).toBeNull()
  } finally { cleanup(); oidcFixture.enabled = false; vi.restoreAllMocks(); oidcFixture.getUser.mockReset().mockResolvedValue(null) }
})
