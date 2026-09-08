import { describe, expect, it, vi } from 'vitest'
import { createCatalog } from '../../../localization'
import { TolgeeRemoteCatalogAdapter, validateTolgeeManifest, type TolgeeCatalogManifest } from './TolgeeRemoteCatalogAdapter'

const catalog = createCatalog('zh-CN', {
  common: { greeting: { message: '你好，{name}', params: ['name'] } },
  shell: { commands: { message: '命令', params: [] } },
})

const manifest: TolgeeCatalogManifest = {
  schemaVersion: 1,
  catalogVersion: '2026.09.0',
  sourceLocale: 'en',
  fallbackLocale: 'en',
  locales: ['en', 'zh-CN'],
  namespaces: ['common', 'shell'],
  contentDigests: { en: 'sha256:8e7930a07e92ae5761f8cf766bb5a4ce82493ae8d3d2a5e831c5ce6922e3e2b9', 'zh-CN': catalog.contentDigest },
  parameterContracts: { 'common.greeting': ['name'], 'shell.commands': [] },
}

describe('Tolgee public Content Delivery adapter', () => {
  it('validates a strict versioned manifest', () => {
    expect(validateTolgeeManifest(manifest).ok).toBe(true)
    expect(validateTolgeeManifest({ ...manifest, schemaVersion: 2 }).ok).toBe(false)
    expect(validateTolgeeManifest({ ...manifest, catalogVersion: 'old' }).ok).toBe(false)
    expect(validateTolgeeManifest({ ...manifest, projectId: 123 }).ok).toBe(false)
    expect(validateTolgeeManifest({ ...manifest, locales: ['fr'] }).ok).toBe(false)
  })

  it('fetches the documented namespaced namespace/locale.json routes without credentials', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input)
      const body = url.endsWith('/manifest.json') ? manifest
        : url.endsWith('/common/zh-CN.json') ? { greeting: '你好，{name}' }
          : url.endsWith('/shell/zh-CN.json') ? { commands: '命令' }
            : null
      return new Response(JSON.stringify(body), { status: body ? 200 : 404, headers: { 'content-type': 'application/json' } })
    })
    const adapter = new TolgeeRemoteCatalogAdapter({
      deliveryPrefix: 'http://127.0.0.1:4179/i18n/v2026-09',
      manifestUrl: 'http://127.0.0.1:4179/i18n/v2026-09/manifest.json',
      fetchImpl: fetcher,
      timeoutMs: 100,
    })
    expect(await adapter.loadCatalog('zh-CN', new AbortController().signal)).toEqual(catalog)
    expect(fetcher.mock.calls.map(([url]) => String(url))).toEqual([
      'http://127.0.0.1:4179/i18n/v2026-09/manifest.json',
      'http://127.0.0.1:4179/i18n/v2026-09/common/zh-CN.json',
      'http://127.0.0.1:4179/i18n/v2026-09/shell/zh-CN.json',
    ])
    for (const [, init] of fetcher.mock.calls) expect(init).toMatchObject({ credentials: 'omit' })
  })

  it('invokes the default platform fetch with the global receiver', async () => {
    const platformFetch = vi.fn(function (this: unknown, input: RequestInfo | URL, _init?: RequestInit) {
      if (this !== globalThis) throw new TypeError('fetch called with a non-platform receiver')
      const url = String(input)
      const body = url.endsWith('/manifest.json') ? manifest
        : url.endsWith('/common/zh-CN.json') ? { greeting: '你好，{name}' }
          : url.endsWith('/shell/zh-CN.json') ? { commands: '命令' }
            : null
      return Promise.resolve(new Response(JSON.stringify(body), { status: body ? 200 : 404, headers: { 'content-type': 'application/json' } }))
    })
    vi.stubGlobal('fetch', platformFetch)
    try {
      const adapter = new TolgeeRemoteCatalogAdapter({
        deliveryPrefix: 'http://127.0.0.1:4179/i18n/v2026-09',
        manifestUrl: 'http://127.0.0.1:4179/i18n/v2026-09/manifest.json',
        timeoutMs: 100,
      })
      expect(await adapter.loadCatalog('zh-CN', new AbortController().signal)).toEqual(catalog)
      expect(platformFetch).toHaveBeenCalledTimes(3)
      for (const [, init] of platformFetch.mock.calls) expect(init).toMatchObject({ credentials: 'omit' })
    } finally {
      vi.unstubAllGlobals()
    }
  })

  it('rejects well-shaped TMS contracts that alter source params or introduce TMS-owned keys', async () => {
    const changed = [
      { ...manifest, parameterContracts: { ...manifest.parameterContracts, 'common.greeting': ['person'] } },
      { ...manifest, parameterContracts: { ...manifest.parameterContracts, 'shell.tmsOwnedKey': [] } },
    ]
    for (const remoteManifest of changed) {
      expect(validateTolgeeManifest(remoteManifest).ok).toBe(true)
      const fetchImpl = vi.fn().mockResolvedValue(new Response(JSON.stringify(remoteManifest), { status: 200 }))
      const adapter = new TolgeeRemoteCatalogAdapter({ deliveryPrefix: 'https://static.example.test/v1', manifestUrl: 'https://static.example.test/v1/manifest.json', fetchImpl })
      await expect(adapter.loadCatalog('zh-CN', new AbortController().signal)).rejects.toThrow(/platform source|platform owned/)
      expect(fetchImpl).toHaveBeenCalledTimes(1)
    }
  })

  it('rejects invalid, outage, and digest-mismatched delivery without returning a catalog', async () => {
    const scenarios = [
      vi.fn().mockRejectedValue(new TypeError('offline')),
      vi.fn().mockResolvedValue(new Response('{', { status: 200 })),
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ ...manifest, contentDigests: { 'zh-CN': 'sha256:' + '0'.repeat(64) } }), { status: 200 })),
    ]
    for (const fetchImpl of scenarios) {
      const adapter = new TolgeeRemoteCatalogAdapter({ deliveryPrefix: 'https://static.example.test/v1', manifestUrl: 'https://static.example.test/v1/manifest.json', fetchImpl, timeoutMs: 25 })
      await expect(adapter.loadCatalog('zh-CN', new AbortController().signal)).rejects.toBeTruthy()
    }
  })

  it('rejects arbitrary or insecure delivery configuration', () => {
    expect(() => new TolgeeRemoteCatalogAdapter({ deliveryPrefix: 'http://evil.example/i18n', manifestUrl: 'http://evil.example/manifest.json' })).toThrow()
    expect(() => new TolgeeRemoteCatalogAdapter({ deliveryPrefix: 'https://a.example/i18n', manifestUrl: 'https://b.example/manifest.json' })).toThrow()
  })
})
