import { createInteractionStore } from '../../interaction/model'
import { describe, expect, it } from 'vitest'
import { changeZoom, fitCanvasViewport, createCanvasState, moveViewport, placeCanvasNode, renameCanvasNode, resetViewport } from './model'

describe('local canvas presentation model', () => {
  it('changes placement and title without altering reference identity or visual guide definitions', () => {
    const initial = createCanvasState('project-one')
    const moved = placeCanvasNode(initial, 'project-node', 250, -40)
    const renamed = renameCanvasNode(moved, 'project-node', 'Local label')
    expect(renamed.nodes[0]).toMatchObject({ x: 250, y: -40, title: 'Local label', semanticReferenceId: 'project-ref', presentationId: 'project-node' })
    expect(renamed.references).toBe(initial.references)
    expect(renamed.edges).toBe(initial.edges)
    expect(initial.nodes[0].x).toBe(120)
  })

  it('bounds placement and zoom, rejects invalid numbers and delegates selection to the shared store', () => {
    const initial = createCanvasState('p')
    expect(placeCanvasNode(initial, 'note-node', Infinity, 0)).toBe(initial)
    expect(placeCanvasNode(initial, 'note-node', -9999, 9999).nodes[1]).toMatchObject({ x: -2000, y: 2000 })
    expect(changeZoom(initial, NaN)).toBe(initial)
    expect(changeZoom(initial, 100).zoom).toBe(2)
    expect(changeZoom(initial, -100).zoom).toBe(0.5)
    expect(initial).not.toHaveProperty('selectedPresentationId')
    expect(resetViewport(changeZoom(moveViewport(initial, 30, -20), 0.4))).toEqual(initial)
    const store = createInteractionStore({ surfaceId: 'canvas' })
    store.register({ objects: () => initial.nodes.map(node => ({ id: node.presentationId, kind: 'NODE', title: node.title })), supports: [], handle: () => false })
    expect(store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['missing'] }).ok).toBe(false)
    expect(store.getSnapshot().primaryRef).toBeNull()
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: ['note-node'] })
    store.dispatch({ category: 'LOCAL_EPHEMERAL', type: 'select', ids: [] })
    expect(store.getSnapshot().primaryRef).toBeNull()
  })
})

// Fit must preserve selection and semantic identity, including distant local placements.
describe('canvas fit', () => {
  it('fits the default composition in a phone stage without changing nodes', () => {
    const state = createCanvasState('p')
    const fitted = fitCanvasViewport(state, 358, 330)
    expect(fitted.nodes).toBe(state.nodes)
    expect(fitted.references).toBe(state.references)
    expect(fitted).not.toHaveProperty('selectedPresentationId')
    expect(fitted.edges).toBe(state.edges)
    for (const node of fitted.nodes) {
      expect(node.x * fitted.zoom + fitted.viewportX).toBeGreaterThanOrEqual(16)
      expect((node.x + 230) * fitted.zoom + fitted.viewportX).toBeLessThanOrEqual(342)
    }
  })
  it('supports distant nodes and rejects zero sized stages', () => {
    const state = placeCanvasNode(createCanvasState('p'), 'note-node', 2000, -2000)
    expect(fitCanvasViewport(state, 0, 0)).toBe(state)
    const fitted = fitCanvasViewport(state, 358, 330)
    expect(fitted.zoom).toBeLessThan(0.5)
    expect(fitted.nodes).toBe(state.nodes)
  })
})

import { screenToCanvas, boundedGroupDelta, moveCanvasGroup } from './model'

describe('Slice1B screen transform', () => {
  it.each([
    [1, 0, 0, 0, 0, 100, 80], [2, 0, 0, 0, 0, 50, 40], [0.5, 0, 0, 0, 0, 200, 160],
    [1, 0, 0, 30, -20, 70, 100], [2, 10, 20, 30, -20, 30, 40], [0.5, 10, 20, -30, 40, 240, 40],
  ])('zoom %s origin %s,%s pan %s,%s -> %s,%s', (zoom, ox, oy, px, py, x, y) => {
    expect(screenToCanvas({ x: 100, y: 80 }, { x: ox, y: oy }, { x: px, y: py }, zoom)).toEqual({ x, y })
  })
})

describe('Slice1B common legal group delta', () => {
  it.each([
    ['left', -9999, 0, -2120, 0], ['right', 9999, 0, 1570, 0],
    ['top', 0, -9999, 0, -2090], ['bottom', 0, 9999, 0, 1770],
  ])('two-node %s bound preserves spacing', (_name, x, y, dx, dy) => {
    const state = createCanvasState('p')
    const delta = boundedGroupDelta(state.nodes, { x, y })
    expect(delta).toEqual({ x: dx, y: dy })
    const next = moveCanvasGroup(state, state.nodes, { x, y })
    expect(next.nodes.map(n => [n.x, n.y])).toEqual(state.nodes.map(n => [n.x + dx, n.y + dy]))
    expect(next.nodes[1].x - next.nodes[0].x).toBe(310)
    expect(next.nodes[1].y - next.nodes[0].y).toBe(140)
    expect(next.references).toBe(state.references); expect(next.edges).toBe(state.edges)
    expect(next).not.toHaveProperty('revision'); expect(next).not.toHaveProperty('receipt')
  })
  it.each([[-9999, 0, -2000, 90], [9999, 0, 2000, 90], [0, -9999, 120, -2000], [0, 9999, 120, 2000]])('single bound %s,%s', (x, y, nx, ny) => {
    const state = createCanvasState('p')
    const next = moveCanvasGroup(state, [state.nodes[0]], { x, y })
    expect(next.nodes[0]).toMatchObject({ x: nx, y: ny })
    expect(next.nodes[1]).toBe(state.nodes[1])
  })
  it('large group respects every boundary with the same fractional delta', () => {
    const initial = createCanvasState('p')
    const nodes = Array.from({ length: 1000 }, (_, i) => ({ ...initial.nodes[0], presentationId: `n${i}`, x: -1999 + i * 4, y: 1999 - i * 4 }))
    const state = { ...initial, nodes }
    for (const requested of [{ x: -9999, y: -9999 }, { x: 9999, y: 9999 }, { x: 0.25, y: -0.5 }]) {
      const delta = boundedGroupDelta(nodes, requested)
      const next = moveCanvasGroup(state, nodes, requested)
      next.nodes.forEach((node, i) => {
        expect(node.x - nodes[i].x).toBe(delta.x); expect(node.y - nodes[i].y).toBe(delta.y)
        expect(Math.abs(node.x)).toBeLessThanOrEqual(2000); expect(Math.abs(node.y)).toBeLessThanOrEqual(2000)
      })
    }
  })
  it('rejects stale, missing, duplicate and nonfinite originals atomically', () => {
    const state = createCanvasState('p')
    for (const originals of [[state.nodes[0], { ...state.nodes[1], x: 400 }], [state.nodes[0], { ...state.nodes[1], presentationId: 'missing' }], [state.nodes[0], state.nodes[0]]]) {
      expect(moveCanvasGroup(state, originals, { x: 20, y: 30 })).toBe(state)
    }
    expect(moveCanvasGroup(state, state.nodes, { x: NaN, y: 10 })).toBe(state)
    expect(moveCanvasGroup(state, [], { x: 10, y: 10 })).toBe(state)
    expect(moveCanvasGroup(state, state.nodes, { x: 0, y: 0 })).toBe(state)
  })
})

import { canvasMarqueeRefs, marqueeHits, isMarqueeArea, CANVAS_NODE_SIZE } from './model'

describe('Slice1B marquee model geometry and order', () => {
  it.each([
    ['inside', 130, 100, 140, 110, ['project-node']],
    ['overlap', 110, 80, 130, 100, ['project-node']],
    ['reverse', 700, 500, 0, 0, ['project-node', 'note-node']],
    ['edge contact', 350, 90, 400, 100, []],
    ['zero width', 130, 100, 130, 120, []],
    ['zero height', 130, 100, 140, 100, []],
    ['empty', -20, -20, 0, 0, []],
    ['bottom overlap', 120, 249, 130, 260, ['project-node']],
    ['bottom contact', 120, 250, 130, 260, []],
  ])('%s uses positive area node bounds', (_name, x1, y1, x2, y2, expected) => {
    expect(CANVAS_NODE_SIZE).toEqual({ width: 230, height: 160 })
    expect(marqueeHits(createCanvasState('p').nodes, { x: x1, y: y1 }, { x: x2, y: y2 }).map(n => n.presentationId)).toEqual(expected)
  })
  it.each([[0, 0, false], [3, 1, false], [4, 0, false], [0, 10, false], [3, 3, true], [4, 1, true]])('client threshold %s,%s -> %s', (x, y, expected) => {
    expect(isMarqueeArea({ x: 0, y: 0 }, { x, y })).toBe(expected)
  })
  it('unions current survivors then hits in deliberately nonlexical model order without edges or stale scope', () => {
    const state = createCanvasState('p')
    const nodes = ['z', 'a', 'm'].map(presentationId => ({ ...state.nodes[0], presentationId }))
    const scope = { workspaceId: 'w', projectId: 'p', surfaceId: 'canvas' as const }
    const ref = (localId: string) => ({ ...scope, kind: 'NODE' as const, localId })
    const start = { x: 0, y: 0 }, end = { x: 700, y: 500 }
    expect(canvasMarqueeRefs(nodes, start, end, scope).map(r => r.localId)).toEqual(['z', 'a', 'm'])
    expect(canvasMarqueeRefs(nodes, start, end, scope, [ref('m'), ref('missing'), { ...ref('a'), projectId: 'wrong' }, { ...ref('z'), kind: 'CLIP' }, ref('m')]).map(r => r.localId)).toEqual(['m', 'z', 'a'])
  })
})
