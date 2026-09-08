import { createContext, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { RENDER_JOB_STATUSES } from '../../contracts/app/render-job'
import { Badge, Button, EmptyState, Panel, PropertyRow, Search, Skeleton, Status } from '../../components/design-system'
import { AsyncStatePanel } from '../../foundation/errors'
import { InteractionDialog } from '../../interaction/InteractionDialog'
import { useTranslation } from '../../localization'
import { localhostRendersFixture } from './fixture'
import {
  contextKey,
  parseRenderSummaries,
  selectRenderJobs,
  sourceAccessExplanation,
  sourceDisposition,
  sourcePresentationOrigin,
  unavailableRendersSource,
  type RenderFilters,
  type RenderListFailureStatus,
  type RenderSummariesSnapshot,
  type RendersSource,
} from './source'

const RendersSourceContext = createContext<RendersSource | undefined>(undefined)
export function RenderBrowserProvider({ source, children }: { source: RendersSource; children: ReactNode }) {
  return <RendersSourceContext.Provider value={source}>{children}</RendersSourceContext.Provider>
}

const adapterIds = new WeakMap<RendersSource['adapter'], number>()
let nextAdapterId = 0
function adapterKey(adapter: RendersSource['adapter']): number {
  if (!adapterIds.has(adapter)) adapterIds.set(adapter, ++nextAdapterId)
  return adapterIds.get(adapter)!
}

export function RenderBrowser({ source: supplied }: { source?: RendersSource }) {
  const provided = useContext(RendersSourceContext)
  const defaultSource = useMemo(() => typeof window === 'undefined'
    ? unavailableRendersSource()
    : localhostRendersFixture(window.location) ?? unavailableRendersSource(), [])
  const source = supplied ?? provided ?? defaultSource
  const sourceKey = JSON.stringify([
    adapterKey(source.adapter), source.adapter.origin, contextKey({ ...source.scope, access: source.access }),
  ])
  // A source/identity change synchronously replaces the prior subtree. Cleanup
  // below also rejects adapters that resolve successfully after cancellation.
  return <RenderBrowserSession key={sourceKey} source={source} />
}

type BrowserStatus = 'loading' | 'ready' | 'cancelled' | RenderListFailureStatus

function RenderBrowserSession({ source }: { source: RendersSource }) {
  const { t } = useTranslation()
  const text = (key: string, parameters?: Record<string, string | number>) => t(`shell.renders.${key}`, parameters)
  const disposition = sourceDisposition(source)
  const [status, setStatus] = useState<BrowserStatus>(disposition === 'ready' ? 'loading' : disposition)
  const [snapshot, setSnapshot] = useState<RenderSummariesSnapshot | null>(null)
  const [filters, setFilters] = useState<RenderFilters>({ query: '', status: '', order: 'id-asc' })
  const [detailId, setDetailId] = useState<string | null>(null)
  const [explanation, setExplanation] = useState<string | null>(null)
  const live = useRef(false)
  const generation = useRef(0)
  const sequence = useRef(0)
  const controller = useRef<AbortController | null>(null)

  useLayoutEffect(() => {
    live.current = true
    return () => {
      live.current = false
      generation.current += 1
      controller.current?.abort()
    }
  }, [])

  async function load() {
    const current = ++generation.current
    controller.current?.abort()
    setSnapshot(null)
    setDetailId(null)
    setExplanation(null)
    if (disposition !== 'ready') {
      setStatus(disposition)
      return
    }
    const requestController = new AbortController()
    controller.current = requestController
    const request = { scope: source.scope, requestId: `render-summaries-${++sequence.current}` }
    setStatus('loading')
    try {
      const result = parseRenderSummaries(await source.adapter.listProject(request, requestController.signal), request)
      if (!live.current || requestController.signal.aborted || current !== generation.current) return
      if (result.status === 'ok') {
        setSnapshot(result)
        setStatus('ready')
      } else {
        setStatus(result.status)
        setExplanation(result.explanation ?? null)
      }
    } catch {
      if (!live.current || requestController.signal.aborted || current !== generation.current) return
      setSnapshot(null)
      setDetailId(null)
      setStatus('error')
    }
  }

  useEffect(() => { void load() }, [])

  function cancel() {
    generation.current += 1
    controller.current?.abort()
    setSnapshot(null)
    setDetailId(null)
    setExplanation(null)
    setStatus('cancelled')
  }

  const jobs = snapshot?.jobs ?? []
  const visible = useMemo(() => selectRenderJobs(jobs, filters), [filters, jobs])
  const detail = visible.find(job => job.id === detailId)
  useEffect(() => {
    if (detailId && !visible.some(job => job.id === detailId)) setDetailId(null)
  }, [detailId, visible])

  const failureCopy: Record<RenderListFailureStatus, { title: string; body: string; state: 'UNAVAILABLE' | 'BLOCKED' | 'ERROR' }> = {
    unavailable: { title: text('failureUnavailableTitle'), body: text('failureUnavailableBody'), state: 'UNAVAILABLE' },
    denied: { title: text('failureDeniedTitle'), body: text('failureDeniedBody'), state: 'BLOCKED' },
    unknown: { title: text('failureUnknownTitle'), body: text('failureUnknownBody'), state: 'BLOCKED' },
    unsupported: { title: text('failureUnsupportedTitle'), body: text('failureUnsupportedBody'), state: 'UNAVAILABLE' },
    error: { title: text('failureErrorTitle'), body: text('failureErrorBody'), state: 'ERROR' },
  }
  const failure = status !== 'loading' && status !== 'ready' && status !== 'cancelled' ? failureCopy[status] : null
  const presentationOrigin = sourcePresentationOrigin(source)
  const originKey = presentationOrigin === 'simulated' ? 'originSimulated' : presentationOrigin === 'real' ? 'originReal' : 'originUnavailable'
  const visibleExplanation = explanation ?? (disposition === 'ready' ? null : sourceAccessExplanation(source))
  const workflowLabel = status === 'loading' ? 'cancel' : status === 'ready' ? 'refresh' : 'retry'

  return <section className="ff-render-browser" aria-label={text('region')}>
    <header className="ff-render-browser-heading">
      <div><span>{text('eyebrow')}</span><h1>{text('title')}</h1><p>{text('description')}</p></div>
      {disposition === 'ready'
        ? <Button onClick={status === 'loading' ? cancel : () => void load()}>{text(workflowLabel)}</Button>
        : null}
    </header>
    <p className={`ff-render-origin ff-render-origin--${presentationOrigin}`}><Badge tone={presentationOrigin === 'simulated' ? 'warning' : 'neutral'}>{text(originKey)}</Badge></p>
    <PropertyRow label={text('projectId')}><code>{source.scope.projectId}</code></PropertyRow>
    <p className="ff-render-boundary">{text('boundary')}</p>

    {status === 'loading' ? <AsyncStatePanel state="LOADING" title={text('loadingTitle')}><Skeleton label={text('loadingLabel')} /></AsyncStatePanel> : null}
    {status === 'cancelled' ? <AsyncStatePanel state="UNAVAILABLE" title={text('cancelledTitle')}><p>{text('cancelledBody')}</p></AsyncStatePanel> : null}
    {failure ? <AsyncStatePanel state={failure.state} title={failure.title}><p>{failure.body}</p>{visibleExplanation ? <p className="ff-render-opaque-explanation">{visibleExplanation}</p> : null}</AsyncStatePanel> : null}

    {status === 'ready' && snapshot ? <>
      <div className="ff-render-controls">
        <Search label={text('search')} placeholder={text('searchPlaceholder')} value={filters.query} onChange={event => setFilters(current => ({ ...current, query: event.target.value }))} />
        <label>{text('statusLabel')}<select value={filters.status} onChange={event => setFilters(current => ({ ...current, status: event.target.value }))}>
          <option value="">{text('allStatuses')}</option>
          {RENDER_JOB_STATUSES.map(value => <option key={value} value={value}>{value}</option>)}
        </select></label>
        <label>{text('sortLabel')}<select value={filters.order} onChange={event => setFilters(current => ({ ...current, order: event.target.value as RenderFilters['order'] }))}>
          <option value="id-asc">{text('sortAscending')}</option><option value="id-desc">{text('sortDescending')}</option>
        </select></label>
      </div>
      <p role="status" aria-live="polite">{text(snapshot.boundary.limited ? 'snapshotLimited' : 'snapshotBounded', { count: jobs.length })}</p>
      {!jobs.length ? <EmptyState title={text('emptyTitle')} description={text('emptyBody')} />
        : !visible.length ? <EmptyState title={text('noMatchesTitle')} description={text('noMatchesBody')} action={<Button onClick={() => setFilters({ query: '', status: '', order: 'id-asc' })}>{text('reset')}</Button>} />
          : <ul className="ff-render-browser-list" aria-label={text('list')}>
            {visible.map(job => <li key={job.id}><Panel title={job.id}>
              <p className="ff-render-profile">{job.profile}</p>
              <Status label={job.status} />
              <Button onClick={() => setDetailId(job.id)} aria-label={text('inspectNamed', { id: job.id })}>{text('inspect')}</Button>
            </Panel></li>)}
          </ul>}
    </> : null}

    {detail ? <InteractionDialog title={text('detailTitle')} closeLabel={text('detailClose')} onClose={() => setDetailId(null)} className="ff-render-detail">
      <Badge tone="info">{text('detailReadOnly')}</Badge>
      <PropertyRow label={text('detailId')}><code>{detail.id}</code></PropertyRow>
      <PropertyRow label={text('detailProjectId')}><code>{detail.projectId}</code></PropertyRow>
      <PropertyRow label={text('detailTimelineSnapshotId')}><code>{detail.timelineSnapshotId}</code></PropertyRow>
      <PropertyRow label={text('detailProfile')}><span>{detail.profile}</span></PropertyRow>
      <PropertyRow label={text('detailStatus')}><span>{detail.status}</span></PropertyRow>
      <p>{text('detailLimit')}</p>
    </InteractionDialog> : null}
  </section>
}
