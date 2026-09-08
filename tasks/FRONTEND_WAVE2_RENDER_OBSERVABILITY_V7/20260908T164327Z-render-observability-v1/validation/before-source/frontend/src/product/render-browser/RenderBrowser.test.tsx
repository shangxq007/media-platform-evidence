import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { EffectiveAccessEntry } from '../../foundation/effectiveAccess'
import { LocalizationProvider } from '../../localization'
import { createRendersFixture } from './fixture'
import { RenderBrowser } from './RenderBrowser'
import { REAL_RENDER_SUMMARIES_QUERY_KEY, type RenderListRequest, type RendersSource } from './source'

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(value => { resolve = value })
  return { promise, resolve }
}

function availableAccess(): EffectiveAccessEntry {
  return {
    key: REAL_RENDER_SUMMARIES_QUERY_KEY, status: 'AVAILABLE', reasonCode: 'TEST_AVAILABLE', explanation: '<server source explanation 原文>',
    factors: { capability: 'SATISFIED', runtime: 'SATISFIED', entitlement: 'SATISFIED', policy: 'SATISFIED', quota: 'SATISFIED' },
    source: 'SERVER',
  }
}

const scope = { principalId: 'principal-1', tenantId: 'tenant-1', sessionId: 'session-1', projectId: 'project-1' }
function ownedResult(request: RenderListRequest, profile = 'Connected profile') {
  return {
    status: 'ok', scope: request.scope, requestId: request.requestId,
    jobs: [{ id: 'render-connected', projectId: request.scope.projectId, timelineSnapshotId: 'snapshot-connected', profile, status: 'EXECUTING' }],
    boundary: { kind: 'project-snapshot', limit: 20, limited: false },
  }
}
function realSource(overrides: Partial<typeof scope> = {}): RendersSource {
  const sourceScope = { ...scope, ...overrides }
  return {
    scope: sourceScope, access: availableAccess(),
    adapter: { origin: 'real', async listProject(request) { return ownedResult(request) } },
  }
}
function setup(source: RendersSource = createRendersFixture(), locale: 'en' | 'zh-CN' = 'en') {
  return render(<LocalizationProvider initialLocale={locale}><RenderBrowser source={source} /></LocalizationProvider>)
}

describe('RenderBrowser', () => {
  it('shows the exact source-owned Project and only bounded safe summaries', async () => {
    setup()
    expect(await screen.findByRole('heading', { name: 'Project renders' })).toBeTruthy()
    expect(screen.getByText('simulated-render-project')).toBeTruthy()
    expect(screen.getByText(/not a global render inventory/i)).toBeTruthy()
    const list = screen.getByRole('list', { name: 'Render summary snapshot' })
    expect(within(list).queryByText(/Provider ID|Worker ID|Runtime ID/i)).toBeNull()
    expect(screen.queryByRole('button', { name: /cancel job|retry job|download/i })).toBeNull()
  })

  it('searches ID/profile, filters established statuses, sorts IDs, and resets locally', async () => {
    setup()
    await screen.findByRole('button', { name: 'Inspect render render-alpha' })
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search render summaries' }), { target: { value: 'Cinema <literal>' } })
    expect(screen.getByRole('button', { name: 'Inspect render render-zeta' })).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Inspect render render-alpha' })).toBeNull()
    expect(screen.queryByText('script', { selector: 'script' })).toBeNull()
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search render summaries' }), { target: { value: '' } })
    fireEvent.change(screen.getByLabelText('Render status'), { target: { value: 'FAILED' } })
    expect(screen.getByRole('button', { name: 'Inspect render render-beta' })).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Sort render summaries'), { target: { value: 'id-desc' } })
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search render summaries' }), { target: { value: 'no match' } })
    expect(screen.getByRole('heading', { name: 'No matching render summaries' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Reset filters' }))
    expect((screen.getByRole('searchbox', { name: 'Search render summaries' }) as HTMLInputElement).value).toBe('')
    expect((screen.getByLabelText('Render status') as HTMLSelectElement).value).toBe('')
    expect((screen.getByLabelText('Sort render summaries') as HTMLSelectElement).value).toBe('id-asc')
  })

  it('distinguishes an empty Project snapshot from local no matches', async () => {
    setup(createRendersFixture({ empty: true }))
    expect(await screen.findByRole('heading', { name: 'No render summaries in this snapshot' })).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Reset filters' })).toBeNull()
  })

  it('opens five exact fields in the shared read-only dialog and Escape restores launcher focus', async () => {
    setup()
    const launcher = await screen.findByRole('button', { name: 'Inspect render render-zeta' })
    launcher.focus(); fireEvent.click(launcher)
    const dialog = screen.getByRole('dialog', { name: 'Render summary details' })
    expect(within(dialog).getByText('Read-only local inspection')).toBeTruthy()
    expect(within(dialog).getByText('render-zeta')).toBeTruthy()
    expect(within(dialog).getByText('simulated-render-project')).toBeTruthy()
    expect(within(dialog).getByText('timeline-snapshot-zeta')).toBeTruthy()
    expect(within(dialog).getByText('Cinema <literal>')).toBeTruthy()
    expect(within(dialog).getByText('COMPLETED')).toBeTruthy()
    expect(dialog.querySelector('script')).toBeNull()
    expect(dialog.querySelectorAll('.ff-property-row')).toHaveLength(5)
    fireEvent.keyDown(dialog, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(launcher)
  })

  it('uses one stable workflow button for Refresh, Cancel and Retry and never steals moved focus asynchronously', async () => {
    const source = realSource()
    render(<LocalizationProvider><button type="button">Stable focus</button><RenderBrowser source={source} /></LocalizationProvider>)
    await screen.findByRole('button', { name: 'Inspect render render-connected' })
    const pending = deferred<unknown>(); let request!: RenderListRequest
    vi.spyOn(source.adapter, 'listProject').mockImplementationOnce(value => { request = value; return pending.promise })
    const workflow = screen.getByRole('button', { name: 'Refresh render summaries' })
    workflow.focus(); fireEvent.click(workflow)
    expect(screen.getByRole('button', { name: 'Cancel loading' })).toBe(workflow)
    const stable = screen.getByRole('button', { name: 'Stable focus' })
    stable.focus()
    await act(async () => pending.resolve({ status: 'error', scope: request.scope, requestId: request.requestId, explanation: '<opaque failure>' }))
    expect(screen.getByRole('button', { name: 'Retry loading' })).toBe(workflow)
    expect(document.activeElement).toBe(stable)

    const success = deferred<unknown>(); let successRequest!: RenderListRequest
    vi.spyOn(source.adapter, 'listProject').mockImplementationOnce(value => { successRequest = value; return success.promise })
    workflow.focus(); fireEvent.click(workflow)
    expect(screen.getByRole('button', { name: 'Cancel loading' })).toBe(workflow)
    fireEvent.click(workflow)
    expect(screen.getByRole('button', { name: 'Retry loading' })).toBe(workflow)
    await act(async () => success.resolve(ownedResult(successRequest, 'Cancelled secret')))
    expect(screen.queryByText('Cancelled secret')).toBeNull()
    expect(document.activeElement).toBe(workflow)

    const final = deferred<unknown>(); let finalRequest!: RenderListRequest
    vi.spyOn(source.adapter, 'listProject').mockImplementationOnce(value => { finalRequest = value; return final.promise })
    fireEvent.click(workflow)
    expect(screen.getByRole('button', { name: 'Cancel loading' })).toBe(workflow)
    await act(async () => final.resolve(ownedResult(finalRequest, 'Focused success')))
    expect(screen.getByRole('button', { name: 'Refresh render summaries' })).toBe(workflow)
    expect(document.activeElement).toBe(workflow)
  })

  it.each(['unavailable', 'denied', 'unknown', 'unsupported', 'error'] as const)('clears old content and renders exact %s receipt explanations as text', async failure => {
    const source = realSource()
    setup(source)
    await screen.findByRole('button', { name: 'Inspect render render-connected' })
    vi.spyOn(source.adapter, 'listProject').mockImplementation(async request => ({
      status: failure, scope: request.scope, requestId: request.requestId, explanation: `<opaque ${failure} 原因>`,
    }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh render summaries' }))
    await waitFor(() => expect(screen.getByRole('heading', { name: new RegExp(failure, 'i') })).toBeTruthy())
    expect(screen.queryByText('Connected profile')).toBeNull()
    expect(screen.getByText(`<opaque ${failure} 原因>`)).toBeTruthy()
    expect(screen.queryByText('opaque', { selector: 'opaque' })).toBeNull()
  })

  it('fails closed on invalid returned content and never retains the old summary', async () => {
    const source = realSource()
    setup(source)
    await screen.findByText('Connected profile')
    vi.spyOn(source.adapter, 'listProject').mockImplementation(async request => ({
      ...ownedResult(request, 'Must stay hidden'),
      jobs: [{ ...ownedResult(request).jobs[0], projectId: 'foreign-project' }],
    }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh render summaries' }))
    expect(await screen.findByRole('heading', { name: 'Render summaries error' })).toBeTruthy()
    expect(screen.queryByText('Connected profile')).toBeNull()
    expect(screen.queryByText('Must stay hidden')).toBeNull()
  })

  it.each(['principalId', 'tenantId', 'sessionId', 'projectId'] as const)('retires a real valid pending response on %s change', async field => {
    const source = realSource()
    const pending = deferred<unknown>(); let oldRequest!: RenderListRequest
    vi.spyOn(source.adapter, 'listProject').mockImplementation(request => { oldRequest = request; return pending.promise })
    const view = setup(source)
    const next = realSource({ [field]: field === 'projectId' ? 'project-2' : 'changed' })
    view.rerender(<LocalizationProvider><RenderBrowser source={next} /></LocalizationProvider>)
    expect(await screen.findByText('Connected profile')).toBeTruthy()
    expect(screen.getByText(next.scope.projectId)).toBeTruthy()
    await act(async () => pending.resolve(ownedResult(oldRequest, 'Retired identity secret')))
    expect(screen.queryByText('Retired identity secret')).toBeNull()
  })

  it('retires real valid pending responses on adapter replacement and unmount', async () => {
    const source = realSource()
    const pending = deferred<unknown>(); let oldRequest!: RenderListRequest
    vi.spyOn(source.adapter, 'listProject').mockImplementation(request => { oldRequest = request; return pending.promise })
    const view = setup(source)
    const replacement = createRendersFixture({ empty: true })
    view.rerender(<LocalizationProvider><RenderBrowser source={replacement} /></LocalizationProvider>)
    expect(await screen.findByRole('heading', { name: 'No render summaries in this snapshot' })).toBeTruthy()
    await act(async () => pending.resolve(ownedResult(oldRequest, 'Retired adapter secret')))
    expect(screen.queryByText('Retired adapter secret')).toBeNull()
    view.unmount()

    const unmountedSource = realSource()
    const unmounted = deferred<unknown>(); let unmountedRequest!: RenderListRequest
    vi.spyOn(unmountedSource.adapter, 'listProject').mockImplementation(request => { unmountedRequest = request; return unmounted.promise })
    const second = setup(unmountedSource)
    second.unmount()
    await act(async () => unmounted.resolve(ownedResult(unmountedRequest, 'Unmounted secret')))
    expect(screen.queryByText('Unmounted secret')).toBeNull()
  })

  it('does not query initial denied/unknown sources and displays their opaque explanations', () => {
    for (const status of ['POLICY_DENIED', 'UNKNOWN_FAIL_CLOSED'] as const) {
      const source = realSource()
      source.access = { ...source.access, status, explanation: `<initial ${status} 原因>` }
      const list = vi.spyOn(source.adapter, 'listProject')
      const view = setup(source)
      expect(screen.getByText(`<initial ${status} 原因>`)).toBeTruthy()
      expect(list).not.toHaveBeenCalled()
      view.unmount()
    }
  })

  it('is unavailable by default and identifies the fixture as simulated read-only data', async () => {
    const unavailable = render(<LocalizationProvider><RenderBrowser /></LocalizationProvider>)
    expect(screen.getByRole('heading', { name: 'Render summaries unavailable' })).toBeTruthy()
    unavailable.unmount()
    setup()
    await screen.findByRole('button', { name: 'Inspect render render-alpha' })
    expect(screen.getByText(/SIMULATED RENDER DATA/)).toBeTruthy()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('localizes controls and states in Chinese while leaving summary fields opaque', async () => {
    setup(createRendersFixture(), 'zh-CN')
    expect(await screen.findByRole('heading', { name: '项目渲染' })).toBeTruthy()
    expect(screen.getByRole('searchbox', { name: '搜索渲染摘要' })).toBeTruthy()
    expect(screen.getByText(/模拟渲染数据/)).toBeTruthy()
    expect(screen.getAllByText('Cinema <literal>').length).toBeGreaterThan(0)
    fireEvent.click(screen.getByRole('button', { name: '检查渲染 render-zeta' }))
    expect(within(screen.getByRole('dialog', { name: '渲染摘要详情' })).getByText('timeline-snapshot-zeta')).toBeTruthy()
  })
})
