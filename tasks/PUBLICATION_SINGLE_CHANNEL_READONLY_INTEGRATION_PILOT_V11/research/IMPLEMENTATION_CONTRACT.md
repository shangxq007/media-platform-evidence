# V11 implementation contract — early implementation handoff

Classification: STATIC_CONTRACT_REVIEW. Retrieved 2026-09-09 UTC. No live integration performed. Finalized after pinned-source review; machine authority: `endpoint-allowlist.json`, `v10-field-mapping.json`, and `deployment-pin.json`.

## Final pinned-source findings — read before implementing
Candidate app v2.23.0 is pinned to `1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9`; no live instance version established. Critical public GET `/posts` behavior: recurring records are expanded from original publishDate through endDate, ignore startDate, and repeat the original post ID. No page/cursor/limit applies to this public route. For this pilot, exclude rows with non-null intervalInDays or actualDate, mark partial with omission diagnostics, and reject remaining duplicate IDs; never invent occurrence or attempt IDs.[16]
Pinned selector includes releaseId/group/intervalInDays/creationMethod/tags and recurring actualDate, but does NOT include settings although current docs advertise settings. Do not require settings, access private getPostsList, or infer copy versions from group.[5][16]
Recommend status map QUEUE→scheduled, PUBLISHED→published, ERROR→failed, DRAFT→draft. Only QUEUE maps validated publishDate to scheduledAt. PUBLISHED/ERROR timeField=unknown, DRAFT=unscheduled; publishedAt remains absent. These are local projection recommendations, not newly claimed Postiz fields.
Only startDate/endDate enabled as pilot post query keys. Keep optional customer/group filters disabled: they are not account filters; pinned customer spread also overwrites the integration deletedAt/org filter (post organization restriction remains).[16]
Pinned guard throttles only POST paths including /public/v1/posts; read quotas remain deployment-specific, not 30/90 proven requests per hour. Continue handling 429 defensively.[19]

## Non-negotiable transport boundary
Only GET `{approvedPublicApiBase}/integrations` and GET `{approvedPublicApiBase}/posts?startDate=...&endDate=...` may be enabled. Default deny every other endpoint, including GET OAuth/connect routes. No sends, uploads, connections, OAuth initiation, account creation, DB/private API, deployment, or credential acquisition.

Use literal `Authorization: <existing-api-key>` (no Bearer prefix); OAuth docs likewise demonstrate raw pos_ tokens, despite token_type=bearer. Do not obtain tokens in this pilot.[1][2]
Cloud public base is `https://api.postiz.com/public/v1`; self-host docs list `https://{your-domain}/api/public/v1`. Base must be explicit approved configuration, not auto-probed.[4][5]

## Response contracts currently verified in official docs
- Accounts are integrations: GET `/integrations` returns an array, optional query `group` (customer ID). No account-id filter or pagination advertised. Fields id/name/identifier/picture/disabled/profile/customer.[4]
- Posts: GET `/posts` returns `{posts: [...]}`. Required startDate/endDate UTC ISO; optional customer. No integration filter or pagination advertised. Fields id/content/settings/publishDate/releaseURL/state/integration:{id,providerIdentifier,name,picture}. States QUEUE/PUBLISHED/ERROR/DRAFT.[5]
- Single-channel projection MUST filter posts by exact `integration.id` at server-side adapter boundary and expose only the preauthorized matching integration. The upstream read can return organization-wide data; filtering is not a provider-side authorization scope. If upstream organization-wide read is unauthorized, block pilot.
- Do not send V10 `limit:200` as upstream query. It is local envelope/schema policy, not Postiz pagination. Preserve bounded window semantics; fail invalid malformed data, never turn fetch failures into empty-success.

## V10 mapping safety
Read authority: sibling V10 `validation-02/snapshot/frontend/src/product/publication/{types.ts,model.ts}`. Map integration id/name/identifier → account id/name/platform. Post id/integration.id/state → plan id/accountId/status (see finalized status map above). `projectId` requires explicit local channel-to-project binding; provider does not prove a project relationship.
No attempt IDs, artifact relationships, copy versions or attempt-linked external publications are established by these list responses. Keep `artifactIds`, `artifacts`, `attempts`, `externalPublications` empty; omit copyVersion. Do not infer external ID from releaseURL or create an attempt from post state. PUBLISHED does not prove publishDate is actual publication time: leave publishedAt absent pending stronger evidence.
V10 externalPublications requires a real attemptId and referential integrity; releaseURL cannot satisfy it. V10 origin `isolated-verification` and test-only access keys are historical frontend proposal, not production authorization proof.

## Documentation discrepancy
Overview says 90 requests/hour (100 cloud) applies only to create post; endpoint embedded OpenAPI description says 30/hour generally. Do not claim a read quota resolved yet.[1][4][5]

## Sources

[1] https://docs.postiz.com/public-api/introduction.md — introduction.md
[2] https://docs.postiz.com/public-api/oauth.md — oauth.md
[4] https://docs.postiz.com/public-api/integrations/list.md — integrations-list.md
[5] https://docs.postiz.com/public-api/posts/list.md — posts-list.md
[16] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts — upstream/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts
[19] https://raw.githubusercontent.com/gitroomhq/postiz-app/1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9/libraries/nestjs-libraries/src/throttler/throttler.provider.ts — upstream/libraries/nestjs-libraries/src/throttler/throttler.provider.ts
