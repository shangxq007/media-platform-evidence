import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Badge, Breadcrumb, Button, CommandPalette, ResizablePanel } from '../design-system'
import { commandRegistry, getCommandAvailability, getShortcut, resolvePaletteShortcut, paletteShortcutChoices, type PaletteShortcut, type ShortcutOverrides } from '../../foundation/commandRegistry'
import { useEffectiveAccessCatalog } from '../../foundation/platformClient'
import { surfaceRegistry, getSurface, type SurfaceId } from '../../foundation/surfaceRegistry'
import { SelectionProvider, useInteractionStore, useSelection } from '../../interaction/SelectionContext'
import { AgentLauncher, AgentShell, SelectionInspector, useSelectionCommands } from '../../interaction/InteractionShell'
import type { ProjectContextValue } from '../../foundation/projectContext'
import { useTranslation, type SupportedLocale } from '../../localization'
import { InteractionDialog } from '../../interaction/InteractionDialog'
import { NotificationInbox } from '../../product/notifications/NotificationInbox'

const localAvailabilityMessageKeys: Readonly<Record<string, string>> = {
  'This surface is not discoverable at its current maturity.': 'shell.commandHiddenSurface',
  'A server-resolved Project context is required.': 'shell.commandUnresolvedProject',
  'Effective access is not available from the server. This action is disabled.': 'shell.commandMissingAccess',
}

export function WorkspaceHeader({ workspaceId, project }: { workspaceId?: string; project?: ProjectContextValue }) {
  const { locale, setLocale, t } = useTranslation()
  return (
    <header className="ff-workspace-header">
      <a className="ff-brand" href={workspaceId ? `/w/${encodeURIComponent(workspaceId)}/home` : '/'} aria-label={t('shell.brandHome')}><span aria-hidden="true">MP</span><strong>{t('shell.brand')}</strong></a>
      <Breadcrumb items={[
        ...(workspaceId ? [{ label: workspaceId, href: `/w/${encodeURIComponent(workspaceId)}/home` }] : []),
        ...(project ? [{ label: project.projectName ?? project.projectId }] : []),
      ]} />
      <span className="ff-header-actions">{t('shell.creativeWorkspace')}</span>
      <label className="ff-locale-selector">{t('common.localeSelector')}<select value={locale} onChange={event => setLocale(event.target.value as SupportedLocale)}><option value="en">{t('common.localeEnglish')}</option><option value="zh-CN">{t('common.localeChinese')}</option></select></label>
    </header>
  )
}

export function GlobalNavigation({ workspaceId }: { workspaceId?: string }) {
  const { t } = useTranslation()
  return <nav className="ff-global-nav" aria-label={t('shell.globalNavigation')}><a href={workspaceId ? `/w/${encodeURIComponent(workspaceId)}/home` : '/'}>{t('shell.workspace')}</a><a href="/operations/overview">{t('shell.operations')}</a><a href="/admin/organization">{t('shell.admin')}</a><a href="/developer/capabilities">{t('shell.developer')}</a></nav>
}

export function ProjectNavigation({ project }: { project: ProjectContextValue }) {
  const { t } = useTranslation()
  return <nav className="ff-project-nav" aria-label={t('shell.projectNavigation')}><a href={`/w/${encodeURIComponent(project.workspaceId)}/projects/${encodeURIComponent(project.projectId)}/overview`}>{t('shell.overview')}</a><a href={`/w/${encodeURIComponent(project.workspaceId)}/projects/${encodeURIComponent(project.projectId)}/review`}>{t('shell.review')}</a><a href={`/w/${encodeURIComponent(project.workspaceId)}/projects/${encodeURIComponent(project.projectId)}/production`}>{t('shell.production')}</a></nav>
}

export function SurfaceSwitcher({ project, currentSurfaceId, label }: { project: ProjectContextValue; currentSurfaceId: SurfaceId; label?: string }) {
  const { t } = useTranslation()
  const surfaces = surfaceRegistry.filter(surface => surface.projectScoped && surface.maturity !== 'HIDDEN')
  return <nav className="ff-surface-switcher" aria-label={label ?? t('shell.projectSurfaceSwitcher')}>{surfaces.map(surface => <a key={surface.id} href={surface.buildRoute(project)} aria-current={surface.id === currentSurfaceId ? 'page' : undefined}>{surface.displayName}<Badge tone={surface.maturity === 'PREVIEW' ? 'warning' : 'neutral'}>{surface.maturity}</Badge></a>)}</nav>
}

export function AssetBrowserHost() {
  const { t } = useTranslation()
  return <div className="ff-host-state"><strong>{t('shell.assets')}</strong><p>{t('shell.assetsUnavailable')}</p></div>
}
export function CenterWorkspace({ children }: { children: ReactNode }) { return <main id="main-content" className="ff-center-workspace" tabIndex={-1}>{children}</main> }
export function BottomPanel() { const { t } = useTranslation(); return <div className="ff-host-state"><strong>{t('shell.timelineActivity')}</strong><p>{t('shell.canonicalResults')}</p></div> }
export function ActivityPanel() { const { t } = useTranslation(); return <aside className="ff-activity-panel" aria-label={t('shell.activityPanel')}><strong>{t('shell.activity')}</strong><p>{t('shell.activityUnavailable')}</p></aside> }

function ShellContent({ surfaceId, workspaceId, project, children, shortcutOverrides = {} }: {
  surfaceId: SurfaceId
  workspaceId?: string
  project?: ProjectContextValue
  children: ReactNode
  shortcutOverrides?: ShortcutOverrides
}) {
  const surface = getSurface(surfaceId)
  const accessKeys = useMemo(() => commandRegistry.flatMap(command => command.requiredAccessKey ? [command.requiredAccessKey] : []), [])
  const access = useEffectiveAccessCatalog(accessKeys)
  const store = useInteractionStore()
  const selection = useSelection()
  const newSession = () => ({ store, lifetime: selection.lifetime, shortcut: undefined as PaletteShortcut | undefined, panel: null as 'palette' | 'editor' | null, draft: '' })
  const [session, setSession] = useState(newSession)
  // Retire only command UI state; preserve the mounted shell and its other consumers.
  if (session.store !== store || session.lifetime !== selection.lifetime) setSession(newSession())
  if (session.panel && selection.agentOpen) setSession(current => ({ ...current, panel: null }))
  const setPaletteOpen = (open: boolean) => setSession(current => ({ ...current, panel: open ? 'palette' : null }))
  const [leftVisible, setLeftVisible] = useState(false)
  const { t } = useTranslation()

  const effectiveOverrides = session.shortcut === undefined ? shortcutOverrides : { ...shortcutOverrides, 'navigation.command-palette.open': session.shortcut }
  const paletteBinding = resolvePaletteShortcut(effectiveOverrides)
  const draftBinding = resolvePaletteShortcut({ ...effectiveOverrides, 'navigation.command-palette.open': session.draft })
  const defaultShortcut = resolvePaletteShortcut().shortcut!
  const defaultBinding = resolvePaletteShortcut({ ...effectiveOverrides, 'navigation.command-palette.open': defaultShortcut })
  const modalPresent = () => Boolean(document.querySelector('[role="dialog"][aria-modal="true"]'))
  const openPalette = () => { if (!modalPresent()) setPaletteOpen(true) }
  const closeEditor = () => setSession(current => ({ ...current, panel: null }))
  const applyShortcut = (shortcut: PaletteShortcut) => setSession(current => ({ ...current, shortcut, panel: null }))

  const composing = useRef(false)
  useEffect(() => {
    const startComposition = () => { composing.current = true }
    const endComposition = () => { composing.current = false }
    const listener = (event: KeyboardEvent) => {
      if ((event.target as HTMLElement)?.closest?.('input, textarea, select, [contenteditable]:not([contenteditable="false"])')) return
      if (paletteBinding.error || event.defaultPrevented || event.repeat || composing.current || event.isComposing || event.keyCode === 229 || event.getModifierState('AltGraph')) return
      if (modalPresent()) return
      if (event.metaKey !== event.ctrlKey && !event.shiftKey && event.altKey === paletteBinding.altKey && event.key.toLowerCase() === paletteBinding.key) { event.preventDefault(); setPaletteOpen(true) }
    }
    window.addEventListener('compositionstart', startComposition, true)
    window.addEventListener('compositionend', endComposition, true)
    window.addEventListener('blur', endComposition)
    window.addEventListener('keydown', listener)
    return () => {
      window.removeEventListener('compositionstart', startComposition, true)
      window.removeEventListener('compositionend', endComposition, true)
      window.removeEventListener('blur', endComposition)
      window.removeEventListener('keydown', listener)
    }
  }, [paletteBinding.error, paletteBinding.shortcut])

  const selectionCommands = useSelectionCommands()
  const paletteActions = [...selectionCommands.map(action => ({ ...action, onSelect: () => { setPaletteOpen(false); action.onSelect() } })), ...commandRegistry.filter(command => command.id !== 'navigation.command-palette.open').map(command => {
    const availability = getCommandAvailability(command, { surfaceId, hasResolvedProject: project?.status === 'RESOLVED', accessCatalog: access.data })
    const accessEntry = command.requiredAccessKey ? access.data?.[command.requiredAccessKey] : undefined
    // Identify the explanation's origin only; getCommandAvailability remains the availability authority.
    // Server text stays verbatim even when it happens to match a known local message.
    const serverExplanation = surface.maturity !== 'HIDDEN' && (!command.projectRequired || project?.status === 'RESOLVED') && accessEntry?.source === 'SERVER' && availability.reason === accessEntry.explanation
    const reasonKey = serverExplanation ? undefined : localAvailabilityMessageKeys[availability.reason]
    const reason = reasonKey ? t(reasonKey) : availability.reason
    const canonicalUnavailable = t('agent.canonicalUnavailable')
    return { id: command.id, label: t(`shell.command.${command.id}`), shortcut: getShortcut(command, shortcutOverrides), disabledReason: availability.available ? canonicalUnavailable : `${canonicalUnavailable} ${reason}`, onSelect: () => { store.dispatch({ category: 'CANONICAL_SEMANTIC', type: 'semantic', commandId: command.id }, 'COMMAND') } }
  })]

  return (
    <div className="ff-app-shell" data-surface={surfaceId} data-studio="horizontal" onClickCapture={event => {
      if (session.panel && modalPresent() && !(event.target as HTMLElement).closest('[role="dialog"][aria-modal="true"]')) {
        event.preventDefault()
        event.stopPropagation()
      }
    }}>
      <a className="skip-link" href="#main-content">{t('shell.skipToMain')}</a>
      <WorkspaceHeader workspaceId={workspaceId} project={project} />
      <div className="ff-shell-toolbar" aria-label={t('shell.panelControls')}>
        <details className="ff-navigation-menu" onKeyDown={event => { if (event.key === 'Escape') { event.currentTarget.open = false; event.currentTarget.querySelector('summary')?.focus() } }}><summary>{t('shell.navigation')}</summary><div className="ff-navigation-drawer">
          <GlobalNavigation workspaceId={workspaceId} />
          {project ? <ProjectNavigation project={project} /> : null}
          {project ? <SurfaceSwitcher project={project} currentSurfaceId={surfaceId} label={t('shell.navigationDrawerSurfaces')} /> : null}
        </div></details>
        <span className="ff-surface-label">{surface.displayName}</span>
        {surface.shellRegions['asset-browser'] !== 'HIDDEN' ? <Button variant="ghost" aria-pressed={leftVisible} onClick={() => setLeftVisible(value => !value)}>{t('shell.toggleAssetBrowser')}</Button> : null}
        <Button variant="ghost" onClick={openPalette}>{t('shell.commands')} <kbd>{paletteBinding.shortcut ?? t('shell.shortcut.unavailable')}</kbd></Button>
        <Button variant="ghost" onClick={() => {
          if (!modalPresent()) setSession(current => ({ ...current, panel: 'editor', draft: paletteBinding.shortcut ?? '' }))
        }}>{t('shell.shortcut.title')}</Button>
        <AgentLauncher />
        <NotificationInbox />
      </div>
      {project ? <div className="ff-primary-surfaces"><SurfaceSwitcher project={project} currentSurfaceId={surfaceId} /></div> : null}
      <div className="ff-shell-body">
        {leftVisible ? <ResizablePanel title={t('shell.assetBrowser')} side="left" initialSize={220}><AssetBrowserHost /></ResizablePanel> : null}
        <div className="ff-shell-center"><CenterWorkspace>{children}</CenterWorkspace></div>
        <SelectionInspector />
      </div>
      <AgentShell />
      {session.panel === 'editor' ? <InteractionDialog title={t('shell.shortcut.title')} closeLabel={t('shell.shortcut.close')} onClose={closeEditor} className="ff-shortcut-editor">
        <p>{t('shell.shortcut.session')}</p>
        <p>{t('shell.shortcut.mod')}</p>
        <p>{t('shell.shortcut.current', { shortcut: paletteBinding.shortcut ?? t('shell.shortcut.unavailable') })}</p>
        {paletteBinding.error ? <p role="alert">{t(paletteBinding.error === 'unsupported' ? 'shell.shortcut.unsupported' : 'shell.shortcut.conflict')}</p> : null}
        <label>{t('shell.shortcut.choice')}<select data-dialog-entry value={session.draft} onChange={event => setSession(current => ({ ...current, draft: event.target.value }))}>
          {!session.draft ? <option value="" disabled>{t('shell.shortcut.choose')}</option> : null}
          {paletteShortcutChoices.map(shortcut => <option key={shortcut} value={shortcut}>{shortcut}</option>)}
        </select></label>
        {session.draft && draftBinding.error ? <p role="alert">{t(draftBinding.error === 'unsupported' ? 'shell.shortcut.unsupported' : 'shell.shortcut.conflict')}</p> : null}
        {defaultBinding.error ? <p>{t('shell.shortcut.defaultConflict')}</p> : null}
        <div className="ff-shortcut-actions">
          <Button disabled={Boolean(draftBinding.error)} onClick={() => { if (!draftBinding.error) applyShortcut(draftBinding.shortcut) }}>{t('shell.shortcut.apply')}</Button>
          <Button variant="ghost" disabled={Boolean(defaultBinding.error)} onClick={() => { if (!defaultBinding.error) applyShortcut(defaultBinding.shortcut) }}>{t('shell.shortcut.reset')}</Button>
          <Button variant="ghost" onClick={closeEditor}>{t('shell.shortcut.cancel')}</Button>
        </div>
      </InteractionDialog> : null}
      <CommandPalette open={session.panel === 'palette'} actions={paletteActions} onClose={() => setPaletteOpen(false)} />
    </div>
  )
}

export function ProductAppShell(props: Parameters<typeof ShellContent>[0]) {
  return <SelectionProvider scope={{ surfaceId: props.surfaceId, workspaceId: props.workspaceId, projectId: props.project?.projectId }}><ShellContent {...props} /></SelectionProvider>
}
