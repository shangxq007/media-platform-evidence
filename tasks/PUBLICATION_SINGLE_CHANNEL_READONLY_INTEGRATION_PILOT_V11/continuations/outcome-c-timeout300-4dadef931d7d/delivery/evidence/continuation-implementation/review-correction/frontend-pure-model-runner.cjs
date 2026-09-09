'use strict'

// Task-local, synchronous proof runner. It transpiles and executes only the actual
// publication model/types modules plus their real installed zod dependency.
const assert = require('node:assert/strict')
const crypto = require('node:crypto')
const fs = require('node:fs')
const path = require('node:path')

const frontendRoot = path.resolve(process.argv[2] || '')
if (!process.argv[2] || !fs.statSync(frontendRoot).isDirectory()) {
  throw new Error('expected one frontend-root argv')
}
const modelPath = fs.realpathSync(path.join(frontendRoot, 'src/product/publication/model.ts'))
const typesPath = fs.realpathSync(path.join(frontendRoot, 'src/product/publication/types.ts'))
const allowedSources = new Set([modelPath, typesPath])
const ts = require(require.resolve('typescript', { paths: [frontendRoot] }))
const zodPath = require.resolve('zod', { paths: [frontendRoot] })
const cache = new Map()

function sourceHash(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')
}

function loadTypeScript(file) {
  const resolved = fs.realpathSync(file)
  if (!allowedSources.has(resolved)) throw new Error(`loader denied source: ${resolved}`)
  if (cache.has(resolved)) return cache.get(resolved).exports
  const source = fs.readFileSync(resolved, 'utf8')
  const emitted = ts.transpileModule(source, {
    fileName: resolved,
    reportDiagnostics: true,
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      esModuleInterop: true,
      isolatedModules: true,
    },
  })
  const errors = (emitted.diagnostics || []).filter(diagnostic => diagnostic.category === ts.DiagnosticCategory.Error)
  if (errors.length) throw new Error(`transpile diagnostics: ${errors.map(error => error.code).join(',')}`)
  const moduleRecord = { exports: {} }
  cache.set(resolved, moduleRecord)
  const boundedRequire = specifier => {
    if (specifier === 'zod' && resolved === modelPath) return require(zodPath)
    if (specifier === './types' && resolved === modelPath) return loadTypeScript(typesPath)
    throw new Error(`loader denied import from ${path.basename(resolved)}: ${specifier}`)
  }
  const execute = new Function('exports', 'require', 'module', '__filename', '__dirname', emitted.outputText)
  execute(moduleRecord.exports, boundedRequire, moduleRecord, resolved, path.dirname(resolved))
  return moduleRecord.exports
}

const model = loadTypeScript(modelPath)
const types = loadTypeScript(typesPath)
const results = []
function test(id, body) {
  try {
    body()
    results.push({ id, status: 'passed' })
  } catch (error) {
    results.push({ id, status: 'failed', error: error instanceof Error ? error.message : String(error) })
  }
}

const scope = { principalId: 'person', tenantId: 'tenant', sessionId: 'session', workspaceId: 'w', projectId: 'p', sourceId: 'source' }
const request = { scope, requestId: 'request1', query: { kind: 'project-publication-snapshot', limit: 200 } }
function grant(key) {
  return {
    key, source: 'SERVER', status: 'AVAILABLE', reasonCode: 'PURE_FIXTURE',
    factors: { capability: 'SATISFIED', runtime: 'NOT_APPLICABLE', entitlement: 'SATISFIED', policy: 'SATISFIED', quota: 'NOT_APPLICABLE' },
  }
}
const listAccess = { [types.LIST_KEY]: grant(types.LIST_KEY) }
function publicationReceipt(changes = {}) {
  return {
    scope, requestId: request.requestId, query: request.query, status: 'ok', contract: 'fixture-only-publication-graph-v1', version: 'v1', completeness: 'bounded',
    relations: { artifacts: 'known-empty', attempts: 'known-empty', externalPublications: 'known-empty' },
    accounts: [{ id: 'account1', name: 'Synthetic account', platform: 'Neutral fixture' }],
    plans: [
      { id: 'scheduled-plan', projectId: 'p', accountId: 'account1', status: 'scheduled', artifactIds: [], timeField: 'scheduledAt', scheduledAt: '2026-09-09T10:00:00Z' },
      { id: 'queued-raw-plan', projectId: 'p', accountId: 'account1', status: 'queued', artifactIds: [], timeField: 'unknown' },
      { id: 'future-plan', projectId: 'p', accountId: 'account1', status: 'FUTURE_PROVIDER_STATE', artifactIds: [], timeField: 'unscheduled' },
    ],
    artifacts: [], attempts: [], externalPublications: [],
    ...changes,
  }
}

const externalRequest = {
  requestId: 'external-request1', binding: { scope, ownerId: 'host1' },
  window: { semantics: 'half-open', startInclusive: '2026-09-01T00:00:00Z', endExclusive: '2026-10-01T00:00:00Z' },
}
function externalReceipt(changes = {}) {
  const observation = {
    kind: 'external-publication-observation',
    externalReferences: { provider: 'neutral-provider', instance: 'instance1', account: 'account1', post: 'post1' },
    coreBinding: { status: 'PENDING_CORE_CONTRACT' }, displayStatus: 'unknown', statusMapping: 'unmapped', timeField: 'unknown',
    relationships: {
      project: { status: 'PENDING_CORE_CONTRACT' }, artifacts: { status: 'PENDING_CORE_CONTRACT' },
      attempts: { status: 'PENDING_CORE_CONTRACT' }, externalOutcomes: { status: 'PENDING_CORE_CONTRACT' },
    },
  }
  return {
    contract: 'external-publication-observation-v2', status: 'ok', requestId: externalRequest.requestId, binding: externalRequest.binding,
    access: { authority: 'owner-local-single-user', scope: 'narrower-than-platform-effective-access', list: true, content: false },
    providerVersion: 'fixture-v1', providerSourceCommit: 'synthetic-source', evidence: 'pure-synthetic-projection',
    window: { ...externalRequest.window, upstreamEndInclusive: '2026-09-30T23:59:59.999Z' }, observedAt: '2026-09-09T13:00:00Z',
    completeness: 'bounded', omissions: {},
    externalAccount: { externalReferences: { provider: 'neutral-provider', instance: 'instance1', account: 'account1' }, label: 'Synthetic account', providerLabel: 'neutral', coreBinding: { status: 'PENDING_CORE_CONTRACT' } },
    observations: [observation],
    ...changes,
  }
}

test('frontend-pure.actual-modules-and-generic-status-boundary', () => {
  assert.equal(model.normalizePublicationStatus('scheduled'), 'scheduled')
  assert.equal(model.normalizePublicationStatus('queue'), 'unknown')
  assert.equal(model.normalizePublicationStatus('queued'), 'unknown')
  assert.equal(model.normalizePublicationStatus('FUTURE_PROVIDER_STATE'), 'unknown')
  const parsed = model.parsePublication(publicationReceipt(), request, listAccess)
  assert.equal(parsed.status, 'ok')
  assert.deepEqual(parsed.plans.map(plan => plan.status), ['scheduled', 'unknown', 'unknown'])
})

test('frontend-pure.parse-publication-exact-request-scope-and-safe-envelope-status', () => {
  assert.equal(model.parsePublication({ ...request, status: 'unavailable' }, request, listAccess).status, 'unavailable')
  assert.equal(model.parsePublication({ ...request, status: 'error' }, request, listAccess).status, 'error')
  assert.equal(model.parsePublication(publicationReceipt(), { ...request, requestId: 'different' }, listAccess).status, 'invalid')
  assert.equal(model.parsePublication(publicationReceipt(), { ...request, scope: { ...scope, projectId: 'different' } }, listAccess).status, 'invalid')
  assert.equal(model.parsePublication(publicationReceipt(), request, {}).status, 'restricted')
})

test('frontend-pure.relation-unavailable-known-empty-and-restricted-remain-distinct', () => {
  const knownEmpty = model.parsePublication(publicationReceipt({ plans: [] }), request, listAccess)
  assert.equal(knownEmpty.status, 'ok')
  assert.deepEqual(knownEmpty.relations, { artifacts: 'known-empty', attempts: 'known-empty', externalPublications: 'known-empty' })
  assert.deepEqual(knownEmpty.artifacts, [])
  const unavailable = model.parsePublication(publicationReceipt({ plans: [], relations: { artifacts: 'unavailable', attempts: 'unavailable', externalPublications: 'unavailable' }, artifacts: undefined, attempts: undefined, externalPublications: undefined }), request, listAccess)
  assert.equal(unavailable.status, 'ok')
  assert.deepEqual(unavailable.relations, { artifacts: 'unavailable', attempts: 'unavailable', externalPublications: 'unavailable' })
  assert.equal(unavailable.artifacts, undefined)
  const restricted = model.parsePublication(publicationReceipt({ plans: [], relations: { artifacts: 'restricted', attempts: 'restricted', externalPublications: 'restricted' }, artifacts: undefined, attempts: undefined, externalPublications: undefined }), request, listAccess)
  assert.equal(restricted.status, 'ok')
  assert.deepEqual(restricted.relations, { artifacts: 'restricted', attempts: 'restricted', externalPublications: 'restricted' })
  assert.equal(restricted.attempts, undefined)
})

test('frontend-pure.parse-external-observations-retains-scoped-unbound-references', () => {
  const parsed = model.parseExternalObservations(externalReceipt(), externalRequest)
  assert.equal(parsed.status, 'ok')
  assert.deepEqual(parsed.observations[0].externalReferences, { provider: 'neutral-provider', instance: 'instance1', account: 'account1', post: 'post1' })
  assert.equal(parsed.observations[0].displayStatus, 'unknown')
  assert.equal(parsed.observations[0].coreBinding.status, 'PENDING_CORE_CONTRACT')
  assert.doesNotMatch(JSON.stringify(parsed), /projectId|planId|attemptId|publishedAt|rawStatus/)
})

test('frontend-pure.parse-external-observations-rejects-binding-and-account-mismatches', () => {
  assert.equal(model.parseExternalObservations(externalReceipt(), { ...externalRequest, binding: { ...externalRequest.binding, ownerId: 'other-owner' } }).status, 'invalid')
  assert.equal(model.parseExternalObservations(externalReceipt(), { ...externalRequest, binding: { ...externalRequest.binding, scope: { ...scope, sessionId: 'other-session' } } }).status, 'invalid')
  const raw = externalReceipt()
  const mismatched = [{ ...raw.observations[0], externalReferences: { ...raw.observations[0].externalReferences, account: 'other-account' } }]
  assert.equal(model.parseExternalObservations(externalReceipt({ observations: mismatched }), externalRequest).status, 'invalid')
  assert.equal(model.parseExternalObservations(externalReceipt({ observations: [raw.observations[0], raw.observations[0]] }), externalRequest).status, 'invalid')
  assert.equal(model.parseExternalObservations(externalReceipt({ observations: [{ ...raw.observations[0], rawStatus: 'PRIVATE_PROVIDER_VALUE' }] }), externalRequest).status, 'invalid')
})

test('frontend-pure.calendar-and-filter-behavior-is-retained', () => {
  assert.equal(model.monthDays('2024-02').length, 29)
  assert.equal(model.monthDays('2100-02').length, 28)
  assert.equal(model.shiftMonth('2024-12', 1), '2025-01')
  assert.equal(model.calendarDay('2024-03-01T00:30:00Z', 'America/Los_Angeles'), '2024-02-29')
  assert.equal(model.calendarDay('2024-03-10', 'UTC'), null)
  const parsed = model.parsePublication(publicationReceipt(), request, listAccess)
  assert.equal(parsed.status, 'ok')
  assert.deepEqual(model.filterPlans(parsed, { query: '', account: '', status: 'unknown', order: 'asc' }).map(plan => plan.id), ['future-plan', 'queued-raw-plan'])
  assert.deepEqual(model.filterPlans(parsed, { query: '', account: 'account1', status: 'scheduled', order: 'desc' }).map(plan => plan.id), ['scheduled-plan'])
})

const failures = results.filter(result => result.status === 'failed').length
const report = {
  schema: 'v11-review-correction-frontend-pure-model-v1',
  execution: 'synchronous-node-no-vite-no-vitest-no-server-no-event-loop-socket',
  loader: { typescript: ts.version, transpileModule: true, format: 'CommonJS', boundedSources: [modelPath, typesPath], zod: zodPath },
  testedSourceHashes: { [modelPath]: sourceHash(modelPath), [typesPath]: sourceHash(typesPath) },
  counts: { total: results.length, passed: results.length - failures, failures, errors: 0, skipped: 0 },
  tests: results,
  claimsNotMade: ['Vite/Vitest equivalence', 'DOM/lifecycle equivalence', 'HTTP behavior', 'live provider data'],
}
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`)
if (failures) process.exitCode = 1
