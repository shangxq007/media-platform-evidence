import type { EffectiveAccessCatalog } from './effectiveAccess'
import { getEffectiveAccess, isAvailable } from './effectiveAccess'
import { getSurface, type SurfaceId } from './surfaceRegistry'

export type CommandId =
  | 'navigation.command-palette.open'
  | 'project.create'
  | 'render.open'
  | 'timeline.operation.apply'
  | 'canvas.reference.add'
  | 'workflow.invoke'
  | 'agent.action.authorize'
  | 'review.merge.request'

export interface CommandContext {
  readonly surfaceId: SurfaceId
  readonly hasResolvedProject: boolean
  readonly accessCatalog?: EffectiveAccessCatalog
}

export interface CommandAvailability {
  readonly available: boolean
  readonly reason: string
}

export interface CommandDescriptor {
  readonly id: CommandId
  readonly label: string
  readonly defaultShortcut?: string
  readonly projectRequired: boolean
  readonly requiredAccessKey: string | null
}

export type ShortcutOverrides = Readonly<Partial<Record<CommandId, string>>>

export const commandRegistry: readonly CommandDescriptor[] = [
  { id: 'navigation.command-palette.open', label: 'Open command palette', defaultShortcut: 'Mod+K', projectRequired: false, requiredAccessKey: null },
  { id: 'project.create', label: 'Create project', defaultShortcut: 'Mod+Shift+N', projectRequired: false, requiredAccessKey: 'project.create' },
  { id: 'render.open', label: 'Open render entry', defaultShortcut: 'Mod+Enter', projectRequired: true, requiredAccessKey: 'render.submit' },
  { id: 'timeline.operation.apply', label: 'Apply timeline operation', projectRequired: true, requiredAccessKey: 'timeline.operation.apply' },
  { id: 'canvas.reference.add', label: 'Add canvas reference', projectRequired: true, requiredAccessKey: 'canvas.reference.add' },
  { id: 'workflow.invoke', label: 'Invoke workflow', projectRequired: true, requiredAccessKey: 'workflow.invoke' },
  { id: 'agent.action.authorize', label: 'Authorize proposed action', projectRequired: true, requiredAccessKey: 'agent.action.authorize' },
  { id: 'review.merge.request', label: 'Request canonical merge', projectRequired: true, requiredAccessKey: 'timeline.merge' },
]

export function getCommandAvailability(command: CommandDescriptor, context: CommandContext): CommandAvailability {
  const surface = getSurface(context.surfaceId)
  if (surface.maturity === 'HIDDEN') return { available: false, reason: 'This surface is not discoverable at its current maturity.' }
  if (command.projectRequired && !context.hasResolvedProject) return { available: false, reason: 'A server-resolved Project context is required.' }
  const access = getEffectiveAccess(context.accessCatalog, command.requiredAccessKey)
  if (!isAvailable(access)) return { available: false, reason: access.explanation }
  return { available: true, reason: 'Available for invocation; the server will authorize the command again.' }
}

export function getShortcut(command: CommandDescriptor, overrides: ShortcutOverrides = {}): string | undefined {
  return overrides[command.id] ?? command.defaultShortcut
}

export function detectShortcutConflicts(
  commands: readonly CommandDescriptor[],
  overrides: ShortcutOverrides = {},
): Readonly<Record<string, readonly CommandId[]>> {
  const entries = commands.reduce<Record<string, CommandId[]>>((accumulator, command) => {
    const shortcut = getShortcut(command, overrides)?.toLowerCase()
    if (!shortcut) return accumulator
    accumulator[shortcut] = [...(accumulator[shortcut] ?? []), command.id]
    return accumulator
  }, {})
  return Object.fromEntries(Object.entries(entries).filter(([, ids]) => ids.length > 1))
}

export function useShortcutOverrides(overrides: ShortcutOverrides = {}): ShortcutOverrides {
  return overrides
}


export const paletteShortcutChoices = ['Mod+K', 'Mod+Alt+K', 'Mod+Alt+P'] as const
export type PaletteShortcut = typeof paletteShortcutChoices[number]
export type PaletteShortcutBinding =
  | { readonly error: null; readonly shortcut: PaletteShortcut; readonly key: string; readonly altKey: boolean }
  | { readonly error: 'unsupported' | 'conflict'; readonly shortcut?: undefined }

export function resolvePaletteShortcut(overrides: ShortcutOverrides = {}): PaletteShortcutBinding {
  const command = commandRegistry.find(command => command.id === 'navigation.command-palette.open')!
  const requested = overrides[command.id]
  if (requested !== undefined && typeof requested !== 'string') return { error: 'unsupported' }
  const shortcut = paletteShortcutChoices.find(choice => choice === getShortcut(command, overrides))
  if (!shortcut) return { error: 'unsupported' }
  if (detectShortcutConflicts(commandRegistry, overrides)[shortcut.toLowerCase()]) return { error: 'conflict' }
  return { error: null, shortcut, key: shortcut.slice(-1).toLowerCase(), altKey: shortcut.includes('+Alt+') }
}
