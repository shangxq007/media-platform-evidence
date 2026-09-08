import { useId, useMemo } from 'react'
import { Badge, EmptyState, PropertyRow } from '../../components/design-system'
import { useTranslation } from '../../localization'
import type { RevisionComparison } from './gateways'

const actionKeys: Readonly<Record<string, string>> = { ALL: 'all', ADDED: 'added', added: 'added', REMOVED: 'removed', removed: 'removed', MODIFIED: 'modified', modified: 'modified' }
const kindKeys: Readonly<Record<string, string>> = { CLIP: 'clip', TRACK: 'track', ASSET: 'asset' }

export function SemanticDiff({ comparison, actionFilter, onActionFilterChange }: {
  comparison: RevisionComparison | null
  actionFilter: string
  onActionFilterChange: (action: string) => void
}) {
  const { t } = useTranslation()
  const pairDetailsId = useId()
  const actions = useMemo(() => comparison
    ? ['ALL', ...Array.from(new Set(comparison.entityChanges.map(change => change.action))).filter(action => action !== 'ALL').sort()]
    : ['ALL'], [comparison])
  const visible = comparison?.entityChanges.filter(change => actionFilter === 'ALL' || change.action === actionFilter) ?? []
  const actionLabel = (action: string) => Object.prototype.hasOwnProperty.call(actionKeys, action) ? t(`review.diff.${actionKeys[action]}`) : action
  const kindLabel = (kind: string) => Object.prototype.hasOwnProperty.call(kindKeys, kind) ? t(`review.diff.${kindKeys[kind]}`) : kind

  if (!comparison) {
    return <EmptyState title={t('review.diff.notLoaded')} description={t('review.diff.notLoadedHelp')} />
  }

  const summary = comparison.summary
  // Only classify the supplied summary's display state; never derive a diff from entities.
  const zeroSummary = summary.supported && [summary.tracksAdded, summary.tracksRemoved, summary.tracksModified,
    summary.clipsAdded, summary.clipsRemoved, summary.clipsModified, summary.assetsAdded, summary.assetsRemoved].every(count => count === 0)
  const emptyKey = comparison.entityChanges.length ? 'filteredEmpty' : zeroSummary ? 'zero' : 'noEntities'

  return (
    <div className="ff-semantic-diff">
      <p aria-label={t('review.diff.resultPair')} aria-details={pairDetailsId}>{t('review.diff.resultPair')}: {t('review.from')}: {t('review.revisionNumber', { number: comparison.fromRevision.revisionNumber })} → {t('review.to')}: {t('review.revisionNumber', { number: comparison.toRevision.revisionNumber })}</p>
      <details id={pairDetailsId}><summary>{t('review.pairDetails')}</summary>
        <dl><dt>{t('review.from')}</dt><dd><code>{comparison.fromRevision.id}</code></dd><dt>{t('review.to')}</dt><dd><code>{comparison.toRevision.id}</code></dd></dl>
      </details>
      <div className="ff-table-toolbar">
        <label>{t('review.diff.action')} <select value={actionFilter} onChange={event => onActionFilterChange(event.target.value)}>{actions.map(action => <option key={action} value={action}>{actionLabel(action)}</option>)}</select></label>
        <Badge tone={summary.supported ? 'info' : 'warning'}>{t(summary.supported ? 'review.diff.server' : 'review.diff.limited')}</Badge>
      </div>
      {summary.supported ? <div className="ff-diff-summary" aria-label={t('review.diff.summary')}>
        <PropertyRow label={t('review.diff.tracks')}><span>{summary.tracksAdded} / {summary.tracksRemoved} / {summary.tracksModified}</span></PropertyRow>
        <PropertyRow label={t('review.diff.clips')}><span>{summary.clipsAdded} / {summary.clipsRemoved} / {summary.clipsModified}</span></PropertyRow>
        <PropertyRow label={t('review.diff.assets')}><span>{summary.assetsAdded} / {summary.assetsRemoved}</span></PropertyRow>
      </div> : <EmptyState title={t('review.diff.unsupported')} description={t('review.diff.unsupportedHelp')} />}
      {visible.length ? <ul className="ff-entity-change-list">{visible.map((change, index) => <li key={JSON.stringify([change.kind, change.entityId, change.action, index])}><Badge>{actionLabel(change.action)}</Badge><strong>{kindLabel(change.kind)}</strong><code>{change.entityId}</code></li>)}</ul>
        : <EmptyState title={t(`review.diff.${emptyKey}`)} description={t(`review.diff.${emptyKey}Help`)} />}
    </div>
  )
}
