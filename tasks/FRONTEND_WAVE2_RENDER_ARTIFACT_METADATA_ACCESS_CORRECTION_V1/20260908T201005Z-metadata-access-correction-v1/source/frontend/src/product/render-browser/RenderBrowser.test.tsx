import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { StrictMode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import type { EffectiveAccessEntry } from '../../foundation/effectiveAccess'
import { SelectionProvider, useInteractionStore } from '../../interaction/SelectionContext'
import type { InteractionStore } from '../../interaction/model'
import { LocalizationProvider } from '../../localization'
import { createRendersFixture } from './fixture'
import { RenderBrowser, RenderBrowserProvider } from './RenderBrowser'
import { TEST_ONLY_RENDER_ACCESS_KEY, type RenderArtifact, type RenderProgress, type RenderReadRequest, type RenderSource } from './source'

const scope = { principalId: 'principal-1', tenantId: 'tenant-1', sessionId: 'session-1', projectId: 'project-1' }
const HOST_ACCESS_KEY = 'host-agreed.render-observability.read'

function deferred<T>() {
  let resolve!: (value: T) => void; let reject!: (reason: Error) => void
  const promise = new Promise<T>((accept, fail) => { resolve = accept; reject = fail })
  return { promise, resolve, reject }
}
function pendingReads(source: RenderSource) {
  const calls: { request: RenderReadRequest; signal: AbortSignal; result: ReturnType<typeof deferred<unknown>> }[] = []
  const read = vi.spyOn(source.adapter, 'readProject').mockImplementation((request, signal) => {
    const result = deferred<unknown>(); calls.push({ request, signal, result }); return result.promise
  })
  return { calls, read }
}
function availableAccess(): EffectiveAccessEntry {
  return { key: HOST_ACCESS_KEY, status: 'AVAILABLE', reasonCode: 'TEST_AVAILABLE', explanation: '<server access explanation 原文>', factors: { capability: 'SATISFIED', runtime: 'SATISFIED', entitlement: 'SATISFIED', policy: 'SATISFIED', quota: 'SATISFIED' }, source: 'SERVER' }
}
function ownedResult(request: RenderReadRequest, name = 'Connected render') {
  return {
    status: 'ok' as const, scope: request.scope, requestId: request.requestId,
    jobs: [{
      id: 'render-connected', projectId: request.scope.projectId, name, status: 'VENDOR_WARMING', version: 'render-v2',
      source: { id: 'revision-connected', kind: 'TIMELINE_REVISION', version: 'revision-v4' },
      createdAt: '2026-09-08T01:00:00Z', updatedAt: '2026-09-08T01:02:00Z', startedAt: '2026-09-08T01:01:00Z',
      progress: { value: 3, unit: 'shots', total: 8, totalUnit: 'shots', stage: 'Composite <literal>' },
      task: { id: 'task-connected', status: 'TASK_RUNNING', version: 'task-v3' },
      attempts: { completeness: 'complete' as const, limit: 2, items: [{ id: 'attempt-connected', ordinal: 1, taskId: 'task-connected', status: 'ATTEMPT_RUNNING', parentAttemptId: undefined as string | undefined }] },
      artifacts: { state: 'available' as const, completeness: 'bounded' as const, limit: 2, items: [{ id: 'artifact-connected', name: 'Preview 原文', type: 'video/mp4', availability: 'PROCESSING?', version: 'artifact-v1', taskId: 'task-connected', metadataAccess: 'inspectable' as const }] },
    }],
    boundary: { kind: 'project-render-observability-snapshot' as const, completeness: 'complete' as const, limit: 20, version: 'projection-connected', freshness: 'current' as const, sourceUpdatedAt: '2026-09-08T01:02:00Z', supportedStatusFilters: ['VENDOR_WARMING'] },
  }
}
function realSource(overrides: Partial<typeof scope> = {}): RenderSource {
  const sourceScope = { ...scope, ...overrides }
  return { scope: sourceScope, access: availableAccess(), readAccessBinding: { kind: 'HOST_AGREED', accessKey: HOST_ACCESS_KEY }, adapter: { origin: 'real', async readProject(request) { return ownedResult(request) } } }
}
function Host({ source, locale = 'en', capture }: { source?: RenderSource; locale?: 'en' | 'zh-CN'; capture?: (store: InteractionStore) => void }) {
  return <LocalizationProvider initialLocale={locale}><SelectionProvider scope={{ workspaceId: undefined, projectId: undefined, surfaceId: 'operations' }}>{capture ? <Capture capture={capture} /> : null}<RenderBrowser source={source} /></SelectionProvider></LocalizationProvider>
}
function Capture({ capture }: { capture: (store: InteractionStore) => void }) { capture(useInteractionStore()); return null }
function setup(source: RenderSource = createRendersFixture({ scope, limit: 3 }), locale: 'en' | 'zh-CN' = 'en') { return render(<Host source={source} locale={locale} />) }

describe('RenderBrowser observability workflow', () => {
  it('does not serialize denied Artifact metadata in an available collection', async () => {
    const source = realSource()
    const protectedArtifact = {
      id: 'artifact-restricted-ordinary', name: 'Restricted courtyard preview', type: 'restricted-media-type',
      availability: 'RESTRICTED_PROCESSING', version: 'restricted-artifact-v9', taskId: 'task-connected', metadataAccess: 'denied',
    }
    vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => {
      const result = ownedResult(request)
      return { ...result, jobs: result.jobs.map(job => ({ ...job, artifacts: { ...job.artifacts, items: [protectedArtifact] } })) }
    })
    setup(source)
    fireEvent.click(await screen.findByRole('button', { name: 'Inspect render Connected render' }))
    const dialog = screen.getByRole('dialog', { name: 'Render details' })
    const artifacts = within(dialog).getByRole('heading', { name: 'Artifacts', level: 3 }).parentElement!
    expect(within(artifacts).getByText('Metadata denied')).toBeTruthy()
    // The task remains independently authorized in its own section, never in the restricted Artifact subtree.
    expect(within(dialog).getByText('Related task').parentElement?.textContent).toContain(protectedArtifact.taskId)
    for (const [field, value] of Object.entries(protectedArtifact)) {
      if (field !== 'metadataAccess') expect.soft(artifacts.outerHTML, `protected Artifact ${field}`).not.toContain(value)
    }
    expect(artifacts.querySelector('a, button, input, [title], [aria-label], [hidden]')).toBeNull()
  })

  it('uses explicit provider injection and remains usable through StrictMode adapter registration replay', async () => {
    const source = realSource(); const read = vi.spyOn(source.adapter, 'readProject'); let store!: InteractionStore
    const replay = deferred<unknown>()
    read.mockImplementationOnce(() => replay.promise)
    render(<StrictMode><LocalizationProvider><SelectionProvider scope={{ workspaceId: undefined, projectId: undefined, surfaceId: 'operations' }}><Capture capture={value => { store = value }} /><RenderBrowserProvider source={source}><RenderBrowser /></RenderBrowserProvider></SelectionProvider></LocalizationProvider></StrictMode>)
    expect(await screen.findByText('Connected render')).toBeTruthy()
    expect(screen.queryByRole('heading', { name: 'Render context retired' })).toBeNull()
    expect(read.mock.calls.length).toBeGreaterThanOrEqual(2)
    const signals = read.mock.calls.map(([, signal]) => signal)
    expect(signals.filter(signal => !signal.aborted)).toHaveLength(1)
    fireEvent.click(screen.getByRole('button', { name: 'Inspect render Connected render' }))
    expect(screen.getByRole('dialog', { name: 'Render details' })).toBeTruthy()
    act(() => store.retireSelectionOwner('owner'))
    expect(signals.every(signal => signal.aborted)).toBe(true)
    expect(screen.queryByText('Connected render')).toBeNull()
    expect(screen.queryByRole('dialog')).toBeNull()
    await act(async () => replay.reject(new Error('Late replay rejection')))
    expect(screen.getByRole('heading', { name: 'Render context retired' })).toBeTruthy()
    expect(read).toHaveBeenCalledTimes(signals.length)
  })

  it('shows supplied summary data, opaque unknown status, valid progress and current-snapshot disclosure without actions', async () => {
    setup()
    expect(await screen.findByRole('heading', { name: 'Render observability' })).toBeTruthy()
    expect(screen.getAllByText('VENDOR_WARMING').length).toBeGreaterThan(0)
    expect(screen.getByText(/3 of 8 shots · 37.5%/)).toBeTruthy()
    expect(screen.getByText(/bounded snapshot; more may exist/i)).toBeTruthy()
    expect(screen.getByText(/last successful frontend fetch/i)).toBeTruthy()
    expect(screen.queryByRole('button', { name: /cancel job|retry task|rerender|delete|publish/i })).toBeNull()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('searches ID/name, filters only source-supported literal statuses, sorts stably and keeps Reset focusable', async () => {
    setup()
    await screen.findByRole('button', { name: 'Inspect render Courtyard <final>' })
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search renders' }), { target: { value: 'Social 原文' } })
    expect(screen.getByRole('button', { name: 'Inspect render Social 原文' })).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Render status'), { target: { value: 'FAILED' } })
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search renders' }), { target: { value: 'no match' } })
    expect(screen.getByRole('heading', { name: 'No matching renders' })).toBeTruthy()
    const reset = screen.getByRole('button', { name: 'Reset filters' })
    reset.focus(); fireEvent.click(reset)
    expect(document.activeElement).toBe(reset)
    expect((screen.getByRole('searchbox', { name: 'Search renders' }) as HTMLInputElement).value).toBe('')
    expect((screen.getByLabelText('Render status') as HTMLSelectElement).value).toBe('')
  })

  it('opens read-only task/attempt/failure/Artifact metadata and restores launcher focus without exposing URLs', async () => {
    setup()
    const failed = await screen.findByRole('button', { name: 'Inspect render Social 原文' })
    failed.focus(); fireEvent.click(failed)
    const dialog = screen.getByRole('dialog', { name: 'Render details' })
    expect(within(dialog).getByText('TASK_FAILED')).toBeTruthy()
    expect(within(dialog).getByText('ATTEMPT_FAILED')).toBeTruthy()
    expect(within(dialog).getAllByText('Encoder rejected supplied media')).toHaveLength(2)
    expect(within(dialog).getByText('Invalid supplied progress')).toBeTruthy()
    for (const [label, value] of [['Supplied value', '140'], ['Value unit', 'frames'], ['Supplied total', '100'], ['Total unit', 'frames'], ['Stage', 'Encode']]) {
      expect(within(dialog).getByText(label).parentElement?.textContent).toBe(`${label}${value}`)
    }
    expect(dialog.textContent).not.toMatch(/(?:100|140)%/)
    expect(within(dialog).queryByRole('progressbar')).toBeNull()
    expect(within(dialog).getByText('Source supplied an empty Artifact collection.')).toBeTruthy()
    expect(within(dialog).queryByRole('link')).toBeNull()
    fireEvent.keyDown(dialog, { key: 'Escape' })
    expect(document.activeElement).toBe(failed)
  })

  it('distinguishes missing attempts/Artifacts from empty and bounded inspectable metadata', async () => {
    setup()
    fireEvent.click(await screen.findByRole('button', { name: 'Inspect render render-queued' }))
    let dialog = screen.getByRole('dialog', { name: 'Render details' })
    expect(within(dialog).getByText('Attempt history was not supplied.')).toBeTruthy()
    expect(within(dialog).getByText('Artifact information was not supplied.')).toBeTruthy()
    fireEvent.keyDown(dialog, { key: 'Escape' })
    fireEvent.click(screen.getByRole('button', { name: 'Inspect render Courtyard <final>' }))
    dialog = screen.getByRole('dialog', { name: 'Render details' })
    expect(within(dialog).getByText('Inspectable metadata')).toBeTruthy()
    expect(within(dialog).getByText(/bounded Artifact metadata/i)).toBeTruthy()
    expect(within(dialog).queryByRole('link')).toBeNull()
  })

  it('retains mismatched progress units and missing totals literally without deriving a percentage', async () => {
    const examples: RenderProgress[] = [
      { value: 3, unit: 'shots', total: 8, totalUnit: 'frames', stage: 'Composite <literal>' },
      { value: 3, unit: 'shots', stage: 'Composite <literal>' },
    ]
    for (const progress of examples) {
      const source = realSource()
      vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => {
        const result = ownedResult(request)
        return { ...result, jobs: result.jobs.map(job => ({ ...job, progress })) }
      })
      const view = setup(source)
      fireEvent.click(await screen.findByRole('button', { name: 'Inspect render Connected render' }))
      const dialog = screen.getByRole('dialog', { name: 'Render details' })
      for (const [label, value] of [['Supplied value', '3'], ['Value unit', 'shots'], ['Supplied total', progress.total === undefined ? 'Not supplied' : '8'], ['Total unit', progress.totalUnit ?? 'Not supplied'], ['Stage', 'Composite <literal>']]) {
        expect(within(dialog).getByText(label).parentElement?.textContent).toBe(`${label}${value}`)
      }
      expect(dialog.textContent).not.toContain('%')
      expect(within(dialog).getByText(progress.total === undefined ? '3 shots · total not supplied' : 'Invalid supplied progress')).toBeTruthy()
      view.unmount()
    }
  })

  it('uses one stable Refresh/Cancel/Retry control, preserves filters, drops cancelled replies and never steals moved focus', async () => {
    const source = realSource()
    render(<LocalizationProvider><SelectionProvider scope={{ workspaceId: undefined, projectId: undefined, surfaceId: 'operations' }}><button type="button">Stable focus</button><RenderBrowser source={source} /></SelectionProvider></LocalizationProvider>)
    await screen.findByText('Connected render')
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search renders' }), { target: { value: 'Connected' } })
    const pending = deferred<unknown>(); let request!: RenderReadRequest
    vi.spyOn(source.adapter, 'readProject').mockImplementationOnce(value => { request = value; return pending.promise })
    const workflow = screen.getByRole('button', { name: 'Refresh renders' })
    workflow.focus(); fireEvent.click(workflow)
    expect(screen.getByRole('button', { name: 'Cancel loading' })).toBe(workflow)
    const stable = screen.getByRole('button', { name: 'Stable focus' }); stable.focus()
    await act(async () => pending.resolve({ status: 'error', scope: request.scope, requestId: request.requestId, explanation: '<opaque error>' }))
    expect(screen.getByRole('button', { name: 'Retry loading' })).toBe(workflow)
    expect(document.activeElement).toBe(stable)
    const cancelled = deferred<unknown>(); let cancelledRequest!: RenderReadRequest
    vi.spyOn(source.adapter, 'readProject').mockImplementationOnce(value => { cancelledRequest = value; return cancelled.promise })
    fireEvent.click(workflow); fireEvent.click(workflow)
    await act(async () => cancelled.resolve(ownedResult(cancelledRequest, 'Cancelled secret')))
    expect(screen.queryByText('Cancelled secret')).toBeNull()
    const restored = deferred<unknown>(); let restoredRequest!: RenderReadRequest
    vi.spyOn(source.adapter, 'readProject').mockImplementationOnce(value => { restoredRequest = value; return restored.promise })
    fireEvent.click(workflow)
    await act(async () => restored.resolve(ownedResult(restoredRequest)))
    expect((screen.getByRole('searchbox', { name: 'Search renders' }) as HTMLInputElement).value).toBe('Connected')
  })

  it.each(['unavailable', 'denied', 'unknown', 'unsupported', 'error', 'stale'] as const)('clears old content for a safe %s receipt and keeps retry available', async failure => {
    const source = realSource(); setup(source); await screen.findByText('Connected render')
    vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => ({ status: failure, scope: request.scope, requestId: request.requestId, explanation: `<opaque ${failure} 原因>` }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh renders' }))
    await waitFor(() => expect(screen.getByText(`<opaque ${failure} 原因>`)).toBeTruthy())
    expect(screen.queryByText('Connected render')).toBeNull()
    expect(screen.getByRole('button', { name: 'Retry loading' })).toBeTruthy()
  })

  it('distinguishes invalid relationships from invalid returned content and never retains stale detail', async () => {
    const source = realSource(); setup(source); await screen.findByText('Connected render')
    vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => {
      const result = ownedResult(request, 'Must stay hidden')
      result.jobs[0].attempts.items[0].parentAttemptId = 'missing-attempt'
      return result
    })
    fireEvent.click(screen.getByRole('button', { name: 'Refresh renders' }))
    expect(await screen.findByRole('heading', { name: 'Invalid Render relationships' })).toBeTruthy()
    expect(screen.queryByText('Must stay hidden')).toBeNull()
  })

  it('shows detail-not-found after a successful refresh removes the inspected Render', async () => {
    const source = realSource(); setup(source)
    fireEvent.click(await screen.findByRole('button', { name: 'Inspect render Connected render' }))
    const workflow = screen.getByRole('button', { name: 'Refresh renders' })
    vi.spyOn(source.adapter, 'readProject').mockImplementationOnce(async request => ({ ...ownedResult(request), jobs: [] }))
    fireEvent.click(workflow)
    expect(await screen.findByRole('dialog', { name: 'Render not found' })).toBeTruthy()
    expect(screen.queryByText('Connected render')).toBeNull()
  })

  it.each(['principalId', 'tenantId', 'sessionId', 'projectId'] as const)('retires a pending valid reply on %s change', async field => {
    const source = realSource(); const pending = deferred<unknown>(); let oldRequest!: RenderReadRequest
    vi.spyOn(source.adapter, 'readProject').mockImplementation(request => { oldRequest = request; return pending.promise })
    const view = setup(source)
    const next = realSource({ [field]: field === 'projectId' ? 'project-2' : 'changed' })
    view.rerender(<Host source={next} />)
    expect(await screen.findByText('Connected render')).toBeTruthy()
    await act(async () => pending.resolve(ownedResult(oldRequest, 'Retired secret')))
    expect(screen.queryByText('Retired secret')).toBeNull()
  })

  it('retires a pending read under StrictMode Selection ownership and rejects its late success', async () => {
    for (const outcome of ['success', 'rejection'] as const) {
        const source = realSource(); const { calls, read } = pendingReads(source); let store!: InteractionStore
        const view = render(<StrictMode><Host source={source} capture={value => { store = value }} /></StrictMode>)
        expect(screen.getByRole('heading', { name: 'Loading Render observability' })).toBeTruthy()
        expect(calls.length).toBeGreaterThanOrEqual(2)
        expect(calls.filter(call => !call.signal.aborted)).toHaveLength(1)
        const callCount = calls.length
        act(() => store.retireSelectionOwner('owner'))
        expect(calls.every(call => call.signal.aborted)).toBe(true)
        expect(screen.getByRole('heading', { name: 'Render context retired' })).toBeTruthy()
        await act(async () => {
          for (const call of calls) {
            if (outcome === 'success') call.result.resolve(ownedResult(call.request, 'Retired owner secret'))
            else call.result.reject(new Error('Late retired owner rejection'))
          }
        })
        expect(screen.queryByText('Retired owner secret')).toBeNull()
        expect(screen.queryByRole('dialog')).toBeNull()
        expect(screen.getByRole('heading', { name: 'Render context retired' })).toBeTruthy()
        expect(read).toHaveBeenCalledTimes(callCount); view.unmount()
      }
    })

    it('retires pending reads on access/source replacement and unmount', async () => {
      for (const replacement of ['access', 'binding', 'adapter', 'unmount'] as const) {
        for (const outcome of ['success', 'rejection'] as const) {
        const source = realSource(); const { calls, read } = pendingReads(source)
        const view = render(<StrictMode><Host source={source} /></StrictMode>)
        expect(screen.getByRole('heading', { name: 'Loading Render observability' })).toBeTruthy()
        expect(calls.length).toBeGreaterThanOrEqual(2)
        expect(calls.filter(call => !call.signal.aborted)).toHaveLength(1)
        const callCount = calls.length
        const next: RenderSource = replacement === 'adapter' ? { ...source, adapter: realSource().adapter }
          : replacement === 'binding' ? { ...source, readAccessBinding: { kind: 'HOST_AGREED', accessKey: 'other.host.binding' } }
            : { ...source, access: { ...source.access, status: 'POLICY_DENIED' } }
        if (replacement === 'unmount') view.unmount()
        else view.rerender(<StrictMode><Host source={next} /></StrictMode>)
        expect(calls.every(call => call.signal.aborted)).toBe(true)
        const expectedTitle = replacement === 'access' ? 'Render observability denied' : 'Render observability access unknown'
        if (replacement === 'adapter') expect(await screen.findByText('Connected render')).toBeTruthy()
        else if (replacement !== 'unmount') expect(screen.getByRole('heading', { name: expectedTitle })).toBeTruthy()
        await act(async () => {
          for (const call of calls) {
            if (outcome === 'success') call.result.resolve(ownedResult(call.request, 'Replaced source secret'))
            else call.result.reject(new Error('Late replaced read rejection'))
          }
        })
        expect(read).toHaveBeenCalledTimes(callCount)
        expect(screen.queryByText('Replaced source secret')).toBeNull()
        expect(screen.queryByRole('dialog')).toBeNull()
        if (replacement === 'adapter') expect(screen.getByText('Connected render')).toBeTruthy()
        else if (replacement !== 'unmount') expect(screen.getByRole('heading', { name: expectedTitle })).toBeTruthy()
        else expect(view.container.childElementCount).toBe(0)
        view.unmount()
      }
    }
  })

  it('clears ready data and detail on access, agreed binding and adapter replacement under StrictMode', async () => {
    for (const replacement of ['access', 'binding', 'adapter'] as const) {
      const source = realSource(); const replay = deferred<unknown>()
      const read = vi.spyOn(source.adapter, 'readProject').mockImplementationOnce(() => replay.promise)
      const view = render(<StrictMode><Host source={source} /></StrictMode>)
      fireEvent.click(await screen.findByRole('button', { name: 'Inspect render Connected render' }))
      expect(screen.getByRole('dialog', { name: 'Render details' })).toBeTruthy()
      expect(read.mock.calls.length).toBeGreaterThanOrEqual(2)
      const signals = read.mock.calls.map(([, signal]) => signal)
      expect(signals.filter(signal => !signal.aborted)).toHaveLength(1)
      const nextAdapter: RenderSource['adapter'] = { origin: 'real', async readProject(request) { return ownedResult(request, 'Replacement render') } }
      const next: RenderSource = replacement === 'adapter' ? { ...source, adapter: nextAdapter }
        : replacement === 'binding' ? {
          ...source, access: { ...source.access, key: 'other.host.binding' },
          readAccessBinding: { kind: 'HOST_AGREED', accessKey: 'other.host.binding' },
        } : { ...source, access: { ...source.access, status: 'UNKNOWN_FAIL_CLOSED' } }
      const bindingCalls = replacement === 'binding' ? pendingReads(next) : null
      view.rerender(<StrictMode><Host source={next} /></StrictMode>)
      expect(signals.every(signal => signal.aborted)).toBe(true)
      expect(screen.queryByText('Connected render')).toBeNull()
      expect(screen.queryByRole('dialog')).toBeNull()
      if (replacement === 'adapter') expect(await screen.findByText('Replacement render')).toBeTruthy()
      if (bindingCalls) {
        expect(bindingCalls.calls.filter(call => !call.signal.aborted)).toHaveLength(1)
        await act(async () => {
          for (const call of bindingCalls.calls) call.result.resolve(ownedResult(call.request, 'Replacement render'))
        })
        expect(screen.getByText('Replacement render')).toBeTruthy()
      }
      await act(async () => replay.resolve(ownedResult(read.mock.calls[0][0], 'Old ready source secret')))
      expect(screen.queryByText('Old ready source secret')).toBeNull()
      expect(screen.queryByRole('dialog')).toBeNull()
      if (replacement === 'access') expect(screen.getByRole('heading', { name: 'Render observability access unknown' })).toBeTruthy()
      else expect(screen.getByText('Replacement render')).toBeTruthy()
      view.unmount()
    }
  })

  it('never queries initially denied or unknown access, including a host-relabelled test key', async () => {
    for (const boundary of ['denied', 'unknown', 'test-key'] as const) {
      const source = realSource()
      const blocked: RenderSource = boundary === 'test-key' ? {
        ...source, access: { ...source.access, key: TEST_ONLY_RENDER_ACCESS_KEY },
        readAccessBinding: { kind: 'HOST_AGREED', accessKey: TEST_ONLY_RENDER_ACCESS_KEY },
      } : { ...source, access: { ...source.access, status: boundary === 'denied' ? 'POLICY_DENIED' : 'UNKNOWN_FAIL_CLOSED' } }
      const read = vi.spyOn(source.adapter, 'readProject')
      const view = render(<StrictMode><Host source={blocked} /></StrictMode>)
      expect(screen.getByRole('heading', { name: boundary === 'denied' ? 'Render observability denied' : 'Render observability access unknown' })).toBeTruthy()
      await act(async () => { await Promise.resolve() })
      expect(read).not.toHaveBeenCalled()
      expect(screen.queryByRole('button', { name: /Refresh renders|Retry loading|Cancel loading/ })).toBeNull()
      expect(screen.queryByText('Connected render')).toBeNull()
      view.unmount()
    }
  })

  it('rebinds only to a fresh pageshow Selection owner after clearing ready data', async () => {
    const source = realSource(); const read = vi.spyOn(source.adapter, 'readProject')
    setup(source); expect(await screen.findByText('Connected render')).toBeTruthy()
    act(() => window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: true })))
    expect(screen.queryByText('Connected render')).toBeNull()
    expect(screen.getByRole('heading', { name: 'Render context retired' })).toBeTruthy()
    act(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })))
    expect(await screen.findByText('Connected render')).toBeTruthy()
    expect(read).toHaveBeenCalledTimes(2)
  })

  it('is unavailable with no injected source and localizes the complete workflow in Chinese', async () => {
    const unavailable = render(<Host />)
    expect(screen.getByRole('heading', { name: 'Render observability unavailable' })).toBeTruthy()
    expect(screen.queryByText(/SIMULATED RENDER DATA/)).toBeNull(); unavailable.unmount()
    setup(createRendersFixture({ scope }), 'zh-CN')
    expect(await screen.findByRole('heading', { name: '渲染可观测性' })).toBeTruthy()
    expect(screen.getByRole('searchbox', { name: '搜索渲染' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '检查渲染 Courtyard <final>' }))
    const dialog = screen.getByRole('dialog', { name: '渲染详情' })
    expect(within(dialog).getByText('VENDOR_WARMING')).toBeTruthy()
    for (const [label, value] of [['提供的数值', '3'], ['数值单位', 'shots'], ['提供的总量', '8'], ['总量单位', 'shots']]) {
      expect(within(dialog).getByText(label).parentElement?.textContent).toBe(`${label}${value}`)
    }
  })
})

const restrictedStates = ['denied', 'unknown', 'unavailable', 'stale'] as const
const metadataLabels = {
  inspectable: 'Inspectable metadata', denied: 'Metadata denied', unknown: 'Metadata access unknown',
  unavailable: 'Metadata unavailable', stale: 'Metadata stale; refresh Render data to check again.',
}
function artifactReceipt(request: RenderReadRequest, metadataAccess: RenderArtifact['metadataAccess']) {
  const result = ownedResult(request)
  const artifact: RenderArtifact = {
    id: 'artifact-permission-sample', name: 'Permission sample preview', type: 'permission-sample-media',
    availability: 'PERMISSION_SAMPLE_READY', version: 'permission-sample-v8', taskId: 'task-connected', metadataAccess,
  }
  return { ...result, jobs: result.jobs.map(job => ({ ...job, artifacts: { ...job.artifacts, items: [artifact] } })) }
}
function artifactSection() {
  return within(screen.getByRole('dialog', { name: 'Render details' })).getByRole('heading', { name: 'Artifacts', level: 3 }).parentElement!
}
function expectArtifactAbsent(root: Element) {
  const artifact = artifactReceipt({ scope, requestId: 'assertion-only' }, 'inspectable').jobs[0].artifacts.items[0]
  for (const [field, value] of Object.entries(artifact)) {
    // taskId may appear independently in the authorized task/attempt sections.
    if (field !== 'metadataAccess' && field !== 'taskId') expect(root.outerHTML, `protected Artifact ${field}`).not.toContain(value)
  }
}
function expectRestrictedArtifact(state: typeof restrictedStates[number]) {
  const section = artifactSection()
  expectArtifactAbsent(section)
  expect(section.outerHTML).not.toContain('task-connected')
  expect(section.outerHTML).not.toContain('revision-connected')
  const item = within(section).getByRole('listitem')
  expect(item.textContent).toBe(metadataLabels[state])
  expect(within(item).getByText(metadataLabels[state])).toBeTruthy()
  expect(item.querySelector('a, button, input, [title], [aria-label], [hidden]')).toBeNull()
}

describe('Artifact item metadata permission boundaries', () => {
  it.each([
    { locale: 'en' as const, inspect: 'Inspect render Connected render', heading: 'Artifacts', guidance: 'Metadata stale; refresh Render data to check again.' },
    { locale: 'zh-CN' as const, inspect: '检查渲染 Connected render', heading: '制品', guidance: '元数据已过期；请刷新渲染数据后再次检查。' },
  ])('gives stale items generic read-refresh guidance in $locale without metadata or render actions', async ({ locale, inspect, heading, guidance }) => {
    const source = realSource()
    const read = vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => artifactReceipt(request, 'stale'))
    setup(source, locale)
    fireEvent.click(await screen.findByRole('button', { name: inspect }))
    const section = within(screen.getByRole('dialog')).getByRole('heading', { name: heading, level: 3 }).parentElement!
    const item = within(section).getByRole('listitem')
    expect.soft(item.textContent).toBe(guidance)
    const artifact = artifactReceipt({ scope, requestId: 'assertion-only' }, 'stale').jobs[0].artifacts.items[0]
    for (const [field, value] of Object.entries(artifact)) {
      if (field !== 'metadataAccess') expect(section.outerHTML, `protected Artifact ${field}`).not.toContain(value)
    }
    expect(item.querySelector('a, button, input, [role="button"], [tabindex], [title], [aria-label], [hidden]')).toBeNull()
    expect(item.textContent).not.toMatch(/retry|rerender|re-render|重试|重新渲染/i)
    expect(read).toHaveBeenCalledTimes(1)
  })

  it.each(restrictedStates)('preserves the separate collection-level %s outcome', async state => {
    const source = realSource()
    vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => {
      const result = artifactReceipt(request, 'inspectable')
      return { ...result, jobs: result.jobs.map(job => ({ ...job, artifacts: { state, explanation: 'Collection metadata cannot be inspected.' } })) }
    })
    setup(source)
    fireEvent.click(await screen.findByRole('button', { name: 'Inspect render Connected render' }))
    const section = artifactSection()
    expect(within(section).getByText('Collection metadata cannot be inspected.')).toBeTruthy()
    expect(section.querySelector('.ff-badge')?.textContent).toBe({
      denied: 'Artifact metadata denied', unknown: 'Artifact metadata access unknown',
      unavailable: 'Artifact metadata unavailable', stale: 'Artifact metadata stale',
    }[state])
    expectArtifactAbsent(section)
    expect(within(section).queryByRole('list')).toBeNull()
    expect(section.outerHTML).not.toContain('task-connected')
  })

  it.each(['inspectable', ...restrictedStates] as const)('renders only the permitted item content for %s', async state => {
    const source = realSource()
    vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => artifactReceipt(request, state))
    setup(source)
    fireEvent.click(await screen.findByRole('button', { name: 'Inspect render Connected render' }))
    if (state === 'inspectable') {
      const section = artifactSection()
      const artifact = artifactReceipt({ scope, requestId: 'assertion-only' }, state).jobs[0].artifacts.items[0]
      for (const [field, value] of Object.entries(artifact)) {
        if (field !== 'metadataAccess') expect(section.outerHTML).toContain(value)
      }
      expect(within(section).getByText(metadataLabels.inspectable)).toBeTruthy()
      expect(section.querySelector('a, button')).toBeNull()
    } else expectRestrictedArtifact(state)
  })

  it('keeps allowed metadata beside all four state-only restricted items in one available collection', async () => {
    const source = realSource()
    vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => {
      const result = ownedResult(request)
      const restricted = restrictedStates.map(state => ({
        ...artifactReceipt(request, state).jobs[0].artifacts.items[0], id: `artifact-permission-sample-${state}`,
      }))
      return { ...result, jobs: result.jobs.map(job => ({ ...job, artifacts: { ...job.artifacts, limit: 5, items: [...job.artifacts.items, ...restricted] } })) }
    })
    setup(source)
    fireEvent.click(await screen.findByRole('button', { name: 'Inspect render Connected render' }))
    const section = artifactSection()
    const items = within(section).getAllByRole('listitem')
    expect(items).toHaveLength(5)
    expect(within(items[0]).getByText('Preview 原文')).toBeTruthy()
    expect(items[0].outerHTML).toContain('task-connected')
    expectArtifactAbsent(section)
    restrictedStates.forEach((state, index) => {
      expect(items[index + 1].textContent).toBe(metadataLabels[state])
      expect(items[index + 1].outerHTML).not.toContain('task-connected')
    })
    expect(section.querySelector('a, button, [title], [aria-label], [hidden]')).toBeNull()
  })

  it.each(restrictedStates)('clears same-ID inspectable metadata during refresh and after %s until a new valid allow', async state => {
    const source = realSource(); const { calls } = pendingReads(source)
    setup(source)
    await act(async () => calls[0].result.resolve(artifactReceipt(calls[0].request, 'inspectable')))
    fireEvent.click(screen.getByRole('button', { name: 'Inspect render Connected render' }))
    const oldSection = artifactSection()
    expect(oldSection.outerHTML).toContain('Permission sample preview')
    fireEvent.click(screen.getByRole('button', { name: 'Refresh renders' }))
    expect(oldSection.isConnected).toBe(false)
    expect(screen.queryByRole('dialog')).toBeNull()
    expectArtifactAbsent(document.body)
    await act(async () => calls[1].result.resolve(artifactReceipt(calls[1].request, state)))
    expectRestrictedArtifact(state)
    expectArtifactAbsent(document.body)
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    fireEvent.click(screen.getByRole('button', { name: 'Inspect render Connected render' }))
    expectRestrictedArtifact(state)
    fireEvent.click(screen.getByRole('button', { name: 'Refresh renders' }))
    expectArtifactAbsent(document.body)
    await act(async () => calls[2].result.resolve(artifactReceipt(calls[2].request, 'inspectable')))
    expect(artifactSection().outerHTML).toContain('Permission sample preview')
    expect(artifactSection().outerHTML).toContain('permission-sample-v8')
  })

  it('keeps item denial after an aborted old allow arrives and restores only a new valid allow', async () => {
    const source = realSource(); const { calls } = pendingReads(source)
    setup(source)
    await act(async () => calls[0].result.resolve(artifactReceipt(calls[0].request, 'inspectable')))
    fireEvent.click(screen.getByRole('button', { name: 'Inspect render Connected render' }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh renders' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel loading' }))
    expect(calls[1].signal.aborted).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Retry loading' }))
    await act(async () => calls[2].result.resolve(artifactReceipt(calls[2].request, 'denied')))
    fireEvent.click(screen.getByRole('button', { name: 'Inspect render Connected render' }))
    expectRestrictedArtifact('denied')
    await act(async () => calls[1].result.resolve(artifactReceipt(calls[1].request, 'inspectable')))
    expectRestrictedArtifact('denied')
    expectArtifactAbsent(document.body)
    fireEvent.click(screen.getByRole('button', { name: 'Refresh renders' }))
    await act(async () => calls[3].result.resolve(artifactReceipt(calls[3].request, 'inspectable')))
    expect(artifactSection().outerHTML).toContain('Permission sample preview')
  })

  it.each(['error', 'cancel', 'stale', 'rejection'] as const)('never fills cached Artifact metadata after refresh %s', async outcome => {
    const source = realSource(); const { calls } = pendingReads(source)
    setup(source)
    await act(async () => calls[0].result.resolve(artifactReceipt(calls[0].request, 'inspectable')))
    fireEvent.click(screen.getByRole('button', { name: 'Inspect render Connected render' }))
    expect(artifactSection().outerHTML).toContain('Permission sample preview')
    fireEvent.click(screen.getByRole('button', { name: 'Refresh renders' }))
    expectArtifactAbsent(document.body)
    expect(screen.queryByRole('dialog')).toBeNull()
    if (outcome === 'cancel') {
      fireEvent.click(screen.getByRole('button', { name: 'Cancel loading' }))
      expect(calls[1].signal.aborted).toBe(true)
      await act(async () => calls[1].result.resolve(artifactReceipt(calls[1].request, 'inspectable')))
    } else if (outcome === 'rejection') {
      await act(async () => calls[1].result.reject(new Error('Read failed')))
    } else {
      await act(async () => calls[1].result.resolve({ ...calls[1].request, status: outcome }))
    }
    expect(screen.getByRole('button', { name: 'Retry loading' })).toBeTruthy()
    expectArtifactAbsent(document.body)
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it.each((['principalId', 'tenantId', 'sessionId', 'projectId', 'access', 'binding', 'adapter', 'owner', 'retire'] as const).flatMap(replacement =>
    (['ready', 'refresh'] as const).map(stage => [replacement, stage] as const),
  ))('removes Artifact DOM and aborts old reads on %s replacement while %s', async (replacement, stage) => {
    const source = realSource(); const { calls } = pendingReads(source); let store!: InteractionStore
    const view = render(<Host source={source} capture={value => { store = value }} />)
    await act(async () => calls[0].result.resolve(artifactReceipt(calls[0].request, 'inspectable')))
    fireEvent.click(screen.getByRole('button', { name: 'Inspect render Connected render' }))
    const oldSection = artifactSection()
    expect(oldSection.outerHTML).toContain('Permission sample preview')
    // Exercise both mounted ready details and a pending refresh across the change.
    if (stage === 'refresh') fireEvent.click(screen.getByRole('button', { name: 'Refresh renders' }))
    const next: RenderSource = replacement === 'access' ? { ...source, access: { ...source.access, status: 'POLICY_DENIED' } }
      : replacement === 'binding' ? { ...source, readAccessBinding: { kind: 'HOST_AGREED', accessKey: 'changed.host.read' } }
        : replacement === 'adapter' ? { ...source, adapter: realSource().adapter }
          : ['owner', 'retire'].includes(replacement) ? source
            : { ...source, scope: { ...source.scope, [replacement]: 'changed-scope' } }
    if (replacement === 'retire') act(() => store.retireSelectionOwner('owner'))
    else view.rerender(<Host key={replacement === 'owner' ? 'new-owner' : undefined} source={next} />)
    expect(oldSection.isConnected).toBe(false)
    expect(calls[0].signal.aborted).toBe(true)
    if (replacement === 'adapter') expect(await screen.findByText('Connected render')).toBeTruthy()
    expectArtifactAbsent(document.body)
    expect(screen.queryByRole('dialog')).toBeNull()
    if (stage === 'refresh') {
      expect(calls[1].signal.aborted).toBe(true)
      await act(async () => calls[1].result.resolve(artifactReceipt(calls[1].request, 'inspectable')))
      expectArtifactAbsent(document.body)
      expect(screen.queryByRole('dialog')).toBeNull()
    }
  })

  it.each(['missing', 'invalid', 'relationship', 'request', 'scope'] as const)('rejects %s receipts before any Artifact metadata renders', async invalid => {
    const source = realSource()
    vi.spyOn(source.adapter, 'readProject').mockImplementation(async request => {
      const result = artifactReceipt(request, 'inspectable')
      const artifact = result.jobs[0].artifacts.items[0]
      if (invalid === 'missing') Reflect.deleteProperty(artifact, 'metadataAccess')
      if (invalid === 'invalid') Reflect.set(artifact, 'metadataAccess', 'allow')
      if (invalid === 'relationship') artifact.taskId = 'unrelated-task'
      if (invalid === 'request') result.requestId = 'old-request'
      if (invalid === 'scope') result.scope = { ...request.scope, principalId: 'different-account' }
      return result
    })
    setup(source)
    expect(await screen.findByRole('heading', { name: invalid === 'relationship' ? 'Invalid Render relationships' : 'Invalid Render snapshot' })).toBeTruthy()
    expectArtifactAbsent(document.body)
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Inspect render Connected render' })).toBeNull()
  })
})
