import type { RemoteCatalogProvider } from '../../localization'
import { TolgeeRemoteCatalogAdapter } from './adapters/TolgeeRemoteCatalogAdapter'

export function createConfiguredRemoteCatalogProvider(environment: ImportMetaEnv = import.meta.env): RemoteCatalogProvider | undefined {
  const deliveryPrefix = environment.VITE_TOLGEE_PUBLIC_DELIVERY_PREFIX?.trim()
  const manifestUrl = environment.VITE_TOLGEE_PUBLIC_MANIFEST_URL?.trim()
  if (!deliveryPrefix && !manifestUrl) return undefined
  if (!deliveryPrefix || !manifestUrl) return undefined
  const configuredTimeout = Number(environment.VITE_TOLGEE_PUBLIC_TIMEOUT_MS ?? '2500')
  try {
    return new TolgeeRemoteCatalogAdapter({ deliveryPrefix, manifestUrl, timeoutMs: configuredTimeout })
  } catch {
    return undefined
  }
}
