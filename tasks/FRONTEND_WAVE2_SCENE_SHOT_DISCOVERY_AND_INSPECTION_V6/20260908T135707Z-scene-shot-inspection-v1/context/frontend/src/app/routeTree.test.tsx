import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createMemoryHistory, createRouter } from '@tanstack/react-router'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { platformClient } from '../foundation/platformClient'
import api, { platformClient as exportedPlatformClient } from '../api'
import { surfaceRegistry } from '../foundation/surfaceRegistry'
import { implementedRouteInventory, legacyRouteInventory, routeTree } from './routeTree'
import { timelineQueryGateway } from '../api/app/timeline-query.gateway'
import { contentHash, projectId, revisionId, timelineId } from '../product/timeline/types'

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
    expect(await screen.findByRole('heading', { name: 'Render summaries unavailable' })).toBeTruthy()
    expect(screen.getByText(/no authenticated, session-bound, single-Project render source/i)).toBeTruthy()
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
