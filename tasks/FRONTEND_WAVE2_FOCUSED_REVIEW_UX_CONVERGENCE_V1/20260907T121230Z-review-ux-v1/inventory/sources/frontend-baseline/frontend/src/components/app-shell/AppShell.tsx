import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Badge, Breadcrumb, Button, CommandPalette, ResizablePanel } from '../design-system'
import { commandRegistry, getCommandAvailability, getShortcut, type ShortcutOverrides } from '../../foundation/commandRegistry'
import { useEffectiveAccessCatalog } from '../../foundation/platformClient'
import { surfaceRegistry, getSurface, type SurfaceId } from '../../foundation/surfaceRegistry'
import { SelectionProvider, useInteractionStore } from '../../interaction/SelectionContext'
import { AgentLauncher, AgentShell, SelectionInspector, useSelectionCommands } from '../../interaction/InteractionShell'
import type { ProjectContextValue } from '../../foundation/projectContext'
import { useTranslation, type SupportedLocale } from '../../localization'

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
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [leftVisible, setLeftVisible] = useState(false)
  const { t } = useTranslation()

  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if ((event.target as HTMLElement)?.closest?.('input, textarea, select, [contenteditable]:not([contenteditable="false"])')) return
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setPaletteOpen(true) }
    }
    window.addEventListener('keydown', listener)
    return () => window.removeEventListener('keydown', listener)
  }, [])

  const store = useInteractionStore()
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
    <div className="ff-app-shell" data-surface={surfaceId} data-studio="horizontal">
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
        <Button variant="ghost" onClick={() => setPaletteOpen(true)}>{t('shell.commands')} <kbd>⌘K</kbd></Button>
        <AgentLauncher />
      </div>
      {project ? <div className="ff-primary-surfaces"><SurfaceSwitcher project={project} currentSurfaceId={surfaceId} /></div> : null}
      <div className="ff-shell-body">
        {leftVisible ? <ResizablePanel title={t('shell.assetBrowser')} side="left" initialSize={220}><AssetBrowserHost /></ResizablePanel> : null}
        <div className="ff-shell-center"><CenterWorkspace>{children}</CenterWorkspace></div>
        <SelectionInspector />
      </div>
      <AgentShell />
      <CommandPalette open={paletteOpen} actions={paletteActions} onClose={() => setPaletteOpen(false)} />
    </div>
  )
}

export function ProductAppShell(props: Parameters<typeof ShellContent>[0]) {
  return <SelectionProvider scope={{ surfaceId: props.surfaceId, workspaceId: props.workspaceId, projectId: props.project?.projectId }}><ShellContent {...props} /></SelectionProvider>
}
