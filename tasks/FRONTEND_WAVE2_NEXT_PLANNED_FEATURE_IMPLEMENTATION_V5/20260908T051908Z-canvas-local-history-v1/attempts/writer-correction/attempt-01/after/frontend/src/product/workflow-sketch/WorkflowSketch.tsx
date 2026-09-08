import { useRef, useState, type CSSProperties, type KeyboardEvent } from 'react'
import { flushSync } from 'react-dom'
import { Badge, Button, EmptyState, Panel } from '../../components/design-system'
import { InteractionDialog } from '../../interaction/InteractionDialog'
import { useInteractionStore, useSelection, useSurfaceAdapter } from '../../interaction/SelectionContext'
import type { PresentationAction, QueryAction, SelectedObject } from '../../interaction/model'
import { useTranslation } from '../../localization'
import {
  WORKFLOW_NODE_CATEGORIES,
  WORKFLOW_SKETCH_BOUNDS,
  WORKFLOW_SKETCH_LIMIT,
  addWorkflowSketchNode,
  createWorkflowSketch,
  moveWorkflowSketchNode,
  removeWorkflowSketchNode,
  renameWorkflowSketchNode,
  resetWorkflowSketch,
  type WorkflowNodeCategory,
  type WorkflowSketchState,
} from './model'

const MOVE_STEP = 24
const SUPPORTED_ACTIONS = ['rename', 'move', 'reveal'] as const

export function WorkflowSketch() {
  const { t } = useTranslation()
  const store = useInteractionStore()
  const selection = useSelection()
  const [owned, setOwned] = useState(() => ({ store, lifetime: selection.lifetime, sketch: createWorkflowSketch(), confirmingReset: false }))
  const ownerChanged = owned.store !== store || owned.lifetime !== selection.lifetime
  const current = ownerChanged ? { store, lifetime: selection.lifetime, sketch: createWorkflowSketch(), confirmingReset: false } : owned
  if (ownerChanged) setOwned(current)
  const { sketch, confirmingReset } = current
  const boardRef = useRef<HTMLDivElement>(null)
  const nodeRefs = useRef(new Map<string, HTMLButtonElement>())

  const updateSketch = (change: (current: WorkflowSketchState) => WorkflowSketchState) => {
    setOwned(current => current.store === store && current.lifetime === selection.lifetime
      ? { ...current, sketch: change(current.sketch) }
      : current)
  }
  const setResetConfirmation = (confirming: boolean) => {
    setOwned(currentOwned => currentOwned.store === store && currentOwned.lifetime === selection.lifetime
      ? { ...currentOwned, confirmingReset: confirming }
      : currentOwned)
  }
  const objects = (): readonly SelectedObject[] => sketch.nodes.map(node => ({
    id: node.id,
    kind: 'NODE',
    title: node.title,
    x: node.x,
    y: node.y,
    reference: node.category,
  }))
  const handle = (action: PresentationAction | QueryAction) => {
    if (action.category !== 'WORKSPACE_PRESENTATION') return false
    if (action.type === 'undo-local' || action.type === 'redo-local') return false
    const exists = sketch.nodes.some(node => node.id === action.targetId)
    if (!exists) return false
    if (action.type === 'rename') updateSketch(current => renameWorkflowSketchNode(current, action.targetId, action.title))
    else if (action.type === 'move') updateSketch(current => moveWorkflowSketchNode(current, action.targetId, action.x, action.y))
    else if (action.type === 'reveal') nodeRefs.current.get(action.targetId)?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
    else return false
    return true
  }
  useSurfaceAdapter({ objects, supports: SUPPORTED_ACTIONS, handle })

  const selectedNode = selection.primarySelectedObject?.kind === 'NODE'
    ? sketch.nodes.find(node => node.id === selection.primarySelectedObject?.id)
    : undefined
  const selectNode = (id: string) => store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [id], primaryId: id }, 'DIRECT')
  const addNode = (category: WorkflowNodeCategory, initiator: HTMLButtonElement) => {
    const next = addWorkflowSketchNode(sketch, category)
    if (next === sketch) return
    if (next.nodes.length === WORKFLOW_SKETCH_LIMIT && document.activeElement === initiator) boardRef.current?.focus()
    updateSketch(() => next)
  }
  const moveSelected = (event: KeyboardEvent<HTMLButtonElement>, id: string, x: number, y: number) => {
    if (selection.primarySelectedObject?.id !== id || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return
    const delta = event.key === 'ArrowLeft' ? [-MOVE_STEP, 0]
      : event.key === 'ArrowRight' ? [MOVE_STEP, 0]
        : event.key === 'ArrowUp' ? [0, -MOVE_STEP]
          : event.key === 'ArrowDown' ? [0, MOVE_STEP]
            : null
    if (!delta) return
    event.preventDefault()
    store.dispatch({ category: 'WORKSPACE_PRESENTATION', type: 'move', targetId: id, x: x + delta[0], y: y + delta[1] }, 'DIRECT')
  }
  const onNodeKeyDown = (event: KeyboardEvent<HTMLButtonElement>, id: string, x: number, y: number) => {
    const activates = event.key === 'Enter' || event.key === ' '
    if (event.nativeEvent.isComposing || event.keyCode === 229) {
      if (activates) event.preventDefault()
      return
    }
    if (activates) {
      event.preventDefault()
      selectNode(id)
      return
    }
    moveSelected(event, id, x, y)
  }
  const removeSelected = (initiator: HTMLButtonElement) => {
    if (!selectedNode) return
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [] }, 'DIRECT')
    if (document.activeElement === initiator) boardRef.current?.focus()
    updateSketch(current => removeWorkflowSketchNode(current, selectedNode.id))
  }
  const discardSketch = (initiator: HTMLButtonElement) => {
    const transferFocus = document.activeElement === initiator
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [] }, 'DIRECT')
    flushSync(() => {
      updateSketch(resetWorkflowSketch)
      setResetConfirmation(false)
    })
    if (transferFocus) boardRef.current?.focus()
  }
  const atLimit = sketch.nodes.length >= WORKFLOW_SKETCH_LIMIT

  return <section className="ff-workflow-sketch" aria-label={t('workflow.region')}>
    <Panel title={t('workflow.title')}>
      <p className="ff-workflow-boundary">{t('workflow.boundary')}</p>
      <div className="ff-workflow-palette" aria-label={t('workflow.palette')}>
        {WORKFLOW_NODE_CATEGORIES.map(category => <Button key={category} disabled={atLimit} onClick={event => addNode(category, event.currentTarget)}>{t('workflow.addCard', { category })}</Button>)}
      </div>
      <div className="ff-workflow-status-row">
        <p role="status">{t('workflow.count', { count: sketch.nodes.length, limit: WORKFLOW_SKETCH_LIMIT })}</p>
        {sketch.nodes.length ? <div className="ff-workflow-local-actions">
          {selectedNode ? <Button onClick={event => removeSelected(event.currentTarget)}>{t('workflow.removeSelected')}</Button> : null}
          <Button onClick={() => setResetConfirmation(true)}>{t('workflow.reset')}</Button>
        </div> : null}
      </div>
      {atLimit ? <p role="alert" className="ff-workflow-limit">{t('workflow.limitReached', { limit: WORKFLOW_SKETCH_LIMIT })}</p> : null}
      <p id="workflow-sketch-bounds" className="ff-workflow-bounds">{t('workflow.bounds', {
        minX: WORKFLOW_SKETCH_BOUNDS.minX,
        maxX: WORKFLOW_SKETCH_BOUNDS.maxX,
        minY: WORKFLOW_SKETCH_BOUNDS.minY,
        maxY: WORKFLOW_SKETCH_BOUNDS.maxY,
      })}</p>
      <div ref={boardRef} className="ff-workflow-board" role="region" aria-label={t('workflow.board')} aria-describedby="workflow-sketch-bounds" tabIndex={0}>
        {sketch.nodes.length ? <div className="ff-workflow-board-plane">
          {sketch.nodes.map(node => {
            const selected = selection.selectedObjects.some(object => object.id === node.id)
            return <button
              key={node.id}
              ref={element => {
                if (element) nodeRefs.current.set(node.id, element)
                else nodeRefs.current.delete(node.id)
              }}
              type="button"
              className="ff-workflow-node"
              style={{ '--workflow-node-x': `${node.x}px`, '--workflow-node-y': `${node.y}px` } as CSSProperties}
              aria-label={node.title || t('common.untitled')}
              aria-pressed={selected}
              data-testid="workflow-sketch-node"
              onClick={() => selectNode(node.id)}
              onKeyDown={event => onNodeKeyDown(event, node.id, node.x, node.y)}
            >
              <Badge>{node.category}</Badge>
              <strong>{node.title || t('common.untitled')}</strong>
              <span>{t('workflow.position', { x: node.x, y: node.y })}</span>
            </button>
          })}
        </div> : <EmptyState title={t('workflow.emptyTitle')} description={t('workflow.emptyBody')} />}
      </div>
      {confirmingReset ? <InteractionDialog title={t('workflow.discardTitle')} closeLabel={t('workflow.closeDiscard')} onClose={() => setResetConfirmation(false)}>
        <p>{t('workflow.discardBody')}</p>
        <div className="ff-workflow-dialog-actions">
          <Button data-dialog-entry onClick={() => setResetConfirmation(false)}>{t('workflow.keep')}</Button>
          <Button variant="danger" onClick={event => discardSketch(event.currentTarget)}>{t('workflow.discard')}</Button>
        </div>
      </InteractionDialog> : null}
    </Panel>
  </section>
}
