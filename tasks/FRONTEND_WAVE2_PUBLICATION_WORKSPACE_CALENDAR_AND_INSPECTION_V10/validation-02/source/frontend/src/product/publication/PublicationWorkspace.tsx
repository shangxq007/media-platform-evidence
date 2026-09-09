import { createContext, useContext, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import { flushSync } from 'react-dom'
import { subscribeOidcSessionRetirement } from '../../auth/oidcClient'
import { Badge, Button, Search, PropertyRow } from '../../components/design-system'
import { InteractionDialog } from '../../interaction/InteractionDialog'
import { useInteractionStore, useSelection, useSurfaceAdapter } from '../../interaction/SelectionContext'
import { useTranslation } from '../../localization'
import { absoluteInstant, accessFingerprint, calendarDay, filterPlans, monthDays, parsePublication, planDay, publicationAccess, scopeKey, shiftMonth } from './model'
import type { PublicationFilters, PublicationPlan, PublicationSnapshot, PublicationSource } from './types'
import './publication.css'

const SourceContext = createContext<PublicationSource | undefined>(undefined)
/** Explicit isolated host only; never a route switch, fixture fallback or real backend adapter. */
export function PublicationSourceProvider({ source, children }: { source: PublicationSource; children: ReactNode }) {
  return <SourceContext.Provider value={source}>{children}</SourceContext.Provider>
}
const identities = new WeakMap<object, number>()
let nextIdentity = 0
function identity(object: object): number {
  if (!identities.has(object)) identities.set(object, ++nextIdentity)
  return identities['get'](object)!
}
interface Props { workspaceId: string; projectId: string; tenantId: string | null; source?: PublicationSource; now?: () => Date }
export function PublicationWorkspace(props: Props) {
  const provided = useContext(SourceContext), store = useInteractionStore()
  const source = props.source ?? provided
  const binding = source ? JSON.stringify([scopeKey(source.scope), identity(source.owner)]) : ''
  const [retiredBinding, setRetiredBinding] = useState<string | null>(null)
  useLayoutEffect(() => subscribeOidcSessionRetirement(() => {
    // The old explicit host is no longer current identity authority. It must supply a
    // fresh scope/owner binding before another read, even when local IDs are reused.
    flushSync(() => setRetiredBinding(binding))
  }), [binding])
  const activeSource = retiredBinding === binding ? undefined : source
  const key = JSON.stringify([identity(store), props.workspaceId, props.projectId, props.tenantId, activeSource && [binding, identity(activeSource.adapter), accessFingerprint(activeSource.access)]])
  return <PublicationSession key={key} {...props} source={activeSource} />
}
const defaultFilters: PublicationFilters = { query: '', account: '', status: '', order: 'asc' }
const displayZones = ['UTC', 'America/Los_Angeles', 'America/New_York', 'Europe/London', 'Europe/Berlin', 'Asia/Shanghai', 'Asia/Kolkata', 'Pacific/Auckland']
function PublicationSession({ workspaceId, projectId, tenantId, source, now = () => new Date() }: Props) {
  const { t, locale } = useTranslation()
  const text = (key: string) => t(`shell.publication.${key}`)
  const store = useInteractionStore(), selection = useSelection()
  const permitted = Boolean(source && publicationAccess(source) && source.scope.workspaceId === workspaceId && source.scope.projectId === projectId && source.scope.tenantId === tenantId)
  type Status = 'loading' | 'ready' | 'unavailable' | 'restricted' | 'error' | 'invalid'
  const [status, setStatus] = useState<Status>(permitted ? 'loading' : source ? 'restricted' : 'unavailable')
  const [snapshot, setSnapshot] = useState<PublicationSnapshot | null>(null)
  const [filters, setFilters] = useState(defaultFilters), [view, setView] = useState<'list' | 'calendar'>('list')
  const [zone, setZone] = useState('UTC')
  const today = calendarDay(now().toISOString(), zone)!
  const [month, setMonth] = useState(today.slice(0, 7)), [day, setDay] = useState(today)
  const [detail, setDetail] = useState<{ id: string; lifetime: object } | null>(null)
  const activeDetail = useRef(detail), live = useRef(false), lifetime = useRef(selection.lifetime)
  const generation = useRef(0), controller = useRef<AbortController | null>(null), currentSnapshot = useRef(snapshot)
  const region = useRef<HTMLElement>(null), results = useRef<HTMLDivElement>(null), scroll = useRef(0)
  const pendingSelection = useRef<string[]>([]), launcher = useRef<HTMLElement | null>(null)
  const owns = () => live.current && lifetime.current === store.getSnapshot().lifetime
  const owned = lifetime.current === selection.lifetime
  const rows = snapshot && owned ? filterPlans(snapshot, filters) : []
  const objects = snapshot && owned ? snapshot.plans.map(p => ({ id: p.id, kind: 'PUBLICATION' as const, title: p.title || p.id })) : []
  useSurfaceAdapter({ objects: () => objects, supports: [], handle: () => false })
  useLayoutEffect(() => {
    live.current = true; lifetime.current = store.getSnapshot().lifetime
    return () => { live.current = false; ++generation.current; controller.current?.abort(); activeDetail.current = null }
  }, [store])
  useLayoutEffect(() => { currentSnapshot.current = snapshot }, [snapshot])
  useLayoutEffect(() => { activeDetail.current = detail; return () => { activeDetail.current = null } }, [detail])
  useLayoutEffect(() => {
    if (!owned) { ++generation.current; controller.current?.abort(); setSnapshot(null); setDetail(null) }
  }, [owned])
  useLayoutEffect(() => store.subscribe(() => {
    const current = store.getSnapshot(), open = activeDetail.current
    if (open && (open.lifetime !== current.lifetime || open.id !== current.primarySelectedObject?.id || !current.inspectorOpen)) { activeDetail.current = null; setDetail(null) }
  }), [store])
  useLayoutEffect(() => {
    if (results.current) results.current.scrollTop = scroll.current
    if (!snapshot || !owns()) return
    const ids = pendingSelection.current.filter(id => snapshot.plans.some(p => p.id === id))
    const disappeared = pendingSelection.current.length > 0 && !ids.length
    pendingSelection.current = []
    if (ids.length) store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids })
    if (disappeared) region.current?.focus()
  }, [snapshot, view])
  async function load() {
    if (!owns() || !source || !permitted) return
    const epoch = ++generation.current
    controller.current?.abort()
    const abort = new AbortController(); controller.current = abort
    pendingSelection.current = store.getSnapshot().selectedObjects.map(p => p.id)
    scroll.current = results.current?.scrollTop ?? scroll.current
    currentSnapshot.current = null; activeDetail.current = null
    setSnapshot(null); setDetail(null); setStatus('loading')
    const request = { scope: source.scope, requestId: `publication-${epoch}`, query: { kind: 'project-publication-snapshot' as const, limit: 200 as const } }
    try {
      const input = await source.adapter.read(request, abort.signal)
      if (!owns() || abort.signal.aborted || epoch !== generation.current) return
      const result = parsePublication(input, request, source.access)
      if (result.status === 'ok') { setSnapshot(result); setStatus('ready') }
      else { pendingSelection.current = []; setStatus(result.status); region.current?.focus() }
    } catch {
      if (owns() && !abort.signal.aborted && epoch === generation.current) { pendingSelection.current = []; setStatus('error'); region.current?.focus() }
    }
  }
  useEffect(() => { void load() }, [])
  const updateFilters = (patch: Partial<PublicationFilters>) => { if (owns()) setFilters(f => ({ ...f, ...patch })) }
  const changeView = (next: 'list' | 'calendar') => { if (owns()) { scroll.current = results.current?.scrollTop ?? scroll.current; setView(next) } }
  const chooseDay = (next: string) => { if (owns() && monthDays(next.slice(0, 7)).includes(next)) { setDay(next); setMonth(next.slice(0, 7)) } }
  const moveMonth = (delta: number) => { if (owns()) { const next = shiftMonth(month, delta); setMonth(next); setDay(`${next}-01`) } }
  const open = (plan: PublicationPlan, element: HTMLElement) => {
    if (!owns() || !snapshot || currentSnapshot.current !== snapshot) return
    launcher.current = element
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [plan.id] })
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'inspect', open: true })
    setDetail({ id: plan.id, lifetime: store.getSnapshot().lifetime })
  }
  const selected = detail && owned && selection.inspectorOpen && detail.lifetime === selection.lifetime && detail.id === selection.primarySelectedObject?.id ? snapshot?.plans.find(p => p.id === detail.id) : undefined
  const close = () => {
    if (!owns() || !detail || activeDetail.current !== detail) return
    activeDetail.current = null; setDetail(null)
    if (launcher.current?.isConnected) launcher.current.focus(); else region.current?.focus()
  }
  function timestamp(value: string | null | undefined) {
    if (value === undefined) return text('notSupplied')
    const instant = absoluteInstant(value)
    if (instant === null) return text('indeterminate')
    return `${new Intl.DateTimeFormat(locale, { timeZone: zone, dateStyle: 'medium', timeStyle: 'long' }).format(instant)} · ${value}`
  }
  const account = (id: string) => snapshot?.accounts.find(a => a.id === id)
  const row = (p: PublicationPlan) => <li key={p.id} className="ff-publication-row"><Button type="button" aria-pressed={selection.primarySelectedObject?.id === p.id} onClick={event => open(p, event.currentTarget)}>{p.title || p.id}</Button><span>{account(p.accountId)?.name} · {account(p.accountId)?.platform}</span><Badge>{p.status}</Badge><small>{text(p.timeField)}{p.timeField === 'scheduledAt' || p.timeField === 'publishedAt' ? ` · ${timestamp(p[p.timeField])}` : ''}</small></li>
  const unscheduled = rows.filter(p => p.timeField === 'unscheduled'), indeterminate = rows.filter(p => p.timeField !== 'unscheduled' && !planDay(p, zone))
  const agenda = rows.filter(p => planDay(p, zone) === day)
  return <section ref={region} tabIndex={-1} className="ff-publication" aria-label={text('title')}>
    <header className="ff-page-heading"><div><span>{text('eyebrow')}</span><h1>{text('title')}</h1><p>{text('description')}</p></div></header>
    <p role="status">{text(owned ? status : 'unavailable')}</p>
    {source && permitted && owned ? <>
      <p className="ff-publication-note">{text('verification')}</p>
      <div className="ff-publication-toolbar">
        <Search label={text('search')} placeholder={text('search')} value={filters.query} onChange={event => updateFilters({ query: event.target.value })} />
        <label>{text('account')}<select value={filters.account} onChange={event => updateFilters({ account: event.target.value })}><option value="">{text('allAccounts')}</option>{snapshot?.accounts.map(a => <option key={a.id} value={a.id}>{a.name} · {a.platform} · {a.id}</option>)}</select></label>
        <label>{text('status')}<select value={filters.status} onChange={event => updateFilters({ status: event.target.value })}><option value="">{text('allStatuses')}</option>{[...new Set(snapshot?.plans.map(p => p.status))].sort().map(s => <option key={s}>{s}</option>)}</select></label>
        <label>{text('sort')}<select value={filters.order} onChange={event => updateFilters({ order: event.target.value as 'asc' | 'desc' })}><option value="asc">{text('earliest')}</option><option value="desc">{text('latest')}</option></select></label>
        <Button type="button" onClick={() => { if (owns()) setFilters(defaultFilters) }}>{text('reset')}</Button>
        <Button type="button" onClick={() => void load()}>{text(status === 'error' || status === 'invalid' || status === 'restricted' ? 'retry' : 'refresh')}</Button>
      </div>
      <div className="ff-publication-toolbar"><div role="group" aria-label={text('view')}><Button type="button" aria-pressed={view === 'list'} onClick={() => changeView('list')}>{text('list')}</Button><Button type="button" aria-pressed={view === 'calendar'} onClick={() => changeView('calendar')}>{text('calendar')}</Button></div>
        <label>{text('timezone')}<select value={zone} onChange={event => { if (owns() && displayZones.includes(event.target.value)) setZone(event.target.value) }}>{displayZones.map(z => <option key={z}>{z}</option>)}</select></label><small>{text('timezoneHelp')}</small>
      </div>
      {snapshot ? <><p>{text(snapshot.completeness)} · {text('project')}: {projectId} · {text('version')}: {snapshot.version}</p><p>{text('fetchedAt')}: {timestamp(snapshot.fetchedAt)}</p><p>{text('timeHelp')}</p></> : null}
      <div ref={results} role="region" aria-label={text('results')} className="ff-publication-results" onScroll={event => { if (owns()) scroll.current = event.currentTarget.scrollTop }}>
        {snapshot && !rows.length ? <p>{text(snapshot.plans.length ? 'noMatch' : snapshot.completeness === 'complete' ? 'empty' : 'partialEmpty')}</p> : null}
        {view === 'list' ? <ul className="ff-publication-list">{rows.map(row)}</ul> : <>
          <div className="ff-publication-toolbar"><Button type="button" onClick={() => moveMonth(-1)}>{text('previous')}</Button><h2>{month}</h2><Button type="button" onClick={() => moveMonth(1)}>{text('next')}</Button><Button type="button" onClick={() => chooseDay(today)}>{text('today')}</Button></div>
          <p>{text('interval')}: [{month}-01, {shiftMonth(month, 1)}-01) · {zone}</p>
          <p>{text('selectedDay')}: {day}</p>
          <div className="ff-publication-calendar" role="group" aria-label={text('month')}>
            {Array.from({ length: 7 }, (_, index) => <span key={index} className="ff-publication-weekday">{new Intl.DateTimeFormat(locale, { weekday: 'short', timeZone: 'UTC' }).format(new Date(Date.UTC(2024, 0, 7 + index)))}</span>)}
            {monthDays(month).map(date => {
              const items = rows.filter(p => planDay(p, zone) === date)
              return <div key={date} className="ff-publication-day" style={date.endsWith('-01') ? { gridColumnStart: new Date(`${date}T12:00:00Z`).getUTCDay() + 1 } : undefined}>
                <Button type="button" aria-label={date} aria-pressed={date === day} aria-current={date === today ? 'date' : undefined} onClick={() => chooseDay(date)}>{date.slice(-2)}{date === today ? ` · ${text('today')}` : ''}{date === day ? ` · ${text('selected')}` : ''}</Button>
                <ul>{items.slice(0, 2).map(p => <li key={p.id}><span>{p.title || p.id}</span><small>{text(p.timeField)} · {p.status}</small></li>)}</ul>
                {items.length > 2 ? <Button type="button" onClick={() => chooseDay(date)}>{t('shell.publication.more', { count: items.length - 2, date })}</Button> : null}
              </div>
            })}
          </div>
          <section role="region" aria-label={text('agenda')} className="ff-publication-agenda"><h3>{text('agenda')} · {day}</h3>{agenda.length ? <ul>{agenda.map(row)}</ul> : <p>{text('emptyDay')}</p>}</section>
          <section role="region" aria-label={text('unscheduled')}><h3>{text('unscheduled')}</h3>{unscheduled.length ? <ul>{unscheduled.map(row)}</ul> : <p>{text('noneSupplied')}</p>}</section>
          <section role="region" aria-label={text('indeterminate')}><h3>{text('indeterminate')}</h3>{indeterminate.length ? <ul>{indeterminate.map(row)}</ul> : <p>{text('noneSupplied')}</p>}</section>
        </>}
      </div>
    </> : null}
    {selected && snapshot ? <InteractionDialog title={text('details')} closeLabel={text('close')} onClose={close} className="ff-publication-details">
      <PropertyRow label={text('planId')}>{selected.id}</PropertyRow>
      {selected.title !== undefined ? <PropertyRow label={text('contentTitle')}>{selected.title}</PropertyRow> : null}
      {selected.summary !== undefined ? <PropertyRow label={text('summary')}>{selected.summary}</PropertyRow> : null}
      <PropertyRow label={text('project')}>{selected.projectId}</PropertyRow><PropertyRow label={text('account')}>{account(selected.accountId)?.name} · {selected.accountId} · {account(selected.accountId)?.platform}</PropertyRow>
      <PropertyRow label={text('status')}>{selected.status}</PropertyRow>
      {selected.copyVersion !== undefined ? <PropertyRow label={text('copyVersion')}>{selected.copyVersion}</PropertyRow> : null}
      <PropertyRow label={text('calendarField')}>{text(selected.timeField)}</PropertyRow>
      <PropertyRow label={text('scheduledAt')}>{timestamp(selected.scheduledAt)}</PropertyRow><PropertyRow label={text('publishedAt')}>{timestamp(selected.publishedAt)}</PropertyRow><PropertyRow label={text('fetchedAt')}>{timestamp(snapshot.fetchedAt)}</PropertyRow>
      <h3>{text('artifacts')}</h3><p>{text('artifactLimit')}</p>
      {snapshot.artifacts.filter(a => selected.artifactIds.includes(a.id)).map(a => <div key={a.id}><code>{a.id}</code>{a.name !== undefined ? <p>{a.name}</p> : null}{a.mediaType !== undefined ? <p>{a.mediaType}</p> : null}{a.version !== undefined ? <p>{a.version}</p> : null}</div>)}
      <h3>{text('attempts')}</h3>{snapshot.attempts.filter(a => a.planId === selected.id).map(a => <section key={a.id}><code>{a.id}</code><p>{text('planId')}: {a.planId} · {text('account')}: {a.accountId}</p><Badge>{a.status}</Badge><p>{text('attemptedAt')}: {timestamp(a.attemptedAt)}</p>{a.failureSummary !== undefined ? <p>{a.failureSummary}</p> : null}</section>)}
      <h3>{text('external')}</h3>{snapshot.externalPublications.filter(e => e.planId === selected.id).map(e => <section key={e.id}><code>{e.id}</code><p>{text('attemptId')}: {e.attemptId} · {text('account')}: {e.accountId}</p><Badge>{e.status}</Badge><p>{text('publishedAt')}: {timestamp(e.publishedAt)}</p></section>)}
    </InteractionDialog> : null}
  </section>
}
