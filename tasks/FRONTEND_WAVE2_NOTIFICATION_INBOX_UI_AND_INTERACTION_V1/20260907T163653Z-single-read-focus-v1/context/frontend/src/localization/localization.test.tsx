import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createHash } from 'node:crypto'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import {
  LocalizationProvider,
  BundledCatalogProvider,
  MemoryCatalogCache,
  createCatalog,
  messageAt,
  requiredSourceKeys,
  useTranslation,
  validateCatalog,
  validateRequiredSourceKeys,
  sha256,
  type RemoteCatalogProvider,
} from './index'

function Probe() {
  const { locale, setLocale, t, formatDate, formatNumber, formatUnit, formatDuration } = useTranslation()
  return <div>
    <output>{locale}</output>
    <p>{t('shell.commands')}</p>
    <p>{t('common.greeting', { name: 'Ari' })}</p>
    <p data-testid="missing">{t('review.missingInZh')}</p>
    <p data-testid="formatters">{formatDate(new Date('2026-09-06T00:00:00Z'), { timeZone: 'UTC' })}|{formatNumber(1200)}|{formatUnit(12, 'megabyte')}|{formatDuration(65)}</p>
    <button onClick={() => setLocale('en')}>English</button>
    <button onClick={() => setLocale('zh-CN')}>简体中文</button>
  </div>
}

describe('localization runtime', () => {
  it('renders bundled English and Chinese, switches at runtime, formats values, and falls back per key', async () => {
    render(<LocalizationProvider initialLocale="en"><Probe /></LocalizationProvider>)
    expect(screen.getByText('Commands')).toBeTruthy()
    expect(screen.getByText('Hello, Ari')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '简体中文' }))
    expect(screen.getByText('命令')).toBeTruthy()
    expect(screen.getByText('你好，Ari')).toBeTruthy()
    expect(screen.getByTestId('missing').textContent).toBe('English fallback proof')
    expect(screen.getByTestId('formatters').textContent).toContain('1,200')
  })

  it('uses an explicit development marker for an unknown key', () => {
    function UnknownProbe() { return <>{useTranslation().t('common.doesNotExist')}</> }
    render(<LocalizationProvider environment="development"><UnknownProbe /></LocalizationProvider>)
    expect(screen.getByText('⟦missing:common.doesNotExist⟧')).toBeTruthy()
  })

  it('validates required interpolation parameters and ignores extras', () => {
    function InterpolationProbe() {
      const { t } = useTranslation()
      return <><p>{t('common.greeting', {} as never)}</p><p>{t('common.greeting', { name: 'Ari', ignored: 'x' })}</p></>
    }
    render(<LocalizationProvider environment="development"><InterpolationProbe /></LocalizationProvider>)
    expect(screen.getByText('⟦params:common.greeting:name⟧')).toBeTruthy()
    expect(screen.getByText('Hello, Ari')).toBeTruthy()
  })

  it('keeps synchronous bundled copy through remote outage and invalid payloads, then accepts valid remote copy', async () => {
    const outage: RemoteCatalogProvider = { loadCatalog: vi.fn().mockRejectedValue(new Error('offline')) }
    const invalid: RemoteCatalogProvider = { loadCatalog: vi.fn().mockResolvedValue({ schemaVersion: 99 }) }
    const remote = createCatalog('zh-CN', { common: { greeting: { message: '远程问候，{name}', params: ['name'] } }, shell: { commands: { message: '远程命令', params: [] } } })

    const first = render(<LocalizationProvider initialLocale="zh-CN" remoteProvider={outage}><Probe /></LocalizationProvider>)
    expect(screen.getByText('命令')).toBeTruthy()
    await waitFor(() => expect(outage.loadCatalog).toHaveBeenCalledWith('zh-CN', expect.any(AbortSignal)))
    first.unmount()

    const second = render(<LocalizationProvider initialLocale="zh-CN" remoteProvider={invalid}><Probe /></LocalizationProvider>)
    expect(screen.getByText('命令')).toBeTruthy()
    await waitFor(() => expect(invalid.loadCatalog).toHaveBeenCalled())
    expect(screen.queryByText('远程命令')).toBeNull()
    second.unmount()

    render(<LocalizationProvider initialLocale="zh-CN" remoteProvider={{ loadCatalog: vi.fn().mockResolvedValue(remote) }}><Probe /></LocalizationProvider>)
    expect(screen.getByText('命令')).toBeTruthy()
    expect(await screen.findByText('远程命令')).toBeTruthy()
  })

  it('prevents a stale locale request from replacing the current locale', async () => {
    let resolveChinese!: (value: unknown) => void
    const provider: RemoteCatalogProvider = {
      loadCatalog: vi.fn((locale) => locale === 'zh-CN'
        ? new Promise(resolve => { resolveChinese = resolve })
        : Promise.resolve(createCatalog('en', { shell: { commands: { message: 'Current English', params: [] } } }))),
    }
    render(<LocalizationProvider remoteProvider={provider}><Probe /></LocalizationProvider>)
    fireEvent.click(screen.getByRole('button', { name: '简体中文' }))
    fireEvent.click(screen.getByRole('button', { name: 'English' }))
    expect(await screen.findByText('Current English')).toBeTruthy()
    resolveChinese(createCatalog('zh-CN', { shell: { commands: { message: 'Stale Chinese', params: [] } } }))
    await Promise.resolve()
    expect(screen.queryByText('Stale Chinese')).toBeNull()
  })

  it('loads a fresh-object provider once per unresolved locale and reuses resolved cache entries', async () => {
    const loadCatalog = vi.fn((locale: 'en' | 'zh-CN') => Promise.resolve(createCatalog(locale, {
      shell: { commands: { message: locale === 'en' ? 'Remote English' : 'Remote Chinese', params: [] } },
    })))
    function Parent() {
      const [renderCount, setRenderCount] = useState(0)
      return <>
        <button onClick={() => setRenderCount(value => value + 1)}>Parent {renderCount}</button>
        <LocalizationProvider remoteProvider={{ loadCatalog }}><Probe /></LocalizationProvider>
      </>
    }

    render(<Parent />)
    expect(await screen.findByText('Remote English')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Parent 0' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Parent 1' })).toBeTruthy())
    expect(loadCatalog).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: '简体中文' }))
    expect(await screen.findByText('Remote Chinese')).toBeTruthy()
    expect(loadCatalog).toHaveBeenCalledTimes(2)
    fireEvent.click(screen.getByRole('button', { name: 'English' }))
    expect(await screen.findByText('Remote English')).toBeTruthy()
    await Promise.resolve()
    expect(loadCatalog).toHaveBeenCalledTimes(2)
  })

  it('honors an injected resolved cache without refreshing it', async () => {
    const cache = new MemoryCatalogCache()
    cache.set(createCatalog('zh-CN', { shell: { commands: { message: 'Injected Chinese', params: [] } } }))
    const remoteProvider: RemoteCatalogProvider = { loadCatalog: vi.fn().mockRejectedValue(new Error('must not refresh')) }
    render(<LocalizationProvider initialLocale="zh-CN" cache={cache} remoteProvider={remoteProvider}><Probe /></LocalizationProvider>)
    expect(screen.getByText('Injected Chinese')).toBeTruthy()
    await Promise.resolve()
    expect(remoteProvider.loadCatalog).not.toHaveBeenCalled()
  })

  it('rejects validly digested remote keys and parameter contracts that diverge from English', async () => {
    const alteredParameters = createCatalog('zh-CN', {
      common: { greeting: { message: '你好，{person}', params: ['person'] } },
      shell: { commands: { message: 'Must not replace bundled copy', params: [] } },
    })
    const unknownKey = createCatalog('zh-CN', {
      shell: {
        commands: { message: 'Must not replace bundled copy either', params: [] },
        tmsOwnedKey: { message: 'Not platform owned', params: [] },
      },
    })
    expect(validateCatalog(alteredParameters).ok).toBe(true)
    expect(validateCatalog(unknownKey).ok).toBe(true)

    const first = render(<LocalizationProvider initialLocale="zh-CN" remoteProvider={{ loadCatalog: vi.fn().mockResolvedValue(alteredParameters) }}><Probe /></LocalizationProvider>)
    await waitFor(() => expect(screen.queryByText('Must not replace bundled copy')).toBeNull())
    expect(screen.getByText('命令')).toBeTruthy()
    first.unmount()

    render(<LocalizationProvider initialLocale="zh-CN" remoteProvider={{ loadCatalog: vi.fn().mockResolvedValue(unknownKey) }}><Probe /></LocalizationProvider>)
    await waitFor(() => expect(screen.queryByText('Must not replace bundled copy either')).toBeNull())
    expect(screen.getByText('命令')).toBeTruthy()
  })
})

describe('catalog contract', () => {
  it('provides bundled catalogs through a concrete synchronous provider boundary', () => {
    const provider = new BundledCatalogProvider()
    expect(provider.getCatalog('en').locale).toBe('en')
    expect(messageAt(provider.getCatalog('zh-CN'), 'shell.commands')?.message).toBe('命令')
    expect(provider.getSourceCatalog()).toBe(provider.getCatalog('en'))
  })

  it('uses the standard SHA-256 digest algorithm', () => {
    expect(sha256('abc')).toBe('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
    for (const value of ['你好，世界', 'localization 😀', '\ud800']) {
      expect(sha256(value)).toBe(createHash('sha256').update(value, 'utf8').digest('hex'))
    }
  })

  it('rejects schema and catalog version mismatches, unknown fields, HTML, malformed locale/namespaces/digest/params, and digest tampering', () => {
    const catalog = createCatalog('en', { common: { greeting: { message: 'Hello, {name}', params: ['name'] } } })
    expect(validateCatalog(catalog).ok).toBe(true)
    const mutations = [
      { ...catalog, schemaVersion: 2 },
      { ...catalog, catalogVersion: 'unsupported' },
      { ...catalog, locale: 'fr' },
      { ...catalog, namespaces: [] },
      { ...catalog, contentDigest: 'sha256:deadbeef' },
      { ...catalog, unexpected: true },
      createCatalog('en', { common: { bad: { message: '<script>alert(1)</script>', params: [] } } }),
      createCatalog('en', { common: { bad: { message: 'Hello, {name}', params: [] } } }),
    ]
    for (const mutation of mutations) expect(validateCatalog(mutation).ok).toBe(false)
  })

  it('contains malformed and prototype-key inputs and permits repeated placeholders under one parameter contract', () => {
    const repeated = createCatalog('en', { common: { repeated: { message: '{name} / {name}', params: ['name'] } } })
    expect(validateCatalog(repeated).ok).toBe(true)

    const prototypeMessages = JSON.parse('{"__proto__":{"message":"hostile","params":[]}}')
    const prototypeKey = createCatalog('en', { common: prototypeMessages })
    expect(() => validateCatalog(prototypeKey)).not.toThrow()
    expect(validateCatalog(prototypeKey).ok).toBe(false)
    expect(messageAt(createCatalog('en', { common: {} }), 'common.__proto__')).toBeUndefined()
    const malformedUnicode = createCatalog('en', { common: { malformed: { message: '\ud800', params: [] } } })
    expect(validateCatalog(malformedUnicode).ok).toBe(false)
    const hostileProxy = new Proxy({}, { ownKeys: () => { throw new Error('hostile trap') } })
    expect(() => validateCatalog(hostileProxy)).not.toThrow()
    expect(validateCatalog(hostileProxy).ok).toBe(false)
  })

  it('guards every required source key', () => {
    expect(validateRequiredSourceKeys(requiredSourceKeys).ok).toBe(true)
    expect(validateRequiredSourceKeys([...requiredSourceKeys, 'shell.notBundled'])).toEqual({ ok: false, missing: ['shell.notBundled'] })
  })
})
