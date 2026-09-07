import type { InboxSource } from './types'

// Intentionally no auth inspection or transport. FB-GAP-010/002 remain open.
export const unavailableSource: InboxSource = {
  context: { principalId: null, tenantId: null, sessionId: 'unconfigured', access: 'unknown' },
  adapter: {
    origin: 'unavailable', capabilities: { singleRead: false, readAll: 'unsupported' },
    async list(request) { return { status: 'unavailable', context: request.context, requestId: request.requestId } },
  },
}
