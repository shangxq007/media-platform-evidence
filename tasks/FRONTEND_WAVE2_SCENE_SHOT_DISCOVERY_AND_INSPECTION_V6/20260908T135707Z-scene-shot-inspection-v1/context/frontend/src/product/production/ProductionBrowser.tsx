import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Badge, Button, EmptyState, Panel, PropertyRow, Search, Skeleton, Status } from '../../components/design-system'
import { AsyncStatePanel } from '../../foundation/errors'
import { InteractionDialog } from '../../interaction/InteractionDialog'
import { useInteractionStore, useSelection, useSurfaceAdapter } from '../../interaction/SelectionContext'
import type { InteractionStore } from '../../interaction/model'
import { useTranslation } from '../../localization'
import {
  parseProductionSnapshot,
  productionAccessExplanation,
  productionContextKey,
  productionPresentationOrigin,
  productionSourceDisposition,
  sceneStatusValues,
  selectScenes,
  type ProductionSnapshot,
} from './model'
import { productionAdapterKey, useProvidedProductionSource } from './source'
import { unavailableProductionSource } from './simulatedSource'
import type {
  ProductionFailureStatus,
  ProductionReference,
  ProductionSource,
  SceneFilters,
  SceneProjection,
  ShotProjection,
} from './types'
import './production.css'

type ExpectedScope = { readonly workspaceId: string; readonly projectId: string }
type BrowserStatus = 'loading' | 'ready' | 'cancelled' | 'invalid' | ProductionFailureStatus
type Detail = { readonly kind: 'SCENE'; readonly value: SceneProjection } | { readonly kind: 'SHOT'; readonly value: ShotProjection }

const interactionStoreIds = new WeakMap<InteractionStore, number>()
let nextInteractionStoreId = 0
function interactionStoreKey(store: InteractionStore): number {
  if (!interactionStoreIds.has(store)) interactionStoreIds.set(store, ++nextInteractionStoreId)
  return interactionStoreIds.get(store)!
}

export function ProductionBrowser({ expectedScope, source: supplied }: { expectedScope: ExpectedScope; source?: ProductionSource }) {
  const store = useInteractionStore()
  const selection = useSelection()
  useSurfaceAdapter({ objects: () => [], supports: [], handle: () => false })
  const owner = useRef({ store, lifetime: selection.lifetime })
  if (owner.current.store !== store) owner.current = { store, lifetime: selection.lifetime }
  useLayoutEffect(() => {
    // StrictMode replays layout-effect cleanup/setup against the same mounted
    // store. Accept the current lifetime only when the adapter setup itself is
    // replayed. Explicit owner/document retirement does not rerun this effect.
    owner.current = { store, lifetime: store.getSnapshot().lifetime }
  }, [store])
  const ownerRetired = owner.current.lifetime !== selection.lifetime
  const provided = useProvidedProductionSource()
  const fallback = useMemo(() => unavailableProductionSource(expectedScope), [expectedScope.workspaceId, expectedScope.projectId])
  const source = supplied ?? provided ?? fallback
  const sourceKey = JSON.stringify([
    productionAdapterKey(source.adapter), source.adapter.origin,
    source.readAccessBinding, productionContextKey({ ...source.scope, access: source.access }),
    expectedScope.workspaceId, expectedScope.projectId, interactionStoreKey(store),
  ])
  if (ownerRetired) return <RetiredProductionBrowser />
  return <ProductionBrowserSession key={sourceKey} expectedScope={expectedScope} source={source} />
}

function RetiredProductionBrowser() {
  const { t } = useTranslation()
  return <section className="ff-production-browser" aria-label={t('shell.productionBrowser.region')}>
    <AsyncStatePanel state="UNAVAILABLE" title={t('shell.productionBrowser.ownerRetiredTitle')}><p>{t('shell.productionBrowser.ownerRetiredBody')}</p></AsyncStatePanel>
  </section>
}

function displayName(entity: SceneProjection | ShotProjection): string {
  return entity.name ?? entity.id
}

function ProductionBrowserSession({ expectedScope, source }: { expectedScope: ExpectedScope; source: ProductionSource }) {
  const { t } = useTranslation()
  const text = (key: string, parameters?: Record<string, string | number>) => t(`shell.productionBrowser.${key}`, parameters)
  const disposition = productionSourceDisposition(source, expectedScope)
  const [status, setStatus] = useState<BrowserStatus>(disposition === 'ready' ? 'loading' : disposition)
  const [snapshot, setSnapshot] = useState<ProductionSnapshot | null>(null)
  const [filters, setFilters] = useState<SceneFilters>({ query: '', status: '', order: 'name-asc' })
  const [sceneId, setSceneId] = useState<string | null>(null)
  const [detail, setDetail] = useState<Detail | null>(null)
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
    setSceneId(null)
    setDetail(null)
    setExplanation(null)
    if (disposition !== 'ready') { setStatus(disposition); return }
    const requestController = new AbortController()
    controller.current = requestController
    const request = { scope: source.scope, requestId: `production-snapshot-${++sequence.current}` }
    setStatus('loading')
    let input: unknown
    try {
      input = await source.adapter.readProject(request, requestController.signal)
    } catch {
      if (!live.current || requestController.signal.aborted || current !== generation.current) return
      setStatus('error')
      return
    }
    if (!live.current || requestController.signal.aborted || current !== generation.current) return
    try {
      const result = parseProductionSnapshot(input, request)
      if (result.status === 'ok') { setSnapshot(result); setStatus('ready') }
      else { setStatus(result.status); setExplanation(result.explanation ?? null) }
    } catch {
      if (!live.current || requestController.signal.aborted || current !== generation.current) return
      setStatus('invalid')
    }
  }

  useEffect(() => { void load() }, [])

  function cancel() {
    generation.current += 1
    controller.current?.abort()
    setSnapshot(null); setSceneId(null); setDetail(null); setExplanation(null); setStatus('cancelled')
  }

  const scenes = snapshot?.scenes ?? []
  const visibleScenes = useMemo(() => selectScenes(scenes, filters), [filters, scenes])
  const selectedScene = visibleScenes.find(scene => scene.id === sceneId) ?? null
  const relatedShotIds = new Set(snapshot?.relations.filter(relation => relation.sceneId === selectedScene?.id).map(relation => relation.shotId) ?? [])
  const relatedShots = snapshot?.shots.filter(shot => relatedShotIds.has(shot.id)) ?? []
  const filtersChanged = filters.query !== '' || filters.status !== '' || filters.order !== 'name-asc'
  const resetFilters = () => {
    if (filtersChanged) setFilters({ query: '', status: '', order: 'name-asc' })
  }
  useEffect(() => {
    if (sceneId && !visibleScenes.some(scene => scene.id === sceneId)) { setSceneId(null); setDetail(null) }
  }, [sceneId, visibleScenes])

  const failures: Record<ProductionFailureStatus | 'invalid', { title: string; body: string; state: 'UNAVAILABLE' | 'BLOCKED' | 'ERROR' }> = {
    unavailable: { title: text('failureUnavailableTitle'), body: text('failureUnavailableBody'), state: 'UNAVAILABLE' },
    denied: { title: text('failureDeniedTitle'), body: text('failureDeniedBody'), state: 'BLOCKED' },
    unknown: { title: text('failureUnknownTitle'), body: text('failureUnknownBody'), state: 'BLOCKED' },
    unsupported: { title: text('failureUnsupportedTitle'), body: text('failureUnsupportedBody'), state: 'UNAVAILABLE' },
    error: { title: text('failureErrorTitle'), body: text('failureErrorBody'), state: 'ERROR' },
    invalid: { title: text('failureInvalidTitle'), body: text('failureInvalidBody'), state: 'ERROR' },
    stale: { title: text('failureStaleTitle'), body: text('failureStaleBody'), state: 'BLOCKED' },
  }
  const failure = status !== 'loading' && status !== 'ready' && status !== 'cancelled' ? failures[status] : null
  const origin = productionPresentationOrigin(source)
  const originKey = origin === 'simulated' ? 'originSimulated' : origin === 'real' ? 'originReal' : 'originUnavailable'
  const visibleExplanation = explanation ?? (disposition === 'ready' ? null : productionAccessExplanation(source))
  const workflowKey = status === 'loading' ? 'cancel' : status === 'ready' ? 'refresh' : 'retry'

  return <section className="ff-production-browser" aria-label={text('region')}>
    <header className="ff-production-heading">
      <div><span>{text('eyebrow')}</span><h1>{text('title')}</h1><p>{text('description')}</p></div>
      {disposition === 'ready' ? <Button onClick={status === 'loading' ? cancel : () => void load()}>{text(workflowKey)}</Button> : null}
    </header>
    <p className={`ff-production-origin ff-production-origin--${origin}`}><Badge tone={origin === 'simulated' ? 'warning' : 'neutral'}>{text(originKey)}</Badge></p>
    <details className="ff-production-scope"><summary>{text('scope')}</summary><dl>
      <dt>{text('workspaceId')}</dt><dd><code>{source.scope.workspaceId}</code></dd>
      <dt>{text('projectId')}</dt><dd><code>{source.scope.projectId}</code></dd>
    </dl></details>
    <p className="ff-production-boundary">{text('boundary')}</p>

    {status === 'loading' ? <AsyncStatePanel state="LOADING" title={text('loadingTitle')}><Skeleton label={text('loadingLabel')} /></AsyncStatePanel> : null}
    {status === 'cancelled' ? <AsyncStatePanel state="UNAVAILABLE" title={text('cancelledTitle')}><p>{text('cancelledBody')}</p></AsyncStatePanel> : null}
    {failure ? <AsyncStatePanel state={failure.state} title={failure.title}><p>{failure.body}</p>{visibleExplanation ? <p className="ff-production-opaque">{visibleExplanation}</p> : null}</AsyncStatePanel> : null}

    {status === 'ready' && snapshot ? <>
      <div className="ff-production-controls">
        <Search label={text('search')} placeholder={text('searchPlaceholder')} value={filters.query} onChange={event => setFilters(current => ({ ...current, query: event.target.value }))} />
        <label>{text('statusLabel')}<select value={filters.status} onChange={event => setFilters(current => ({ ...current, status: event.target.value }))}>
          <option value="">{text('allStatuses')}</option>{sceneStatusValues(scenes).map(value => <option key={value} value={value}>{value}</option>)}
        </select></label>
        <label>{text('sortLabel')}<select value={filters.order} onChange={event => setFilters(current => ({ ...current, order: event.target.value as SceneFilters['order'] }))}>
          <option value="name-asc">{text('sortAscending')}</option><option value="name-desc">{text('sortDescending')}</option>
        </select></label>
        <Button aria-disabled={!filtersChanged} onClick={resetFilters}>{text('reset')}</Button>
      </div>
      <p role="status" aria-live="polite">{text(snapshot.boundary.completeness === 'bounded' ? 'snapshotBounded' : 'snapshotComplete', { sceneCount: scenes.length, shotCount: snapshot.shots.length, version: snapshot.boundary.version })}</p>
      {!scenes.length ? <EmptyState title={text('emptyTitle')} description={text('emptyBody')} />
        : !visibleScenes.length ? <EmptyState title={text('noMatchesTitle')} description={text('noMatchesBody')} />
          : <div className="ff-production-layout">
            <ul className="ff-production-scene-list" aria-label={text('sceneList')}>{visibleScenes.map(scene => <li key={scene.id}>
              <Panel title={displayName(scene)} className={scene.id === sceneId ? 'ff-production-selected' : ''}>
                <p>{scene.description === undefined || scene.description === null ? text('notSupplied') : scene.description || text('emptySupplied')}</p>
                <Status label={scene.status ?? text('notSupplied')} />
                <div className="ff-production-actions"><Button onClick={() => { setSceneId(scene.id); setDetail(null) }} aria-pressed={scene.id === sceneId} aria-label={text('browseSceneNamed', { name: displayName(scene) })}>{text('browseScene')}</Button><Button onClick={() => setDetail({ kind: 'SCENE', value: scene })} aria-label={text('inspectSceneNamed', { name: displayName(scene) })}>{text('inspect')}</Button></div>
              </Panel>
            </li>)}</ul>
            <Panel title={selectedScene ? text('relatedShotsTitle', { name: displayName(selectedScene) }) : text('selectSceneTitle')} className="ff-production-shots">
              {!selectedScene ? <p>{text('selectSceneBody')}</p>
                : !relatedShots.length ? <EmptyState title={text('noShotsTitle')} description={text('noShotsBody')} />
                  : <ul aria-label={text('shotListNamed', { name: displayName(selectedScene) })}>{relatedShots.map(shot => <li key={shot.id}>
                    <div><strong>{displayName(shot)}</strong><span>{shot.status ?? text('notSupplied')}</span></div>
                    <Button onClick={() => setDetail({ kind: 'SHOT', value: shot })} aria-label={text('inspectShotNamed', { name: displayName(shot) })}>{text('inspect')}</Button>
                  </li>)}</ul>}
            </Panel>
          </div>}
    </> : null}

    {detail ? <ProductionDetail detail={detail} text={text} onClose={() => setDetail(null)} /> : null}
  </section>
}

function ProductionDetail({ detail, text, onClose }: { detail: Detail; text: (key: string, parameters?: Record<string, string | number>) => string; onClose: () => void }) {
  const value = detail.value
  const field = (content: string | null | undefined) => content === undefined || content === null ? text('notSupplied') : content || text('emptySupplied')
  return <InteractionDialog title={text(detail.kind === 'SCENE' ? 'sceneDetailTitle' : 'shotDetailTitle')} closeLabel={text('detailClose')} onClose={onClose} className="ff-production-detail">
    <Badge tone="info">{text('detailReadOnly')}</Badge>
    <PropertyRow label={text('detailKind')}><span>{detail.kind}</span></PropertyRow>
    <PropertyRow label={text('detailId')}><code>{value.id}</code></PropertyRow>
    <PropertyRow label={text('detailProjectId')}><code>{value.projectId}</code></PropertyRow>
    <PropertyRow label={text('detailName')}><span>{field(value.name)}</span></PropertyRow>
    <PropertyRow label={text('detailDescription')}><span>{field(value.description)}</span></PropertyRow>
    <PropertyRow label={text('detailStatus')}><span>{field(value.status)}</span></PropertyRow>
    <PropertyRow label={text('detailVersion')}><span>{field(value.version)}</span></PropertyRow>
    {detail.kind === 'SHOT' ? <ReferenceList references={detail.value.references ?? []} text={text} /> : null}
    <p>{text('detailLimit')}</p>
  </InteractionDialog>
}

function ReferenceList({ references, text }: { references: readonly ProductionReference[]; text: (key: string, parameters?: Record<string, string | number>) => string }) {
  return <section className="ff-production-references"><h3>{text('references')}</h3>
    {!references.length ? <p>{text('noReferences')}</p> : <ul>{references.map(reference => <li key={`${reference.kind}:${reference.id}`}>
      <div><strong>{reference.label ?? reference.kind}</strong><code>{reference.id}</code></div>
      <Badge tone={reference.availability === 'SUPPORTED' ? 'info' : 'warning'}>{text(reference.availability === 'SUPPORTED' ? 'referenceSupported' : 'referenceUnsupported')}</Badge>
      {reference.availability === 'UNSUPPORTED' ? <p>{reference.explanation}</p> : null}
    </li>)}</ul>}
    <p>{text('referenceAuthority')}</p>
  </section>
}
