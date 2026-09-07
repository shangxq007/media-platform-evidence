import { useEffect, useId, useRef, useState } from 'react'
import { timelineQueryGateway as defaultTimelineQueryGateway } from '../../api/app/timeline-query.gateway'
import { Badge, Button, EmptyState, Panel, Skeleton, Tabs } from '../../components/design-system'
import { useProjectContext } from '../../foundation/projectContext'
import { PageHeading, ProjectFrame } from '../../surfaces/FoundationPages'
import { SemanticDiff } from '../timeline/SemanticDiff'
import type { RevisionComparison, RevisionListEntry, TimelineQueryGateway } from '../timeline/gateways'
import { useInteractionStore, useSurfaceAdapter } from '../../interaction/SelectionContext'
import { projectId } from '../timeline/types'
import { useTranslation } from '../../localization'

const sections = ['Overview', 'Visual Changes', 'Semantic Changes', 'Conversation', 'Checks'] as const
const chooseMessage = 'Choose two different revisions to compare their changes.'

export function ReviewWorkspace({ queryGateway }: { queryGateway: TimelineQueryGateway }) {
  const project = useProjectContext()
  return <ReviewSession key={JSON.stringify([project.workspaceId, project.projectId])} queryGateway={queryGateway} />
}

function ReviewSession({ queryGateway }: { queryGateway: TimelineQueryGateway }) {
  const project = useProjectContext()
  const { t } = useTranslation()
  const store = useInteractionStore()
  const tabsId = useId()
  const [active, setActive] = useState<string>('Semantic Changes')
  const [history, setHistory] = useState<readonly RevisionListEntry[]>([])
  const [historyState, setHistoryState] = useState<'LOADING' | 'READY' | 'ERROR'>('LOADING')
  const [historyError, setHistoryError] = useState('')
  const [retry, setRetry] = useState(0)
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [comparison, setComparison] = useState<RevisionComparison | null>(null)
  const [filter, setFilter] = useState('ALL')
  const [pending, setPending] = useState(false)
  const [compareError, setCompareError] = useState(false)
  const [message, setMessage] = useState(chooseMessage)
  const comparisonGeneration = useRef(0)
  const pendingRequest = useRef(false)

  useEffect(() => {
    let activeRequest = true
    comparisonGeneration.current += 1
    pendingRequest.current = false
    setPending(false)
    setHistoryState('LOADING')
    setHistoryError('')
    setHistory([])
    setFrom('')
    setTo('')
    store.setRevisionPair(undefined)
    setComparison(null)
    setCompareError(false)
    setMessage(chooseMessage)
    const load = async () => {
      try {
        const result = await queryGateway.listRevisions(projectId(project.projectId))
        if (!activeRequest) return
        if (result.ok) {
          // Repeated entries do not create a second distinct revision.
          setHistory(result.value.filter((item, index, entries) => entries.findIndex(entry => entry.id === item.id) === index))
          setHistoryState('READY')
        } else { setHistoryError(`${result.code}: ${result.message}`); setHistoryState('ERROR') }
      } catch {
        if (activeRequest) { setHistoryError('Revision history could not be loaded. Try again.'); setHistoryState('ERROR') }
      }
    }
    void load()
    return () => { activeRequest = false; comparisonGeneration.current += 1; pendingRequest.current = false }
  }, [project.projectId, queryGateway, retry, store])

  const canCompare = historyState === 'READY' && history.length >= 2 && from !== to && history.some(item => item.id === from) && history.some(item => item.id === to)
  const compare = async () => {
    if (!canCompare || pendingRequest.current) return
    const fromRevision = history.find(item => item.id === from)!
    const toRevision = history.find(item => item.id === to)!
    const generation = ++comparisonGeneration.current
    pendingRequest.current = true
    setPending(true)
    setComparison(null)
    setFilter('ALL')
    setCompareError(false)
    setMessage('Loading revision comparison…')
    try {
      const result = await queryGateway.compare(projectId(project.projectId), fromRevision.id, toRevision.id)
      if (comparisonGeneration.current !== generation) return
      if (result.ok) { setComparison(result.value); setMessage(result.value.entityChanges.length ? 'Comparison loaded.' : 'Comparison loaded with no entity changes.'); }
      else { setCompareError(true); setMessage(`${result.code}: ${result.message}`) }
    } catch {
      if (comparisonGeneration.current === generation) { setCompareError(true); setMessage('Revision comparison could not be loaded. Retry comparison.'); }
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
    comparisonGeneration.current += 1
    pendingRequest.current = false
    setPending(false)
    setComparison(null)
    setFilter('ALL')
    setCompareError(false)
    setMessage(chooseMessage)
    if (side === 'from') setFrom(value)
    else setTo(value)
    const pair = { from: side === 'from' ? value : from, to: side === 'to' ? value : to }
    store.setRevisionPair(pair.from && pair.to && pair.from !== pair.to && history.some(item => item.id === pair.from) && history.some(item => item.id === pair.to) ? pair : undefined)
  }

  return <>
    <PageHeading eyebrow={t('review.eyebrow')} title={t('review.title')} description={t('review.description')} />
    <Tabs label="Review sections" activeId={active} onChange={setActive} tabs={sections.map((label, index) => ({ id: label, label, tabId: `${tabsId}-tab-${index}`, panelId: `${tabsId}-panel-${index}` }))} />
    {sections.map((section, index) => <div key={section} role="tabpanel" id={`${tabsId}-panel-${index}`} aria-labelledby={`${tabsId}-tab-${index}`} hidden={active !== section} tabIndex={0}>
      {active === section ? <Panel title={section}>{section === 'Semantic Changes' ? <>
        <div aria-label="Revision history" aria-busy={historyState === 'LOADING'}>
          {historyState === 'LOADING' ? <><p role="status">Loading revision history…</p><Skeleton label="Loading revision choices and change summary" /></> : null}
          {historyState === 'ERROR' ? <><p role="alert">We couldn’t load revision history. Try again to choose revisions.</p><Button onClick={() => setRetry(value => value + 1)}>Retry history</Button><details><summary>Technical details</summary><p>{historyError}</p></details></> : null}
          {historyState === 'READY' && history.length === 0 ? <EmptyState title="No revisions available" description="No revisions were returned for this project. Comparison needs two distinct revisions." action={<Button onClick={() => setRetry(value => value + 1)}>Refresh history</Button>} /> : null}
          {historyState === 'READY' && history.length === 1 ? <p role="status">Only one distinct revision is available. Comparison needs two.<Button onClick={() => setRetry(value => value + 1)}>Refresh history</Button></p> : null}
          <div className="ff-review-compare-controls">
            {(['from', 'to'] as const).map(side => <label key={side}>{side === 'from' ? 'From revision' : 'To revision'}<select disabled={historyState !== 'READY' || history.length < 2} value={side === 'from' ? from : to} onChange={event => changeRevision(side, event.target.value)}><option value="">Select revision</option>{history.map(item => <option key={item.id} value={item.id}>r{item.revisionNumber} · {item.id}</option>)}</select></label>)}
            <Button disabled={!canCompare || pending} onClick={requestComparison}>{pending ? 'Comparing…' : compareError ? 'Retry comparison' : 'Compare revisions'}</Button><Badge tone="warning">MERGE DISABLED</Badge>
          </div>
        </div>
        <p role={compareError ? 'alert' : 'status'}>{compareError ? 'We couldn’t compare these revisions. Retry comparison above.' : message}</p>{compareError ? <details><summary>Comparison technical details</summary><p>{message}</p></details> : null}
        <details className="ff-compact-details"><summary>How comparison works</summary><p>Semantic changes are a formatted server comparison. Timeline retains revision and merge authority. No client diff is computed; merge resolution is unavailable.</p></details>
        <div aria-label="Server comparison" aria-busy={pending}><SemanticDiff comparison={comparison} actionFilter={filter} onActionFilterChange={setFilter} /></div>
      </> : <EmptyState title={`${section} unavailable`} description="This bounded product slice does not fabricate a review projection." />}</Panel> : null}
    </div>)}
  </>
}

export function ReviewPage({ queryGateway = defaultTimelineQueryGateway }: { queryGateway?: TimelineQueryGateway }) {
  return <ProjectFrame surfaceId="review"><ReviewWorkspace queryGateway={queryGateway} /></ProjectFrame>
}
