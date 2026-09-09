# Platform contract ownership audit — V11 continuation gate

**Disposition: bounded corrections required before writer continuation; not final acceptance.**

The existing platform is neither contract-free nor already compliant with the proposed Publication workspace. Core social post/account identities, lifecycle enums, application reads and provider interfaces exist. The newer Project-scoped plan → attempt → external-publication graph, its authorized read envelope, stable cross-provider identity bindings and relation-availability semantics are **not established core contracts** in the inspected implementation. Preserve the useful V10 UX; do not turn either its verification types or the Postiz draft into platform authority by renaming fields.

## Scope and evidence boundary

- Repository: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`.
- Task root: `/home/user/Documents/workspace/audit-runs/PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11`.
- Actual HEAD: `f5e19cf53fd010eea2935dd29557e82a879e042c`; branch `agent/frontend-wave2-product-ux-v1`; pre-existing dirty/untracked product files remain untouched. Exact state is in `AUDIT_STATE.json`.
- Owner baseline token `afc966ad4872e6dd65997281c75fe49e7aaed376` is preserved literally. Local `git cat-file -t` cannot resolve it; no fetch attempted. Prior `writer/baseline-check.json` reports zero differences, but that historical claim is not independent baseline verification here. This audit is of actual working files, hashed in the map, not a claim to reconstruct the accepted tree. `full945` is supplied context, not a test result produced here.
- Loaded contract-first-architecture, provider-lifecycle-evaluation and extensible-platform-architecture skills. Repository root `AGENTS.md` applies; no narrower repository AGENTS was found. Owner read-only task restrictions govern. No Skill/Memory updates, product/backend/adapter edits, test execution, sockets, credentials, deployments, remote operations or EP19 operations were performed. Only the new audit directory is written.
- Source review covered actual social domain/application/persistence/provider definitions, related Project/Artifact authority, frontend query/access/Selection/router/filter dependencies, V10 test source, FB-GAP-014/planning and the external draft. Repository searches distinguished social publishing from unrelated workflow/artifact/Git “publication” names. Absence findings apply to the inspected definitions/schema and repository symbol searches; they are not an assertion that all platform APIs are absent.
- `PLATFORM_CONTRACT_MAP.json` is the machine map: exact source paths, SHA-256, line ranges, existing authority → frontend consumed contract → provider mapping, findings and dependencies. The source-key citations below resolve to its absolute-path source registry. The appendix repeats paths for standalone reading.

## Findings and minimal scope

### PC-01 — Platform identity boundary is not carried through the draft

`service:36–47` creates `SocialPost.id` with `Ids.newId("pst")`; `auth:34–48` creates `ConnectedPlatform.id` with `Ids.newId("cn")`. Core records separately hold `platformPostId` and `platformUserId` (`post:6–23`, `account:5–14`). This is real existing authority to preserve, not a reason to create a new frontend ID standard.

By contrast, `pilot:143–168` projects integration.id directly into channel.id and post.id directly into record.id, and uses the former as accountId. Historical research explicitly recommends copying those into V10 account/plan IDs (`research:24–27`; `oldMap`). V10 consumes those IDs as joins, filter values and Selection identities (`model:37–43,93–102`, `workspace:59–61`). The draft is not yet connected to V10, so this is a blocked proposed ownership crossing, not evidence of a live production collision.

**Minimum correction:** an approved platform-side binding must resolve existing platform identity separately from a scoped provider reference (provider/instance and external account/post context). A prefix or hash of the provider ID alone does not demonstrate platform ownership or survival of provider replacement. No browser minting, name matching or guessed Project assignment. If no binding exists, treat the item as an unresolved external observation, not a platform publication plan; its consumer representation is pending agreement.

### PC-02/03 — Real relationships exist elsewhere; the publication graph remains a proposal

`project:5–15` is a core Project record. `artifact:10–28` declares immutable Artifact identity; `artifactQuery:8–14`, `artifactScope:5–16`, `artifactDb:30–55` provide tenant/Project/producing-render-job scoped discovery. Do not redefine Artifact IDs or substitute media URLs. Artifact `schemaVersion` is not publication copyVersion.

`SocialPost` and `social_post` lack projectId, connected-account ID, Artifact refs, copy-version refs, attempt IDs or a separate publication outcome collection (`post:6–23`, `schema:2753–2807`). Service account selection is tenant/user/platform, not a persisted post→account edge (`service:70–79`). Provider selection by PlatformType is not a demonstrated multiple-provider-for-one-platform registry. These are gaps, not authority to rewrite the backend in V11.

V10 requires relation arrays and validates explicit links (`types:28–44`, `model:37–43`). Good: no time/name/order joins. Missing: availability of each relation. Required empty arrays, filtered artifactIds and blank detail sections cannot distinguish known empty, unsupported, not supplied and restricted (`model:45–52`, `workspace:181–184`). Research recommends empty arrays for unavailable facts. The draft's `relationshipStatus='not-supplied'` is an improvement, but lives in a different envelope and is not consumed by the V10 parser (`pilot:164`).

**Minimum correction:** keep the explicit graph where actually supplied. Agree a platform-owned relation-availability/completeness projection before the bridge; do not fill required arrays with invented “known empty” truth. Missing backend relationship contracts remain **PENDING_CORE_CONTRACT**, not an invented canonical TypeScript graph. Restriction messaging must not disclose hidden object existence. No attempts/outcomes are synthesized to satisfy referential integrity.

### PC-04 — Accepted request, executed attempt and actual external result are not equivalent

Core create returns DRAFT; schedule stores SCHEDULED; publishNow calls `PlatformAdapter.publish` and maps boolean success to PUBLISHED with local `Instant.now()` (`service:36–98`). `PublishResult` has a boolean, external ID/URL and error strings, not separate accepted/attempted/confirmed evidence (`result:3–9`). `retryCount` is not an attempt history. Scheduler exceptions can set FAILED without an external outcome (`scheduler:27–38`). The concrete Twitter adapter still manufactures a stub post ID and successful result (`twitter:26–37`); a non-Stub class name or `@Component` is not real publication proof.

V10's separate attempt/outcome types are directionally useful but proposal-only. A successful GET receipt (`pilot:171`), observationId, an upstream QUEUE, PUBLISHED/ERROR state or supplied releaseId does not prove a platform command was accepted, identify an attempt or verify an actual external outcome. The draft correctly omits publishedAt for PUBLISHED/ERROR and does not fabricate attempts.

**Minimum correction:** preserve that restraint; only attach explicitly sourced result/attempt facts. Require the platform owner to settle event/result semantics before stronger claims. Read error must never become publication failure; read success must never become send success. No scheduler or send changes in this continuation audit.

### PC-05 — Raw provider statuses cannot own generic product semantics

Core `PostStatus` contains DRAFT, SCHEDULED, PUBLISHING, PUBLISHED, FAILED and CANCELLED (`status:3–10`). Legacy frontend `SocialPost` omits PUBLISHING (`legacyApi:11–23`), showing that merely reusing its type is not exact contract recovery. Core response also exposes errorMessage (`dto:12–21`); do not blindly forward it to a generic consumer.

V10 accepts arbitrary status strings and renders/filters them literally; tests deliberately preserve `alien-state` (`model:10–16,93–102`, `workspace:129–140`, `modelTests:35–60`). This follows the old proposal, but is insufficient for the current Owner requirement if provider values become generic product states. Draft maps QUEUE/PUBLISHED/ERROR/DRAFT to locally chosen lower-case states and rejects any new state with UNKNOWN_STATE (`pilot:162–164`). That mapping is not an accepted platform status contract. Unknown provider state currently invalidates the whole observation instead of representing an explicit unmapped state.

**Minimum correction:** platform owner approves generic lifecycle/read/error vocabulary and unknown/capability semantics; adapter translates to that vocabulary. Preserve safe, explicitly diagnostic raw status/provenance separately where authorized, never as the generic status filter or control-flow authority. Unsupported/missing capability differs from denied access, absent data and a failed publication. Do not expand core enums or claim a new frontend enum is canonical in this task.

### PC-06/07 — Application reads exist, but not this agreed Project Publication API

FB-GAP-014's broad “No actual publication/social query or access contract” wording (`gap:484`) is misleading if read repository-wide. `SocialPublishController` exposes `/api/social/platforms`, `/api/social/posts` and `/api/social/posts/{id}`; existing `frontend/src/api/publish.ts` calls those reads (`controller:47–58,162–191`, `legacyApi:37–69`). Their existence does not establish deployment, authorization sufficiency, or the coherent new graph. Read details are tenant-filtered at repository level, while user/Project relationship verification is not established by that code (`repo:45–56`, `service:132–143`). No runtime/security certification is made.

`platformClient` actually exposes only workspace home and a deliberately fail-closed access catalog (`platformClient:50–108`). `projectContext:24–29` says Workspace→Project is not verified. V10 direct injected read uses `PublicationRequest` and echoed identity/query/request ID; ordinary route has no source (`types:15–24`, `workspace:84–101`, `pages:138–143`). Pilot instead defines `postiz-owner-local-v1`, binding/access/query/channel/records and provider-specific headers (`pilot:18–21,82–87,179–192`); its errors do not have the V10 echo envelope. A new private component branch that directly understands this protocol would make the provider own the frontend application API.

Owner-local single-user list/content booleans are not the platform's five-factor EffectiveAccess. V10 fixture `source='SERVER'` grants are explicitly synthetic (`fixture:1–20`, `platformClient:81–86`); do not manufacture them from a successful provider GET. Artifact discovery is not access permission (`artifactService:48–77`). Keep generic safe read failures; do not branch generic UX on provider HTTP/error identifiers.

**Minimum correction:** correct the ledger's claim narrowly, under subsequent authorized writer work: legacy social reads exist; accepted Project Publication read/access/relationship contract remains pending. Approve a bounded platform-owned application boundary, then adapt external observations behind it. Do not silently connect the ordinary route to legacy social endpoints, relabel live data “isolated-verification”, or replace the shared platform client/access/Selection architecture. If owner-local pilot access is retained, label its narrower scope rather than calling it production authorization.

## Preserve the useful implementation

Do not wholesale-rewrite `PublicationWorkspace`:

- Keep list/calendar/day agenda sharing filters and snapshot; account filtering must remain by platform-owned account identity, not display name or platform type.
- Keep strict offset instants, Gregorian month construction, stable time/ID ordering, explicit selected calendar field, unscheduled/indeterminate separation and display-only timezone (`model:54–102`).
- Keep distinct scheduled/published/attempted/fetched times. The pilot already avoids turning publishDate into actual publication time. Provider version, observation version and content version must stay distinct; pilot `version='v2.23.0'` is not a snapshot revision.
- Retain bounded/partial disclosure and honest partial-empty results; query errors are not empty success. Upstream start/end filtering is not UI month completeness. Pilot end comparison is inclusive, while UI month interval is half-open; document/translate that boundary rather than silently equating them.
- Keep shared Selection, abort/generation guards, OIDC retirement and fresh-owner requirement, stale callback rejection, no automatic detail revival, refresh/view context retention and dialog focus (`workspace:23–108`, `selection:6–51`). The mounted route test checks renewal/retirement (`routeTests:650–684`). These are inspected test intentions, not rerun results.
- Keep permitted metadata detail sections, inert Artifact references, no external URLs/media playback/write buttons and separate content/Artifact trimming. Only change status/identity/relationship presentation where needed to make the contract truthful.

## Fixture assessment and lightweight second-adapter proof proposal

V10 `testing.ts` is hand-authored neutral synthetic graph data with same-platform distinct accounts, multiple attempts, explicit outcome refs, arbitrary unknown status and protected URL sentinel. It is **not merely a renamed Postiz response**. It is also **not proof of a platform-native accepted backend contract**: no imported/generated backend schema establishes its new graph or statuses. Its existing UI regression value should be preserved.

Conversely `adapter/test_pilot.py:17–27` is deliberately Postiz-shaped data (`integration`, `state`, `publishDate`, `releaseId`) with synthetic names; changing labels does not prove replaceability. Only one scenario is drafted (`pilotTests:58–68`), and historical handoff reports socket setup failure before behavioral assertions (`handoff:5–18`). No test was retried here, and no alternative mock is claimed to cure that failed HTTP verification.

**Propose, do not implement/run here:** a tiny in-memory second adapter with a deliberately different input layout (e.g. delivery jobs plus separately keyed receipt events; numeric external refs; no Postiz integration/state/publishDate keys). Use a platform-controlled, explicitly synthetic identity/binding table and event graph approved against the pending decisions. Both adapters must feed the same platform-owned read projection and unchanged consumer. Exercise only after authorization:

1. Provider external IDs deliberately collide across provider/instance/account scopes; platform account/intent IDs remain stable and distinct, including after provider replacement. Names and input order change without affecting joins or Selection identity.
2. Accepted-only, an explicit attempt without result, and an explicit confirmed outcome stay distinguishable. No invented attempt for QUEUE/ERROR or a successful read; actual time remains absent without evidence.
3. Second adapter lacks Artifact/attempt capability in one case; another returns an authoritative empty relation; a denied relation remains non-disclosing. Consumer distinguishes these without provider-specific branches.
4. A new raw status and a raw provider error containing a synthetic sentinel produce safe unknown/read-error behavior, never generic failed/published state or leaked raw message. Retained raw diagnostics cannot drive generic filters.
5. Same platform snapshot yields the same list/month/day/filter/timezone/detail behavior regardless of adapter; switching source retires pending reads and old callbacks. No new route/shell/Selection or calendar implementation is justified.

This would be **synthetic contract/replaceability evidence only**, not HTTP transport validation, backend implementation, real accounts, actual publication or final acceptance. No real connection, socket, credential or new service is needed for the proposed lightweight proof. Keep historical HTTP blocker separate.

## Writer gate and bounded next scope

Before implementation, Owner/platform contract authority must decide: (a) ID/binding ownership; (b) which existing social record, if any, is the publication intent authority; (c) scoped application projection and access authority; (d) generic status/read/attempt/result/unknown semantics; (e) per-relation availability/completeness. Missing decisions stay pending. Do not invent canonical intent/attempt entities, endpoint names, permission keys or registry persistence as a frontend fix.

Once approved, the minimum writer scope is the isolated adapter projection/binding and validation, publication types/parser boundary, status/relationship-specific rendering and focused fixtures/tests, plus existing FB-GAP/planning corrections. Keep the current route, shell, calendar functions, filters, timezone handling and detail lifecycle. Backend/schema/shared domain/EP19 changes, sends/connections/credentials and wholesale provider framework work remain outside scope. If an approved projection cannot be expressed without a new core contract, return that exact gap instead of wiring provider data directly into the component.

This report gates the writer; it neither accepts the draft nor authorizes execution. No product acceptance criteria or test counts have been claimed satisfied by this static audit.

## Exact source-path appendix
- `post` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/domain/SocialPost.java`
- `account` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/domain/ConnectedPlatform.java`
- `status` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/domain/PostStatus.java`
- `service` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/app/SocialPublishService.java`
- `auth` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/app/PlatformAuthService.java`
- `scheduler` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/app/PostSchedulerService.java`
- `repo` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/infrastructure/persistence/SocialPostRepository.java`
- `spi` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/infrastructure/platform/PlatformAdapter.java`
- `result` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/infrastructure/platform/PublishResult.java`
- `twitter` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/infrastructure/platform/TwitterPlatformAdapter.java`
- `controller` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/api/SocialPublishController.java`
- `dto` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/social-publish-module/src/main/java/com/example/platform/social/api/dto/PublishPostResponse.java`
- `schema` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/platform-app/src/main/resources/db/migration/V1__initial_schema.sql`
- `artifact` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/artifact-module/src/main/java/com/example/platform/artifact/domain/Artifact.java`
- `artifactQuery` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/artifact-module/src/main/java/com/example/platform/artifact/app/ArtifactApplicationQuery.java`
- `artifactService` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/artifact-module/src/main/java/com/example/platform/artifact/app/ArtifactApplicationService.java`
- `artifactScope` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/artifact-module/src/main/java/com/example/platform/artifact/app/ArtifactScope.java`
- `artifactDb` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/artifact-module/src/main/java/com/example/platform/artifact/infrastructure/JooqArtifactApplicationQuery.java`
- `project` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/identity-access-module/src/main/java/com/example/platform/identity/domain/Project.java`
- `types` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/product/publication/types.ts`
- `model` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/product/publication/model.ts`
- `workspace` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/product/publication/PublicationWorkspace.tsx`
- `fixture` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/product/publication/testing.ts`
- `modelTests` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/product/publication/model.test.ts`
- `workspaceTests` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/product/publication/PublicationWorkspace.test.tsx`
- `platformClient` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/foundation/platformClient.ts`
- `access` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/foundation/effectiveAccess.tsx`
- `projectContext` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/foundation/projectContext.tsx`
- `selection` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/interaction/SelectionContext.tsx`
- `routes` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/app/routeTree.tsx`
- `routeTests` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/app/routeTree.test.tsx`
- `pages` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/surfaces/FoundationPages.tsx`
- `legacyApi` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/api/publish.ts`
- `gap` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md`
- `planning` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/docs/architecture/governance/frontend-product-information-architecture-v1.md`
- `enablement` → `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv`
- `pilot` → `/home/user/Documents/workspace/audit-runs/PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11/adapter/pilot.py`
- `pilotTests` → `/home/user/Documents/workspace/audit-runs/PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11/adapter/test_pilot.py`
- `research` → `/home/user/Documents/workspace/audit-runs/PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11/research/IMPLEMENTATION_CONTRACT.md`
- `oldMap` → `/home/user/Documents/workspace/audit-runs/PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11/research/v10-field-mapping.json`
- `handoff` → `/home/user/Documents/workspace/audit-runs/PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11/writer/WRITER_HANDOFF.md`
