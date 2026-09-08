import { describe, expect, it } from 'vitest'
import { commandRegistry, detectShortcutConflicts, getCommandAvailability, resolvePaletteShortcut } from './commandRegistry'

describe('command availability registry', () => {
  it('blocks project commands without resolved Project context', () => {
    const command = commandRegistry.find(candidate => candidate.id === 'timeline.operation.apply')!
    expect(getCommandAvailability(command, { surfaceId: 'nle', hasResolvedProject: false }).available).toBe(false)
  })

  it('does not let surface maturity or navigation bypass access', () => {
    const command = commandRegistry.find(candidate => candidate.id === 'project.create')!
    const availability = getCommandAvailability(command, { surfaceId: 'workspace', hasResolvedProject: false })
    expect(availability.available).toBe(false)
    expect(availability.reason).toContain('disabled')
  })

  it('detects default and user-override shortcut conflicts', () => {
    expect(detectShortcutConflicts(commandRegistry)).toEqual({})
    expect(detectShortcutConflicts(commandRegistry, { 'project.create': 'Mod+K' })).toEqual({
      'mod+k': ['navigation.command-palette.open', 'project.create'],
    })
  })
})


describe('bounded command palette shortcut resolution', () => {
  it('fails closed for unsupported external values and registry collisions while retaining other overrides', () => {
    for (const value of ['', 'Ctrl+K', 'mod+k', 'Mod+Shift+K', 'Mod+Alt+Delete', '<img src=x onerror=alert(1)>', null, 42]) {
      expect(resolvePaletteShortcut({ 'navigation.command-palette.open': value as string })).toEqual({ error: 'unsupported' })
    }
    const overrides = { 'navigation.command-palette.open': 'Mod+Alt+P', 'project.create': 'mod+alt+p' } as const
    expect(resolvePaletteShortcut(overrides)).toEqual({ error: 'conflict' })
    expect(overrides['project.create']).toBe('mod+alt+p')
    expect(resolvePaletteShortcut({ 'project.create': 'Mod+K' })).toEqual({ error: 'conflict' })
    for (const [shortcut, key, altKey] of [['Mod+K', 'k', false], ['Mod+Alt+K', 'k', true], ['Mod+Alt+P', 'p', true]] as const) {
      expect(resolvePaletteShortcut({ 'navigation.command-palette.open': shortcut, 'project.create': 'Mod+Alt+N' })).toEqual({ error: null, shortcut, key, altKey })
    }
  })
})
