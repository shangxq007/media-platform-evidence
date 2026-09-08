import { describe, expect, it } from 'vitest'
import {
  WORKFLOW_NODE_CATEGORIES,
  WORKFLOW_SKETCH_BOUNDS,
  WORKFLOW_SKETCH_LIMIT,
  WORKFLOW_SKETCH_TITLE_LIMIT,
  addWorkflowSketchNode,
  createWorkflowSketch,
  moveWorkflowSketchNode,
  removeWorkflowSketchNode,
  renameWorkflowSketchNode,
  resetWorkflowSketch,
} from './model'

describe('workflow local sketch model', () => {
  it('begins empty and adds a category with stable local identity', () => {
    const empty = createWorkflowSketch()
    const one = addWorkflowSketchNode(empty, 'OPERATION')
    const two = addWorkflowSketchNode(one, 'RENDER')

    expect(empty.nodes).toEqual([])
    expect(one.nodes).toEqual([
      { id: 'workflow-node-1', category: 'OPERATION', title: 'OPERATION', x: 32, y: 32 },
    ])
    expect(two.nodes.map(node => node.id)).toEqual(['workflow-node-1', 'workflow-node-2'])
  })

  it('supports all exact categories and refuses a thirteenth local card', () => {
    let sketch = createWorkflowSketch()
    for (let index = 0; index < WORKFLOW_SKETCH_LIMIT; index += 1) {
      sketch = addWorkflowSketchNode(sketch, WORKFLOW_NODE_CATEGORIES[index % WORKFLOW_NODE_CATEGORIES.length])
    }
    const full = sketch

    expect(new Set(sketch.nodes.slice(0, 7).map(node => node.category))).toEqual(new Set(WORKFLOW_NODE_CATEGORIES))
    expect(sketch.nodes).toHaveLength(12)
    expect(addWorkflowSketchNode(sketch, 'WAIT')).toBe(full)
  })

  it('bounds placement and labels while rejecting invalid movement', () => {
    const created = addWorkflowSketchNode(createWorkflowSketch(), 'CONDITION')
    const moved = moveWorkflowSketchNode(created, 'workflow-node-1', -999, 999)
    const renamed = renameWorkflowSketchNode(moved, 'workflow-node-1', '<img src=x onerror=alert(1)>' + 'x'.repeat(200))

    expect(moved.nodes[0]).toMatchObject({ x: WORKFLOW_SKETCH_BOUNDS.minX, y: WORKFLOW_SKETCH_BOUNDS.maxY })
    expect(renameWorkflowSketchNode(moved, 'missing', 'ignored')).toBe(moved)
    expect(moveWorkflowSketchNode(moved, 'workflow-node-1', Infinity, 0)).toBe(moved)
    expect(renamed.nodes[0].title).toHaveLength(WORKFLOW_SKETCH_TITLE_LIMIT)
    expect(renamed.nodes[0].title).toContain('<img src=x onerror=alert(1)>')
  })

  it('removes and resets cards without reusing an identity in the same lifetime', () => {
    const first = addWorkflowSketchNode(createWorkflowSketch(), 'AGENT')
    const removed = removeWorkflowSketchNode(first, 'workflow-node-1')
    const second = addWorkflowSketchNode(removed, 'INTEGRATION')
    const reset = resetWorkflowSketch(second)
    const third = addWorkflowSketchNode(reset, 'REVIEW')

    expect(second.nodes.map(node => node.id)).toEqual(['workflow-node-2'])
    expect(reset.nodes).toEqual([])
    expect(third.nodes.map(node => node.id)).toEqual(['workflow-node-3'])
  })
})
