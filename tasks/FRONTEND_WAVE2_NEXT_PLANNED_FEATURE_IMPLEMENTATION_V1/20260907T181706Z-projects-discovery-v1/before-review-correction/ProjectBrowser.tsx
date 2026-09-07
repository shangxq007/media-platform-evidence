import { createContext, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Badge, Button, EmptyState, Panel, PropertyRow, Search, Skeleton, Status } from '../../components/design-system'
import { AsyncStatePanel } from '../../foundation/errors'
import { InteractionDialog } from '../../interaction/InteractionDialog'
import { useTranslation } from '../../localization'
import { localhostProjectsFixture } from './fixture'
import {
  contextKey, parseRecentProjects, projectStatusValues, selectProjects, sourceDisposition,
  unavailableProjectsSource, type ProjectFilters, type ProjectListFailureStatus, type ProjectsSource,
  type RecentProjectsSnapshot,
} from './source'

const ProjectsSourceContext = createContext<ProjectsSource | undefined>(undefined)
export function ProjectBrowserProvider({ source, children }: { source: ProjectsSource; children: ReactNode }) {
  return <ProjectsSourceContext.Provider value={source}>{children}</ProjectsSourceContext.Provider>
}

const adapterIds = new WeakMap<ProjectsSource['adapter'], number>()
let nextAdapterId = 0
function adapterKey(adapter: ProjectsSource['adapter']) {
  if (!adapterIds.has(adapter)) adapterIds.set(adapter, ++nextAdapterId)
  return adapterIds.get(adapter)
}

export function ProjectBrowser({ workspaceId, source: supplied }: { workspaceId: string; source?: ProjectsSource }) {
  const provided = useContext(ProjectsSourceContext)
  const defaultSource = useMemo(() => typeof window === 'undefined'
    ? unavailableProjectsSource(workspaceId)
    : localhostProjectsFixture(window.location, workspaceId) ?? unavailableProjectsSource(workspaceId), [workspaceId])
  const source = supplied ?? provided ?? defaultSource
  const sourceKey = JSON.stringify([workspaceId, adapterKey(source.adapter), contextKey({ ...source.scope, access: source.access }), source.adapter.origin])
  // The keyed subtree removes the prior identity's content in the same render.
  // Its request cleanup independently rejects adapters that ignore AbortSignal.
  return <ProjectBrowserSession key={sourceKey} workspaceId={workspaceId} source={source} />
}

type BrowserStatus = 'loading' | 'ready' | 'cancelled' | ProjectListFailureStatus
type LocalProjectAction =
  | { category: 'LOCAL_EPHEMERAL'; type: 'inspect-project'; projectId: string }
  | { category: 'LOCAL_EPHEMERAL'; type: 'close-project-inspection' }

function ProjectBrowserSession({ workspaceId, source }: { workspaceId: string; source: ProjectsSource }) {
  const { t } = useTranslation()
  const text = (key: string, parameters?: Record<string, string | number>) => t(`shell.projects.${key}`, parameters)
  const disposition = sourceDisposition(source, workspaceId)
  const [status, setStatus] = useState<BrowserStatus>(disposition === 'ready' ? 'loading' : disposition)
  const [snapshot, setSnapshot] = useState<RecentProjectsSnapshot | null>(null)
  const [filters, setFilters] = useState<ProjectFilters>({ query: '', status: '', order: 'name-asc' })
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
    const request = { scope: source.scope, requestId: `recent-projects-${++sequence.current}` }
    setStatus('loading')
    try {
      const result = parseRecentProjects(await source.adapter.listRecent(request, requestController.signal), request)
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

  // One page-local dispatcher owns all local inspection entry handlers. It is
  // deliberately not registered as a command and never changes canonical state.
  function dispatchLocal(action: LocalProjectAction) {
    if (action.category !== 'LOCAL_EPHEMERAL') return
    setDetailId(action.type === 'inspect-project' ? action.projectId : null)
  }

  const projects = snapshot?.projects ?? []
  const statusValues = useMemo(() => projectStatusValues(projects), [projects])
  const visible = useMemo(() => selectProjects(projects, filters), [filters, projects])
  const detail = visible.find(project => project.id === detailId)
  useEffect(() => {
    if (detailId && !visible.some(project => project.id === detailId)) setDetailId(null)
  }, [detailId, visible])

  const failureCopy: Record<ProjectListFailureStatus, { title: string; body: string; state: 'UNAVAILABLE' | 'BLOCKED' | 'ERROR' }> = {
    unavailable: { title: text('failureUnavailableTitle'), body: text('failureUnavailableBody'), state: 'UNAVAILABLE' },
    denied: { title: text('failureDeniedTitle'), body: text('failureDeniedBody'), state: 'BLOCKED' },
    unknown: { title: text('failureUnknownTitle'), body: text('failureUnknownBody'), state: 'BLOCKED' },
    unsupported: { title: text('failureUnsupportedTitle'), body: text('failureUnsupportedBody'), state: 'UNAVAILABLE' },
    error: { title: text('failureErrorTitle'), body: text('failureErrorBody'), state: 'ERROR' },
  }
  const failure = status !== 'loading' && status !== 'ready' && status !== 'cancelled' ? failureCopy[status] : null
  const originKey = source.adapter.origin === 'simulated' ? 'originSimulated' : source.adapter.origin === 'real' ? 'originReal' : 'originUnavailable'

  return <section className="ff-project-browser" aria-label={text('region')}>
    <header className="ff-project-browser-heading">
      <div><span>{text('eyebrow')}</span><h1>{text('title')}</h1><p>{text('description')}</p></div>
      {status === 'ready' ? <Button onClick={() => void load()}>{text('refresh')}</Button> : null}
    </header>
    <p className={`ff-project-origin ff-project-origin--${source.adapter.origin}`}><Badge tone={source.adapter.origin === 'simulated' ? 'warning' : 'neutral'}>{text(originKey)}</Badge></p>
    <p className="ff-project-boundary">{text('boundary')}</p>

    {status === 'loading' ? <AsyncStatePanel state="LOADING" title={text('loadingTitle')}><Skeleton label={text('loadingLabel')} /><Button onClick={cancel}>{text('cancel')}</Button></AsyncStatePanel> : null}
    {status === 'cancelled' ? <AsyncStatePanel state="UNAVAILABLE" title={text('cancelledTitle')}><p>{text('cancelledBody')}</p><Button onClick={() => void load()}>{text('retry')}</Button></AsyncStatePanel> : null}
    {failure ? <AsyncStatePanel state={failure.state} title={failure.title}><p>{failure.body}</p>{explanation ? <p className="ff-project-opaque-explanation">{explanation}</p> : null}{disposition === 'ready' ? <Button onClick={() => void load()}>{text('retry')}</Button> : null}</AsyncStatePanel> : null}

    {status === 'ready' && snapshot ? <>
      <div className="ff-project-controls">
        <Search label={text('search')} placeholder={text('searchPlaceholder')} value={filters.query} onChange={event => setFilters(current => ({ ...current, query: event.target.value }))} />
        <label>{text('statusLabel')}<select value={filters.status} onChange={event => setFilters(current => ({ ...current, status: event.target.value }))}>
          <option value="">{text('allStatuses')}</option>
          {statusValues.map(value => <option key={value} value={value}>{value}</option>)}
        </select></label>
        <label>{text('sortLabel')}<select value={filters.order} onChange={event => setFilters(current => ({ ...current, order: event.target.value as ProjectFilters['order'] }))}>
          <option value="name-asc">{text('sortAscending')}</option><option value="name-desc">{text('sortDescending')}</option>
        </select></label>
      </div>
      <p role="status" aria-live="polite">{text(snapshot.boundary.limited ? 'snapshotLimited' : 'snapshotRecent', { count: projects.length })}</p>
      {!projects.length ? <EmptyState title={text('emptyTitle')} description={text('emptyBody')} />
        : !visible.length ? <EmptyState title={text('noMatchesTitle')} description={text('noMatchesBody')} action={<Button onClick={() => setFilters({ query: '', status: '', order: 'name-asc' })}>{text('reset')}</Button>} />
          : <ul className="ff-project-browser-list" aria-label={text('list')}>
            {visible.map(project => <li key={project.id}><Panel title={project.name}>
              <p className="ff-project-description">{project.description || text('noDescription')}</p>
              <Status label={project.status ?? text('statusUnknown')} />
              <Button onClick={() => dispatchLocal({ category: 'LOCAL_EPHEMERAL', type: 'inspect-project', projectId: project.id })} aria-label={text('inspectNamed', { name: project.name })}>{text('inspect')}</Button>
            </Panel></li>)}
          </ul>}
    </> : null}

    {detail ? <InteractionDialog title={text('detailTitle')} closeLabel={text('detailClose')} onClose={() => dispatchLocal({ category: 'LOCAL_EPHEMERAL', type: 'close-project-inspection' })} className="ff-project-detail">
      <Badge tone="info">{text('detailReadOnly')}</Badge>
      <h3>{detail.name}</h3>
      <p className="ff-project-detail-description">{detail.description || text('noDescription')}</p>
      <PropertyRow label={text('detailId')}><code>{detail.id}</code></PropertyRow>
      <PropertyRow label={text('detailStatus')}><span>{detail.status ?? text('statusUnknown')}</span></PropertyRow>
      <PropertyRow label={text('detailCreated')}><span>{detail.createdAt ?? text('notProjected')}</span></PropertyRow>
      <p>{text('detailLimit')}</p>
    </InteractionDialog> : null}
  </section>
}
