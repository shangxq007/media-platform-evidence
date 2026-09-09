import { StrictMode, useLayoutEffect } from 'react'
import { act, fireEvent, render, screen, within, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { SelectionProvider, useInteractionStore } from '../../interaction/SelectionContext'
import { LocalizationProvider } from '../../localization'
import { PublicationWorkspace } from './PublicationWorkspace'
import { LIST_KEY } from './types'
import type { InteractionStore } from '../../interaction/model'
import type { PublicationRequest, PublicationSource } from './types'
import { receipt, source, grant } from './testing'
import { readFileSync } from 'node:fs'

function Probe({ capture }: { capture?: (store: InteractionStore) => void }) {
  const store = useInteractionStore(); useLayoutEffect(() => { capture?.(store) }, [store, capture]); return null
}
function host(value?: PublicationSource, owner = 'owner', capture?: (store: InteractionStore) => void) {
  return <StrictMode><LocalizationProvider initialLocale="en"><SelectionProvider key={owner} scope={{ surfaceId: 'publication', workspaceId: 'w', projectId: 'p' }}><Probe capture={capture} /><PublicationWorkspace workspaceId="w" projectId="p" tenantId="tenant" source={value} now={() => new Date('2024-03-10T12:00:00Z')} /></SelectionProvider></LocalizationProvider></StrictMode>
}
const button = (name: string) => screen.getByRole('button', { name })
async function ready() { await screen.findByRole('button', { name: 'Opening story' }) }

describe('publication workspace discovery and lifecycle', () => {
  it('ordinary entry is not connected, without fixtures or publish controls', () => {
    render(host())
    expect(screen.getByText('Publication source not connected')).toBeTruthy()
    expect(screen.queryByText(/Opening story|isolated|fixture|harness/i)).toBeNull()
    expect(document.querySelector('a[href],video,audio')).toBeNull()
    expect(screen.queryByRole('button', { name: /publish|schedule|send/i })).toBeNull()
  })
  it('distinguishes loading, complete empty, partial empty, error, retry and restricted receipts', async () => {
    let resolve!: (v: unknown) => void
    const read = vi.fn((_r: PublicationRequest) => new Promise<unknown>(done => { resolve = done }))
    render(host(source(read)))
    expect(screen.getByText('Loading publications…')).toBeTruthy()
    await act(async () => resolve(receipt(read.mock.calls[read.mock.calls.length - 1][0], { plans: [], attempts: [], artifacts: [], externalPublications: [] })))
    expect(screen.getByText('No publications in this Project')).toBeTruthy()
    read.mockImplementation(async r => receipt(r, { plans: [], attempts: [], artifacts: [], externalPublications: [], completeness: 'partial' }))
    fireEvent.click(button('Refresh publications'))
    await screen.findByText('No publications in the supplied partial scope')
    read.mockRejectedValue(new Error('SECRET_TRANSPORT'))
    fireEvent.click(button('Refresh publications'))
    await screen.findByText('Could not load publications')
    expect(document.body.innerHTML).not.toContain('SECRET_TRANSPORT')
    read.mockImplementation(async r => ({ ...r, status: 'restricted' }))
    fireEvent.click(button('Retry publications'))
    await screen.findByText('Publication access unavailable')
  })
  it('shares content/account/status filters between list and calendar, with reset and same-platform accounts', async () => {
    render(host(source())); await ready()
    fireEvent.change(screen.getByLabelText('Account'), { target: { value: 'b' } })
    expect(screen.queryByRole('button', { name: 'Opening story' })).toBeNull()
    expect(button('Second story')).toBeTruthy()
    fireEvent.click(button('Calendar'))
    expect(screen.getByLabelText('Account').getAttribute('value') ?? (screen.getByLabelText('Account') as HTMLSelectElement).value).toBe('b')
    expect(screen.queryByRole('button', { name: 'Opening story' })).toBeNull()
    fireEvent.change(screen.getByLabelText('Search supplied publications'), { target: { value: 'no match' } })
    expect(screen.getByText('No publications match these filters')).toBeTruthy()
    fireEvent.click(button('Reset filters'))
    fireEvent.click(button('List'))
    expect(button('Opening story')).toBeTruthy(); expect(button('Second story')).toBeTruthy()
  })
  it('inspects explicit relationships and timestamps then closes to the focused row with context preserved', async () => {
    render(host(source())); await ready()
    const row = button('Opening story'); row.focus(); fireEvent.click(row)
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByText('copy-v1')).toBeTruthy()
    expect(within(dialog).getByText('output')).toBeTruthy()
    expect(within(dialog).getByText('try1')).toBeTruthy(); expect(within(dialog).getByText('try2')).toBeTruthy()
    expect(within(dialog).getByText('external1')).toBeTruthy()
    expect(dialog.querySelector('a[href]')).toBeNull()
    fireEvent.keyDown(dialog, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(row)
    expect((screen.getByLabelText('Search supplied publications') as HTMLInputElement).value).toBe('')
  })
  it('keeps unscheduled and indeterminate separate, month overflow opens a complete selected-day agenda', async () => {
    const read = async (r: PublicationRequest) => {
      const raw = receipt(r); return { ...raw, plans: [...raw.plans, ...['three', 'four'].map(id => ({ ...raw.plans[0], id })), { ...raw.plans[0], id: 'unscheduled', timeField: 'unscheduled', scheduledAt: undefined }, { ...raw.plans[0], id: 'invalid', scheduledAt: '2024-03-10T12:00:00' }] }
    }
    render(host(source(read))); await ready(); fireEvent.click(button('Calendar'))
    expect(screen.getByRole('region', { name: 'Unscheduled' }).textContent).toContain('unscheduled')
    expect(screen.getByRole('region', { name: 'Indeterminate date' }).textContent).toContain('invalid')
    fireEvent.click(button('2 more · 2024-03-10'))
    expect(within(screen.getByRole('region', { name: 'Selected day agenda' })).getAllByRole('button')).toHaveLength(4)
    fireEvent.click(button('Previous month')); expect(screen.getByText('2024-02')).toBeTruthy()
    fireEvent.click(button('Next month')); expect(screen.getByText('2024-03')).toBeTruthy()
    fireEvent.click(button('Today')); expect(screen.getByText('Selected day: 2024-03-10')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Display timezone'), { target: { value: 'America/Los_Angeles' } })
    expect(screen.getByText('Display timezone changes presentation only.')).toBeTruthy()
  })
  it('same-context refresh preserves filters, date and scroll but withdraws details without same-ID revival', async () => {
    const s = source(); render(host(s)); await ready()
    fireEvent.change(screen.getByLabelText('Search supplied publications'), { target: { value: 'Opening' } })
    const list = screen.getByRole('region', { name: 'Publication results' }); list.scrollTop = 87
    fireEvent.click(button('Opening story')); fireEvent.click(button('Close publication details'))
    fireEvent.click(button('Refresh publications')); await ready()
    expect((screen.getByLabelText('Search supplied publications') as HTMLInputElement).value).toBe('Opening')
    expect(list.scrollTop).toBe(87); expect(screen.queryByRole('dialog')).toBeNull()
  })
  it('aborts old reads on source/session/owner replacement and rejects late success with reused IDs', async () => {
    const pending: { r: PublicationRequest; signal: AbortSignal; resolve: (v: unknown) => void }[] = []
    const s = source((r, signal) => new Promise(resolve => pending.push({ r, signal, resolve })))
    const view = render(host(s)); expect(pending.length).toBeGreaterThan(0)
    const next = source(); next.scope = { ...next.scope, sessionId: 'new' }
    view.rerender(host(next)); await ready()
    expect(pending.every(p => p.signal.aborted)).toBe(true)
    fireEvent.click(button('Opening story')); view.rerender(host(next, 'replacement')); await ready()
    expect(screen.queryByRole('dialog')).toBeNull()
    await act(async () => pending.forEach(p => p.resolve(receipt(p.r, { plans: [{ ...receipt().plans[0], title: 'OLD_SECRET' }] }))))
    expect(document.body.innerHTML).not.toContain('OLD_SECRET')
  })
  it('access revocation removes protected values from the entire DOM and no self-allowed source revives them', async () => {
    const s = source(); const view = render(host(s)); await ready(); fireEvent.click(button('Opening story'))
    view.rerender(host({ ...s, access: {} })); await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(document.body.innerHTML).not.toMatch(/Opening story|copy-v1|Master|Delivery rejected|SECRET_URL/)
    expect(screen.getByText('Publication access unavailable')).toBeTruthy()
  })
})

function retained<T>(element: HTMLElement, name: string): T {
  const key = Object.keys(element).find(key => key.startsWith('__reactProps$'))!
  return (element as unknown as Record<string, Record<string, T>>)[key][name]
}
it('rejects actual old date/filter/view/open/refresh/dismiss callbacks after source or Selection ownership changes', async () => {
  let store!: InteractionStore
  const s = source(); const view = render(host(s, 'owner', value => { store = value })); await ready()
  const oldRow = button('Opening story')
  const open = retained<(e: { currentTarget: HTMLElement }) => void>(oldRow, 'onClick')
  const filter = retained<(e: { target: { value: string } }) => void>(screen.getByLabelText('Search supplied publications'), 'onChange')
  const refresh = retained<() => void>(button('Refresh publications'), 'onClick')
  const viewChange = retained<() => void>(button('Calendar'), 'onClick')
  fireEvent.click(button('Calendar'))
  const date = retained<() => void>(button('Previous month'), 'onClick')
  fireEvent.click(button('List')); fireEvent.click(button('Opening story'))
  const dismiss = retained<() => void>(button('Close publication details'), 'onClick')
  const next = { ...s, scope: { ...s.scope, principalId: 'new-person' } }
  view.rerender(host(next, 'owner', value => { store = value })); await ready()
  fireEvent.click(button('Opening story'))
  const dialog = screen.getByRole('dialog')
  act(() => { filter({ target: { value: 'OLD_FILTER' } }); refresh(); viewChange(); date(); open({ currentTarget: oldRow }); dismiss() })
  expect(screen.getByRole('dialog')).toBe(dialog)
  expect((screen.getByLabelText('Search supplied publications') as HTMLInputElement).value).toBe('')
  fireEvent.click(button('Close publication details')); fireEvent.click(button('Calendar'))
  expect(screen.getByText('2024-03')).toBeTruthy()
  act(() => store.retireSelectionOwner('document'))
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(document.body.innerHTML).not.toContain('Opening story')
  act(() => { refresh(); open({ currentTarget: oldRow }) })
  expect(document.body.innerHTML).not.toContain('Opening story')
})
it('a retained dismissal cannot close a later dialog occurrence with the same plan ID', async () => {
  render(host(source())); await ready(); fireEvent.click(button('Opening story'))
  const dismiss = retained<() => void>(button('Close publication details'), 'onClick')
  fireEvent.click(button('Close publication details')); fireEvent.click(button('Opening story'))
  act(dismiss)
  expect(screen.getByRole('dialog')).toBeTruthy()
})
it('equal access observation changes preserve browsing; real item grants, adapter and source owner changes retire it', async () => {
  const s = source(); const view = render(host(s)); await ready()
  fireEvent.change(screen.getByLabelText('Search supplied publications'), { target: { value: 'Opening' } })
  fireEvent.click(button('Opening story')); const dialog = screen.getByRole('dialog')
  view.rerender(host({ ...s, access: { ...s.access, [LIST_KEY]: { ...grant(LIST_KEY), observedAt: 'new observation', explanation: 'updated explanation' } } }))
  expect(screen.getByRole('dialog')).toBe(dialog)
  view.rerender(host({ ...s, access: { [LIST_KEY]: grant(LIST_KEY) } }))
  await screen.findByRole('button', { name: 'one' })
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(document.body.innerHTML).not.toMatch(/Opening story|Permitted summary|copy-v1|output|Master|Delivery rejected/)
  view.rerender(host({ ...s, owner: {} })); await ready()
  expect((screen.getByLabelText('Search supplied publications') as HTMLInputElement).value).toBe('')
  fireEvent.click(button('Opening story'))
  view.rerender(host({ ...s, adapter: { ...s.adapter } })); await ready()
  expect(screen.queryByRole('dialog')).toBeNull()
})
it('refresh disappearance clears shared Selection and focuses a safe region; invalid/error data never revives it', async () => {
  let store!: InteractionStore
  const read = vi.fn(async (r: PublicationRequest) => receipt(r))
  render(host(source(read), 'owner', value => { store = value })); await ready()
  fireEvent.click(button('Opening story')); fireEvent.click(button('Close publication details'))
  read.mockImplementation(async r => receipt(r, { plans: [], attempts: [], artifacts: [], externalPublications: [] }))
  fireEvent.click(button('Refresh publications')); await screen.findByText('No publications in this Project')
  expect(store.getSnapshot().selectedObjects).toEqual([])
  expect(document.activeElement).toBe(screen.getByRole('region', { name: 'Publication workspace' }))
  read.mockImplementation(async r => receipt({ ...r, requestId: 'old-request' }))
  fireEvent.click(button('Refresh publications')); await screen.findByText('Publication response could not be verified')
  expect(screen.queryByRole('dialog')).toBeNull()
  read.mockImplementation(async r => receipt(r))
  fireEvent.click(button('Retry publications')); await ready()
  expect(store.getSnapshot().selectedObjects).toEqual([])
  expect(screen.queryByRole('dialog')).toBeNull()
})
it('display timezone crosses a month boundary without modifying source schedule; view/refresh preserve date and filters', async () => {
  const read = vi.fn(async (r: PublicationRequest) => {
    const raw = receipt(r); raw.plans[0].scheduledAt = '2024-03-01T00:30:00Z'; return raw
  })
  render(host(source(read))); await ready(); fireEvent.click(button('Calendar'))
  fireEvent.change(screen.getByLabelText('Display timezone'), { target: { value: 'America/Los_Angeles' } })
  fireEvent.click(button('Previous month')); fireEvent.click(button('2024-02-29'))
  const agenda = screen.getByRole('region', { name: 'Selected day agenda' })
  expect(within(agenda).getByRole('button', { name: 'Opening story' })).toBeTruthy()
  fireEvent.change(screen.getByLabelText('Account'), { target: { value: 'a' } })
  fireEvent.click(button('List')); fireEvent.click(button('Calendar')); fireEvent.click(button('Refresh publications'))
  await within(screen.getByRole('region', { name: 'Selected day agenda' })).findByRole('button', { name: 'Opening story' })
  expect(screen.getByText('Selected day: 2024-02-29')).toBeTruthy()
  expect((screen.getByLabelText('Display timezone') as HTMLSelectElement).value).toBe('America/Los_Angeles')
  expect((screen.getByLabelText('Account') as HTMLSelectElement).value).toBe('a')
  for (const [r] of read.mock.calls) expect(r.query).toEqual({ kind: 'project-publication-snapshot', limit: 200 })
  fireEvent.click(within(screen.getByRole('region', { name: 'Selected day agenda' })).getByRole('button', { name: 'Opening story' }))
  expect(screen.getByRole('dialog').textContent).toContain('2024-03-01T00:30:00Z')
})
it('all native form controls are non-submitting, details contain focus and long permitted titles remain readable', async () => {
  const title = '完整标题'.repeat(200)
  const read = async (r: PublicationRequest) => { const raw = receipt(r); raw.plans[0].title = title; return raw }
  const submit = vi.fn((e: React.FormEvent) => e.preventDefault())
  render(<form onSubmit={submit}>{host(source(read))}</form>)
  await screen.findByRole('button', { name: title }); fireEvent.click(button(title))
  const dialog = screen.getByRole('dialog'), close = within(dialog).getByRole('button', { name: 'Close publication details' })
  close.focus(); fireEvent.keyDown(dialog, { key: 'Tab' }); expect(document.activeElement).toBe(close)
  fireEvent.keyDown(dialog, { key: 'Tab', shiftKey: true }); expect(document.activeElement).toBe(close)
  expect(within(dialog).getByText(title)).toBeTruthy()
  expect([...document.querySelectorAll('button')].every(b => b.type === 'button')).toBe(true)
  expect(submit).not.toHaveBeenCalled()
})

// Resolve inherited/transparent colors explicitly: happy-dom retains CSS `inherit`.
function effectiveColor(element: Element, property: 'color' | 'backgroundColor'): string {
  const value = getComputedStyle(element)[property]
  if (value && !['inherit', 'transparent', 'rgba(0, 0, 0, 0)'].includes(value)) return value
  if (element.parentElement) return effectiveColor(element.parentElement, property)
  throw new Error(`No effective ${property}`)
}
function luminance(color: string): number {
  const hex = color === 'white' ? '#ffffff' : color
  const channels = /^#[0-9a-f]{6}$/i.test(hex)
    ? [1, 3, 5].map(start => parseInt(hex.slice(start, start + 2), 16))
    : color.match(/[\d.]+/g)?.slice(0, 3).map(Number)
  if (!channels || channels.length !== 3) throw new Error(`Unsupported color: ${color}`)
  const linear = channels.map(channel => { const c = channel / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 })
  return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722
}
it.each(['dark', 'light'])('Publication select values and options have readable contrast in %s theme', async theme => {
  const style = document.createElement('style')
  style.textContent = ['src/styles/tokens.css', 'src/styles/foundation.css', 'src/product/publication/publication.css'].map(path => readFileSync(path, 'utf8')).join('\n')
  document.head.append(style)
  const previousTheme = document.documentElement.getAttribute('data-theme')
  document.documentElement.setAttribute('data-theme', theme)
  try {
    render(<div className="ff-root">{host(source())}</div>); await ready()
    const selects = screen.getAllByRole('combobox')
    expect(selects).toHaveLength(4)
    const colors = selects.flatMap(select => [select, ...select.querySelectorAll('option')]).map(element => {
      const foreground = effectiveColor(element, 'color'), background = effectiveColor(element, 'backgroundColor')
      const values = [luminance(foreground), luminance(background)].sort((a, b) => a - b)
      return { element: element.tagName, value: (element as HTMLSelectElement).value, foreground, background, contrast: (values[1] + 0.05) / (values[0] + 0.05) }
    })
    console.info('Publication computed style evidence (happy-dom; inherited colors resolved)', JSON.stringify({ theme, colors }))
    for (const color of colors) expect(color.contrast).toBeGreaterThanOrEqual(4.5)
  } finally {
    style.remove()
    if (previousTheme === null) document.documentElement.removeAttribute('data-theme')
    else document.documentElement.setAttribute('data-theme', previousTheme)
  }
})
it('uses the supplied Chinese Publication search translation for its visible placeholder', async () => {
  render(<LocalizationProvider initialLocale="zh-CN"><SelectionProvider scope={{ surfaceId: 'publication', workspaceId: 'w', projectId: 'p' }}><PublicationWorkspace workspaceId="w" projectId="p" tenantId="tenant" source={source()} /></SelectionProvider></LocalizationProvider>)
  await ready()
  expect(screen.getByRole('searchbox', { name: '搜索已提供的发布内容' }).getAttribute('placeholder')).toBe('搜索已提供的发布内容')
})
