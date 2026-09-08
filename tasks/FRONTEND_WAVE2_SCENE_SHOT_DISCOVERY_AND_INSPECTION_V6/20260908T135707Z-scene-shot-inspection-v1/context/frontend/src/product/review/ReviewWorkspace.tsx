import { useEffect, useId, useRef, useState } from 'react'
import { timelineQueryGateway as defaultTimelineQueryGateway } from '../../api/app/timeline-query.gateway'
import { Badge, Button, EmptyState, Panel, Skeleton, Tabs } from '../../components/design-system'
import { useProjectContext } from '../../foundation/projectContext'
import { PageHeading, ProjectFrame } from '../../surfaces/FoundationPages'
import { SemanticDiff } from '../timeline/SemanticDiff'
import type { GatewayFailure, RevisionComparison, RevisionListEntry, TimelineQueryGateway } from '../timeline/gateways'
import { useInteractionStore, useSurfaceAdapter } from '../../interaction/SelectionContext'
import { projectId } from '../timeline/types'
import { useTranslation } from '../../localization'

const sections = ['Overview', 'Visual Changes', 'Semantic Changes', 'Conversation', 'Checks'] as const
const sectionKeys = ['overview', 'visual', 'panel', 'conversation', 'checks'] as const

type ReviewFailure = { kind: 'gateway'; failure: GatewayFailure } | { kind: 'network' } | { kind: 'mismatch' }
const retryable = (error: ReviewFailure) => error.kind === 'network' || (error.kind === 'gateway' && error.failure.retryable)

function FailureDetails({ error, comparison = false }: { error: ReviewFailure; comparison?: boolean }) {
  const { t } = useTranslation()
  if (error.kind !== 'gateway') return null
  return <details><summary>{t(comparison ? 'review.comparisonTechnical' : 'review.technical')}</summary>
    <code>{error.failure.code}</code><p>{error.failure.message}</p>
    {error.failure.details.map((detail, index) => <p key={index}>{detail}</p>)}
  </details>
}

export function ReviewWorkspace({ queryGateway }: { queryGateway: TimelineQueryGateway }) {
  const project = useProjectContext()
  return <ReviewSession key={JSON.stringify([project.workspaceId, project.projectId])} queryGateway={queryGateway} />
}

function ReviewSession({ queryGateway }: { queryGateway: TimelineQueryGateway }) {
  const project = useProjectContext()
  const { t, formatDate } = useTranslation()
  const store = useInteractionStore()
  const tabsId = useId()
  const [active, setActive] = useState<string>('Semantic Changes')
  const [history, setHistory] = useState<readonly RevisionListEntry[]>([])
  const [historyState, setHistoryState] = useState<'LOADING' | 'READY' | 'ERROR'>('LOADING')
  const [historyError, setHistoryError] = useState<ReviewFailure | null>(null)
  const [retry, setRetry] = useState(0)
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [comparison, setComparison] = useState<RevisionComparison | null>(null)
  const [filter, setFilter] = useState('ALL')
  const [pending, setPending] = useState(false)
  const [compareError, setCompareError] = useState<ReviewFailure | null>(null)
  const comparisonGeneration = useRef(0)
  const pendingRequest = useRef(false)

  useEffect(() => {
    let activeRequest = true
    comparisonGeneration.current += 1
    pendingRequest.current = false
    setPending(false)
    setHistoryState('LOADING')
    setHistoryError(null)
    setHistory([])
    setFrom('')
    setTo('')
    store.setRevisionPair(undefined)
    setComparison(null)
    setCompareError(null)
    const load = async () => {
      try {
        const result = await queryGateway.listRevisions(projectId(project.projectId))
        if (!activeRequest) return
        if (result.ok) {
          // Repeated entries do not create a second distinct revision.
          setHistory(result.value.filter((item, index, entries) => entries.findIndex(entry => entry.id === item.id) === index))
          setHistoryState('READY')
        } else { setHistoryError({ kind: 'gateway', failure: result }); setHistoryState('ERROR') }
      } catch {
        if (activeRequest) { setHistoryError({ kind: 'network' }); setHistoryState('ERROR') }
      }
    }
    void load()
    return () => { activeRequest = false; comparisonGeneration.current += 1; pendingRequest.current = false }
  }, [project.projectId, queryGateway, retry, store])

  const validPair = historyState === 'READY' && history.length >= 2 && from !== to && history.some(item => item.id === from) && history.some(item => item.id === to)
  // Only the unchanged current failure suppresses a repeat; pair edits clear it.
  const canCompare = validPair && !(compareError && !retryable(compareError))
  const compare = async () => {
    if (!canCompare || pendingRequest.current) return
    const fromRevision = history.find(item => item.id === from)!
    const toRevision = history.find(item => item.id === to)!
    const generation = ++comparisonGeneration.current
    pendingRequest.current = true
    setPending(true)
    setComparison(null)
    setFilter('ALL')
    setCompareError(null)
    try {
      const result = await queryGateway.compare(projectId(project.projectId), fromRevision.id, toRevision.id)
      if (comparisonGeneration.current !== generation) return
      if (result.ok) {
        if (result.value.fromRevision.id !== fromRevision.id || result.value.toRevision.id !== toRevision.id) setCompareError({ kind: 'mismatch' })
        else setComparison(result.value)
      } else setCompareError({ kind: 'gateway', failure: result })
    } catch {
      if (comparisonGeneration.current === generation) setCompareError({ kind: 'network' })
    } finally {
      if (comparisonGeneration.current === generation) { pendingRequest.current = false; setPending(false) }
    }
  }

  useSurfaceAdapter({ objects: () => [], supports: ['compare-revisions'], handle: action => {
    if (action.type !== 'compare-revisions' || !canCompare || pendingRequest.current || action.pair.from !== from || action.pair.to !== to) return false
    void compare()
    return true
  } })
  const requestComparison = () => { if (canCompare) store.dispatch({ category: 'READ_ONLY_QUERY', type: 'compare-revisions', pair: { from, to } }) }

  const changeRevision = (side: 'from' | 'to', value: string) => {
    if (value === (side === 'from' ? from : to)) return
    comparisonGeneration.current += 1
    pendingRequest.current = false
    setPending(false)
    setComparison(null)
    setFilter('ALL')
    if (side === 'from') setFrom(value)
    else setTo(value)
    const pair = { from: side === 'from' ? value : from, to: side === 'to' ? value : to }
    setCompareError(null)
    store.setRevisionPair(pair.from && pair.to && pair.from !== pair.to && history.some(item => item.id === pair.from) && history.some(item => item.id === pair.to) ? pair : undefined)
  }

  const failureExplanation = (error: ReviewFailure) => t(error.kind === 'gateway' ? `review.failure.${error.failure.code}` : error.kind === 'network' ? 'review.failure.NETWORK' : 'review.failureMismatch')
  const choiceHelp = !from && !to ? 'chooseBoth' : !from ? 'chooseFrom' : !to ? 'chooseTo' : from === to ? 'chooseDifferent' : !validPair ? 'chooseKnown' : 'ready'
  const revisionLabel = (item: RevisionListEntry) => {
    const date = new Date(item.createdAt)
    const readableDate = item.createdAt && Number.isFinite(date.getTime()) ? formatDate(date, { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' }) : item.createdAt
    return [t('review.revisionNumber', { number: item.revisionNumber }), item.message, readableDate, item.id].filter(Boolean).join(' · ')
  }

  const selectedFrom = history.find(item => item.id === from)
  const selectedTo = history.find(item => item.id === to)

  return <div className="ff-review-workspace">
    <PageHeading eyebrow={t('review.eyebrow')} title={t('review.title')} description={t('review.description')} />
    {project.projectName ? <h2>{project.projectName}</h2> : null}
    <details className="ff-review-identities"><summary>{t('review.projectDetails')}</summary>
      <dl><dt>{t('review.workspaceId')}</dt><dd><code>{project.workspaceId}</code></dd><dt>{t('review.projectId')}</dt><dd><code>{project.projectId}</code></dd></dl>
    </details>
    <Tabs label={t('review.sections')} activeId={active} onChange={setActive} tabs={sections.map((label, index) => ({ id: label, label: t(`review.${sectionKeys[index]}`), tabId: `${tabsId}-tab-${index}`, panelId: `${tabsId}-panel-${index}` }))} />
    {sections.map((section, index) => <div key={section} role="tabpanel" id={`${tabsId}-panel-${index}`} aria-labelledby={`${tabsId}-tab-${index}`} hidden={active !== section} tabIndex={0}>
      {active === section ? <Panel title={t(`review.${sectionKeys[index]}`)}>{section === 'Semantic Changes' ? <>
        <p id={`${tabsId}-direction`}>{t('review.direction')}</p>
        <div aria-label={t('review.history')} aria-busy={historyState === 'LOADING'}>
          {historyState === 'LOADING' ? <><p role="status">{t('review.loadingHistory')}</p><Skeleton label={t('review.loadingChoices')} /></> : null}
          {historyState === 'ERROR' && historyError ? <>
            <p role="alert">{t('review.historyFailed')} {failureExplanation(historyError)} {t(retryable(historyError) ? 'review.historyRetryHelp' : 'review.historyBlockedHelp')}</p>
            {retryable(historyError) ? <Button onClick={() => setRetry(value => value + 1)}>{t('review.retryHistory')}</Button> : null}
            <FailureDetails error={historyError} />
          </> : null}
          {historyState === 'READY' && history.length === 0 ? <EmptyState title={t('review.noRevisions')} description={t('review.noRevisionsHelp')} action={<Button onClick={() => setRetry(value => value + 1)}>{t('review.refreshHistory')}</Button>} /> : null}
          {historyState === 'READY' && history.length === 1 ? <p role="status">{t('review.oneRevision')}<Button onClick={() => setRetry(value => value + 1)}>{t('review.refreshHistory')}</Button></p> : null}
          <div className="ff-review-compare-controls">
            {(['from', 'to'] as const).map(side => <label key={side}>{t(side === 'from' ? 'review.from' : 'review.to')}<select aria-describedby={`${tabsId}-direction ${tabsId}-comparison-status`} disabled={historyState !== 'READY' || history.length < 2} value={side === 'from' ? from : to} onChange={event => changeRevision(side, event.target.value)}><option value="">{t('review.selectRevision')}</option>{history.map(item => <option key={item.id} value={item.id}>{revisionLabel(item)}</option>)}</select></label>)}
            <Button aria-describedby={`${tabsId}-comparison-status`} disabled={!canCompare || pending} onClick={requestComparison}>{t(pending ? 'review.comparing' : compareError && retryable(compareError) ? 'review.retryComparison' : 'review.compare')}</Button><Badge tone="warning">{t('review.mergeDisabled')}</Badge>
          </div>
        </div>
        {from && to ? <>
          <p aria-label={t(pending ? 'review.requestedPair' : 'review.selectedPair')} aria-details={`${tabsId}-pair-details`}>{t(pending ? 'review.requestedPair' : 'review.selectedPair')}: {t('review.from')}: {selectedFrom ? t('review.revisionNumber', { number: selectedFrom.revisionNumber }) : t('review.selectRevision')} → {t('review.to')}: {selectedTo ? t('review.revisionNumber', { number: selectedTo.revisionNumber }) : t('review.selectRevision')}</p>
          <details id={`${tabsId}-pair-details`}><summary>{t('review.pairDetails')}</summary>
            <dl><dt>{t('review.from')}</dt><dd><code>{from}</code></dd><dt>{t('review.to')}</dt><dd><code>{to}</code></dd></dl>
          </details>
        </> : null}
        <p id={`${tabsId}-comparison-status`} role={compareError ? 'alert' : 'status'}>{compareError
          ? <>{t('review.comparisonFailed')} {failureExplanation(compareError)} {t(retryable(compareError) ? 'review.comparisonRetryHelp' : 'review.comparisonBlockedHelp')}</>
          : pending ? t('review.loadingComparison') : comparison ? t(comparison.entityChanges.length ? 'review.loaded' : 'review.loadedNoEntities') : historyState === 'READY' && history.length >= 2 ? t(`review.${choiceHelp}`) : t('review.needsHistory')}</p>
        {compareError ? <FailureDetails error={compareError} comparison /> : null}
        <div aria-label={t('review.serverComparison')} aria-busy={pending}><SemanticDiff comparison={comparison} actionFilter={filter} onActionFilterChange={setFilter} /></div>
      </> : <EmptyState title={t('review.sectionUnavailable', { section: t(`review.${sectionKeys[index]}`) })} description={t('review.sectionUnavailableHelp')} />}</Panel> : null}
    </div>)}
  </div>
}

export function ReviewPage({ queryGateway = defaultTimelineQueryGateway }: { queryGateway?: TimelineQueryGateway }) {
  return <ProjectFrame surfaceId="review"><ReviewWorkspace queryGateway={queryGateway} /></ProjectFrame>
}
