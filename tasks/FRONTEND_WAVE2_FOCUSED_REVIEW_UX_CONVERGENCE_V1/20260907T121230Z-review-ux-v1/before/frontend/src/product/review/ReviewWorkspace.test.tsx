import { SelectionProvider } from '../../interaction/SelectionContext'
import { AgentLauncher, AgentShell, SelectionInspector } from '../../interaction/InteractionShell'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { platformClient } from '../../foundation/platformClient'
import { ProjectContextProvider } from '../../foundation/projectContext'
import type { GatewayResult, RevisionComparison, RevisionDetail, RevisionListEntry } from '../timeline/gateways'
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
    render(<QueryClientProvider client={client}><ProjectContextProvider workspaceId="workspace-1" projectId="project-1"><SelectionProvider scope={{ surfaceId: 'review', workspaceId: "workspace-1", projectId: "project-1" }}><ReviewWorkspace queryGateway={queries} /><SelectionInspector /><AgentLauncher /><AgentShell /></SelectionProvider></ProjectContextProvider></QueryClientProvider>)

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
    render(<QueryClientProvider client={client}><ProjectContextProvider workspaceId="workspace-1" projectId="project-1"><SelectionProvider scope={{ surfaceId: 'review', workspaceId: "workspace-1", projectId: "project-1" }}><ReviewWorkspace queryGateway={queries} /><SelectionInspector /><AgentLauncher /><AgentShell /></SelectionProvider></ProjectContextProvider></QueryClientProvider>)

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

function reviewSetup() {
  vi.spyOn(platformClient.workspace, 'getHome').mockResolvedValue({ workspace: { id: 'workspace-1', name: 'Editorial' }, tenantId: 'tenant-1', recentProjects: [] })
  const queries = new ScriptedTimelineQueryGateway({ head: { ok: true, value: head }, history: { ok: true, value: [revision0, revision1] }, detail: { ok: true, value: detail }, comparison: { ok: true, value: comparison(revision0, revision1, 'clip-result') } })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const content = (workspaceId = 'workspace-1', projectId = 'project-1') => <QueryClientProvider client={client}><ProjectContextProvider workspaceId={workspaceId} projectId={projectId}><SelectionProvider scope={{ surfaceId: 'review', workspaceId: workspaceId, projectId: projectId }}><ReviewWorkspace queryGateway={queries} /><SelectionInspector /><AgentLauncher /><AgentShell /></SelectionProvider></ProjectContextProvider></QueryClientProvider>
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
    expect(screen.getByText(/UNAVAILABLE/).closest('details')).toBeTruthy()
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
    expect(spy).toHaveBeenCalledTimes(2)
    await act(async () => pending.reject(new Error('offline')))
    expect(screen.getByRole('alert').textContent).toContain('Retry comparison')
    expect(screen.queryByText('clip-result')).toBeNull()
    spy.mockResolvedValueOnce(mockFailure('UNAVAILABLE'))
    fireEvent.click(screen.getByRole('button', { name: 'Retry comparison' }))
    await waitFor(() => expect(screen.getByText(/UNAVAILABLE/).closest('details')).toBeTruthy())
    expect(screen.getByRole('alert').textContent).toContain('Retry comparison')
    spy.mockResolvedValueOnce({ ok: true, value: { ...comparison(revision0, revision1, 'unused'), entityChanges: [] } })
    fireEvent.click(screen.getByRole('button', { name: 'Retry comparison' }))
    await screen.findByText('Comparison loaded with no entity changes.')
    expect(screen.getByText('No matching entity changes')).toBeTruthy()
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
