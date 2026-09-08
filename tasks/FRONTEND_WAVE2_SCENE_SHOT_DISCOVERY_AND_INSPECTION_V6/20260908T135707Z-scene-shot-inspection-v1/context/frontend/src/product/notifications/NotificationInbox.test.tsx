import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { NotificationInbox } from './NotificationInbox'
import { createNotificationFixture } from './fixture'
import { LocalizationProvider } from '../../localization'
import { parseList, parseMutation, type InboxSource, type ListRequest, type MutationRequest } from './types'

function deferred<T = unknown>() { let resolve!: (value: T) => void; let reject!: (reason?: unknown) => void; const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail }); return { promise, resolve, reject } }
function setup(source = createNotificationFixture(), locale: 'en' | 'zh-CN' = 'en') {
  const view = render(<LocalizationProvider initialLocale={locale}><NotificationInbox source={source} /></LocalizationProvider>)
  fireEvent.click(screen.getByRole('button', { name: locale === 'en' ? /Notifications/ : /通知/ }))
  return { ...view, source }
}
const row = (title = 'Preview is ready') => screen.getByRole('listitem', { name: title })
const clickRead = () => fireEvent.click(within(row()).getByRole('button', { name: 'Mark as read' }))

describe('notification inbox interaction', () => {
  it('default entry makes no mount query and explains unknown unread/unavailable, with dialog keyboard restoration', () => {
    render(<NotificationInbox />)
    const entry = screen.getByRole('button', { name: 'Notifications · unread count unknown' })
    entry.focus(); fireEvent.click(entry)
    expect(screen.getByText('Notifications are not connected yet. Unread count is unknown.')).toBeTruthy()
    const dialog = screen.getByRole('dialog', { name: 'Notifications' })
    const close = within(dialog).getByRole('button', { name: 'Close notifications' })
    expect(document.activeElement).toBe(close)
    fireEvent.keyDown(close, { key: 'Tab', shiftKey: true })
    expect(dialog.contains(document.activeElement)).toBe(true)
    fireEvent.keyDown(dialog, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(entry)
  })
  it('opens full text separately from read and related actions; renders unknown types and invalid times neutrally', async () => {
    const source = createNotificationFixture()
    const read = vi.spyOn(source.adapter, 'markRead')
    setup(source)
    fireEvent.click(await screen.findByRole('button', { name: 'Read notification: Preview is ready' }))
    expect(screen.getByRole('region', { name: 'Notification detail' }).querySelector('p')?.textContent).toBe('A simulated preview is ready.\nNo media was rendered.')
    expect(read).not.toHaveBeenCalled()
    expect(within(row()).getByText('Unread')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Read notification: <img src=x onerror=alert(1)>' }))
    expect(screen.getByText('Original opaque text 原文')).toBeTruthy()
    expect(document.querySelector('.ff-notification-inbox img')).toBeNull()
    expect(screen.getAllByText('Other notification').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Time unavailable').length).toBeGreaterThan(0)
    expect(screen.getByText('This related destination is not supported yet.')).toBeTruthy()
  })
  it('reports partial loaded items separately from the global count and read-all scope', async () => {
    setup(createNotificationFixture({ limit: 1 }))
    await screen.findByRole('listitem')
    expect(screen.getByRole('button', { name: 'Notifications · 2 unread in inbox' })).toBeTruthy()
    expect(screen.getByText('Showing a limited snapshot. More notifications may exist.')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Mark entire inbox as read' })).toBeTruthy()
  })
  it('requires confirmed reads, suppresses duplicate and read-all overlap synchronously, then re-queries', async () => {
    const source = createNotificationFixture(); const pending = deferred()
    const realRead = source.adapter.markRead!
    let request!: MutationRequest
    const read = vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    const all = vi.spyOn(source.adapter, 'markAllRead')
    const list = vi.spyOn(source.adapter, 'list')
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    const button = within(row()).getByRole('button', { name: 'Mark as read' })
    act(() => { button.click(); button.click(); screen.getByRole('button', { name: 'Mark entire inbox as read' }).click() })
    expect(read).toHaveBeenCalledTimes(1); expect(all).not.toHaveBeenCalled()
    expect(within(row()).getByText('Unread')).toBeTruthy()
    await act(async () => pending.resolve(await realRead(request, new AbortController().signal)))
    await waitFor(() => expect(within(row()).getByText('Read')).toBeTruthy())
    expect(list).toHaveBeenCalledTimes(2)
  })
  it.each([undefined, { error: 'NOT_FOUND' }, 'throw', 'wrong-id', 'denied', 'not-found'])('retains unread on failed or invalid receipt %s without automatic mutation retry', async failure => {
    const source = createNotificationFixture()
    const read = vi.spyOn(source.adapter, 'markRead').mockImplementation(async request => {
      if (failure === 'throw') throw new Error('secret transport detail')
      if (failure === 'wrong-id') return { status: 'ok', ...request, operation: { kind: 'single', id: 'foreign' }, read: true }
      if (failure === 'denied' || failure === 'not-found') return { status: failure, context: request.context, requestId: request.requestId, explanation: 'Opaque failure 原因' }
      return failure
    })
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' }); clickRead()
    await waitFor(() => expect(screen.getByRole('status').textContent).toMatch(/could not|denied|no longer/i))
    expect(within(row()).getByText('Unread')).toBeTruthy(); expect(read).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('secret transport detail')).toBeNull()
  })
  it('never enables page-only read-all and reconciles inbox-wide partial failure', async () => {
    const source = createNotificationFixture({ failReadIds: ['simulated-2'] })
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    fireEvent.click(screen.getByRole('button', { name: 'Mark entire inbox as read' }))
    await waitFor(() => expect(screen.getByRole('status').textContent).toContain('Some notifications could not be marked read.'))
    expect(within(row('<img src=x onerror=alert(1)>')).getByText('Unread')).toBeTruthy()
    expect(within(row()).getByText('Read')).toBeTruthy()
  })
  it('disables unsupported single and read-all operations', async () => {
    const source = createNotificationFixture(); source.adapter.capabilities = { singleRead: false, readAll: 'unsupported' }
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    expect((within(row()).getByRole('button', { name: 'Mark as read' }) as HTMLButtonElement).disabled).toBe(true)
    expect((screen.getByRole('button', { name: 'Mark entire inbox as read' }) as HTMLButtonElement).disabled).toBe(true)
    expect(screen.getByText('Marking the entire inbox read is not supported by this source.')).toBeTruthy()
  })
  it('keeps latest refresh/filter result when older requests finish last', async () => {
    const source = createNotificationFixture(); const original = source.adapter.list
    const pending = deferred(); let first!: ListRequest
    vi.spyOn(source.adapter, 'list').mockImplementationOnce(req => { first = req; return pending.promise })
    setup(source)
    expect(screen.getByRole('status').textContent).toContain('Loading')
    fireEvent.click(screen.getByRole('button', { name: 'Unread' }))
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    await act(async () => pending.resolve(await original(first, new AbortController().signal)))
    expect(screen.getByRole('button', { name: 'Unread', pressed: true })).toBeTruthy()
    expect(screen.queryByRole('listitem', { name: 'Earlier update' })).toBeNull()
  })
  it('does not steal focus on refresh; moves focus only when the focused unread row disappears', async () => {
    setup(); await screen.findByRole('listitem', { name: 'Preview is ready' })
    const refresh = screen.getByRole('button', { name: 'Refresh notifications' }); refresh.focus(); fireEvent.click(refresh)
    await waitFor(() => expect((within(row()).getByRole('button', { name: 'Mark as read' }) as HTMLButtonElement).disabled).toBe(false))
    expect(document.activeElement).toBe(refresh)
    fireEvent.click(screen.getByRole('button', { name: 'Unread' }))
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    const mark = within(row()).getByRole('button', { name: 'Mark as read' }); mark.focus(); fireEvent.click(mark)
    await waitFor(() => expect(screen.queryByRole('listitem', { name: 'Preview is ready' })).toBeNull())
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Unread', pressed: true }))
  })
  it.each(['principalId', 'tenantId', 'sessionId', 'access'] as const)('hides old content synchronously on %s change and drops old mutation completion', async key => {
    const source = createNotificationFixture(); const pending = deferred()
    vi.spyOn(source.adapter, 'markRead').mockReturnValue(pending.promise)
    const view = setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' }); clickRead()
    const next: InboxSource = { ...source, context: { ...source.context, [key]: key === 'access' ? 'denied' : 'changed' } }
    view.rerender(<LocalizationProvider initialLocale="en"><NotificationInbox source={next} /></LocalizationProvider>)
    expect(screen.queryByText('Preview is ready')).toBeNull()
    expect(screen.getByRole('button', { name: /unread count unknown/ })).toBeTruthy()
    await act(async () => pending.resolve({ status: 'ok' }))
    expect(screen.queryByText('Preview is ready')).toBeNull()
  })
  it('invalidates close/unmount work, refetches on reopen and never presents a late read result', async () => {
    const source = createNotificationFixture(); const pending = deferred()
    vi.spyOn(source.adapter, 'markRead').mockReturnValue(pending.promise)
    const view = setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' }); clickRead()
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    await act(async () => pending.resolve({ status: 'ok' }))
    fireEvent.click(screen.getByRole('button', { name: /Notifications/ }))
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    expect(within(row()).getByText('Unread')).toBeTruthy()
    view.unmount()
  })
  it.each(['denied', 'unknown'] as const)('does not query or expose data for %s access', access => {
    const source = createNotificationFixture({ access }); const list = vi.spyOn(source.adapter, 'list')
    setup(source)
    expect(screen.queryByRole('listitem')).toBeNull(); expect(list).not.toHaveBeenCalled()
    expect(screen.getByRole('status').textContent).toMatch(/denied|unknown/)
  })
  it('shows empty/error states without substituting simulation after real failure', async () => {
    const source = createNotificationFixture({ empty: true }); source.adapter.origin = 'real'
    const view = setup(source)
    await screen.findByText('No notifications in this snapshot.')
    vi.spyOn(source.adapter, 'list').mockRejectedValue(new Error('private'))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh notifications' }))
    await waitFor(() => expect(screen.getByRole('status').textContent).toContain('Notifications could not be loaded.'))
    expect(screen.queryByText('Preview is ready')).toBeNull(); expect(screen.queryByText(/SIMULATED/)).toBeNull()
    view.unmount()
  })
  it('persistently discloses simulation and related navigation cannot grant real app permissions', async () => {
    setup(); await screen.findByRole('listitem', { name: 'Preview is ready' })
    fireEvent.click(screen.getByRole('button', { name: 'Read notification: Preview is ready' }))
    expect(screen.getAllByText(/SIMULATED/).length).toBeGreaterThan(0)
    expect(screen.getByRole('link', { name: 'Open related resource' }).getAttribute('href')).toBe('/w/simulated-workspace/projects/simulated-project/overview?notificationFixture=1')
    expect(screen.getByText('The destination checks current resource access. This notification does not grant permission.')).toBeTruthy()
  })
  it('localizes Chinese entry, detail, filters, statuses and simulation while preserving original content', async () => {
    setup(createNotificationFixture(), 'zh-CN')
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    expect(screen.getByRole('dialog', { name: '通知' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '通知 · 收件箱有 2 条未读' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '未读', pressed: false })).toBeTruthy()
    expect(screen.getByRole('button', { name: '将整个收件箱标为已读' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '阅读通知：<img src=x onerror=alert(1)>' }))
    expect(screen.getByText('Original opaque text 原文')).toBeTruthy()
    expect(screen.getAllByText('时间不可用').length).toBeGreaterThan(0)
    expect(screen.getAllByText(/模拟数据/).length).toBeGreaterThan(0)
  })
})

describe('notification request ownership regressions', () => {
  it('keeps the last concurrent refresh and ignores a late error', async () => {
    const source = createNotificationFixture(); setup(source)
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    const old = deferred(); const fresh = deferred(); const original = source.adapter.list
    let latest!: ListRequest
    vi.spyOn(source.adapter, 'list').mockImplementationOnce(() => old.promise).mockImplementationOnce(req => { latest = req; return fresh.promise })
    fireEvent.click(screen.getByRole('button', { name: 'Refresh notifications' }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh notifications' }))
    await act(async () => fresh.resolve(await original(latest, new AbortController().signal)))
    await act(async () => old.resolve({ error: 'NOT_FOUND' }))
    expect(screen.getByRole('status').textContent).toBe('Notification snapshot loaded.')
    expect(screen.getByRole('button', { name: 'Notifications · 2 unread in inbox' })).toBeTruthy()
  })
  it('reconciles a confirmed mutation against the active filter after an overlapping refresh', async () => {
    const source = createNotificationFixture(); const pending = deferred(); const original = source.adapter.markRead!
    let request!: MutationRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' }); clickRead()
    fireEvent.click(screen.getByRole('button', { name: 'Unread' }))
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    fireEvent.click(screen.getByRole('button', { name: 'Refresh notifications' }))
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    await act(async () => pending.resolve(await original(request, new AbortController().signal)))
    await waitFor(() => expect(screen.queryByRole('listitem', { name: 'Preview is ready' })).toBeNull())
    expect(screen.getByRole('button', { name: 'Unread', pressed: true })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Notifications · 1 unread in inbox' })).toBeTruthy()
  })
  it('suppresses single read during read-all and never restores old data on reconciliation failure', async () => {
    const source = createNotificationFixture(); const pending = deferred(); const original = source.adapter.markAllRead!
    let request!: MutationRequest
    vi.spyOn(source.adapter, 'markAllRead').mockImplementation(req => { request = req; return pending.promise })
    const single = vi.spyOn(source.adapter, 'markRead')
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    fireEvent.click(screen.getByRole('button', { name: 'Mark entire inbox as read' })); clickRead()
    expect(single).not.toHaveBeenCalled()
    vi.spyOn(source.adapter, 'list').mockRejectedValue(new Error('unavailable'))
    await act(async () => pending.resolve(await original(request, new AbortController().signal)))
    await waitFor(() => expect(screen.getByRole('status').textContent).toContain('Notifications could not be loaded.'))
    expect(screen.queryByRole('listitem')).toBeNull()
    expect(screen.getByRole('button', { name: /unread count unknown/ })).toBeTruthy()
  })
  it('does not steal focus when the user moves away before an unread mutation finishes', async () => {
    const source = createNotificationFixture(); const pending = deferred(); const original = source.adapter.markRead!
    let request!: MutationRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    fireEvent.click(screen.getByRole('button', { name: 'Unread' }))
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    within(row()).getByRole('button', { name: 'Mark as read' }).focus(); clickRead()
    const refresh = screen.getByRole('button', { name: 'Refresh notifications' }); refresh.focus()
    await act(async () => pending.resolve(await original(request, new AbortController().signal)))
    await waitFor(() => expect(screen.queryByRole('listitem', { name: 'Preview is ready' })).toBeNull())
    expect(document.activeElement).toBe(refresh)
  })
  it('drops pending lists on logout, adapter replacement and unmount', async () => {
    const source = createNotificationFixture(); const pending = deferred(); const original = source.adapter.list
    let request!: ListRequest
    vi.spyOn(source.adapter, 'list').mockImplementation(req => { request = req; return pending.promise })
    const view = setup(source)
    view.rerender(<LocalizationProvider><NotificationInbox source={{ ...source, context: { ...source.context, principalId: null, access: 'unknown' } }} /></LocalizationProvider>)
    await act(async () => pending.resolve(await original(request, new AbortController().signal)))
    expect(screen.queryByRole('listitem')).toBeNull()
    view.rerender(<LocalizationProvider><NotificationInbox source={createNotificationFixture({ empty: true })} /></LocalizationProvider>)
    fireEvent.click(screen.getByRole('button', { name: /Notifications/ }))
    await screen.findByText('No notifications in this snapshot.')
    view.unmount()
  })
  it('treats a loaded unknown count as unknown and keeps read-all explicitly inbox-wide', async () => {
    const source = createNotificationFixture({ limit: 1 }); const original = source.adapter.list
    vi.spyOn(source.adapter, 'list').mockImplementation(async (req, signal) => ({ ...(await original(req, signal) as object), unread: { kind: 'unknown' } }))
    setup(source); await screen.findByRole('listitem')
    expect(screen.getByRole('button', { name: /unread count unknown/ })).toBeTruthy()
    expect(screen.getByText('Unread count is unknown. Loaded items are not the inbox total.')).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Mark entire inbox as read' }) as HTMLButtonElement).disabled).toBe(false)
  })
  it('has exact Tab wrapping and backdrop restoration without detail focus theft', async () => {
    const source = createNotificationFixture(); render(<NotificationInbox source={source} />)
    const entry = screen.getByRole('button', { name: /Notifications/ }); entry.focus(); fireEvent.click(entry)
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    const close = screen.getByRole('button', { name: 'Close notifications' })
    const last = screen.getByRole('button', { name: 'Read notification: Earlier update' })
    close.focus(); fireEvent.keyDown(close, { key: 'Tab', shiftKey: true }); expect(document.activeElement).toBe(last)
    fireEvent.keyDown(last, { key: 'Tab' }); expect(document.activeElement).toBe(close)
    const title = screen.getByRole('button', { name: 'Read notification: Preview is ready' }); title.focus(); fireEvent.click(title)
    expect(document.activeElement).toBe(title)
    fireEvent.mouseDown(screen.getByRole('dialog').parentElement!)
    expect(screen.queryByRole('dialog')).toBeNull(); expect(document.activeElement).toBe(entry)
  })
  it('uses existing typed related links for real injected sources while retaining target permission failures', async () => {
    const source = createNotificationFixture(); source.adapter.origin = 'real'
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    fireEvent.click(screen.getByRole('button', { name: 'Read notification: Preview is ready' }))
    expect(screen.getByRole('link', { name: 'Open related resource' }).getAttribute('href')).toBe('/w/simulated-workspace/projects/simulated-project/overview')
    expect(screen.getByText('The destination checks current resource access. This notification does not grant permission.')).toBeTruthy()
  })
  it('rejects calendar-invalid timestamps instead of rolling them forward', async () => {
    const source = createNotificationFixture({ limit: 1 }); const original = source.adapter.list
    vi.spyOn(source.adapter, 'list').mockImplementation(async (request, signal) => {
      const page = await original(request, signal) as { items: Array<{ content: { createdAt: string } }> }
      page.items[0].content.createdAt = '2026-02-30T10:00:00Z'
      return page
    })
    setup(source); await screen.findByRole('listitem')
    expect(within(row()).getByText('Time unavailable')).toBeTruthy()
    expect(row().querySelector('time')).toBeNull()
  })
})


describe('bounded review corrections', () => {
  it.each(['__proto__', 'constructor', 'toString'])('labels adversarial unknown type %s neutrally', async type => {
    const source = createNotificationFixture({ limit: 1 }); const original = source.adapter.list
    vi.spyOn(source.adapter, 'list').mockImplementation(async (request, signal) => {
      const page = parseList(await original(request, signal), request)
      if (page.status !== 'ok') throw new Error('Expected fixture page')
      return { ...page, items: page.items.map(item => ({ ...item, content: { ...item.content, type } })) }
    })
    setup(source); await screen.findByRole('listitem')
    expect(within(row()).getByText('Other notification')).toBeTruthy()
  })
  it('reopens while an aborted mutation ignores cancellation; old completion cannot unlock the new mutation', async () => {
    const source = createNotificationFixture(); const old = deferred(); const fresh = deferred()
    let oldRequest!: MutationRequest; let freshRequest!: MutationRequest; let oldSignal!: AbortSignal
    const read = vi.spyOn(source.adapter, 'markRead')
      .mockImplementationOnce((req, signal) => { oldRequest = req; oldSignal = signal; return old.promise })
      .mockImplementationOnce(req => { freshRequest = req; return fresh.promise })
    const all = vi.spyOn(source.adapter, 'markAllRead'); const list = vi.spyOn(source.adapter, 'list')
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' }); clickRead()
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(oldSignal.aborted).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: /Notifications/ }))
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    expect((within(row()).getByRole('button', { name: 'Mark as read' }) as HTMLButtonElement).disabled).toBe(false)
    clickRead(); expect(read).toHaveBeenCalledTimes(2)
    expect(freshRequest.requestId).not.toBe(oldRequest.requestId)
    const receipt = { status: 'ok', ...oldRequest, read: true }
    expect(parseMutation(receipt, oldRequest).status).toBe('ok')
    await act(async () => old.resolve(receipt))
    expect(screen.getByRole('status').textContent).toBe('Waiting for read confirmation…')
    expect(list).toHaveBeenCalledTimes(2)
    expect((within(row()).getByRole('button', { name: 'Mark as read' }) as HTMLButtonElement).disabled).toBe(true)
    act(() => { clickRead(); screen.getByRole('button', { name: 'Mark entire inbox as read' }).click() })
    expect(read).toHaveBeenCalledTimes(2); expect(all).not.toHaveBeenCalled()
    await act(async () => fresh.resolve({ status: 'denied', context: freshRequest.context, requestId: freshRequest.requestId }))
    expect(screen.getByRole('status').textContent).toMatch(/denied/i)
    expect(within(row()).getByText('Unread')).toBeTruthy()
    expect((within(row()).getByRole('button', { name: 'Mark as read' }) as HTMLButtonElement).disabled).toBe(false)
  })
  it.each([false, true])('reconciles disabled-button focus loss, moved-away=%s (modeled browser blur)', async movedAway => {
    const source = createNotificationFixture(); const pending = deferred(); const original = source.adapter.markRead
    let request!: MutationRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    fireEvent.click(screen.getByRole('button', { name: 'Unread' }))
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    const mark = within(row()).getByRole('button', { name: 'Mark as read' }); mark.focus(); clickRead()
    // happy-dom does not implement Chromium's disabled-control focus loss.
    // Explicit blur models that input; Hermes still owns native browser proof.
    expect((mark as HTMLButtonElement).disabled).toBe(true)
    // happy-dom also refuses blur() on disabled elements. Model that browser
    // input only if this exact disabled control still owns focus.
    if (document.activeElement === mark) {
      ;(mark as HTMLButtonElement).disabled = false; mark.blur(); (mark as HTMLButtonElement).disabled = true
      expect(document.activeElement).toBe(document.body)
    }
    if (movedAway) { const refresh = screen.getByRole('button', { name: 'Refresh notifications' }); refresh.focus(); refresh.blur() }
    await act(async () => pending.resolve(await original(request, new AbortController().signal)))
    await waitFor(() => expect(screen.queryByRole('listitem', { name: 'Preview is ready' })).toBeNull())
    expect(document.activeElement).toBe(movedAway ? document.body : screen.getByRole('button', { name: 'Unread', pressed: true }))
  })
  it('retains a newer successful refresh when an older valid successful snapshot completes last', async () => {
    const source = createNotificationFixture(); const original = source.adapter.list
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    const old = deferred(); const fresh = deferred(); let oldRequest!: ListRequest; let freshRequest!: ListRequest
    vi.spyOn(source.adapter, 'list').mockImplementationOnce(req => { oldRequest = req; return old.promise })
      .mockImplementationOnce(req => { freshRequest = req; return fresh.promise })
    fireEvent.click(screen.getByRole('button', { name: 'Refresh notifications' }))
    const oldPage = parseList(await original(oldRequest, new AbortController().signal), oldRequest)
    const mutation: MutationRequest = { context: source.context, requestId: 'external-read', operation: { kind: 'all', scope: 'inbox' } }
    expect(parseMutation(await source.adapter.markAllRead(mutation, new AbortController().signal), mutation).status).toBe('ok')
    fireEvent.click(screen.getByRole('button', { name: 'Refresh notifications' }))
    const freshPage = parseList(await original(freshRequest, new AbortController().signal), freshRequest)
    await act(async () => fresh.resolve(freshPage))
    expect(screen.getByRole('button', { name: 'Notifications · 0 unread in inbox' })).toBeTruthy()
    await act(async () => old.resolve(oldPage))
    expect(within(row()).getByText('Read')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Notifications · 0 unread in inbox' })).toBeTruthy()
  })
  it.each(['principalId', 'tenantId', 'logout'] as const)('drops valid pending lists across %s transition even after reopening', async key => {
    const source = createNotificationFixture(); const original = source.adapter.list; const pending = deferred()
    let request!: ListRequest; let signal!: AbortSignal
    vi.spyOn(source.adapter, 'list').mockImplementationOnce((req, abort) => { request = req; signal = abort; return pending.promise })
    const view = setup(source)
    const next: InboxSource = { ...source, context: { ...source.context, ...(key === 'logout' ? { principalId: null, access: 'unknown' as const } : { [key]: 'changed' }) } }
    view.rerender(<LocalizationProvider initialLocale="en"><NotificationInbox source={next} /></LocalizationProvider>)
    expect(signal.aborted).toBe(true); expect(screen.queryByRole('dialog')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /Notifications/ }))
    await waitFor(() => expect(screen.getByRole('status').textContent).toMatch(/denied|unknown/i))
    const receipt = parseList(await original(request, new AbortController().signal), request)
    expect(receipt.status).toBe('ok')
    await act(async () => pending.resolve(receipt))
    expect(screen.queryByRole('listitem')).toBeNull()
    expect(screen.getByRole('button', { name: /unread count unknown/ })).toBeTruthy()
    expect(screen.getByRole('status').textContent).toMatch(/denied|unknown/i)
  })
  it.each(['single', 'all'] as const)('serializes %s-first overlap before React disables controls', async first => {
    const source = createNotificationFixture(); const pending = deferred(); let request!: MutationRequest
    const method = first === 'single' ? 'markRead' : 'markAllRead'; const original = source.adapter[method]
    const active = vi.spyOn(source.adapter, method).mockImplementation((req, signal) => { expect(signal.aborted).toBe(false); request = req; return pending.promise })
    const other = vi.spyOn(source.adapter, first === 'single' ? 'markAllRead' : 'markRead')
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    const single = within(row()).getByRole('button', { name: 'Mark as read' }); const all = screen.getByRole('button', { name: 'Mark entire inbox as read' })
    act(() => { (first === 'single' ? single : all).click(); (first === 'single' ? all : single).click() })
    expect(active).toHaveBeenCalledTimes(1); expect(other).not.toHaveBeenCalled()
    expect(request.context).toEqual(source.context); expect(request.operation.kind).toBe(first)
    await act(async () => pending.resolve(await original(request, new AbortController().signal)))
    await waitFor(() => expect(within(row()).getByText('Read')).toBeTruthy())
  })
  it('distinguishes loaded unknown from known zero and confirms inbox-wide reads beyond a limited page', async () => {
    const source = createNotificationFixture({ limit: 1 }); const original = source.adapter.list
    const list = vi.spyOn(source.adapter, 'list').mockImplementationOnce(async (request, signal) => {
      const page = parseList(await original(request, signal), request)
      return { ...page, unread: { kind: 'unknown' } }
    })
    const all = vi.spyOn(source.adapter, 'markAllRead')
    setup(source); await screen.findByRole('listitem')
    expect(screen.getByRole('button', { name: /unread count unknown/ })).toBeTruthy()
    expect(screen.getAllByRole('listitem')).toHaveLength(1)
    expect((screen.getByRole('button', { name: 'Mark entire inbox as read' }) as HTMLButtonElement).disabled).toBe(false)
    fireEvent.click(screen.getByRole('button', { name: 'Mark entire inbox as read' }))
    await screen.findByRole('button', { name: 'Notifications · 0 unread in inbox' })
    const request = all.mock.calls[0][0]
    expect(request.operation).toEqual({ kind: 'all', scope: 'inbox' })
    expect(parseMutation(await all.mock.results[0].value, request)).toMatchObject({ status: 'ok', readIds: ['simulated-1', 'simulated-2'], failures: [] })
    expect(list).toHaveBeenCalledTimes(2)
    expect(screen.queryByText('Unread count is unknown. Loaded items are not the inbox total.')).toBeNull()
    expect((screen.getByRole('button', { name: 'Mark entire inbox as read' }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Unread' }))
    await screen.findByText('No notifications in this snapshot.')
    expect(screen.queryByRole('listitem')).toBeNull()
  })
  it.each(['single', 'all'] as const)('clears confirmation/count if the fresh query after %s succeeds with an invalid context', async kind => {
    const source = createNotificationFixture(); const method = kind === 'single' ? 'markRead' : 'markAllRead'
    const mutation = vi.spyOn(source.adapter, method)
    setup(source); await screen.findByRole('listitem', { name: 'Preview is ready' })
    vi.spyOn(source.adapter, 'list').mockImplementation(async request => ({ status: 'denied', requestId: request.requestId, context: { ...request.context, tenantId: 'foreign' }, explanation: 'Foreign explanation' }))
    if (kind === 'single') clickRead(); else fireEvent.click(screen.getByRole('button', { name: 'Mark entire inbox as read' }))
    await waitFor(() => expect(screen.getByRole('status').textContent).toBe('Notifications could not be loaded. Refresh to try again.'))
    expect(parseMutation(await mutation.mock.results[0].value, mutation.mock.calls[0][0]).status).toBe('ok')
    expect(mutation).toHaveBeenCalledTimes(1)
    expect(screen.queryByRole('listitem')).toBeNull(); expect(screen.queryByText('Foreign explanation')).toBeNull()
    expect(screen.getByRole('button', { name: /unread count unknown/ })).toBeTruthy()
  })
  it.each([
    ['missing', { availability: 'missing' }, 'The related resource is missing or was deleted.'],
    ['denied', { availability: 'denied' }, 'Access to the related resource was denied.'],
    ['unknown', { availability: 'unknown' }, 'Access to the related resource is unknown.'],
    ['unsupported', { kind: 'other' }, 'This related destination is not supported yet.'],
    ['cross-tenant', { tenantId: 'foreign' }, 'This related destination is not supported yet.'],
    ['ambiguous', { projectId: ['one', 'two'] }, 'This related destination is not supported yet.'],
  ])('does not expose a link for a %s target', async (_name, overrides, explanation) => {
    const source = createNotificationFixture({ limit: 1 }); const original = source.adapter.list
    vi.spyOn(source.adapter, 'list').mockImplementation(async (request, signal) => {
      const page = parseList(await original(request, signal), request)
      if (page.status !== 'ok') throw new Error('Expected fixture page')
      return { ...page, items: page.items.map(item => ({ ...item, target: { ...(item.target as object), ...(overrides as object) } })) }
    })
    setup(source); fireEvent.click(await screen.findByRole('button', { name: 'Read notification: Preview is ready' }))
    expect(screen.queryByRole('link', { name: 'Open related resource' })).toBeNull()
    expect(within(screen.getByRole('region', { name: 'Notification detail' })).getByText(explanation as string)).toBeTruthy()
  })
})



describe('single-read focus continuity correction', () => {
  function expectStableFocus(element: HTMLElement) {
    expect(document.activeElement).toBe(element)
    expect(element.isConnected).toBe(true)
    expect((element as HTMLButtonElement).disabled).toBe(false)
  }
  function modelNativeDisabledReadBlur(button: HTMLButtonElement) {
    expect(button.disabled).toBe(true)
    // MODELED NATIVE LIMITATION: happy-dom neither blurs a newly disabled
    // focused button nor permits blur() while it remains disabled. Supplement
    // the stable-focus assertions by modeling Chromium blur only when this
    // exact disabled single-read button still owns focus.
    if (document.activeElement === button) {
      button.disabled = false; button.blur(); button.disabled = true
    }
  }
  async function openForSingleRead(source: InboxSource, filter: 'all' | 'unread' = 'all') {
    const view = render(<LocalizationProvider initialLocale="en"><NotificationInbox source={source} /></LocalizationProvider>)
    const entry = screen.getByRole('button', { name: /Notifications/ })
    entry.focus(); fireEvent.click(entry)
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    const activeFilter = screen.getByRole('button', { name: filter === 'all' ? 'All' : 'Unread' })
    if (filter === 'unread') {
      activeFilter.focus(); fireEvent.click(activeFilter)
      await screen.findByRole('listitem', { name: 'Preview is ready' })
    }
    const item = row()
    return {
      ...view,
      entry,
      filter: activeFilter,
      title: within(item).getByRole('button', { name: 'Read notification: Preview is ready' }),
      read: within(item).getByRole('button', { name: 'Mark as read' }) as HTMLButtonElement,
    }
  }

  it('keeps focus on the active All filter while a single read is pending and after the retained row reconciles', async () => {
    const source = createNotificationFixture(); const mutation = deferred(); const reconciliation = deferred()
    const originalRead = source.adapter.markRead; const originalList = source.adapter.list
    let request!: MutationRequest; let listRequest!: ListRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return mutation.promise })
    const { filter, read } = await openForSingleRead(source)
    const list = vi.spyOn(source.adapter, 'list').mockImplementation(req => { listRequest = req; return reconciliation.promise })
    read.focus(); fireEvent.click(read)
    expect(read.disabled).toBe(true); expectStableFocus(filter)
    await act(async () => mutation.resolve(await originalRead(request, new AbortController().signal)))
    expect(list).toHaveBeenCalledTimes(1); expectStableFocus(filter)
    await act(async () => reconciliation.resolve(await originalList(listRequest, new AbortController().signal)))
    expect(within(row()).getByText('Read')).toBeTruthy()
    expectStableFocus(filter)
  })

  it('keeps active All filter focus through narrowly modeled native single-read blur', async () => {
    const source = createNotificationFixture(); const pending = deferred(); let request!: MutationRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    const { filter, read } = await openForSingleRead(source)
    read.focus(); fireEvent.click(read); modelNativeDisabledReadBlur(read)
    expectStableFocus(filter)
    await act(async () => pending.resolve({ status: 'error', context: request.context, requestId: request.requestId }))
    expectStableFocus(filter)
  })

  it('moves focus to the active Unread filter before disable and keeps it through row-removal reconciliation', async () => {
    const source = createNotificationFixture(); const pending = deferred(); const originalRead = source.adapter.markRead
    let request!: MutationRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    const { filter, read } = await openForSingleRead(source, 'unread')
    read.focus(); fireEvent.click(read)
    expectStableFocus(filter)
    await act(async () => pending.resolve(await originalRead(request, new AbortController().signal)))
    await waitFor(() => expect(screen.queryByRole('listitem', { name: 'Preview is ready' })).toBeNull())
    expectStableFocus(filter)
  })

  it('closes from actual enabled focus while a single read is pending and restores the launcher', async () => {
    const source = createNotificationFixture(); const pending = deferred(); let request!: MutationRequest; let signal!: AbortSignal
    vi.spyOn(source.adapter, 'markRead').mockImplementation((req, abort) => { request = req; signal = abort; return pending.promise })
    const { entry, filter, read } = await openForSingleRead(source)
    read.focus(); fireEvent.click(read); expectStableFocus(filter)
    fireEvent.keyDown(document.activeElement!, { key: 'Escape', keyCode: 27 })
    expect(screen.queryByRole('dialog')).toBeNull(); expect(document.activeElement).toBe(entry); expect(signal.aborted).toBe(true)
    await act(async () => pending.resolve({ status: 'error', context: request.context, requestId: request.requestId }))
    expect(screen.queryByRole('dialog')).toBeNull(); expect(document.activeElement).toBe(entry)
  })

  it.each(['failure', 'invalid', 'reject'] as const)('retains active All filter focus after deferred single-read %s', async outcome => {
    const source = createNotificationFixture(); const pending = deferred(); let request!: MutationRequest
    const list = vi.spyOn(source.adapter, 'list')
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    const { filter, read } = await openForSingleRead(source)
    read.focus(); fireEvent.click(read); expectStableFocus(filter)
    if (outcome === 'failure') {
      await act(async () => pending.resolve({ status: 'error', context: request.context, requestId: request.requestId }))
    } else if (outcome === 'invalid') {
      await act(async () => pending.resolve({ status: 'ok', context: request.context, requestId: request.requestId, operation: { kind: 'single', id: 'foreign' }, read: true }))
    } else {
      await act(async () => pending.reject(new Error('controlled rejection')))
    }
    expect(screen.getByRole('status').textContent).toContain('could not be confirmed as read')
    expect(within(row()).getByText('Unread')).toBeTruthy(); expect(list).toHaveBeenCalledTimes(1)
    expectStableFocus(filter)
  })

  it('keeps active All filter focus during reconciliation loading and failure', async () => {
    const source = createNotificationFixture(); const mutation = deferred(); const reconciliation = deferred()
    const originalRead = source.adapter.markRead; let request!: MutationRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return mutation.promise })
    const { filter, read } = await openForSingleRead(source)
    vi.spyOn(source.adapter, 'list').mockReturnValue(reconciliation.promise)
    read.focus(); fireEvent.click(read); expectStableFocus(filter)
    await act(async () => mutation.resolve(await originalRead(request, new AbortController().signal)))
    expect(screen.getByRole('status').textContent).toContain('Loading notifications')
    expect(row()).toBeTruthy(); expectStableFocus(filter)
    await act(async () => reconciliation.reject(new Error('controlled reconciliation failure')))
    await waitFor(() => expect(screen.queryByRole('listitem')).toBeNull())
    expect(screen.getByRole('status').textContent).toContain('Notifications could not be loaded')
    expectStableFocus(filter)
  })

  it('does not reclaim focus after the user deliberately moves during a single read', async () => {
    const source = createNotificationFixture(); const pending = deferred(); const originalRead = source.adapter.markRead
    let request!: MutationRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    const { read } = await openForSingleRead(source)
    read.focus(); fireEvent.click(read)
    const refresh = screen.getByRole('button', { name: 'Refresh notifications' }); refresh.focus()
    await act(async () => pending.resolve(await originalRead(request, new AbortController().signal)))
    await waitFor(() => expect(within(row()).getByText('Read')).toBeTruthy())
    expectStableFocus(refresh)
  })

  it('does not move focus for programmatic single-read activation from another valid control', async () => {
    const source = createNotificationFixture(); const pending = deferred(); let request!: MutationRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    const { read } = await openForSingleRead(source)
    const refresh = screen.getByRole('button', { name: 'Refresh notifications' }); refresh.focus()
    read.click(); expectStableFocus(refresh)
    await act(async () => pending.resolve({ status: 'error', context: request.context, requestId: request.requestId }))
    expectStableFocus(refresh)
  })

  it('cannot let an old closed read unlock or focus over a newer reopened read', async () => {
    const source = createNotificationFixture(); const old = deferred(); const fresh = deferred()
    let oldRequest!: MutationRequest; let freshRequest!: MutationRequest
    const readMutation = vi.spyOn(source.adapter, 'markRead')
      .mockImplementationOnce(req => { oldRequest = req; return old.promise })
      .mockImplementationOnce(req => { freshRequest = req; return fresh.promise })
    const allMutation = vi.spyOn(source.adapter, 'markAllRead')
    const first = await openForSingleRead(source)
    first.read.focus(); fireEvent.click(first.read); expectStableFocus(first.filter)
    fireEvent.keyDown(document.activeElement!, { key: 'Escape', keyCode: 27 })
    expect(document.activeElement).toBe(first.entry)
    fireEvent.click(first.entry); await screen.findByRole('listitem', { name: 'Preview is ready' })
    const freshFilter = screen.getByRole('button', { name: 'All', pressed: true })
    const freshRead = within(row()).getByRole('button', { name: 'Mark as read' }) as HTMLButtonElement
    freshRead.focus(); fireEvent.click(freshRead); expectStableFocus(freshFilter)
    await act(async () => old.resolve({ status: 'ok', context: oldRequest.context, requestId: oldRequest.requestId, operation: oldRequest.operation, read: true }))
    expect(screen.getByRole('status').textContent).toBe('Waiting for read confirmation…')
    expect(freshRead.disabled).toBe(true); expectStableFocus(freshFilter)
    act(() => { freshRead.click(); screen.getByRole('button', { name: 'Mark entire inbox as read' }).click() })
    expect(readMutation).toHaveBeenCalledTimes(2); expect(allMutation).not.toHaveBeenCalled()
    await act(async () => fresh.resolve({ status: 'error', context: freshRequest.context, requestId: freshRequest.requestId }))
    expectStableFocus(freshFilter)
  })

  it.each(['context', 'unmount'] as const)('retires old single-read focus intent on %s', async transition => {
    const source = createNotificationFixture(); const pending = deferred(); let request!: MutationRequest
    vi.spyOn(source.adapter, 'markRead').mockImplementation(req => { request = req; return pending.promise })
    const view = await openForSingleRead(source)
    view.read.focus(); fireEvent.click(view.read)
    if (transition === 'context') {
      const next = { ...source, context: { ...source.context, sessionId: 'replacement-session' } }
      view.rerender(<LocalizationProvider initialLocale="en"><NotificationInbox source={next} /></LocalizationProvider>)
      expect(screen.queryByRole('dialog')).toBeNull()
    } else {
      view.unmount(); expect(screen.queryByRole('button')).toBeNull()
    }
    expect(document.activeElement).toBe(document.body)
    await act(async () => pending.resolve({ status: 'ok', context: request.context, requestId: request.requestId, operation: request.operation, read: true }))
    expect(document.activeElement).toBe(document.body); expect(screen.queryByRole('dialog')).toBeNull()
  })
})


describe('toolbar read-all focus correction', () => {
  function modelDisabledToolbarBlur(button: HTMLButtonElement) {
    expect(button.disabled).toBe(true)
    // happy-dom neither blurs on disable nor permits blur() while disabled.
    // Model Chromium's focus loss only if the toolbar still owns focus. A
    // synchronous transfer to a stable control must survive this modeled input.
    if (document.activeElement === button) {
      button.disabled = false; button.blur(); button.disabled = true
    }
  }
  async function openUnread(source: InboxSource, locale: 'en' | 'zh-CN' = 'en') {
    render(<LocalizationProvider initialLocale={locale}><NotificationInbox source={source} /></LocalizationProvider>)
    const entry = screen.getByRole('button', { name: locale === 'en' ? /Notifications/ : /通知/ })
    entry.focus(); fireEvent.click(entry)
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    const filter = screen.getByRole('button', { name: locale === 'en' ? 'Unread' : '未读' })
    filter.focus(); fireEvent.click(filter)
    await screen.findByRole('listitem', { name: 'Preview is ready' })
    const toolbar = screen.getByRole('button', { name: locale === 'en' ? 'Mark entire inbox as read' : '将整个收件箱标为已读' }) as HTMLButtonElement
    return { entry, filter, toolbar }
  }
  it.each([
    ['en', 'success'], ['en', 'failure'], ['zh-CN', 'success'], ['zh-CN', 'failure'],
  ] as const)('keeps keyboard focus through disabled toolbar blur and %s read-all %s', async (locale, outcome) => {
    const source = createNotificationFixture(); const pending = deferred(); const reconciliation = deferred()
    const originalRead = source.adapter.markAllRead; const originalList = source.adapter.list
    let request!: MutationRequest; let listRequest!: ListRequest
    const mutation = vi.spyOn(source.adapter, 'markAllRead').mockImplementation(req => { request = req; return pending.promise })
    const { entry, filter, toolbar } = await openUnread(source, locale)
    const list = vi.spyOn(source.adapter, 'list').mockImplementation(req => { listRequest = req; return reconciliation.promise })
    toolbar.focus(); fireEvent.click(toolbar); modelDisabledToolbarBlur(toolbar)
    expect(document.activeElement).toBe(filter)
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
    if (outcome === 'success') {
      await act(async () => pending.resolve(await originalRead(request, new AbortController().signal)))
      expect(list).toHaveBeenCalledTimes(1)
      expect(toolbar.disabled).toBe(true)
      expect(document.activeElement).toBe(filter)
      await act(async () => reconciliation.resolve(await originalList(listRequest, new AbortController().signal)))
      expect(screen.queryByRole('listitem')).toBeNull()
      expect(screen.getByRole('button', { name: locale === 'en' ? 'Notifications · 0 unread in inbox' : '通知 · 收件箱有 0 条未读' })).toBe(entry)
      expect(toolbar.disabled).toBe(true)
    } else {
      await act(async () => pending.resolve({ status: 'error', context: request.context, requestId: request.requestId }))
      expect(list).not.toHaveBeenCalled()
      expect(screen.getAllByRole('listitem')).toHaveLength(2)
      expect(screen.getByRole('button', { name: locale === 'en' ? 'Notifications · 2 unread in inbox' : '通知 · 收件箱有 2 条未读' })).toBe(entry)
      expect(toolbar.disabled).toBe(false)
    }
    expect(mutation).toHaveBeenCalledTimes(1)
    expect(document.activeElement).toBe(filter)
    // Dispatch on actual focus: targeting the dialog directly hides BODY loss.
    fireEvent.keyDown(document.activeElement!, { key: 'Escape', keyCode: 27 })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(entry)
  })
  it.each([
    ['success', false], ['success', true], ['failure', false], ['failure', true],
  ] as const)('does not reclaim focus after moving away during read-all %s, later blur=%s', async (outcome, blur) => {
    const source = createNotificationFixture(); const pending = deferred(); const original = source.adapter.markAllRead
    let request!: MutationRequest
    vi.spyOn(source.adapter, 'markAllRead').mockImplementation(req => { request = req; return pending.promise })
    const { toolbar } = await openUnread(source)
    toolbar.focus(); fireEvent.click(toolbar); modelDisabledToolbarBlur(toolbar)
    const refresh = screen.getByRole('button', { name: 'Refresh notifications' })
    refresh.focus(); if (blur) refresh.blur()
    await act(async () => pending.resolve(outcome === 'success' ? await original(request, new AbortController().signal) : { status: 'error', context: request.context, requestId: request.requestId }))
    expect(screen.getByRole('button', { name: outcome === 'success' ? 'Notifications · 0 unread in inbox' : 'Notifications · 2 unread in inbox' })).toBeTruthy()
    expect(document.activeElement).toBe(blur ? document.body : refresh)
  })
  it('closes from actual focus while read-all is pending and ignores its late completion', async () => {
    const source = createNotificationFixture(); const pending = deferred(); let request!: MutationRequest; let signal!: AbortSignal
    vi.spyOn(source.adapter, 'markAllRead').mockImplementation((req, abort) => { request = req; signal = abort; return pending.promise })
    const { entry, toolbar } = await openUnread(source)
    toolbar.focus(); fireEvent.click(toolbar); modelDisabledToolbarBlur(toolbar)
    fireEvent.keyDown(document.activeElement!, { key: 'Escape', keyCode: 27 })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(entry); expect(signal.aborted).toBe(true)
    await act(async () => pending.resolve({ status: 'error', context: request.context, requestId: request.requestId }))
    expect(screen.queryByRole('dialog')).toBeNull(); expect(document.activeElement).toBe(entry)
  })
  it('does not move another valid control when read-all is activated without toolbar focus', async () => {
    const source = createNotificationFixture(); const pending = deferred(); const original = source.adapter.markAllRead
    let request!: MutationRequest
    vi.spyOn(source.adapter, 'markAllRead').mockImplementation(req => { request = req; return pending.promise })
    const { toolbar } = await openUnread(source)
    const refresh = screen.getByRole('button', { name: 'Refresh notifications' }); refresh.focus()
    fireEvent.click(toolbar); modelDisabledToolbarBlur(toolbar)
    expect(document.activeElement).toBe(refresh)
    await act(async () => pending.resolve(await original(request, new AbortController().signal)))
    expect(screen.queryByRole('listitem')).toBeNull(); expect(document.activeElement).toBe(refresh)
  })
})
