import { createContext, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Badge, Button, EmptyState, Panel, PropertyRow, Search, Skeleton, Status } from '../../components/design-system'
import { AsyncStatePanel } from '../../foundation/errors'
import { InteractionDialog } from '../../interaction/InteractionDialog'
import { useInteractionStore, useSelection, useSurfaceAdapter } from '../../interaction/SelectionContext'
import type { InteractionStore } from '../../interaction/model'
import { useTranslation } from '../../localization'
import {
  RenderProjectionError,
  contextKey,
  deriveProgressPercent,
  parseRenderSnapshot,
  renderStatusValues,
  selectRenderJobs,
  sourceAccessExplanation,
  sourceDisposition,
  sourcePresentationOrigin,
  unavailableRendersSource,
  type RenderArtifact,
  type RenderFailureStatus,
  type RenderFilters,
  type RenderProgress,
  type RenderProjection,
  type RenderSnapshot,
  type RenderSource,
} from './source'
import './render-browser.css'

const RendersSourceContext = createContext<RenderSource | undefined>(undefined)
export function RenderBrowserProvider({ source, children }: { source: RenderSource; children: ReactNode }) {
  return <RendersSourceContext.Provider value={source}>{children}</RendersSourceContext.Provider>
}
const adapterIds = new WeakMap<RenderSource['adapter'], number>()
let nextAdapterId = 0
function adapterKey(adapter: RenderSource['adapter']): number {
  if (!adapterIds.has(adapter)) adapterIds.set(adapter, ++nextAdapterId)
  return adapterIds.get(adapter)!
}
const interactionStoreIds = new WeakMap<InteractionStore, number>()
let nextInteractionStoreId = 0
function interactionStoreKey(store: InteractionStore): number {
  if (!interactionStoreIds.has(store)) interactionStoreIds.set(store, ++nextInteractionStoreId)
  return interactionStoreIds.get(store)!
}

export function RenderBrowser({ source: supplied }: { source?: RenderSource }) {
  const store = useInteractionStore()
  const selection = useSelection()
  useSurfaceAdapter({ objects: () => [], supports: [], handle: () => false })
  const owner = useRef({ store, lifetime: selection.lifetime })
  if (owner.current.store !== store) owner.current = { store, lifetime: selection.lifetime }
  useLayoutEffect(() => {
    // StrictMode cleanup/setup re-registers the current surface adapter. An
    // explicit owner/document retirement does not replay this effect.
    owner.current = { store, lifetime: store.getSnapshot().lifetime }
  }, [store])
  const provided = useContext(RendersSourceContext)
  const fallback = useMemo(unavailableRendersSource, [])
  const source = supplied ?? provided ?? fallback
  const sourceKey = JSON.stringify([
    adapterKey(source.adapter), source.adapter.origin, source.readAccessBinding,
    contextKey({ ...source.scope, access: source.access }), interactionStoreKey(store),
  ])
  if (owner.current.lifetime !== selection.lifetime) return <RetiredRenderBrowser />
  return <RenderBrowserSession key={sourceKey} source={source} />
}

function RetiredRenderBrowser() {
  const { t } = useTranslation()
  return <section className="ff-render-browser" aria-label={t('shell.renders.region')}>
    <AsyncStatePanel state="UNAVAILABLE" title={t('shell.renders.ownerRetiredTitle')}><p>{t('shell.renders.ownerRetiredBody')}</p></AsyncStatePanel>
  </section>
}

type BrowserStatus = 'loading' | 'ready' | 'cancelled' | 'invalid' | 'invalid-relationship' | RenderFailureStatus
type Text = (key: string, parameters?: Record<string, string | number>) => string

function displayName(render: RenderProjection): string { return render.name || render.id }
function supplied(value: string | null | undefined, text: Text): ReactNode {
  return value === undefined ? text('notSupplied') : value === null || value === '' ? text('emptySupplied') : value
}
function sourceTime(value: string | null | undefined, text: Text): ReactNode {
  return value === undefined ? text('notSupplied') : value === null ? text('emptySupplied') : <time dateTime={value}>{value}</time>
}
function progressText(progress: RenderProgress | undefined, text: Text): string | null {
  if (!progress) return null
  const percent = deriveProgressPercent(progress)
  if (progress.total === undefined || progress.totalUnit === undefined) return text('progressPartial', { value: progress.value, unit: progress.unit })
  if (percent === null) return text('progressInvalid')
  return text('progressComplete', { value: progress.value, total: progress.total, unit: progress.unit, percent: Number(percent.toFixed(2)) })
}

function RenderBrowserSession({ source }: { source: RenderSource }) {
  const { t } = useTranslation()
  const text: Text = (key, parameters) => t(`shell.renders.${key}`, parameters)
  const disposition = sourceDisposition(source)
  const [status, setStatus] = useState<BrowserStatus>(disposition === 'ready' ? 'loading' : disposition)
  const [snapshot, setSnapshot] = useState<RenderSnapshot | null>(null)
  const [filters, setFilters] = useState<RenderFilters>({ query: '', status: '', order: 'name-asc' })
  const [detailId, setDetailId] = useState<string | null>(null)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [fetchedAt, setFetchedAt] = useState<Date | null>(null)
  const live = useRef(false)
  const generation = useRef(0)
  const sequence = useRef(0)
  const controller = useRef<AbortController | null>(null)
  const listScroll = useRef<HTMLDivElement>(null)
  const pendingScrollTop = useRef(0)

  useLayoutEffect(() => {
    live.current = true
    return () => { live.current = false; generation.current += 1; controller.current?.abort() }
  }, [])
  useLayoutEffect(() => {
    if (status === 'ready' && listScroll.current) listScroll.current.scrollTop = pendingScrollTop.current
  }, [snapshot, status])

  async function load() {
    const current = ++generation.current
    controller.current?.abort()
    pendingScrollTop.current = listScroll.current?.scrollTop ?? pendingScrollTop.current
    setSnapshot(null); setExplanation(null); setFetchedAt(null)
    if (disposition !== 'ready') { setDetailId(null); setStatus(disposition); return }
    const requestController = new AbortController()
    controller.current = requestController
    const request = { scope: source.scope, requestId: `render-observability-${++sequence.current}` }
    setStatus('loading')
    let input: unknown
    try { input = await source.adapter.readProject(request, requestController.signal) }
    catch {
      if (!live.current || requestController.signal.aborted || current !== generation.current) return
      setDetailId(null); setStatus('error'); return
    }
    if (!live.current || requestController.signal.aborted || current !== generation.current) return
    try {
      const result = parseRenderSnapshot(input, request)
      if (result.status === 'ok') { setSnapshot(result); setFetchedAt(new Date()); setStatus('ready') }
      else { setDetailId(null); setStatus(result.status); setExplanation(result.explanation ?? null) }
    } catch (error) {
      if (!live.current || requestController.signal.aborted || current !== generation.current) return
      setDetailId(null)
      setStatus(error instanceof RenderProjectionError && error.kind === 'invalid-relationship' ? 'invalid-relationship' : 'invalid')
    }
  }
  useEffect(() => { void load() }, [])

  function cancel() {
    generation.current += 1; controller.current?.abort()
    setSnapshot(null); setDetailId(null); setExplanation(null); setFetchedAt(null); setStatus('cancelled')
  }

  const jobs = snapshot?.jobs ?? []
  const visible = useMemo(() => selectRenderJobs(jobs, filters), [filters, jobs])
  const detail = snapshot?.jobs.find(job => job.id === detailId) ?? null
  const detailNotFound = status === 'ready' && snapshot !== null && detailId !== null && detail === null
  const filtersChanged = filters.query !== '' || filters.status !== '' || filters.order !== 'name-asc'
  const resetFilters = () => { if (filtersChanged) setFilters({ query: '', status: '', order: 'name-asc' }) }
  const failures: Record<RenderFailureStatus | 'invalid' | 'invalid-relationship', { title: string; body: string; state: 'UNAVAILABLE' | 'BLOCKED' | 'ERROR' }> = {
    unavailable: { title: text('failureUnavailableTitle'), body: text('failureUnavailableBody'), state: 'UNAVAILABLE' },
    denied: { title: text('failureDeniedTitle'), body: text('failureDeniedBody'), state: 'BLOCKED' },
    unknown: { title: text('failureUnknownTitle'), body: text('failureUnknownBody'), state: 'BLOCKED' },
    unsupported: { title: text('failureUnsupportedTitle'), body: text('failureUnsupportedBody'), state: 'UNAVAILABLE' },
    error: { title: text('failureErrorTitle'), body: text('failureErrorBody'), state: 'ERROR' },
    stale: { title: text('failureStaleTitle'), body: text('failureStaleBody'), state: 'BLOCKED' },
    invalid: { title: text('failureInvalidTitle'), body: text('failureInvalidBody'), state: 'ERROR' },
    'invalid-relationship': { title: text('failureRelationshipTitle'), body: text('failureRelationshipBody'), state: 'ERROR' },
  }
  const failure = status !== 'loading' && status !== 'ready' && status !== 'cancelled' ? failures[status] : null
  const origin = sourcePresentationOrigin(source)
  const originKey = origin === 'simulated' ? 'originSimulated' : origin === 'real' ? 'originReal' : 'originUnavailable'
  const visibleExplanation = explanation ?? (disposition === 'ready' ? null : sourceAccessExplanation(source))
  const workflowKey = status === 'loading' ? 'cancel' : status === 'ready' ? 'refresh' : 'retry'

  return <section className="ff-render-browser" aria-label={text('region')}>
    <header className="ff-render-browser-heading">
      <div><span>{text('eyebrow')}</span><h1>{text('title')}</h1><p>{text('description')}</p></div>
      {disposition === 'ready' ? <Button onClick={status === 'loading' ? cancel : () => void load()}>{text(workflowKey)}</Button> : null}
    </header>
    <p className={`ff-render-origin ff-render-origin--${origin}`}><Badge tone={origin === 'simulated' ? 'warning' : 'neutral'}>{text(originKey)}</Badge></p>
    <details className="ff-render-scope"><summary>{text('scope')}</summary><dl><dt>{text('projectId')}</dt><dd><code>{source.scope.projectId}</code></dd></dl></details>
    <p className="ff-render-boundary">{text('boundary')}</p>

    {status === 'loading' ? <AsyncStatePanel state="LOADING" title={text('loadingTitle')}><Skeleton label={text('loadingLabel')} /></AsyncStatePanel> : null}
    {status === 'cancelled' ? <AsyncStatePanel state="UNAVAILABLE" title={text('cancelledTitle')}><p>{text('cancelledBody')}</p></AsyncStatePanel> : null}
    {failure ? <AsyncStatePanel state={failure.state} title={failure.title}><p>{failure.body}</p>{visibleExplanation ? <p className="ff-render-opaque">{visibleExplanation}</p> : null}</AsyncStatePanel> : null}

    {status === 'ready' && snapshot ? <>
      <div className="ff-render-controls">
        <Search label={text('search')} placeholder={text('searchPlaceholder')} value={filters.query} onChange={event => setFilters(current => ({ ...current, query: event.target.value }))} />
        <label>{text('statusLabel')}<select value={filters.status} onChange={event => setFilters(current => ({ ...current, status: event.target.value }))}>
          <option value="">{text('allStatuses')}</option>{renderStatusValues(snapshot.boundary).map(value => <option key={value} value={value}>{value}</option>)}
        </select></label>
        <label>{text('sortLabel')}<select value={filters.order} onChange={event => setFilters(current => ({ ...current, order: event.target.value as RenderFilters['order'] }))}>
          <option value="name-asc">{text('sortAscending')}</option><option value="name-desc">{text('sortDescending')}</option>
        </select></label>
        <Button onClick={resetFilters}>{text('reset')}</Button>
      </div>
      <div className="ff-render-receipt" role="status" aria-live="polite">
        <p>{text(snapshot.boundary.completeness === 'bounded' ? 'snapshotBounded' : 'snapshotComplete', { count: jobs.length, version: snapshot.boundary.version })}</p>
        <p>{snapshot.boundary.sourceUpdatedAt ? text('sourceUpdatedAt', { time: snapshot.boundary.sourceUpdatedAt }) : text('sourceUpdatedMissing')}</p>
        <p>{fetchedAt ? text('fetchedAt', { time: fetchedAt.toISOString() }) : null}</p>
        {snapshot.boundary.freshness === 'stale' ? <Badge tone="warning">{text('sourceStale')}</Badge> : null}
      </div>
      {!jobs.length ? <EmptyState title={text('emptyTitle')} description={text('emptyBody')} />
        : !visible.length ? <EmptyState title={text('noMatchesTitle')} description={text('noMatchesBody')} />
          : <div className="ff-render-list-scroll" ref={listScroll}><ul className="ff-render-browser-list" aria-label={text('list')}>{visible.map(job => {
            const progress = progressText(job.progress, text)
            return <li key={job.id}><Panel title={displayName(job)}>
              <code>{job.id}</code><Status label={job.status} />
              {job.createdAt !== undefined ? <p>{text('summaryCreated', { time: job.createdAt ?? text('emptySupplied') })}</p> : null}
              {job.updatedAt !== undefined ? <p>{text('summaryUpdated', { time: job.updatedAt ?? text('emptySupplied') })}</p> : null}
              {progress ? <p>{progress}</p> : null}
              <Button onClick={() => setDetailId(job.id)} aria-label={text('inspectNamed', { name: displayName(job) })}>{text('inspect')}</Button>
            </Panel></li>
          })}</ul></div>}
    </> : null}

    {detail ? <RenderDetail render={detail} fetchedAt={fetchedAt} text={text} onClose={() => setDetailId(null)} /> : null}
    {detailNotFound ? <InteractionDialog title={text('detailNotFoundTitle')} closeLabel={text('detailNotFoundClose')} onClose={() => setDetailId(null)} className="ff-render-detail">
      <AsyncStatePanel state="UNAVAILABLE" title={text('detailNotFoundHeading')}><p>{text('detailNotFoundBody')}</p></AsyncStatePanel>
    </InteractionDialog> : null}
  </section>
}

function RenderDetail({ render, fetchedAt, text, onClose }: { render: RenderProjection; fetchedAt: Date | null; text: Text; onClose: () => void }) {
  const progress = progressText(render.progress, text)
  return <InteractionDialog title={text('detailTitle')} closeLabel={text('detailClose')} onClose={onClose} className="ff-render-detail">
    <Badge tone="info">{text('detailReadOnly')}</Badge>
    <section className="ff-render-detail-grid" aria-label={text('identitySection')}>
      <PropertyRow label={text('detailId')}><code>{render.id}</code></PropertyRow>
      <PropertyRow label={text('detailName')}><span>{supplied(render.name, text)}</span></PropertyRow>
      <PropertyRow label={text('detailProjectId')}><code>{render.projectId}</code></PropertyRow>
      <PropertyRow label={text('detailStatus')}><span>{render.status}</span></PropertyRow>
      <PropertyRow label={text('detailVersion')}><span>{supplied(render.version, text)}</span></PropertyRow>
      <PropertyRow label={text('detailSourceKind')}><span>{render.source.kind}</span></PropertyRow>
      <PropertyRow label={text('detailSourceId')}><code>{render.source.id}</code></PropertyRow>
      <PropertyRow label={text('detailSourceVersion')}><span>{supplied(render.source.version, text)}</span></PropertyRow>
    </section>
    <section className="ff-render-detail-section"><h3>{text('timesTitle')}</h3>
      <PropertyRow label={text('createdAt')}><span>{sourceTime(render.createdAt, text)}</span></PropertyRow>
      <PropertyRow label={text('updatedAt')}><span>{sourceTime(render.updatedAt, text)}</span></PropertyRow>
      <PropertyRow label={text('startedAt')}><span>{sourceTime(render.startedAt, text)}</span></PropertyRow>
      <PropertyRow label={text('endedAt')}><span>{sourceTime(render.endedAt, text)}</span></PropertyRow>
      <PropertyRow label={text('fetchedAtLabel')}><span>{fetchedAt ? fetchedAt.toISOString() : text('notSupplied')}</span></PropertyRow>
      <p>{text('timeAuthority')}</p>
    </section>
    <section className="ff-render-detail-section"><h3>{text('progressTitle')}</h3>
      {!render.progress ? <p>{text('progressMissing')}</p> : <>
        <p>{progress}</p>
        <PropertyRow label={text('progressValue')}><span>{render.progress.value}</span></PropertyRow>
        <PropertyRow label={text('progressUnit')}><span>{render.progress.unit}</span></PropertyRow>
        <PropertyRow label={text('progressTotal')}><span>{render.progress.total ?? text('notSupplied')}</span></PropertyRow>
        <PropertyRow label={text('progressTotalUnit')}><span>{supplied(render.progress.totalUnit, text)}</span></PropertyRow>
        <PropertyRow label={text('progressStage')}><span>{supplied(render.progress.stage, text)}</span></PropertyRow>
      </>}
    </section>
    <section className="ff-render-detail-section"><h3>{text('taskTitle')}</h3>
      {!render.task ? <p>{text('taskMissing')}</p> : <><PropertyRow label={text('taskId')}><code>{render.task.id}</code></PropertyRow><PropertyRow label={text('taskStatus')}><span>{supplied(render.task.status, text)}</span></PropertyRow><PropertyRow label={text('taskVersion')}><span>{supplied(render.task.version, text)}</span></PropertyRow></>}
      <h4>{text('taskFailureTitle')}</h4>{!render.failure ? <p>{text('failureMissing')}</p> : <FailureDetail failure={render.failure} text={text} />}
    </section>
    <section className="ff-render-detail-section"><h3>{text('attemptsTitle')}</h3>
      {!render.attempts ? <p>{text('attemptsMissing')}</p> : <>{render.attempts.completeness === 'bounded' ? <p>{text('attemptsBounded')}</p> : <p>{text('attemptsComplete')}</p>}{!render.attempts.items.length ? <p>{text('attemptsEmpty')}</p> : <ol className="ff-render-attempts">{render.attempts.items.map(attempt => <li key={attempt.id}>
        <h4>{text('attemptOrdinal', { ordinal: attempt.ordinal })}</h4><PropertyRow label={text('attemptId')}><code>{attempt.id}</code></PropertyRow><PropertyRow label={text('attemptStatus')}><span>{attempt.status}</span></PropertyRow><PropertyRow label={text('attemptTaskId')}><code>{attempt.taskId}</code></PropertyRow><PropertyRow label={text('attemptParent')}><span>{supplied(attempt.parentAttemptId, text)}</span></PropertyRow><PropertyRow label={text('attemptRetry')}><span>{supplied(attempt.retryOfAttemptId, text)}</span></PropertyRow>
        {attempt.failure ? <FailureDetail failure={attempt.failure} text={text} /> : <p>{text('failureMissing')}</p>}
      </li>)}</ol>}</>}
    </section>
    <ArtifactDetail render={render} text={text} />
    <p className="ff-render-readonly-limit">{text('detailLimit')}</p>
  </InteractionDialog>
}

function FailureDetail({ failure, text }: { failure: NonNullable<RenderProjection['failure']>; text: Text }) {
  return <div className="ff-render-failure"><PropertyRow label={text('failureSummary')}><span>{failure.summary}</span></PropertyRow><PropertyRow label={text('failureCode')}><span>{supplied(failure.code, text)}</span></PropertyRow><PropertyRow label={text('failureTime')}><span>{sourceTime(failure.occurredAt, text)}</span></PropertyRow></div>
}
function metadataLabel(value: RenderArtifact['metadataAccess'], text: Text): string {
  return text(value === 'inspectable' ? 'artifactInspectable' : value === 'denied' ? 'artifactDenied' : value === 'unavailable' ? 'artifactUnavailable' : value === 'stale' ? 'artifactStale' : 'artifactUnknown')
}
function ArtifactDetail({ render, text }: { render: RenderProjection; text: Text }) {
  const artifacts = render.artifacts
  return <section className="ff-render-detail-section"><h3>{text('artifactsTitle')}</h3>
    {!artifacts ? <p>{text('artifactsMissing')}</p>
      : artifacts.state === 'empty' ? <p>{text('artifactsEmpty')}</p>
        : artifacts.state !== 'available' ? <><Badge tone="warning">{text(`artifactsState_${artifacts.state}`)}</Badge>{artifacts.explanation ? <p>{artifacts.explanation}</p> : null}</>
          : <>{artifacts.completeness === 'bounded' ? <p>{text('artifactsBounded')}</p> : <p>{text('artifactsComplete')}</p>}
            {!artifacts.items.length ? <p>{text('artifactsEmpty')}</p> : <ul className="ff-render-artifacts">{artifacts.items.map(artifact => artifact.metadataAccess !== 'inspectable'
              ? <li key={artifact.id}><Badge tone="warning">{metadataLabel(artifact.metadataAccess, text)}</Badge></li>
              : <li key={artifact.id}>
              <div><strong>{artifact.name || artifact.id}</strong><code>{artifact.id}</code></div><Badge tone="info">{metadataLabel(artifact.metadataAccess, text)}</Badge>
              <PropertyRow label={text('artifactType')}><span>{artifact.type}</span></PropertyRow><PropertyRow label={text('artifactAvailability')}><span>{artifact.availability}</span></PropertyRow><PropertyRow label={text('artifactVersion')}><span>{supplied(artifact.version, text)}</span></PropertyRow><PropertyRow label={text('artifactTaskId')}><code>{artifact.taskId}</code></PropertyRow>
              <p>{text('artifactNoOpen')}</p>
            </li>)}</ul>}
          </>}
  </section>
}
