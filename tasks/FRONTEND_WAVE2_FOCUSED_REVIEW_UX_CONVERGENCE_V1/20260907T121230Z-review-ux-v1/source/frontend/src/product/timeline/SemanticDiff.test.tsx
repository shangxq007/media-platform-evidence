import { LocalizationProvider } from '../../localization'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { RevisionComparison, RevisionListEntry } from './gateways'
import { revisionId } from './types'
import { SemanticDiff } from './SemanticDiff'

const from: RevisionListEntry = { id: revisionId('revision-R0'), revisionNumber: 1, parentRevisionId: null, source: 'USER', message: null, labels: [], authorUserId: null, createdAt: '2026-01-01', isMerge: false }
const comparison: RevisionComparison = {
  fromRevision: from,
  toRevision: { ...from, id: revisionId('revision-R1'), revisionNumber: 2, parentRevisionId: from.id },
  summary: { supported: true, tracksAdded: 0, tracksRemoved: 0, tracksModified: 1, clipsAdded: 1, clipsRemoved: 0, clipsModified: 0, assetsAdded: 1, assetsRemoved: 0 },
  entityChanges: [
    { kind: 'CLIP', entityId: 'clip-1', action: 'added' },
    { kind: 'TRACK', entityId: 'video-1', action: 'modified' },
  ],
}

describe('server semantic diff presentation', () => {
  it('only formats, groups, and filters server entities', () => {
    const onFilter = vi.fn()
    render(<SemanticDiff comparison={comparison} actionFilter="ALL" onActionFilterChange={onFilter} />)
    expect(screen.getByText('clip-1')).toBeTruthy()
    expect(screen.getByText('video-1')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Action'), { target: { value: 'added' } })
    expect(onFilter).toHaveBeenCalledWith('added')
  })
})


describe('SemanticDiff truthful empty and localized projections', () => {
  it('shows supplied asset counters and exact ordered server identities', () => {
    render(<SemanticDiff comparison={comparison} actionFilter="ALL" onActionFilterChange={vi.fn()} />)
    expect(screen.getByText('Assets added / removed').parentElement?.textContent).toContain('1 / 0')
    const pair = screen.getByLabelText('Server result revision pair')
    expect(pair.textContent).toContain('From revision: Revision 1 → To revision: Revision 2')
    expect(pair.textContent).not.toContain('revision-R0')
    const details = document.getElementById(pair.getAttribute('aria-details') ?? '') as HTMLDetailsElement
    expect(details?.tagName).toBe('DETAILS')
    expect(details.open).toBe(false)
    expect(Array.from(details.querySelectorAll('code'), code => code.textContent)).toEqual(['revision-R0', 'revision-R1'])
  })

  it.each([
    { supported: false, nonzero: false, title: 'Summary unavailable', absent: 'No changes reported' },
    { supported: true, nonzero: false, title: 'No changes reported', absent: 'No matching entity changes' },
    { supported: true, nonzero: true, title: 'No entity details returned', absent: 'No changes reported' },
  ])('distinguishes summary support=$supported, nonzero=$nonzero with no entities', ({ supported, nonzero, title, absent }) => {
    const summary = { supported, tracksAdded: 0, tracksRemoved: 0, tracksModified: 0, clipsAdded: 0, clipsRemoved: 0, clipsModified: 0, assetsAdded: nonzero ? 2 : 0, assetsRemoved: 0 }
    render(<SemanticDiff comparison={{ ...comparison, summary, entityChanges: [] }} actionFilter="ALL" onActionFilterChange={vi.fn()} />)
    expect(screen.getByText(title)).toBeTruthy()
    expect(screen.queryByText(absent)).toBeNull()
    if (!supported) expect(screen.queryByText('Tracks added / removed / changed')).toBeNull()
  })

  it('distinguishes a filtered empty list from server empty and preserves unknown opaque values', () => {
    const input = { ...comparison, entityChanges: [{ kind: 'SERVER_KIND_甲', action: 'server-action-甲', entityId: 'entity-甲' }] }
    const view = render(<SemanticDiff comparison={input} actionFilter="ADDED" onActionFilterChange={vi.fn()} />)
    expect(screen.getByText('No matching entity changes')).toBeTruthy()
    expect(screen.queryByText('No changes reported')).toBeNull()
    view.rerender(<SemanticDiff comparison={input} actionFilter="ALL" onActionFilterChange={vi.fn()} />)
    expect(screen.getByText('SERVER_KIND_甲')).toBeTruthy()
    expect(screen.getByRole('option', { name: 'server-action-甲' }).getAttribute('value')).toBe('server-action-甲')
    expect(screen.getByText('entity-甲')).toBeTruthy()
  })

  it('shows entity details even when summary is unsupported', () => {
    render(<SemanticDiff comparison={{ ...comparison, summary: { ...comparison.summary, supported: false } }} actionFilter="ALL" onActionFilterChange={vi.fn()} />)
    expect(screen.getByText('Summary unavailable')).toBeTruthy()
    expect(screen.getByText('clip-1')).toBeTruthy()
    expect(screen.queryByText('No changes reported')).toBeNull()
  })

  it('localizes Chinese labels while keeping action values and server IDs unchanged', () => {
    const change = vi.fn()
    render(<LocalizationProvider initialLocale="zh-CN"><SemanticDiff comparison={comparison} actionFilter="ALL" onActionFilterChange={change} /></LocalizationProvider>)
    expect(screen.getByText('新增 / 移除素材')).toBeTruthy()
    expect(screen.getByRole('option', { name: '新增' }).getAttribute('value')).toBe('added')
    fireEvent.change(screen.getByLabelText('操作'), { target: { value: 'added' } })
    expect(change).toHaveBeenCalledWith('added')
    expect(screen.getByText('clip-1')).toBeTruthy()
  })
})
