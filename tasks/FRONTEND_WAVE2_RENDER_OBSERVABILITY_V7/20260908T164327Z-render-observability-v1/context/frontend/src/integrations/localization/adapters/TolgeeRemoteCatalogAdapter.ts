import {
  CATALOG_NAMESPACES,
  CATALOG_SCHEMA_VERSION,
  CATALOG_VERSION,
  SOURCE_LOCALE,
  SUPPORTED_LOCALES,
  createCatalog,
  isSupportedLocale,
  validatePlatformCatalogContract,
  validatePlatformParameterContracts,
  type CatalogNamespace,
  type CatalogNamespaces,
  type RemoteCatalogProvider,
  type SupportedLocale,
  type ValidationResult,
} from '../../../localization'

export interface TolgeeCatalogManifest {
  readonly schemaVersion: typeof CATALOG_SCHEMA_VERSION
  readonly catalogVersion: typeof CATALOG_VERSION
  readonly sourceLocale: typeof SOURCE_LOCALE
  readonly fallbackLocale: typeof SOURCE_LOCALE
  readonly locales: readonly SupportedLocale[]
  readonly namespaces: readonly CatalogNamespace[]
  readonly contentDigests: Readonly<Partial<Record<SupportedLocale, string>>>
  readonly parameterContracts: Readonly<Record<string, readonly string[]>>
}

type FetchImplementation = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
const manifestFields = ['schemaVersion', 'catalogVersion', 'sourceLocale', 'fallbackLocale', 'locales', 'namespaces', 'contentDigests', 'parameterContracts']
const identifierPattern = /^[a-z][a-zA-Z0-9]*(?:[._-][a-zA-Z0-9]+)*$/
const digestPattern = /^sha256:[a-f0-9]{64}$/

function isRecord(value: unknown): value is Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return false
  const prototype = Object.getPrototypeOf(value)
  return prototype === Object.prototype || prototype === null
}

function hasExactFields(value: Record<string, unknown>, fields: readonly string[]): boolean {
  const keys = Object.keys(value).sort()
  return keys.length === fields.length && [...fields].sort().every((field, index) => keys[index] === field)
}

function hasOwn(value: object, key: PropertyKey): boolean {
  return Object.prototype.hasOwnProperty.call(value, key)
}

export function validateTolgeeManifest(input: unknown): ValidationResult<TolgeeCatalogManifest> {
  if (!isRecord(input) || !hasExactFields(input, manifestFields)) return { ok: false, error: 'manifest fields are malformed or unknown' }
  if (input.schemaVersion !== CATALOG_SCHEMA_VERSION || input.catalogVersion !== CATALOG_VERSION) return { ok: false, error: 'incompatible manifest version' }
  if (input.sourceLocale !== SOURCE_LOCALE || input.fallbackLocale !== SOURCE_LOCALE) return { ok: false, error: 'invalid manifest locale contract' }
  const locales = input.locales
  if (!Array.isArray(locales) || locales.length !== SUPPORTED_LOCALES.length || !locales.every(isSupportedLocale) || new Set(locales).size !== locales.length || !SUPPORTED_LOCALES.every(locale => locales.includes(locale))) return { ok: false, error: 'malformed manifest locales' }
  if (!Array.isArray(input.namespaces) || !input.namespaces.length || !input.namespaces.every(value => typeof value === 'string' && (CATALOG_NAMESPACES as readonly string[]).includes(value)) || new Set(input.namespaces).size !== input.namespaces.length) return { ok: false, error: 'malformed manifest namespaces' }
  const contentDigests = input.contentDigests
  if (!isRecord(contentDigests) || Object.keys(contentDigests).length !== SUPPORTED_LOCALES.length || Object.entries(contentDigests).some(([locale, digest]) => !isSupportedLocale(locale) || typeof digest !== 'string' || !digestPattern.test(digest)) || !SUPPORTED_LOCALES.every(locale => typeof contentDigests[locale] === 'string')) return { ok: false, error: 'malformed manifest digests' }
  if (!isRecord(input.parameterContracts)) return { ok: false, error: 'malformed parameter contracts' }
  for (const [key, params] of Object.entries(input.parameterContracts)) {
    const namespace = key.split('.')[0]
    if (!identifierPattern.test(key) || !(input.namespaces as string[]).includes(namespace) || !Array.isArray(params) || !params.every(param => typeof param === 'string' && identifierPattern.test(param)) || new Set(params).size !== params.length) return { ok: false, error: `malformed parameter contract: ${key}` }
  }
  return { ok: true, value: input as unknown as TolgeeCatalogManifest }
}

function validatedBaseUrl(value: string, label: string): URL {
  const url = new URL(value)
  const localFixture = url.protocol === 'http:' && (url.hostname === '127.0.0.1' || url.hostname === 'localhost')
  if (url.protocol !== 'https:' && !localFixture) throw new Error(`${label} must use HTTPS (HTTP is allowed only for a local fixture)`)
  if (url.username || url.password || url.search || url.hash) throw new Error(`${label} must not contain credentials, query, or fragment`)
  return url
}

export class TolgeeRemoteCatalogAdapter implements RemoteCatalogProvider {
  private readonly deliveryPrefix: URL
  private readonly manifestUrl: URL
  private readonly fetchImpl: FetchImplementation
  private readonly timeoutMs: number

  constructor({ deliveryPrefix, manifestUrl, fetchImpl = globalThis.fetch.bind(globalThis), timeoutMs = 2500 }: {
    deliveryPrefix: string
    manifestUrl: string
    fetchImpl?: FetchImplementation
    timeoutMs?: number
  }) {
    this.deliveryPrefix = validatedBaseUrl(deliveryPrefix.replace(/\/$/, ''), 'deliveryPrefix')
    this.manifestUrl = validatedBaseUrl(manifestUrl, 'manifestUrl')
    if (this.deliveryPrefix.origin !== this.manifestUrl.origin || !this.manifestUrl.pathname.startsWith(`${this.deliveryPrefix.pathname}/`)) throw new Error('manifestUrl must be under the configured deliveryPrefix')
    if (!/(?:^|\/)v[0-9][a-zA-Z0-9._-]*(?:\/|$)/.test(this.deliveryPrefix.pathname)) throw new Error('deliveryPrefix must contain an explicit version segment')
    if (!Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30_000) throw new Error('timeoutMs must be between 1 and 30000')
    this.fetchImpl = fetchImpl
    this.timeoutMs = timeoutMs
  }

  async loadCatalog(locale: SupportedLocale, signal: AbortSignal): Promise<unknown> {
    const controller = new AbortController()
    const abort = () => controller.abort(signal.reason)
    if (signal.aborted) abort()
    else signal.addEventListener('abort', abort, { once: true })
    const timer = globalThis.setTimeout(() => controller.abort(new DOMException('Localization delivery timeout', 'TimeoutError')), this.timeoutMs)
    try {
      const manifestInput = await this.fetchJson(this.manifestUrl.href, controller.signal)
      const result = validateTolgeeManifest(manifestInput)
      if (!result.ok) throw new Error(result.error)
      const manifest = result.value
      const platformContracts = validatePlatformParameterContracts(manifest.parameterContracts)
      if (!platformContracts.ok) throw new Error(platformContracts.error)
      if (!manifest.locales.includes(locale) || !manifest.contentDigests[locale]) throw new Error(`locale ${locale} is not manifested`)
      const namespaces: CatalogNamespaces = {}
      for (const namespace of manifest.namespaces) {
        const input = await this.fetchJson(`${this.deliveryPrefix.href}/${namespace}/${locale}.json`, controller.signal)
        if (!isRecord(input) || Object.values(input).some(value => typeof value !== 'string')) throw new Error(`${namespace}: Tolgee export must be a flat JSON string map`)
        const definitions: Record<string, { message: string; params: readonly string[] }> = Object.create(null)
        for (const [key, value] of Object.entries(input)) {
          const fullKey = `${namespace}.${key}`
          const contract = hasOwn(manifest.parameterContracts, fullKey) ? manifest.parameterContracts[fullKey] : undefined
          if (!contract) throw new Error(`${namespace}.${key}: missing explicit parameter contract`)
          definitions[key] = { message: value as string, params: contract }
        }
        namespaces[namespace] = definitions
      }
      const catalog = createCatalog(locale, namespaces)
      if (catalog.contentDigest !== manifest.contentDigests[locale]) throw new Error('delivered content digest does not match manifest')
      const platformCatalog = validatePlatformCatalogContract(catalog)
      if (!platformCatalog.ok) throw new Error(platformCatalog.error)
      return platformCatalog.value
    } finally {
      globalThis.clearTimeout(timer)
      signal.removeEventListener('abort', abort)
    }
  }

  private async fetchJson(url: string, signal: AbortSignal): Promise<unknown> {
    const response = await this.fetchImpl(url, { credentials: 'omit', signal, headers: { Accept: 'application/json' } })
    if (!response.ok) throw new Error(`localization delivery returned HTTP ${response.status}`)
    return response.json()
  }
}
