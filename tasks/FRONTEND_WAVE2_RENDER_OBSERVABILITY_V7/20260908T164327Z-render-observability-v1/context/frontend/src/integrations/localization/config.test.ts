import { describe, expect, it } from 'vitest'
import { createConfiguredRemoteCatalogProvider } from './config'
import { TolgeeRemoteCatalogAdapter } from './adapters/TolgeeRemoteCatalogAdapter'

describe('localization integration composition', () => {
  it('is disabled when public delivery configuration is absent or incomplete', () => {
    expect(createConfiguredRemoteCatalogProvider({} as ImportMetaEnv)).toBeUndefined()
    expect(createConfiguredRemoteCatalogProvider({ VITE_TOLGEE_PUBLIC_DELIVERY_PREFIX: 'https://static.example.test/v1' } as ImportMetaEnv)).toBeUndefined()
  })

  it('constructs only a validated credential-free public adapter', () => {
    const adapter = createConfiguredRemoteCatalogProvider({
      VITE_TOLGEE_PUBLIC_DELIVERY_PREFIX: 'https://static.example.test/i18n/v2026-09',
      VITE_TOLGEE_PUBLIC_MANIFEST_URL: 'https://static.example.test/i18n/v2026-09/manifest.json',
      VITE_TOLGEE_PUBLIC_TIMEOUT_MS: '1200',
    } as ImportMetaEnv)
    expect(adapter).toBeInstanceOf(TolgeeRemoteCatalogAdapter)
    expect(createConfiguredRemoteCatalogProvider({
      VITE_TOLGEE_PUBLIC_DELIVERY_PREFIX: 'http://uncontrolled.example/i18n/v1',
      VITE_TOLGEE_PUBLIC_MANIFEST_URL: 'http://uncontrolled.example/i18n/v1/manifest.json',
    } as ImportMetaEnv)).toBeUndefined()
  })
})
