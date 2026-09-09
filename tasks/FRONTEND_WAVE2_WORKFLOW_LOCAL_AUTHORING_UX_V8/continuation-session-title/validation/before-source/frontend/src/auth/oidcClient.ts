import { UserManager, WebStorageStateStore, type User } from 'oidc-client-ts'
import { getOidcSettings, isOidcEnabled } from './oidcConfig'

let userManager: UserManager | null = null
// Initiation has no native SDK event; retire local consumers before redirect work.
const signoutListeners = new Set<() => void>()

function manager(): UserManager {
  if (!isOidcEnabled()) {
    throw new Error('OIDC is not configured (set VITE_OIDC_ISSUER)')
  }
  if (!userManager) {
    const { issuer, clientId, redirectUri, scope } = getOidcSettings()
    userManager = new UserManager({
      authority: issuer,
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope,
      automaticSilentRenew: true,
      loadUserInfo: true,
      userStore: new WebStorageStateStore({ store: window.sessionStorage }),
    })
  }
  return userManager
}

/** Invalidation only: no principal, token, stored hints or async user hydration. */
export function subscribeOidcSessionRetirement(onRetire: () => void): () => void {
  if (!isOidcEnabled()) return () => {}
  const { events } = manager()
  let active = true
  const retire = () => { if (active) onRetire() }
  // A reload/renewal conservatively retires even when the principal is unchanged.
  events.addUserLoaded(retire)
  events.addUserUnloaded(retire)
  events.addAccessTokenExpired(retire)
  events.addUserSignedIn(retire)
  events.addUserSignedOut(retire)
  events.addUserSessionChanged(retire)
  signoutListeners.add(retire)
  return () => {
    active = false
    events.removeUserLoaded(retire)
    events.removeUserUnloaded(retire)
    events.removeAccessTokenExpired(retire)
    events.removeUserSignedIn(retire)
    events.removeUserSignedOut(retire)
    events.removeUserSessionChanged(retire)
    signoutListeners.delete(retire)
  }
}

export async function signInRedirect(): Promise<void> {
  await manager().signinRedirect()
}

export async function handleOAuthCallback(): Promise<User> {
  const user = await manager().signinRedirectCallback()
  if (user.profile?.sub) {
    localStorage.setItem('user_id', user.profile.sub)
  }
  const tenant =
    (user.profile as Record<string, unknown>)?.tenantId ??
    (user.profile as Record<string, unknown>)?.tenant_id
  if (typeof tenant === 'string' && tenant) {
    localStorage.setItem('tenant_id', tenant)
  }
  return user
}

export async function getOidcUser(): Promise<User | null> {
  if (!isOidcEnabled()) return null
  try {
    return await manager().getUser()
  } catch {
    return null
  }
}

export async function getAccessToken(): Promise<string | null> {
  const user = await getOidcUser()
  if (!user || user.expired) return null
  return user.access_token ?? null
}

export async function signOutOidc(): Promise<void> {
  if (!isOidcEnabled()) return
  for (const retire of signoutListeners) retire()
  await manager().signoutRedirect()
}
