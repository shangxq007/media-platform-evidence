# Official contract review — V11

**Decision: static contract recovered; narrowly scoped adapter implementation can proceed against this documented candidate. Live integration acceptance remains BLOCKED pending approved instance, existing credential, exact channel binding, and read authorization.** No live Postiz API, user account, provider connection, upload, send, database, private API, deployment, product write, or Skill/Memory change was performed.

## Evidence and authority

Review retrieval date: **2026-09-09 UTC**. `source-manifest.json` records individual retrieval timestamps, requested/final URLs, HTTP status and content SHA-256. Full official pages/source files are under `sources/`; `source-excerpts.json` preserves verbatim line-ranged quotations. Required introduction/OAuth/Docker Compose URLs returned HTTP 200; Markdown and original HTML were retained. Introduction Markdown left reusable base-URL snippets unexpanded; endpoint OpenAPI server declarations and pinned Nginx source independently establish the paths.[1][4][28]

Official release API returned **v2.23.0**, published **2026-08-04T06:53:15Z**. The actual tag reference points directly to commit **`1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9`**, not merely `target_commitish: main`. This is the reviewed candidate, **not any live instance version**.[6][8]

Official installation docs delegate compose to `gitroomhq/postiz-docker-compose`. Its retrieved main commit is **`dd4969e5e694cd009619a0d53cff14c21104580b`**, commit time **2026-07-30T21:56:16Z**. The compose and both dynamicconfig files were downloaded from commit-fixed raw URLs, not floating main links.[3][9][21]

### Implementation inputs

| File | Role |
|---|---|
| `IMPLEMENTATION_CONTRACT.md` | Early handoff, now amended with final pinned-source hazards |
| `endpoint-allowlist.json` | Exact semantic GET allowlist, query/response/rate/error/completeness/time policies |
| `v10-field-mapping.json` | Field-by-field recommendation, including unavailable fields and local authority boundaries |
| `deployment-pin.json` | Fixed compose/source release and image evidence; not deployment approval |
| `deployment-images.json` | Every compose service image, observed immutable manifest digest and platforms |
| `sources/deployment/` | Unmodified official compose, README and mounted dynamicconfig source |
| `sources/v10/` and `v10-source-manifest.json` | Exact copied read-only V10 validation-02 snapshot type/model authority |
| `source-manifest.json`, `source-excerpts.json`, `citations.json` | Dated retrieval and citation evidence |

## 1. Semantically read-only allowlist

Only these two routes are admissible:

| Operation | Method and public-relative path | Pilot query keys | Root |
|---|---|---|---|
| List accounts/channels | `GET /integrations` | none | JSON array |
| List posts | `GET /posts` | required `startDate`, `endDate` | object with `posts` array |

Public controller delegates account listing to organization-scoped integration findMany and posts to the read-only getPosts repository method. These perform no post/channel mutation or provider OAuth initiation; ordinary request metrics and authentication bookkeeping are not promises of zero infrastructure side effects.[13][15][17]

Documentation supports optional `group` for integrations and `customer` for posts, but both are customer/group filters, **not channel IDs**. Disable them in this pilot; neither route has a documented account/integration-ID query filter. No `/accounts` route is invented.[4][5]

All other routes default-deny, even if GET. Particularly, **GET `/social/:integration` is not safe**: the pinned controller generates OAuth authorization material and writes state to Redis. Analytics, settings/tools, missing-content and notifications are not needed and remain denied; missing-content documentation was read solely to clarify the releaseId sentinel.[13][41]

### Single-channel authorization limitation

A list request can retrieve the credential's **organization-wide data** before local filtering. The pinned middleware grants organization context for either key or existing OAuth token; it does not implement a read-only/single-channel scope for these list routes.[14]

Therefore, require an existing isolated organization holding only the authorized channel, or explicit authorization for the broader upstream read. **Do not claim post-fetch filtering makes an organization-wide credential single-channel scoped.** The adapter must project only the exact configured integration ID before browser exposure, raw logging, or content handling. Never choose the first account or match by display name. Missing selected channel is unavailable/restricted, not permission to choose another channel.

## 2. Auth, base paths and errors

`Authorization` contains the **raw key**, or an already authorized `pos_` token. Do **not** add `Bearer `. OAuth docs return `token_type: bearer` but their request examples use the raw token; the pinned middleware tests `auth.startsWith('pos_')` and otherwise looks up the whole string as an API key. New OAuth initiation/exchange and API-key acquisition are out of scope.[1][2][14]

- Cloud: `https://api.postiz.com/public/v1`.[4]
- Self-hosted reverse proxy: `https://<approved-domain>/api/public/v1`.[4]
- Official compose example: `http://localhost:4007/api/public/v1`; Nginx listens on container port 5000 and strips `/api/` before the backend route `/public/v1`.[21][28]

Use an explicitly approved base URL; do not probe path variations, send cookies, use browser-held credentials, follow redirects with authorization, or accept user-controlled origin/path/query keys. All local HTTP exceptions must be restricted to explicitly approved isolated loopback preparation.

Pinned 401 bodies use `msg`: `No API Key found`, `Invalid API key`, `Invalid OAuth token`, or `No subscription found`; middleware exceptions may become forbidden. A 401 does not uniquely prove bad credentials.[14] Treat 400 as request/contract failure, 401/403 restricted, list-route 404 unavailable/contract mismatch, malformed 200 invalid, and 5xx/network failures as genuine errors with bounded backoff. Never import the docs' DELETE-already-absent interpretation into GET list handling.[1]

Overview rate text says 90/hour (100 cloud) applies only to create-post; embedded OpenAPI says generic 30/hour. Pinned throttler only calls its superclass for POST URLs containing `/public/v1/posts`; official compose sets `API_LIMIT:30`. Thus the current documentation conflicts, while this candidate's guard does not throttle these GETs. **No universal live read allowance or unlimited-read claim is established.** Handle proxy 429 and valid Retry-After defensively; response rate headers are not guaranteed.[1][19][21]

## 3. Account response

The public projection exposes id, name, identifier, picture, disabled, profile and optional customer `{id,name}`. The repository selects all nondeleted organization integrations, including disabled ones; no pagination, total, cursor, hasMore, ordering or snapshot revision is returned.[13][15]

Recommendation: map only exact valid id/name/identifier to V10 account id/name/platform. Treat disabled as an explicit adapter policy input (recommend restricted), not as authentication health. Do not read a missing `disabled` property as false or a disabled=false property as proof a provider token works. Unknown provider strings should remain strings unless the pilot explicitly authorizes a specific platform; the docs' varying provider counts are not a trustworthy enum-version authority.

## 4. Post response: important source/documentation differences

The public route invokes **getPosts**, not the nearby **getPostsList** method. The latter has page/limit/total/hasMore; those parameters and completion claims do **not** belong to this public contract.[13][16]

The pinned selector returns id/content/publishDate/releaseURL/releaseId/state/intervalInDays/group/creationMethod/tags/integration. Integration has id/providerIdentifier/name/picture. **Current docs advertise settings, but this release's selector omits settings.** Do not require or fabricate it. The selector also omits title, image, error, createdAt, updatedAt, actual publication timestamp, media/version and attempt relationships even where the internal data model contains such fields.[5][16]

### Date bounds, recurrence, completeness

For normal posts, publishDate bounds are inclusive `gte startDate` / `lte endDate`; root posts only (`parentPostId:null`), deleted posts excluded. The optional customer spread overwrites the integration deletedAt/organization filter object; post organization restriction remains. The pilot does not enable that optional filter.[16]

**Recurrence is hazardous:** `intervalInDays != null` bypasses the normal date predicate. Expansion begins at the original publishDate and continues through endDate, without respecting requested startDate. Expanded rows reuse the same original ID, change publishDate and add actualDate. A bounded endDate can still return historical repetitions from long before startDate; rows are not independently identified publication attempts.[16]

Pilot policy: exclude any row with non-null intervalInDays or actualDate, mark the snapshot partial and disclose omitted counts in trusted diagnostics. Reject duplicate IDs in remaining rows. Validate absolute date strings and apply the configured inclusive window again. If a consumer cannot represent partial results, block instead. Never deduplicate recurring instances into one arbitrary row, manufacture occurrence IDs, infer actual publishes, or use unseen private paging.

V10 supports at most 200 plans/accounts/artifacts and requires unique IDs/referential integrity. A local cap is not an upstream limit. Recommended overflow handling is deterministic local sorting and a visibly partial capped projection (or reject); never silent truncation or `complete`. Even a clean successful result is **bounded** to date window and selected nonrecurring roots; accounts/posts requests are not an atomic snapshot. Count returned, wrong-channel, recurrence-excluded, out-of-window and capped rows separately without exposing other-channel content.

## 5. V10 mapping recommendation

Authority is the sibling V10 **`validation-02/snapshot/frontend/src/product/publication/types.ts` and `model.ts`**, not prior research or a guessed backend. Full field inventory is in `v10-field-mapping.json`; hashes in `v10-source-manifest.json` preserve the exact local authority. The supplied frontend baseline `afc966ad4872e6dd65997281c75fe49e7aaed376` is task context, not claimed reverified Git identity of these snapshots.

| Target | Recommendation |
|---|---|
| account.id/name/platform | integration.id/name/identifier |
| plan.id/accountId | post.id / post.integration.id |
| plan.projectId | explicit authenticated local channel→project binding, not an upstream association |
| plan.status | QUEUE→scheduled; PUBLISHED→published; ERROR→failed; DRAFT→draft |
| plan.timeField/scheduledAt | QUEUE only: scheduledAt plus validated publishDate |
| PUBLISHED/ERROR time | unknown; publishedAt absent |
| DRAFT time | unscheduled; omit scheduledAt/publishedAt |
| title | absent; no title projection |
| summary | content only with explicit per-plan content access; otherwise omit |
| copyVersion | absent |
| artifactIds/artifacts | empty, meaning unavailable relationships, not proof of no media |
| attempts | empty; no attempt IDs, failure history or attemptedAt exposed |
| externalPublications | empty; no genuine attemptId relationship |
| snapshot version/fetchedAt | clearly local observation identifier/time, not provider revision/release time |
| scope/access/owner/requestId | trusted local authority and request echo, not derived from Postiz list success |

These are **local adapter recommendations**, not native Postiz fields. Unknown states/invalid IDs must fail closed or use a separately approved unknown-state model, never silently repaired. V10 content length max4000 and identifier syntax are local validation constraints; do not silently normalize malformed remote tokens to fit them. V10 test-only keys and `isolated-verification` origin must not be promoted into live authority by assertion.

`releaseId` is a source-proven extra field at this release, while `releaseURL` is documented. Null/empty/missing-sentinel release IDs remain unavailable. A release URL is not an external ID, an attempt, a verified live artifact, or an actual publish timestamp. Do not derive IDs by URL parsing, fetch URLs, embed previews, or synthesize V10 externalPublications: V10 requires a real attemptId and matching plan/account relationship, which the allowed response does not provide.[5][16][41]

## 6. Fixed deployment preparation inputs — not deployed

All **nine** official compose service images were read from public registry manifests and pinned with digest equality checked against the registry's Docker-Content-Digest. `deployment-images.json` stores per-platform descriptors and retrieval times. No Docker pull, container startup, configuration application or live health/version test ran.

Postiz candidate image:

```text
ghcr.io/gitroomhq/postiz-app:v2.23.0
ghcr.io/gitroomhq/postiz-app@sha256:785f97312f66a347fb96cdccc4ded5a33ced69a672c89a9adc8054e7d6a21dc5
```

The manifest contains linux/amd64 and linux/arm64. Official build workflow uses the Git tag as the image tag and builds architecture variants, then publishes a shared manifest. This establishes public tag resolution and the official build convention, **not a signed source-to-image attestation or proof of a running deployment's contents**.[27][30]

Other immutable image references cover Postgres 17-alpine, Redis 7.2, Spotlight latest, Elasticsearch 7.17.27, Temporal Postgres 16, auto-setup 1.28.1, admin-tools 1.28.1-tctl-1.18.4-cli-1.4.1, and UI 2.34.0. Exact digests are in the image manifest artifact, not inferred from tags.[21]

Keep the preserved official compose immutable as evidence. It contains upstream sample/default passwords and JWT configuration, fixed names/volumes/networks, and service exposure. Those are public example values, not acquired user credentials, and must never be used unchanged. Later separately authorized isolated preparation must choose fresh private secrets outside evidence, isolated resource names, approved loopback ports, pinned overrides and outbound controls. Registry digest pinning is neither vulnerability assessment nor runtime compatibility verification.

## 7. Remaining gates and limitations

- No existing credential/approved instance/channel ID was supplied to this static reviewer; none was searched for or created.
- Actual deployed version/schema/rate behavior remains unverified. Source candidate and mutable current docs are explicitly separate authorities.
- Organization-wide upstream reads need scope approval; local filtering alone is insufficient.
- Live data may reveal recurrence, schema divergence, disabled/deleted channel races or malformed dates; adapter must report bounded/partial/error rather than manufacture completeness.
- Actual attempt/artifact/copy-version relationships and real publication times remain absent. No mapping technique can recover evidence the allowed API does not expose.
- Registry inspection initially hit a local image-reference parser bug on a dotted tag (`redis:7.2`); parser fixed and the complete image pass rerun successfully. No substitute output was invented.
- Official required pages and pinned source retrievals were available. Search primary backend returned no results and its fallback returned the official release page; release/tag evidence comes from the directly retrieved GitHub API, not the search snippet.

## Static verification result

`validate_static.py` completed successfully: **145 checks**, covering **32 retrieved source files**, **9 compose service image manifests**, **52 mapping targets**, exact allowlisted route pairs, source/excerpt integrity, tag/compose pins and V10 snapshot equality. Results are in `verification.json`. Normal citation consistency verification passed for both reports. Strict citation mode additionally warns when a retrieved source is intentionally not cited in a particular draft; those unused-source warnings are preserved in `citation-verification.json` and are not evidence-hash or unknown-citation failures.

**Acceptance here is STATIC_CONTRACT_REVIEW only.** The supplied allowlist is sufficient to implement and test a fail-closed HTTP adapter, but this report does not certify a live read, readonly provider credential, content lineage, deployment, or a successful single-channel integration.

## Sources

[1] https://docs.postiz.com/public-api/introduction.md — introduction.md
[2] https://docs.postiz.com/public-api/oauth.md — oauth.md
[3] https://docs.postiz.com/self-host/installation/docker-compose.md — docker-compose.md
[4] https://docs.postiz.com/public-api/integrations/list.md — integrations-list.md
[5] https://docs.postiz.com/public-api/posts/list.md — posts-list.md
[6] https://api.github.com/repos/gitroomhq/postiz-app/releases/latest — releases.json
[8] https://api.github.com/repos/gitroomhq/postiz-app/git/ref/tags/v2.23.0 — app-tag.json
[9] https://api.github.com/repos/gitroomhq/postiz-docker-compose/commits/main — compose-head.json
[13] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/apps/backend/src/public-api/routes/v1/public.integrations.controller.ts — upstream/apps/backend/src/public-api/routes/v1/public.integrations.controller.ts
[14] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/apps/backend/src/services/auth/public.auth.middleware.ts — upstream/apps/backend/src/services/auth/public.auth.middleware.ts
[15] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/libraries/nestjs-libraries/src/database/prisma/integrations/integration.repository.ts — upstream/libraries/nestjs-libraries/src/database/prisma/integrations/integration.repository.ts
[16] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts — upstream/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts
[17] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/libraries/nestjs-libraries/src/database/prisma/posts/posts.service.ts — upstream/libraries/nestjs-libraries/src/database/prisma/posts/posts.service.ts
[19] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/libraries/nestjs-libraries/src/throttler/throttler.provider.ts — upstream/libraries/nestjs-libraries/src/throttler/throttler.provider.ts
[21] https://raw.githubusercontent.com/gitroomhq/postiz-docker-compose/dd4969e5e694cd009619a0d53cff14c21104580b/docker-compose.yaml — deployment/docker-compose.yaml
[27] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/.github/workflows/build-containers.yml — upstream/.github/workflows/build-containers.yml
[28] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/var/docker/nginx.conf — upstream/var/docker/nginx.conf
[30] https://ghcr.io/v2/gitroomhq/postiz-app/manifests/v2.23.0 — postiz public registry manifest
[41] https://docs.postiz.com/public-api/posts/missing-content.md — missing-content-doc-only.md
