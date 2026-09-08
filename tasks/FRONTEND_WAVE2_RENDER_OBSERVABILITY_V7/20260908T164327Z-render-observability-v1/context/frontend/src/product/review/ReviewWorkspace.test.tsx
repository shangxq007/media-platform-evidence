import { LocalizationProvider } from '../../localization'
import { SelectionProvider, useInteractionStore } from '../../interaction/SelectionContext'
import { AgentLauncher, AgentShell, SelectionInspector } from '../../interaction/InteractionShell'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { platformClient } from '../../foundation/platformClient'
import { ProjectContextProvider } from '../../foundation/projectContext'
import type { GatewayFailureCode, GatewayResult, RevisionComparison, RevisionDetail, RevisionListEntry } from '../timeline/gateways'
import { ScriptedTimelineQueryGateway, mockFailure } from '../timeline/testing/mocks'
import { contentHash, projectId, revisionId, timelineId } from '../timeline/types'
import { ReviewWorkspace } from './ReviewWorkspace'

const head = {
  projectId: projectId('project-1'), timelineId: timelineId('project-1'),
  revisionId: revisionId('revision-R1'), contentHash: contentHash('a'.repeat(64)),
}
const summary = {
  supported: true, tracksAdded: 0, tracksRemoved: 0, tracksModified: 0,
  clipsAdded: 0, clipsRemoved: 0, clipsModified: 0, assetsAdded: 0, assetsRemoved: 0,
}
const revision0: RevisionListEntry = {
  id: revisionId('revision-R0'), revisionNumber: 1, parentRevisionId: null, source: 'OPERATION',
  message: 'Base', labels: [], authorUserId: null, createdAt: '2026-01-01T00:00:00Z', isMerge: false,
}
const revision1: RevisionListEntry = {
  ...revision0, id: revisionId('revision-R1'), revisionNumber: 2, parentRevisionId: revision0.id, message: 'Current',
}
const detail: RevisionDetail = { revision: revision1, changeSummary: summary, changeCount: 0 }

function comparison(fromRevision: RevisionListEntry, toRevision: RevisionListEntry, entityId: string): RevisionComparison {
  return { fromRevision, toRevision, summary, entityChanges: [{ kind: 'CLIP', entityId, action: 'MODIFIED' }] }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason: unknown) => void
  const promise = new Promise<T>((accept, decline) => { resolve = accept; reject = decline })
  return { promise, resolve, reject }
}

describe('Review comparison request ownership', () => {
  afterEach(() => vi.restoreAllMocks())

  it('keeps the newest ordered comparison when an older request resolves last', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({
      workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1',
      recentProjects: [{ id: 'project-1', name: 'Launch film' }],
    })
    const queries = new ScriptedTimelineQueryGateway({
      head: { ok: true, value: head },
      history: { ok: true, value: [revision0, revision1] },
      detail: { ok: true, value: detail },
      comparison: { ok: true, value: comparison(revision0, revision1, 'unused') },
    })
    const older = deferred<GatewayResult<RevisionComparison>>()
    const newer = deferred<GatewayResult<RevisionComparison>>()
    vi.spyOn(queries, 'compare')
      .mockImplementationOnce(async () => older.promise)
      .mockImplementationOnce(async () => newer.promise)
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<QueryClientProvider client={client}><ProjectContextProvider workspaceId="workspace-1" projectId="project-1"><SelectionProvider scope={{ surfaceId: 'review', workspaceId: "workspace-1", projectId: "project-1" }}><ReviewWorkspace queryGateway={queries} /><DispatchProbe /><SelectionInspector /><AgentLauncher /><AgentShell /></SelectionProvider></ProjectContextProvider></QueryClientProvider>)

    expect((await screen.findAllByRole('option', { name: /revision-R0/ })).length).toBe(2)
    fireEvent.change(screen.getByLabelText('From revision'), { target: { value: 'revision-R0' } })
    fireEvent.change(screen.getByLabelText('To revision'), { target: { value: 'revision-R1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    fireEvent.change(screen.getByLabelText('From revision'), { target: { value: 'revision-R1' } })
    fireEvent.change(screen.getByLabelText('To revision'), { target: { value: 'revision-R0' } })
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))

    await act(async () => newer.resolve({ ok: true, value: comparison(revision1, revision0, 'clip-newest') }))
    expect(await screen.findByText('clip-newest')).toBeTruthy()
    await act(async () => older.resolve({ ok: true, value: comparison(revision0, revision1, 'clip-stale') }))
    expect(screen.getByText('clip-newest')).toBeTruthy()
    expect(screen.queryByText('clip-stale')).toBeNull()
  })

  it('moves active review tabs and focus with the complete ARIA keyboard pattern', async () => {
    vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({
      workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1',
      recentProjects: [{ id: 'project-1', name: 'Launch film' }],
    })
    const queries = new ScriptedTimelineQueryGateway({
      head: { ok: true, value: head }, history: { ok: true, value: [revision0, revision1] },
      detail: { ok: true, value: detail }, comparison: { ok: true, value: comparison(revision0, revision1, 'clip-1') },
    })
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<QueryClientProvider client={client}><ProjectContextProvider workspaceId="workspace-1" projectId="project-1"><SelectionProvider scope={{ surfaceId: 'review', workspaceId: "workspace-1", projectId: "project-1" }}><ReviewWorkspace queryGateway={queries} /><DispatchProbe /><SelectionInspector /><AgentLauncher /><AgentShell /></SelectionProvider></ProjectContextProvider></QueryClientProvider>)

    expect((await screen.findAllByRole('option', { name: /revision-R0/ })).length).toBe(2)
    const semantic = screen.getByRole('tab', { name: 'Semantic Changes' })
    semantic.focus()
    fireEvent.keyDown(semantic, { key: 'ArrowRight' })
    const conversation = screen.getByRole('tab', { name: 'Conversation' })
    expect(conversation.getAttribute('aria-selected')).toBe('true')
    expect(document.activeElement).toBe(conversation)

    fireEvent.keyDown(conversation, { key: 'End' })
    const checks = screen.getByRole('tab', { name: 'Checks' })
    expect(checks.getAttribute('aria-selected')).toBe('true')
    expect(document.activeElement).toBe(checks)

    fireEvent.keyDown(checks, { key: 'Home' })
    const overview = screen.getByRole('tab', { name: 'Overview' })
    expect(overview.getAttribute('aria-selected')).toBe('true')
    expect(document.activeElement).toBe(overview)

    fireEvent.keyDown(overview, { key: 'ArrowLeft' })
    expect(screen.getByRole('tab', { name: 'Checks' }).getAttribute('aria-selected')).toBe('true')
    expect(document.activeElement).toBe(checks)
  })
})

function DispatchProbe() {
  const store = useInteractionStore()
  return <button onClick={() => { const pair = store.getSnapshot().revisionPair; if (pair) store.dispatch({ category: 'READ_ONLY_QUERY', type: 'compare-revisions', pair }) }}>Dispatch current pair</button>
}

function reviewSetup() {
  vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({ workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1', recentProjects: [] })
  const queries = new ScriptedTimelineQueryGateway({ head: { ok: true, value: head }, history: { ok: true, value: [revision0, revision1] }, detail: { ok: true, value: detail }, comparison: { ok: true, value: comparison(revision0, revision1, 'clip-result') } })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const content = (workspaceId = 'workspace-1', projectId = 'project-1') => <QueryClientProvider client={client}><ProjectContextProvider workspaceId={workspaceId} projectId={projectId}><SelectionProvider scope={{ surfaceId: 'review', workspaceId: workspaceId, projectId: projectId }}><ReviewWorkspace queryGateway={queries} /><DispatchProbe /><SelectionInspector /><AgentLauncher /><AgentShell /></SelectionProvider></ProjectContextProvider></QueryClientProvider>
  return { queries, content }
}

async function choosePair() {
  await screen.findAllByRole('option', { name: /revision-R0/ })
  fireEvent.change(screen.getByLabelText('From revision'), { target: { value: revision0.id } })
  fireEvent.change(screen.getByLabelText('To revision'), { target: { value: revision1.id } })
}

const disabled = (name: string) => (screen.getByRole('button', { name }) as HTMLButtonElement).disabled

describe('Review loading, retry and invalidation', () => {
  afterEach(() => vi.restoreAllMocks())

  it('announces deferred history loading, rejection, retry and empty results', async () => {
    const { queries, content } = reviewSetup()
    const request = deferred<GatewayResult<readonly RevisionListEntry[]>>()
    vi.spyOn(queries, 'listRevisions').mockImplementationOnce(() => request.promise).mockResolvedValueOnce({ ok: true, value: [] })
    render(content())
    expect(screen.getByText('Loading revision history…').getAttribute('role')).toBe('status')
    expect(disabled('Compare revisions')).toBe(true)
    await act(async () => request.reject(new Error('offline')))
    expect(screen.getByRole('alert').textContent).toContain('couldn’t load revision history')
    fireEvent.click(screen.getByRole('button', { name: 'Retry history' }))
    expect(await screen.findByText('No revisions available')).toBeTruthy()
    expect(disabled('Compare revisions')).toBe(true)
    expect((screen.getByLabelText('From revision') as HTMLSelectElement).disabled).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Refresh history' }))
    await choosePair()
    expect(disabled('Compare revisions')).toBe(false)
  })

  it('handles typed history failure and duplicate history entries as only one distinct revision', async () => {
    const { queries, content } = reviewSetup()
    vi.spyOn(queries, 'listRevisions').mockResolvedValueOnce(mockFailure('UNAVAILABLE')).mockResolvedValueOnce({ ok: true, value: [revision0, revision0] })
    render(content())
    expect((await screen.findByRole('alert')).textContent).toContain('Try again')
    expect(screen.getAllByText('UNAVAILABLE')).toHaveLength(2)
    expect(screen.getAllByText('UNAVAILABLE').every(element => element.closest('details'))).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Retry history' }))
    await screen.findByText(/Only one distinct revision/)
    expect(disabled('Compare revisions')).toBe(true)
  })

  it('rejects same revision selection, suppresses pending duplicates, and clears results on retry failure', async () => {
    const { queries, content } = reviewSetup()
    const pending = deferred<GatewayResult<RevisionComparison>>()
    const spy = vi.spyOn(queries, 'compare')
    render(content())
    await choosePair()
    fireEvent.change(screen.getByLabelText('To revision'), { target: { value: revision0.id } })
    expect(disabled('Compare revisions')).toBe(true)
    fireEvent.change(screen.getByLabelText('To revision'), { target: { value: revision1.id } })
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    await screen.findByText('clip-result')
    spy.mockImplementationOnce(() => pending.promise)
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    expect(screen.queryByText('clip-result')).toBeNull()
    expect(disabled('Comparing…')).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Comparing…' }))
    fireEvent.click(screen.getByRole('button', { name: 'Dispatch current pair' }))
    expect(spy).toHaveBeenCalledTimes(2)
    await act(async () => pending.reject(new Error('offline')))
    expect(screen.getByRole('alert').textContent).toContain('Retry comparison')
    expect(screen.queryByText('clip-result')).toBeNull()
    spy.mockResolvedValueOnce(mockFailure('UNAVAILABLE'))
    fireEvent.click(screen.getByRole('button', { name: 'Retry comparison' }))
    await waitFor(() => expect(screen.getAllByText('UNAVAILABLE')).toHaveLength(2))
    expect(screen.getAllByText('UNAVAILABLE').every(element => element.closest('details'))).toBe(true)
    expect(screen.getByRole('alert').textContent).toContain('Retry comparison')
    spy.mockResolvedValueOnce({ ok: true, value: { ...comparison(revision0, revision1, 'unused'), entityChanges: [] } })
    fireEvent.click(screen.getByRole('button', { name: 'Retry comparison' }))
    await screen.findByText('Comparison loaded; no entity details were returned.')
    expect(screen.getByText('No changes reported')).toBeTruthy()
  })

  it.each(['project', 'workspace'])('discards old history and comparisons after %s scope changes', async scope => {
    const { queries, content } = reviewSetup()
    const oldHistory = deferred<GatewayResult<readonly RevisionListEntry[]>>()
    const oldCompare = deferred<GatewayResult<RevisionComparison>>()
    const historySpy = vi.spyOn(queries, 'listRevisions').mockImplementationOnce(() => oldHistory.promise)
    const view = render(content())
    view.rerender(scope === 'project' ? content('workspace-1', 'project-2') : content('workspace-2', 'project-1'))
    await choosePair()
    await act(async () => oldHistory.resolve({ ok: true, value: [] }))
    expect(screen.queryByText('No revisions available')).toBeNull()
    vi.spyOn(queries, 'compare').mockImplementationOnce(() => oldCompare.promise)
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    historySpy.mockResolvedValueOnce({ ok: true, value: [] })
    view.rerender(content('workspace-3', 'project-3'))
    await screen.findByText('No revisions available')
    await act(async () => oldCompare.resolve({ ok: true, value: comparison(revision0, revision1, 'stale-project-clip') }))
    expect(screen.queryByText('stale-project-clip')).toBeNull()
    expect(disabled('Compare revisions')).toBe(true)
  })

  it('links tabs to panels and clears loaded comparison on selector changes', async () => {
    const { content } = reviewSetup()
    render(content())
    await choosePair()
    const tab = screen.getByRole('tab', { name: 'Semantic Changes' })
    const panel = screen.getByRole('tabpanel', { name: 'Semantic Changes' })
    expect(tab.getAttribute('aria-controls')).toBe(panel.id)
    expect(panel.getAttribute('aria-labelledby')).toBe(tab.id)
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    await screen.findByText('clip-result')
    fireEvent.change(screen.getByLabelText('From revision'), { target: { value: '' } })
    expect(screen.queryByText('clip-result')).toBeNull()
    expect(disabled('Compare revisions')).toBe(true)
  })
})

it('uses the explicit Review pair as Agent read-only context and invokes the existing query without inventing facts', async () => {
  const { queries, content } = reviewSetup()
  const compare = vi.spyOn(queries, 'compare')
  render(content())
  await choosePair()
  fireEvent.click(screen.getByRole('button', { name: 'Ask Agent' }))
  expect(screen.getByTestId('agent-context').textContent).toContain('Revision pair: revision-R0 → revision-R1')
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }))
  expect(screen.getByLabelText('Synthetic proposal').textContent).toContain('No diff facts')
  expect(compare).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Run read-only comparison' }))
  await screen.findByText('clip-result')
  expect(compare).toHaveBeenCalledExactlyOnceWith(projectId('project-1'), revision0.id, revision1.id)
  fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
  fireEvent.change(screen.getByLabelText('To revision'), { target: { value: revision0.id } })
  expect(screen.queryByText('clip-result')).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: 'Ask Agent' }))
  expect(screen.getByTestId('agent-context').textContent).not.toContain('Revision pair')
})


describe('Focused Review UX contract', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows projected name, route IDs and full readable history without choosing or querying automatically', async () => {
    const { queries, content } = reviewSetup()
    vi.mocked(platformClient.workspace.getHome).mockResolvedValue({ workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1', recentProjects: [{ id: 'project-1', name: 'Launch film' }] })
    queries.historyResult = { ok: true, value: Array.from({ length: 85 }, (_, index) => ({ ...revision0, id: revisionId(`revision-${index}`), revisionNumber: index + 1, message: `Edit ${index}` })) }
    const compare = vi.spyOn(queries, 'compare')
    render(content())
    await screen.findByText('Launch film')
    expect(screen.getByText('workspace-1').closest('details')).toBeTruthy()
    expect(screen.getByText('project-1').closest('details')).toBeTruthy()
    expect(screen.getAllByRole('option', { name: /Edit 84/ })).toHaveLength(2)
    expect(screen.getAllByRole('option', { name: /Jan 1, 2026/ })).toHaveLength(170)
    expect((screen.getByLabelText('From revision') as HTMLSelectElement).value).toBe('')
    expect(compare).not.toHaveBeenCalled()
    expect(screen.getByText(/From is the starting revision/)).toBeTruthy()
  })

  it('explains missing, same and unknown choices, forwards reverse order explicitly, and binds the server result', async () => {
    const { queries, content } = reviewSetup()
    const compare = vi.spyOn(queries, 'compare').mockResolvedValue({ ok: true, value: comparison(revision1, revision0, 'reverse-clip') })
    render(content())
    await screen.findAllByRole('option', { name: /revision-R0/ })
    expect(screen.getByText('Choose a From revision and a To revision.')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('From revision'), { target: { value: revision1.id } })
    expect(screen.getByText('Choose a To revision.')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('To revision'), { target: { value: revision1.id } })
    expect(screen.getByText('Choose different revisions; the current pair is the same revision.')).toBeTruthy()
    const select = screen.getByLabelText('To revision') as HTMLSelectElement
    const unknown = document.createElement('option')
    unknown.textContent = 'Unknown revision'
    unknown.value = 'unknown-id'
    select.append(unknown)
    fireEvent.change(select, { target: { value: 'unknown-id' } })
    expect(screen.getByText('Choose revisions from the available history.')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Dispatch current pair' }))
    expect(compare).not.toHaveBeenCalled()
    fireEvent.change(select, { target: { value: revision0.id } })
    expect(compare).not.toHaveBeenCalled()
    expect(screen.getByLabelText('Selected revision pair').textContent).toContain('From revision: Revision 2 → To revision: Revision 1')
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    await screen.findByText('reverse-clip')
    expect(compare).toHaveBeenCalledExactlyOnceWith(projectId('project-1'), revision1.id, revision0.id)
    expect(screen.getByLabelText('Server result revision pair').textContent).toContain('From revision: Revision 2 → To revision: Revision 1')
  })

  it.each(['AUTHORIZATION_DENIED', 'UNSUPPORTED', 'UNAVAILABLE', 'NETWORK'] as GatewayFailureCode[])('honors both retryable values for %s in history and comparison, including dispatch', async code => {
    for (const retryable of [false, true]) {
      const { queries, content } = reviewSetup()
      const failure = { ok: false as const, code, message: 'Opaque server message', details: ['opaque diagnostic 甲'], retryable }
      const history = vi.spyOn(queries, 'listRevisions').mockResolvedValueOnce(failure)
      const view = render(content())
      await screen.findByRole('alert')
      expect(screen.getByText('opaque diagnostic 甲').closest('details')).toBeTruthy()
      expect(screen.getByText('Opaque server message').closest('details')).toBeTruthy()
      expect(screen.queryByRole('button', { name: 'Retry history' }) !== null).toBe(retryable)
      if (retryable) {
        fireEvent.click(screen.getByRole('button', { name: 'Retry history' }))
        await choosePair()
        expect(history).toHaveBeenCalledTimes(2)
      }
      view.unmount()
      const next = reviewSetup()
      const compare = vi.spyOn(next.queries, 'compare').mockResolvedValueOnce(failure)
      const nextView = render(next.content())
      await choosePair()
      fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
      await screen.findByRole('alert')
      expect(screen.getByText('opaque diagnostic 甲').closest('details')).toBeTruthy()
      if (retryable) {
        expect(disabled('Retry comparison')).toBe(false)
        fireEvent.click(screen.getByRole('button', { name: 'Retry comparison' }))
        await screen.findByText('clip-result')
        expect(compare).toHaveBeenCalledTimes(2)
      } else {
        expect(screen.queryByRole('button', { name: 'Retry comparison' })).toBeNull()
        expect(disabled('Compare revisions')).toBe(true)
        fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
        fireEvent.click(screen.getByRole('button', { name: 'Dispatch current pair' }))
        expect(compare).toHaveBeenCalledTimes(1)
        fireEvent.change(screen.getByLabelText('From revision'), { target: { value: revision1.id } })
        fireEvent.change(screen.getByLabelText('To revision'), { target: { value: revision0.id } })
        compare.mockResolvedValueOnce({ ok: true, value: comparison(revision1, revision0, 'new-pair') })
        fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
        await screen.findByText('new-pair')
        expect(compare).toHaveBeenCalledTimes(2)
        fireEvent.change(screen.getByLabelText('From revision'), { target: { value: revision0.id } })
        fireEvent.change(screen.getByLabelText('To revision'), { target: { value: revision1.id } })
        expect(screen.queryByRole('alert')).toBeNull()
        expect(screen.queryByText('opaque diagnostic 甲')).toBeNull()
        expect(disabled('Compare revisions')).toBe(false)
        expect(compare).toHaveBeenCalledTimes(2)
        fireEvent.click(screen.getByRole('button', { name: 'Dispatch current pair' }))
        await screen.findByText('clip-result')
        expect(compare).toHaveBeenCalledTimes(3)
        expect(compare).toHaveBeenLastCalledWith(projectId('project-1'), revision0.id, revision1.id)
      }
      nextView.unmount()
    }
  })

  it('rejects a scripted mismatched response without displaying its diff', async () => {
    const { queries, content } = reviewSetup()
    queries.comparisonResult = { ok: true, value: comparison(revision1, revision0, 'wrong-result') }
    render(content())
    await choosePair()
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    expect((await screen.findByRole('alert')).textContent).toContain('does not match')
    expect(screen.queryByText('wrong-result')).toBeNull()
  })

  it('keeps newer success when an older comparison rejects', async () => {
    const { queries, content } = reviewSetup()
    const older = deferred<GatewayResult<RevisionComparison>>()
    vi.spyOn(queries, 'compare').mockImplementationOnce(() => older.promise).mockResolvedValueOnce({ ok: true, value: comparison(revision1, revision0, 'new-success') })
    render(content())
    await choosePair()
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    fireEvent.change(screen.getByLabelText('From revision'), { target: { value: revision1.id } })
    fireEvent.change(screen.getByLabelText('To revision'), { target: { value: revision0.id } })
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    await screen.findByText('new-success')
    await act(async () => older.reject(new Error('old failure')))
    expect(screen.getByText('new-success')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it.each(['project', 'workspace', 'unmount'])('ignores rejected history and comparison completions after %s retirement', async scope => {
    for (const phase of ['history', 'comparison']) {
      const { queries, content } = reviewSetup()
      const late = deferred<never>()
      if (phase === 'history') vi.spyOn(queries, 'listRevisions').mockImplementationOnce(() => late.promise)
      else vi.spyOn(queries, 'compare').mockImplementationOnce(() => late.promise)
      const view = render(content())
      if (phase === 'comparison') {
        await choosePair()
        fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
      }
      if (scope === 'unmount') view.unmount()
      else {
        view.rerender(scope === 'project' ? content('workspace-1', 'project-2') : content('workspace-2', 'project-1'))
        await choosePair()
      }
      await act(async () => late.reject(new Error('retired failure')))
      expect(screen.queryByRole('alert')).toBeNull()
      if (scope !== 'unmount') expect(disabled('Compare revisions')).toBe(false)
      view.unmount()
    }
  })

  it('keeps filter focus and complete entities without requesting again', async () => {
    const { queries, content } = reviewSetup()
    queries.comparisonResult = { ok: true, value: { ...comparison(revision0, revision1, 'unused'), entityChanges: Array.from({ length: 125 }, (_, i) => ({ kind: 'CLIP', entityId: `entity-${i}`, action: i % 2 ? 'ADDED' : 'MODIFIED' })) } }
    const compare = vi.spyOn(queries, 'compare')
    render(content())
    await choosePair()
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
    await screen.findByText('entity-124')
    expect(screen.getAllByRole('listitem')).toHaveLength(125)
    const filter = screen.getByLabelText('Action')
    filter.focus()
    fireEvent.change(filter, { target: { value: 'ADDED' } })
    expect(document.activeElement).toBe(filter)
    expect(screen.queryByText('entity-124')).toBeNull()
    expect(compare).toHaveBeenCalledTimes(1)
  })

  it('localizes Review controls, states, tabs and technical labels in Chinese with opaque diagnostics', async () => {
    const { queries, content } = reviewSetup()
    queries.comparisonResult = { ok: false, code: 'AUTHORIZATION_DENIED', message: 'opaque denial', details: ['opaque detail'], retryable: false }
    render(<LocalizationProvider initialLocale="zh-CN">{content()}</LocalizationProvider>)
    await screen.findAllByRole('option', { name: /Base/ })
    const tab = screen.getByRole('tab', { name: '语义更改' })
    const panel = screen.getByRole('tabpanel', { name: '语义更改' })
    expect(tab.getAttribute('aria-controls')).toBe(panel.id)
    expect(panel.getAttribute('aria-labelledby')).toBe(tab.id)
    fireEvent.change(screen.getByLabelText('起始修订'), { target: { value: revision0.id } })
    fireEvent.change(screen.getByLabelText('目标修订'), { target: { value: revision1.id } })
    fireEvent.click(screen.getByRole('button', { name: '比较修订' }))
    expect((await screen.findByRole('alert')).textContent).toContain('没有权限')
    expect(screen.getByText('比较技术详情')).toBeTruthy()
    expect(screen.getByText('opaque detail').closest('details')).toBeTruthy()
    fireEvent.click(screen.getByRole('tab', { name: '讨论' }))
    expect(screen.getByText('讨论暂不可用')).toBeTruthy()
    expect(screen.queryByText(/bounded product slice/)).toBeNull()
  })
})


it.each(['history', 'comparison'])('retires successful %s completion on unmount without reviving a later session', async phase => {
  const { queries, content } = reviewSetup()
  const oldHistory = deferred<GatewayResult<readonly RevisionListEntry[]>>()
  const oldComparison = deferred<GatewayResult<RevisionComparison>>()
  if (phase === 'history') vi.spyOn(queries, 'listRevisions').mockImplementationOnce(() => oldHistory.promise)
  else vi.spyOn(queries, 'compare').mockImplementationOnce(() => oldComparison.promise)
  const view = render(content())
  if (phase === 'comparison') {
    await choosePair()
    fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
  }
  view.unmount()
  render(content())
  await choosePair()
  await act(async () => {
    oldHistory.resolve({ ok: true, value: [] })
    oldComparison.resolve({ ok: true, value: comparison(revision0, revision1, 'retired-clip') })
  })
  expect(screen.queryByText('retired-clip')).toBeNull()
  expect(screen.queryByText('No revisions available')).toBeNull()
  expect(screen.queryByRole('alert')).toBeNull()
  expect(disabled('Compare revisions')).toBe(false)
})

const failureCopy: Array<[GatewayFailureCode, string, string]> = [
  ['STALE_BASE_REVISION', 'starting revision is no longer current', '起始修订已不是当前版本'],
  ['STALE_TARGET_REF', 'target reference has changed', '目标引用已更改'],
  ['PLAN_CHANGED', 'server plan has changed', '服务器计划已更改'],
  ['AUTHORIZATION_DENIED', 'do not have permission', '没有权限'],
  ['AUTHORIZATION_CONTEXT_MISMATCH', 'authorization context does not match', '授权上下文与此请求不匹配'],
  ['TENANT_CONTEXT_MISMATCH', 'tenant context does not match', '租户上下文与此请求不匹配'],
  ['UNAUTHENTICATED', 'Sign in', '请登录'],
  ['VALIDATION', 'could not be validated', '无法验证'],
  ['UNSUPPORTED', 'does not support', '不支持'],
  ['CONFLICT', 'conflict prevented', '冲突阻止'],
  ['NOT_FOUND', 'revisions or project are not available', '修订或项目不可用'],
  ['UNAVAILABLE', 'temporarily unavailable', '暂时不可用'],
  ['NETWORK', 'network problem', '网络问题'],
  ['UNKNOWN', 'unrecognized reason', '未知原因'],
]

it.each(failureCopy)('explains actual %s failure in both locales without translating server diagnostics', async (code, en, zh) => {
  for (const locale of ['en', 'zh-CN'] as const) {
    const { queries, content } = reviewSetup()
    queries.historyResult = { ok: false, code, message: 'server:opaque', details: ['server:detail'], retryable: false }
    const view = render(<LocalizationProvider initialLocale={locale}>{content()}</LocalizationProvider>)
    expect((await screen.findByRole('alert')).textContent).toContain(locale === 'en' ? en : zh)
    expect(screen.getByText('server:opaque').closest('details')).toBeTruthy()
    expect(screen.getByText('server:detail').closest('details')).toBeTruthy()
    expect(screen.getByText(code).closest('details')).toBeTruthy()
    view.unmount()
  }
})


it.each([
  { supported: false, assetsAdded: 0, title: 'Summary unavailable' },
  { supported: true, assetsAdded: 0, title: 'No changes reported' },
  { supported: true, assetsAdded: 3, title: 'No entity details returned' },
])('keeps loaded status distinct from summary conclusions ($supported, $assetsAdded)', async ({ supported, assetsAdded, title }) => {
  const { queries, content } = reviewSetup()
  queries.comparisonResult = { ok: true, value: { ...comparison(revision0, revision1, 'unused'), summary: { ...summary, supported, assetsAdded }, entityChanges: [] } }
  render(content())
  await choosePair()
  fireEvent.click(screen.getByRole('button', { name: 'Compare revisions' }))
  await screen.findByText('Comparison loaded; no entity details were returned.')
  expect(screen.getByText(title)).toBeTruthy()
  if (!supported || assetsAdded) expect(screen.queryByText('No changes reported')).toBeNull()
  expect(screen.queryByText('No matching entity changes')).toBeNull()
})


it.each(['en', 'zh-CN'] as const)('shows readable selected, requested and result direction with disclosed full IDs in %s', async locale => {
  const { queries, content } = reviewSetup()
  const from = { ...revision1, id: revisionId(`from-${'a'.repeat(59)}`), revisionNumber: 84, message: 'Full projected message '.repeat(20) }
  const to = { ...revision0, id: revisionId(`to-${'b'.repeat(61)}`), revisionNumber: 12 }
  queries.historyResult = { ok: true, value: [from, to] }
  const pending = deferred<GatewayResult<RevisionComparison>>()
  const compare = vi.spyOn(queries, 'compare').mockImplementationOnce(() => pending.promise)
  render(<LocalizationProvider initialLocale={locale}>{content()}</LocalizationProvider>)
  const zh = locale === 'zh-CN'
  await screen.findAllByRole('option', { name: new RegExp(from.id) })
  expect(screen.getAllByRole('option', { name: new RegExp(from.id) })[0].textContent).toContain(from.message)
  fireEvent.change(screen.getByLabelText(zh ? '起始修订' : 'From revision'), { target: { value: from.id } })
  fireEvent.change(screen.getByLabelText(zh ? '目标修订' : 'To revision'), { target: { value: to.id } })
  const assertPair = (label: string) => {
    const pair = screen.getByLabelText(label)
    expect(pair.textContent).toContain(zh ? '起始修订: 修订 84 → 目标修订: 修订 12' : 'From revision: Revision 84 → To revision: Revision 12')
    expect(pair.textContent).not.toContain(from.id)
    expect(pair.textContent).not.toContain(to.id)
    const details = document.getElementById(pair.getAttribute('aria-details') ?? '') as HTMLDetailsElement
    expect(details?.tagName).toBe('DETAILS')
    expect(details.open).toBe(false)
    expect(details.querySelector('summary')?.textContent).toBe(zh ? '修订标识' : 'Revision IDs')
    expect(Array.from(details.querySelectorAll('code'), code => code.textContent)).toEqual([from.id, to.id])
    fireEvent.click(details.querySelector('summary')!)
    expect(details.open).toBe(true)
    fireEvent.click(details.querySelector('summary')!)
  }
  assertPair(zh ? '已选修订对' : 'Selected revision pair')
  expect(compare).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: zh ? '比较修订' : 'Compare revisions' }))
  assertPair(zh ? '正在请求的修订对' : 'Requested revision pair')
  expect(compare).toHaveBeenCalledExactlyOnceWith(projectId('project-1'), from.id, to.id)
  await act(async () => pending.resolve({ ok: true, value: comparison(from, to, 'readable-pair-result') }))
  assertPair(zh ? '服务器结果修订对' : 'Server result revision pair')
})
