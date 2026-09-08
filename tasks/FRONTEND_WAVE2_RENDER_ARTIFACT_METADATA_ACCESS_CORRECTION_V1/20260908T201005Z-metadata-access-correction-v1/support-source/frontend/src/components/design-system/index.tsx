import { InteractionDialog } from '../../interaction/InteractionDialog'
import { useTranslation } from '../../localization'
import {
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type ComponentPropsWithRef,
  type KeyboardEvent,
  type ReactNode,
} from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

export function Button({ variant = 'secondary', className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return <button className={`ff-button ff-button--${variant} ${className}`} {...props} />
}

export function IconButton({ label, icon, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; icon: ReactNode }) {
  return <button className="ff-icon-button" aria-label={label} title={label} {...props}>{icon}</button>
}

export function Input(props: ComponentPropsWithRef<'input'>) {
  return <input className={`ff-input ${props.className ?? ''}`} {...props} />
}

export function Search({ label = 'Search', ...props }: ComponentPropsWithRef<'input'> & { label?: string }) {
  return <Input type="search" aria-label={label} placeholder={props.placeholder ?? 'Search'} {...props} />
}

export interface TabDefinition { id: string; label: string; disabled?: boolean; tabId?: string; panelId?: string }

export function Tabs({ tabs, activeId, onChange, label }: { tabs: readonly TabDefinition[]; activeId: string; onChange: (id: string) => void; label: string }) {
  const tabElements = useRef(new Map<string, HTMLButtonElement>())
  const moveTab = (event: KeyboardEvent<HTMLButtonElement>, currentId: string) => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return
    const enabled = tabs.filter(tab => !tab.disabled)
    const currentIndex = enabled.findIndex(tab => tab.id === currentId)
    if (currentIndex < 0) return
    let nextIndex: number | null = null
    if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % enabled.length
    if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + enabled.length) % enabled.length
    if (event.key === 'Home') nextIndex = 0
    if (event.key === 'End') nextIndex = enabled.length - 1
    if (nextIndex === null) return
    event.preventDefault()
    const next = enabled[nextIndex]
    onChange(next.id)
    tabElements.current.get(next.id)?.focus()
  }
  return (
    <div className="ff-tabs" role="tablist" aria-label={label}>
      {tabs.map(tab => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          id={tab.tabId}
          aria-controls={tab.panelId}
          aria-selected={activeId === tab.id}
          disabled={tab.disabled}
          tabIndex={activeId === tab.id ? 0 : -1}
          ref={element => {
            if (element) tabElements.current.set(tab.id, element)
            else tabElements.current.delete(tab.id)
          }}
          onKeyDown={event => moveTab(event, tab.id)}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'info' | 'success' | 'warning' | 'danger' }) {
  return <span className={`ff-badge ff-badge--${tone}`}>{children}</span>
}

export function Status({ label, tone = 'neutral' }: { label: string; tone?: 'neutral' | 'info' | 'success' | 'warning' | 'danger' }) {
  return <span className={`ff-status ff-status--${tone}`}><span aria-hidden="true" />{label}</span>
}

export function Panel({ title, actions, children, className = '' }: { title?: string; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`ff-panel ${className}`}>
      {title ? <header className="ff-panel__header"><h2>{title}</h2>{actions}</header> : null}
      <div className="ff-panel__body">{children}</div>
    </section>
  )
}

export function ResizablePanel({ title, side, initialSize = 260, min = 180, max = 480, children }: {
  title: string
  side: 'left' | 'right' | 'bottom'
  initialSize?: number
  min?: number
  max?: number
  children: ReactNode
}) {
  const [size, setSize] = useState(initialSize)
  const horizontal = side !== 'bottom'
  const change = (delta: number) => setSize(current => Math.min(max, Math.max(min, current + delta)))
  return (
    <section className={`ff-resizable ff-resizable--${side}`} style={horizontal ? { width: size } : { height: size }}>
      <div
        className="ff-resizable__handle"
        role="separator"
        aria-label={`Resize ${title}`}
        aria-orientation={horizontal ? 'vertical' : 'horizontal'}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={size}
        tabIndex={0}
        onKeyDown={event => {
          if (event.key === (horizontal ? 'ArrowLeft' : 'ArrowUp')) { event.preventDefault(); change(-16) }
          if (event.key === (horizontal ? 'ArrowRight' : 'ArrowDown')) { event.preventDefault(); change(16) }
        }}
      />
      <Panel title={title}>{children}</Panel>
    </section>
  )
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="ff-empty"><span aria-hidden="true">◇</span><h2>{title}</h2><p>{description}</p>{action}</div>
}

export function Skeleton({ label = 'Loading' }: { label?: string }) {
  return <div className="ff-skeleton" role="status" aria-label={label}><span className="sr-only">{label}</span></div>
}

export interface BreadcrumbItem { label: string; href?: string }
export function Breadcrumb({ items }: { items: readonly BreadcrumbItem[] }) {
  return (
    <nav aria-label="Breadcrumb"><ol className="ff-breadcrumb">
      {items.map((item, index) => <li key={`${item.label}-${index}`}>{item.href ? <a href={item.href}>{item.label}</a> : <span aria-current="page">{item.label}</span>}</li>)}
    </ol></nav>
  )
}

export function InspectorSection({ title, children }: { title: string; children: ReactNode }) {
  return <section className="ff-inspector-section"><h3>{title}</h3>{children}</section>
}

export function PropertyRow({ label, children }: { label: string; children: ReactNode }) {
  return <div className="ff-property-row"><span>{label}</span><div>{children}</div></div>
}

export function Toast({ title, message, onDismiss }: { title: string; message: string; onDismiss?: () => void }) {
  return <div className="ff-toast" role="status"><div><strong>{title}</strong><p>{message}</p></div>{onDismiss ? <IconButton label="Dismiss notification" icon="×" onClick={onDismiss} /> : null}</div>
}

export interface PaletteAction { id: string; label: string; shortcut?: string; disabledReason?: string; onSelect: () => void }
export function CommandPalette({ open, actions, onClose }: { open: boolean; actions: readonly PaletteAction[]; onClose: () => void }) {
  return open ? <PaletteContent actions={actions} onClose={onClose} /> : null
}
function PaletteContent({ actions, onClose }: { actions: readonly PaletteAction[]; onClose: () => void }) {
  const [query, setQuery] = useState('')
  const { t } = useTranslation()
  const id = useId()
  const input = useRef<HTMLInputElement>(null)
  const buttons = useRef(new Map<string, HTMLButtonElement>())
  const activeId = useRef<string | null>(null)
  const composing = useRef(false)
  const composingActivationKeys = useRef(new Set<string>())
  const visible = actions.filter(action => action.label.toLowerCase().includes(query.toLowerCase()))
  const enabled = visible.filter(action => !action.disabledReason)
  const currentActions = useRef(visible)
  useLayoutEffect(() => {
    currentActions.current = visible
    if (activeId.current !== null && !enabled.some(action => action.id === activeId.current)) {
      activeId.current = null
      input.current?.focus()
    }
  })
  const guardComposition = (event: KeyboardEvent<HTMLDivElement>) => {
    // Space activates on release, which can arrive after compositionend.
    const blockedRelease = event.type === 'keyup' && composingActivationKeys.current.delete(event.key)
    const isComposing = composing.current || event.nativeEvent.isComposing || event.nativeEvent.keyCode === 229
    if (!isComposing && !blockedRelease) return
    // Keep composed text native, but isolate IME keys from the dialog and shell.
    event.stopPropagation()
    if (event.target instanceof HTMLButtonElement && (event.key === 'Enter' || event.key === ' ')) {
      if (event.type === 'keydown') composingActivationKeys.current.add(event.key)
      event.preventDefault()
    }
  }
  const navigate = (event: KeyboardEvent<HTMLInputElement | HTMLButtonElement>, fromId?: string) => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return
    const currentIndex = fromId === undefined ? -1 : enabled.findIndex(action => action.id === fromId)
    if (fromId !== undefined && currentIndex < 0) return
    let nextIndex: number
    if (event.key === 'ArrowDown') nextIndex = fromId === undefined ? 0 : Math.min(currentIndex + 1, enabled.length - 1)
    else if (event.key === 'ArrowUp') nextIndex = fromId === undefined ? enabled.length - 1 : Math.max(currentIndex - 1, 0)
    else if (fromId !== undefined && event.key === 'Home') nextIndex = 0
    else if (fromId !== undefined && event.key === 'End') nextIndex = enabled.length - 1
    else return // Enter/Space activate only through the result button's native click.
    event.preventDefault()
    const next = enabled[nextIndex]
    if (next) buttons.current.get(next.id)?.focus()
  }
  return <InteractionDialog title={t('shell.commandPalette')} closeLabel={t('shell.closeCommandPalette')} onClose={onClose} className="ff-command-palette">
    <div className="ff-command-content" onCompositionStart={() => { composing.current = true }} onCompositionEnd={() => { composing.current = false }} onKeyDownCapture={guardComposition} onKeyUpCapture={guardComposition} onBlur={event => {
      if (event.relatedTarget && !Array.from(buttons.current.values()).includes(event.relatedTarget as HTMLButtonElement)) activeId.current = null
    }}>
      <Search ref={input} data-dialog-entry aria-describedby={`${id}-help`} label={t('shell.searchCommands')} value={query} onChange={event => {
        setQuery(event.target.value)
        activeId.current = null
        input.current?.focus()
      }} onKeyDown={event => navigate(event)} placeholder={t('shell.typeCommand')} />
      <p id={`${id}-help`} className="ff-command-help">{t('shell.commandNavigationHelp')}</p>
      <p role="status" className="ff-command-status">{visible.length ? t('shell.commandResultCount', { count: visible.length, available: enabled.length }) : t('shell.noMatchingCommands')}</p>
      <ul>{visible.map(action => <li key={action.id}>
        <button type="button" disabled={Boolean(action.disabledReason)} aria-describedby={action.disabledReason ? `${id}-reason-${action.id}` : undefined} ref={element => {
          if (element) buttons.current.set(action.id, element)
          else buttons.current.delete(action.id)
        }} onFocus={event => {
          activeId.current = action.id
          event.currentTarget.scrollIntoView?.({ block: 'nearest' })
        }} onKeyDown={event => navigate(event, action.id)} onClick={event => {
          const current = currentActions.current.find(candidate => candidate.id === action.id)
          if (composing.current || !event.currentTarget.isConnected || buttons.current.get(action.id) !== event.currentTarget || !current || current.disabledReason) return
          current.onSelect()
        }}><span>{action.label}</span>{action.shortcut ? <kbd>{action.shortcut}</kbd> : null}</button>
        {action.disabledReason ? <><p id={`${id}-reason-${action.id}`}>{action.disabledReason}</p><details><summary>{t('shell.technicalDetails')}</summary><p>{t('shell.commandUnavailable')}</p></details></> : null}
      </li>)}</ul>
    </div>
  </InteractionDialog>
}
