import { createContext, useContext, useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import { InteractionDialog } from '../../interaction/InteractionDialog'
import { useTranslation } from '../../localization'
import { canQuery, contextKey, parseList, parseMutation, resolveTarget, notificationDate, type InboxFilter, type InboxItem, type InboxPage, type InboxSource, type MutationRequest } from './types'
import { unavailableSource } from './unavailable'
import { localhostFixture } from './fixture'

const SourceContext = createContext<InboxSource | undefined>(undefined)
export function NotificationInboxProvider({ source, children }: { source: InboxSource; children: ReactNode }) {
  return <SourceContext.Provider value={source}>{children}</SourceContext.Provider>
}
const adapterIds = new WeakMap<InboxSource['adapter'], number>()
let nextAdapterId = 0
function adapterKey(adapter: InboxSource['adapter']) {
  if (!adapterIds.has(adapter)) adapterIds.set(adapter, ++nextAdapterId)
  return adapterIds.get(adapter)
}
export function NotificationInbox({ source: supplied }: { source?: InboxSource }) {
  const provided = useContext(SourceContext)
  const [defaultSource] = useState(() => typeof window === 'undefined' ? unavailableSource : localhostFixture(window.location) ?? unavailableSource)
  const source = supplied ?? provided ?? defaultSource
  // Only the inbox remounts. The media selection, project and application request
  // lifetimes are independent. No old principal content survives this render.
  const key = JSON.stringify([adapterKey(source.adapter), contextKey(source.context), source.adapter.origin, source.adapter.capabilities])
  return <InboxSession key={key} source={source} />
}

type Notice = { key: string; explanation?: string }
function InboxSession({ source }: { source: InboxSource }) {
  const { t, formatNumber, formatDate } = useTranslation()
  const originId = useId()
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState<InboxFilter>('all')
  const [page, setPage] = useState<InboxPage | null>(null)
  const [detailId, setDetailId] = useState<string | null>(null)
  const [status, setStatus] = useState('idle')
  const [notice, setNotice] = useState<Notice | null>(null)
  const [busy, setBusy] = useState(false)
  const live = useRef(false)
  const isOpen = useRef(false)
  const activeFilter = useRef<InboxFilter>('all')
  const generation = useRef(0)
  const sequence = useRef(0)
  const queryController = useRef<AbortController | null>(null)
  const mutationController = useRef<AbortController | null>(null)
  const mutationOwner = useRef<AbortController | null>(null)
  const focusedRow = useRef<{ element: HTMLElement; id: string } | null>(null)
  const filterButton = useRef<HTMLButtonElement>(null)
  const readAllButton = useRef<HTMLButtonElement>(null)
  const focusAfter = useRef<HTMLElement | null>(null)
  const latestPage = useRef<InboxPage | null>(null)
  const allowed = canQuery(source)
  const initialStatus = source.context.access === 'denied' ? 'denied' : 'unavailable'
  const text = (key: string) => t(`shell.notifications.${key}`)

  useLayoutEffect(() => {
    live.current = true
    // Disabling a focused button may return native focus to body. Preserve its
    // row intent, but permanently cancel it when the user focuses/clicks elsewhere.
    const cancelMovedFocus = (event: Event) => {
      const intent = focusedRow.current
      if (intent && event.target !== intent.element && (event.type === 'pointerdown' || event.target !== document.body)) focusedRow.current = null
    }
    document.addEventListener('focusin', cancelMovedFocus)
    document.addEventListener('pointerdown', cancelMovedFocus)
    return () => {
      live.current = false; isOpen.current = false; generation.current += 1
      queryController.current?.abort(); mutationController.current?.abort()
      mutationOwner.current = null; focusedRow.current = null
      document.removeEventListener('focusin', cancelMovedFocus)
      document.removeEventListener('pointerdown', cancelMovedFocus)
    }
  }, [])
  useLayoutEffect(() => {
    const previous = focusAfter.current
    focusAfter.current = null
    if (previous && !previous.isConnected && (document.activeElement === document.body || document.activeElement === previous)) filterButton.current?.focus()
  }, [page])

  async function query(nextFilter: InboxFilter, retainedNotice: Notice | null = null) {
    const current = ++generation.current
    queryController.current?.abort()
    if (!allowed || !isOpen.current) return
    const controller = new AbortController()
    queryController.current = controller
    const request = { context: source.context, requestId: `list-${++sequence.current}`, filter: nextFilter }
    setStatus('loading'); setNotice(retainedNotice)
    try {
      const result = parseList(await source.adapter.list(request, controller.signal), request)
      if (!live.current || !isOpen.current || controller.signal.aborted || current !== generation.current) return
      if (result.status !== 'ok') {
        setPage(null); latestPage.current = null; setDetailId(null); setStatus(result.status)
        setNotice({ key: result.status === 'not-found' ? 'notFound' : result.status, explanation: result.explanation })
        return
      }
      const active = document.activeElement as HTMLElement | null
      const intent = focusedRow.current
      const focused = active === document.body && intent ? intent.element : active
      const focusedId = focused?.closest<HTMLElement>('[data-notification-id]')?.dataset.notificationId
      focusedRow.current = null
      if (nextFilter === 'unread' && focusedId && !result.items.some(item => item.id === focusedId)) focusAfter.current = focused
      latestPage.current = result; setPage(result); setStatus('ready')
      setDetailId(id => result.items.some(item => item.id === id) ? id : null)
    } catch {
      if (!live.current || !isOpen.current || controller.signal.aborted || current !== generation.current) return
      setStatus('error'); setPage(null); latestPage.current = null; setDetailId(null)
      setNotice({ key: 'error' })
    }
  }

  useEffect(() => {
    if (open) void query(activeFilter.current)
    // This keyed session owns one immutable source/context. User refresh/filter
    // requests run directly so they invalidate previous work synchronously.
  }, [open])

  function close() {
    isOpen.current = false; generation.current += 1
    queryController.current?.abort(); mutationController.current?.abort()
    mutationOwner.current = null; focusedRow.current = null; focusAfter.current = null; setBusy(false)
    setOpen(false); setPage(null); latestPage.current = null; setDetailId(null); setStatus('idle'); setNotice(null)
  }
  function changeFilter(next: InboxFilter) {
    if (activeFilter.current === next) return
    focusedRow.current = null
    activeFilter.current = next; setFilter(next); setPage(null); latestPage.current = null; setDetailId(null)
    void query(next)
  }
  async function mark(operation: MutationRequest['operation']) {
    const currentPage = latestPage.current
    const supported = operation.kind === 'single' ? source.adapter.capabilities.singleRead && source.adapter.markRead : source.adapter.capabilities.readAll === 'inbox' && source.adapter.markAllRead
    if (!allowed || !isOpen.current || mutationOwner.current || status !== 'ready' || !currentPage || !supported) return
    if (operation.kind === 'single' && !currentPage.items.some(item => item.id === operation.id && !item.read)) return
    // One synchronous lock serializes single and inbox-wide changes, including
    // double activation before React commits disabled controls.
    const focused = document.activeElement as HTMLElement | null
    const focusedId = focused?.closest<HTMLElement>('[data-notification-id]')?.dataset.notificationId
    focusedRow.current = focused && focusedId ? { element: focused, id: focusedId } : null
    const controller = new AbortController()
    mutationOwner.current = controller; mutationController.current = controller
    // Native disable can blur the toolbar to BODY, outside the dialog's keys.
    // Transfer only its current focus before disabling, to a stable control.
    // No deferred restoration can reclaim focus after the user moves away.
    if (focused === readAllButton.current) filterButton.current?.focus()
    setBusy(true); setNotice({ key: 'marking' })
    const current = ++generation.current
    queryController.current?.abort()
    const request: MutationRequest = { context: source.context, requestId: `read-${++sequence.current}`, operation }
    try {
      const result = parseMutation(await supported.call(source.adapter, request, controller.signal), request)
      if (!live.current || !isOpen.current || controller.signal.aborted || mutationOwner.current !== controller) return
      if (result.status === 'ok' || result.status === 'partial') {
        // Never patch/decrement locally. Refresh the active filter, even if a
        // refresh/filter request overlapped the mutation, to reconcile its result.
        void query(activeFilter.current, { key: result.status === 'partial' ? 'partialRead' : 'readConfirmed' })
      } else if (current === generation.current) {
        setNotice({ key: result.status === 'not-found' ? 'notFound' : result.status === 'error' ? 'readError' : result.status, explanation: 'explanation' in result ? result.explanation : undefined })
      }
    } catch {
      if (live.current && isOpen.current && !controller.signal.aborted && current === generation.current) setNotice({ key: 'readError' })
    } finally {
      // Only this operation can release its lock. Close retires ownership even
      // if the adapter ignores abort; its late finally cannot unlock a new read.
      if (mutationOwner.current === controller) {
        mutationOwner.current = null
        if (live.current) setBusy(false)
      }
    }
  }

  const visiblePage = page?.filter === filter ? page : null
  const detail = visiblePage?.items.find(item => item.id === detailId)
  const count = status === 'ready' && visiblePage?.unread.kind === 'known' ? visiblePage.unread.total : null
  const entryLabel = count === null ? text('entryUnknown') : t('shell.notifications.entryCount', { count: formatNumber(count) })
  const activeStatus = !allowed ? initialStatus : status
  const statusKey = !allowed ? initialStatus : status === 'loading' ? 'loading' : notice?.key ?? (status === 'ready' ? (visiblePage?.items.length ? 'loaded' : 'empty') : status === 'idle' ? 'loading' : status)
  const readDisabled = !allowed || busy || status !== 'ready'
  const target = detail ? resolveTarget(detail.target, source.context, source.adapter.origin) : null
  function timestamp(item: InboxItem) {
    const value = item.content.createdAt
    const date = notificationDate(value)
    return date ? <time dateTime={value!}>{formatDate(date, { dateStyle: 'medium', timeStyle: 'short' })}</time> : <span>{text('invalidTime')}</span>
  }
  function typeLabel(item: InboxItem) {
    const keys: Record<string, string> = { 'render.completed': 'typeRender', 'review.requested': 'typeReview', 'system.announcement': 'typeAnnouncement' }
    return text(Object.prototype.hasOwnProperty.call(keys, item.content.type) ? keys[item.content.type] : 'typeOther')
  }
  return <>
    <button type="button" className="ff-notification-entry" aria-label={entryLabel} aria-describedby={source.adapter.origin === 'simulated' ? originId : undefined} aria-haspopup="dialog" aria-expanded={open} onClick={() => { isOpen.current = true; setOpen(true) }}>
      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg>
      <span>{text('title')}</span>{count !== null ? <span aria-hidden="true" className="ff-notification-count">{formatNumber(count)}</span> : null}
      {source.adapter.origin === 'simulated' ? <small id={originId}>{text('simulatedBadge')}</small> : null}
    </button>
    {open ? <InteractionDialog title={text('title')} closeLabel={text('close')} onClose={close} className="ff-notification-inbox">
      <p className="ff-notification-origin">{text(source.adapter.origin === 'simulated' ? 'simulated' : source.adapter.origin === 'real' ? 'real' : 'originUnavailable')}</p>
      <div className="ff-notification-controls">
        <div role="group" aria-label={text('filter')}>
          {(['all', 'unread'] as const).map(value => <button key={value} ref={value === filter ? filterButton : undefined} type="button" aria-pressed={filter === value} onClick={() => changeFilter(value)}>{text(value)}</button>)}
        </div>
        <button type="button" disabled={!allowed} onClick={() => void query(activeFilter.current)}>{text('refresh')}</button>
        <button ref={readAllButton} type="button" disabled={readDisabled || !source.adapter.markAllRead || source.adapter.capabilities.readAll !== 'inbox' || (count === 0)} onClick={() => void mark({ kind: 'all', scope: 'inbox' })}>{text('readAll')}</button>
      </div>
      {source.adapter.capabilities.readAll !== 'inbox' ? <p>{text('readAllUnsupported')}</p> : <p>{text('readAllScope')}</p>}
      {!source.adapter.capabilities.singleRead ? <p>{text('singleUnsupported')}</p> : null}
      <p role="status" aria-live="polite" aria-atomic="true">{text(statusKey)}{notice?.explanation ? <> {notice.explanation}</> : null}</p>
      {visiblePage ? <>
        <p>{visiblePage.unread.kind === 'known' ? t('shell.notifications.globalCount', { count: formatNumber(visiblePage.unread.total) }) : text('unknownCount')}</p>
        <p>{text(visiblePage.traversal.kind === 'limited' ? 'limited' : 'complete')}</p>
        <ul className="ff-notification-list" aria-label={text('list')} aria-busy={activeStatus === 'loading'}>
          {visiblePage.items.map(item => <li key={item.id} aria-label={item.content.title || text('untitled')} data-notification-id={item.id}>
            <div className="ff-notification-meta"><span>{typeLabel(item)}</span><span>{text(item.read ? 'read' : 'unread')}</span>{timestamp(item)}</div>
            <button type="button" className="ff-notification-title" aria-label={t('shell.notifications.readDetail', { title: item.content.title || text('untitled') })} aria-expanded={detailId === item.id} onClick={() => setDetailId(item.id)}>{item.content.title || text('untitled')}</button>
            <button type="button" disabled={readDisabled || item.read || !source.adapter.capabilities.singleRead || !source.adapter.markRead} onClick={() => void mark({ kind: 'single', id: item.id })}>{text('markRead')}</button>
          </li>)}
        </ul>
      </> : null}
      {detail ? <section className="ff-notification-detail" aria-label={text('detail')} data-notification-id={detail.id}>
        <h3>{detail.content.title || text('untitled')}</h3><p className="ff-notification-body">{detail.content.body}</p>
        {target && 'href' in target ? <>{source.adapter.origin === 'simulated' ? <p>{text('simulatedTarget')}</p> : null}<p>{text('destinationChecks')}</p><a href={target.href}>{text('openResource')}</a></>
          : <p>{text(target && 'reason' in target ? target.reason : 'unsupportedTarget')}</p>}
      </section> : null}
    </InteractionDialog> : null}
  </>
}
