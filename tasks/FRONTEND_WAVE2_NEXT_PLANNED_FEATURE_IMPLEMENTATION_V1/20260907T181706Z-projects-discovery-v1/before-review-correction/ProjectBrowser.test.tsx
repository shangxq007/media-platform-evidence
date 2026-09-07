import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { LocalizationProvider } from '../../localization'
import { ProjectBrowser } from './ProjectBrowser'
import { createProjectsFixture } from './fixture'
import type { ProjectListRequest, ProjectsSource } from './source'

function deferred<T = unknown>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail })
  return { promise, resolve, reject }
}
function setup(source: ProjectsSource = createProjectsFixture({ workspaceId: 'workspace-1' }), locale: 'en' | 'zh-CN' = 'en') {
  return render(<LocalizationProvider initialLocale={locale}><ProjectBrowser workspaceId="workspace-1" source={source} /></LocalizationProvider>)
}

describe('Workspace recent Project discovery and inspection', () => {
  it('searches literal name and description content, filters opaque statuses, sorts deterministically, and resets no matches', async () => {
    setup()
    await screen.findAllByRole('button', { name: 'Inspect Alpha project' })
    expect(screen.getAllByRole('button', { name: /^Inspect / }).map(button => button.getAttribute('aria-label'))).toEqual(['Inspect Alpha project', 'Inspect Alpha project', 'Inspect Zeta <project>'])
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search recent projects' }), { target: { value: 'description literal' } })
    expect(screen.getByRole('button', { name: 'Inspect Zeta <project>' })).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Inspect Alpha project' })).toBeNull()
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search recent projects' }), { target: { value: '' } })
    fireEvent.change(screen.getByLabelText('Projected status'), { target: { value: 'future::READY<script>' } })
    expect(screen.getByRole('button', { name: 'Inspect Zeta <project>' })).toBeTruthy()
    expect(screen.queryByText('script', { selector: 'script' })).toBeNull()
    fireEvent.change(screen.getByLabelText('Sort recent projects'), { target: { value: 'name-desc' } })
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search recent projects' }), { target: { value: 'no literal match' } })
    expect(screen.getByRole('heading', { name: 'No matching recent projects' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Reset filters' }))
    expect((screen.getByRole('searchbox', { name: 'Search recent projects' }) as HTMLInputElement).value).toBe('')
    expect((screen.getByLabelText('Projected status') as HTMLSelectElement).value).toBe('')
    expect((screen.getByLabelText('Sort recent projects') as HTMLSelectElement).value).toBe('name-asc')
  })

  it('distinguishes an empty recent snapshot from local no matches', async () => {
    setup(createProjectsFixture({ workspaceId: 'workspace-1', empty: true }))
    expect(await screen.findByRole('heading', { name: 'No recent projects in this snapshot' })).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Reset filters' })).toBeNull()
  })

  it('inspects the exact item in a read-only dialog, renders opaque text safely, and restores launcher focus after Escape', async () => {
    setup()
    const launchers = await screen.findAllByRole('button', { name: 'Inspect Alpha project' })
    launchers[1].focus(); fireEvent.click(launchers[1])
    const dialog = screen.getByRole('dialog', { name: 'Project details' })
    expect(within(dialog).getByText('project-alpha-b')).toBeTruthy()
    expect(within(dialog).getByText('<b>opaque description</b>')).toBeTruthy()
    expect(dialog.querySelector('b')).toBeNull()
    expect(within(dialog).getByText('Read-only local inspection')).toBeTruthy()
    fireEvent.keyDown(dialog, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(launchers[1])
  })

  it('supports cancel, retry and refresh; each new request clears content and late cancelled replies stay hidden', async () => {
    const source = createProjectsFixture({ workspaceId: 'workspace-1' })
    const original = source.adapter.listRecent
    const first = deferred(); let firstRequest!: ProjectListRequest
    vi.spyOn(source.adapter, 'listRecent').mockImplementationOnce(request => { firstRequest = request; return first.promise })
    setup(source)
    expect(screen.getByRole('status', { name: 'Loading recent projects' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Cancel loading' }))
    expect(screen.getByText('Loading cancelled.')).toBeTruthy()
    await act(async () => first.resolve(await original(firstRequest, new AbortController().signal)))
    expect(screen.queryByRole('button', { name: /^Inspect / })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Retry loading' }))
    await screen.findAllByRole('button', { name: 'Inspect Alpha project' })

    const refresh = deferred(); let refreshRequest!: ProjectListRequest
    vi.spyOn(source.adapter, 'listRecent').mockImplementationOnce(request => { refreshRequest = request; return refresh.promise })
    fireEvent.click(screen.getByRole('button', { name: 'Refresh recent projects' }))
    expect(screen.queryByRole('button', { name: /^Inspect / })).toBeNull()
    await act(async () => refresh.resolve(await original(refreshRequest, new AbortController().signal)))
    expect((await screen.findAllByRole('button', { name: 'Inspect Alpha project' })).length).toBe(2)
  })

  it.each(['unavailable', 'denied', 'unknown', 'unsupported', 'error'] as const)('clears content and presents the exact %s failure without simulation fallback', async failure => {
    const source = createProjectsFixture({ workspaceId: 'workspace-1' })
    source.adapter.origin = 'real'
    setup(source)
    await screen.findAllByRole('button', { name: 'Inspect Alpha project' })
    vi.spyOn(source.adapter, 'listRecent').mockImplementation(async request => ({ status: failure, scope: request.scope, requestId: request.requestId, explanation: '<opaque failure 原因>' }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh recent projects' }))
    await waitFor(() => expect(screen.getByRole('heading', { name: new RegExp(failure, 'i') })).toBeTruthy())
    expect(screen.queryByRole('button', { name: /^Inspect / })).toBeNull()
    expect(screen.queryByText(/SIMULATED PROJECT DATA/)).toBeNull()
    expect(screen.getByText('<opaque failure 原因>')).toBeTruthy()
  })

  it('treats malformed and mismatched success receipts as errors and exposes no returned content', async () => {
    const source = createProjectsFixture({ workspaceId: 'workspace-1' })
    vi.spyOn(source.adapter, 'listRecent').mockImplementation(async request => ({
      status: 'ok', scope: { ...request.scope, sessionId: 'foreign' }, requestId: request.requestId,
      projects: [{ id: 'leaked', name: 'Must stay hidden' }], boundary: { kind: 'recent', limit: 1, limited: false },
    }))
    setup(source)
    expect(await screen.findByRole('heading', { name: 'Recent projects error' })).toBeTruthy()
    expect(screen.queryByText('Must stay hidden')).toBeNull()
  })

  it.each(['principalId', 'tenantId', 'sessionId', 'workspaceId'] as const)('synchronously hides old content on %s change and ignores the old late reply', async field => {
    const source = createProjectsFixture({ workspaceId: 'workspace-1' })
    const view = setup(source)
    await screen.findAllByRole('button', { name: 'Inspect Alpha project' })
    const pending = deferred(); let oldRequest!: ProjectListRequest
    vi.spyOn(source.adapter, 'listRecent').mockImplementationOnce(request => { oldRequest = request; return pending.promise })
    fireEvent.click(screen.getByRole('button', { name: 'Refresh recent projects' }))
    const next = createProjectsFixture({
      workspaceId: field === 'workspaceId' ? 'workspace-2' : 'workspace-1',
      principalId: field === 'principalId' ? 'changed' : undefined,
      tenantId: field === 'tenantId' ? 'changed' : undefined,
      sessionId: field === 'sessionId' ? 'changed' : undefined,
      empty: true,
    })
    view.rerender(<LocalizationProvider><ProjectBrowser workspaceId={next.scope.workspaceId} source={next} /></LocalizationProvider>)
    expect(screen.queryByRole('button', { name: /^Inspect / })).toBeNull()
    expect(await screen.findByRole('heading', { name: 'No recent projects in this snapshot' })).toBeTruthy()
    await act(async () => pending.resolve({ status: 'ok', scope: oldRequest.scope, requestId: oldRequest.requestId, projects: [{ id: 'late', tenantId: oldRequest.scope.tenantId, name: 'Late secret' }], boundary: { kind: 'recent', limit: 1, limited: false } }))
    expect(screen.queryByText('Late secret')).toBeNull()
  })

  it('drops late replies after adapter replacement and unmount', async () => {
    const source = createProjectsFixture({ workspaceId: 'workspace-1' })
    const pending = deferred()
    vi.spyOn(source.adapter, 'listRecent').mockReturnValue(pending.promise)
    const view = setup(source)
    const replacement = createProjectsFixture({ workspaceId: 'workspace-1', empty: true })
    view.rerender(<LocalizationProvider><ProjectBrowser workspaceId="workspace-1" source={replacement} /></LocalizationProvider>)
    expect(await screen.findByRole('heading', { name: 'No recent projects in this snapshot' })).toBeTruthy()
    await act(async () => pending.resolve({ status: 'ok', scope: source.scope, requestId: 'late', projects: [{ id: 'late', name: 'Late secret' }], boundary: { kind: 'recent', limit: 1, limited: false } }))
    expect(screen.queryByText('Late secret')).toBeNull()
    view.unmount()
  })

  it('aborts and drops a source reply that arrives after unmount', async () => {
    const source = createProjectsFixture({ workspaceId: 'workspace-1' })
    const pending = deferred(); let request!: ProjectListRequest
    vi.spyOn(source.adapter, 'listRecent').mockImplementation(value => { request = value; return pending.promise })
    const view = setup(source)
    view.unmount()
    await act(async () => pending.resolve({ status: 'ok', scope: request.scope, requestId: request.requestId, projects: [{ id: 'late', tenantId: request.scope.tenantId, name: 'Unmounted secret' }], boundary: { kind: 'recent', limit: 1, limited: false } }))
    expect(screen.queryByText('Unmounted secret')).toBeNull()
  })

  it('never reopens inspection or steals newly placed focus when a retired refresh replies late', async () => {
    const source = createProjectsFixture({ workspaceId: 'workspace-1' })
    const view = render(<LocalizationProvider><button type="button">Stable focus</button><ProjectBrowser workspaceId="workspace-1" source={source} /></LocalizationProvider>)
    const launchers = await screen.findAllByRole('button', { name: 'Inspect Alpha project' })
    fireEvent.click(launchers[1])
    expect(screen.getByRole('dialog', { name: 'Project details' })).toBeTruthy()
    const pending = deferred(); let request!: ProjectListRequest
    vi.spyOn(source.adapter, 'listRecent').mockImplementationOnce(value => { request = value; return pending.promise })
    fireEvent.click(screen.getByRole('button', { name: 'Refresh recent projects', hidden: true }))
    expect(screen.queryByRole('dialog')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Cancel loading' }))
    const stable = screen.getByRole('button', { name: 'Stable focus' })
    stable.focus()
    await act(async () => pending.resolve({ status: 'ok', scope: request.scope, requestId: request.requestId, projects: [{ id: 'late', tenantId: request.scope.tenantId, name: 'Late secret' }], boundary: { kind: 'recent', limit: 1, limited: false } }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.queryByText('Late secret')).toBeNull()
    expect(document.activeElement).toBe(stable)
    view.unmount()
  })
  it('does not query denied or unknown projections and presents no content', () => {
    for (const accessStatus of ['POLICY_DENIED', 'UNKNOWN_FAIL_CLOSED'] as const) {
      const source = createProjectsFixture({ workspaceId: 'workspace-1', accessStatus })
      const list = vi.spyOn(source.adapter, 'listRecent')
      const view = setup(source)
      expect(screen.queryByRole('button', { name: /^Inspect / })).toBeNull()
      expect(list).not.toHaveBeenCalled()
      view.unmount()
    }
  })

  it('is unavailable by default and persistently identifies the localhost fixture as simulated and read-only', async () => {
    const unavailable = render(<LocalizationProvider><ProjectBrowser workspaceId="workspace-1" /></LocalizationProvider>)
    expect(screen.getByRole('heading', { name: 'Recent projects unavailable' })).toBeTruthy()
    unavailable.unmount()
    setup()
    await screen.findAllByRole('button', { name: 'Inspect Alpha project' })
    expect(screen.getByText(/SIMULATED PROJECT DATA/)).toBeTruthy()
    expect(screen.getByText(/recent snapshot.*not a full project inventory/i)).toBeTruthy()
    expect(screen.queryByRole('link', { name: /Open/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Create/ })).toBeNull()
  })

  it('localizes the full Projects UI in zh-CN while preserving projected names, descriptions and statuses', async () => {
    setup(createProjectsFixture({ workspaceId: 'workspace-1' }), 'zh-CN')
    expect(await screen.findByRole('heading', { name: '最近项目' })).toBeTruthy()
    expect(screen.getByRole('searchbox', { name: '搜索最近项目' })).toBeTruthy()
    expect(screen.getByText(/模拟项目数据/)).toBeTruthy()
    expect(screen.getAllByText('future::READY<script>').length).toBeGreaterThan(0)
    fireEvent.click(screen.getByRole('button', { name: '检查 Zeta <project>' }))
    const dialog = screen.getByRole('dialog', { name: '项目详情' })
    expect(within(dialog).getByText('description literal 原文')).toBeTruthy()
  })
})
