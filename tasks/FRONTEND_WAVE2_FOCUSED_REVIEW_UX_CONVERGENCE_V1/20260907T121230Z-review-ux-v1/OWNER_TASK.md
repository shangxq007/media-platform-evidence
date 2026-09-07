TASK=FRONTEND_WAVE2_FOCUSED_REVIEW_UX_CONVERGENCE_V1
LANE=FRONTEND
MODE=BOUNDED_LOCAL_UI_IMPLEMENTATION_AND_VALIDATION
SECONDARY_SCOPE=READ_ONLY_NOTIFICATION_CAPABILITY_INVENTORY

Proceed with the existing planned focused Review UX work, using existing query gateways. This is explicit implementation authorization within the scope below. Do not invent a new Slice1D designation.

1. Adopted baseline and decisions

The Owner adopts the independent acceptance of:
FRONTEND_WAVE2_COMMAND_DISCOVERY_AND_ACCESSIBILITY_CONVERGENCE_V1

INDEPENDENT_REVIEW=PASS_BOUNDED_COMMAND_DISCOVERY_AND_ACCESSIBILITY
BASELINE_IMPLEMENTATION_TREE=43038f740997d0ebb3a8c67f293da7edab563fdb
ACCEPTED_EVIDENCE_COMMIT=67e97ee7082956c350a93aba0370990853e93795
ACCEPTED_PUBLIC_MANIFEST_SHA256=6dd56fba448a9a8bb45816af197f5ee1eb04e4255475390687f8d7ab4455353f

Accepted evidence:
https://github.com/shangxq007/media-platform-evidence/blob/67e97ee7082956c350a93aba0370990853e93795/tasks/FRONTEND_WAVE2_COMMAND_DISCOVERY_AND_ACCESSIBILITY_CONVERGENCE_V1/20260907T103036Z-command-palette-v1/INDEX.md

The prior Canvas correction, recorded Chromium pagehide acceptance, and validator completeness correction remain accepted. Do not reopen or rerun those tasks.

H4 Proposal A and tracked-dist Proposal A remain adopted:

* Preserve the historical H4 ledger.
* Complete current-scope append-forward reconciliation before the applicable product freeze gate.
* Retain the tracked-artifact policy.
* Use external build output for independent frontend validation.
* Leave backend static generation, copying, cleanup and packaging to a separately authorized integration/release task.

This bounded local Review UI implementation may proceed before formal Slice1C acceptance-ledger integration. Do not request the branch, Proposal A, or this development sequence confirmation again.

Overall Slice1C closure and product freeze/publication are not granted by this task.

2. Independent frontend lane

The exact frontend branch ref is:
refs/heads/agent/frontend-wave2-product-ux-v1

It contains no spaces.

Frontend and backend are independent concurrent lanes. Do not modify the backend lane or require its HEAD, refs, working tree or runtime to remain unchanged.

Recover the registered frontend worktree and its existing dirty implementation. Verify the accepted implementation identity using the established external identity method. Preserve all pre-existing changes; do not reset, clean, stash, restore, stage or overwrite them.

Do not create a product commit, freeze, merge, push or publication.

3. Recover current implementation and finalize the bounded worklist

Read:

* 03-大模型上下文-精简版.md.
* Applicable repository instructions.
* docs/architecture/governance/frontend-product-information-architecture-v1.md.
* frontend/governance/agent-shell-convergence/DESIGN.md.
* frontend/governance/pre-freeze-closure-v1/DESIGN.md.
* The existing Wave2 plan that places focused Review UX after command discovery/accessibility convergence.
* Current ReviewWorkspace, SemanticDiff, their tests, and the existing TimelineQueryGateway integration.

The public backend baseline is useful for reference, but it is not the authority for the dirty frontend implementation. Inspect actual current frontend files before editing.

Record a short acceptance checklist and exact changed-path allowlist, then implement. Do not turn this into a separate open-ended design recovery task.

Primary permitted existing paths:

* frontend/src/product/review/ReviewWorkspace.tsx
* frontend/src/product/review/ReviewWorkspace.test.tsx
* frontend/src/product/timeline/SemanticDiff.tsx
* frontend/src/product/timeline/SemanticDiff.test.tsx
* frontend/src/localization/catalogs.ts
* frontend/src/localization/source-manifest.json
* frontend/src/styles/foundation.css

Resolve existing paths before using them. Limit SemanticDiff and shared CSS changes to what the Review UX needs, and account for other consumers.

Read shared shell, Selection and gateway code as needed. Changes to backend code, gateway contracts, global routing, shared Selec tion lifetime machinery, or new production modules are outside this implementation scope. If a concrete dependency requires them, complete the unaffected authorized work and report the exact additional scope needed.

4. User-visible Review outcome

The user must be able to:

* Understand the current Workspace/Project and the purpose of Review.
* Identify two explicit server-projected revisions and their comparison direction.
* Distinguish the requested revision pair from any previously displayed result.
* Start a read-only comparison through the existing gateway.
* Read available summary and entity changes, and use existing presentation filters.
* Understand what to do when history is empty, only one revision exists, a selection is invalid, comparison is unsupported, access is denied, or a request fails.

Improve existing behavior rather than recreating it.

Use available revision metadata to improve readability. Keep exact revision identities inspectable, but do not make raw IDs or implementation details the dominant creator-facing explanation.

Do not invent missing revision metadata or compute canonical semantic differences in the browser.

Do not automatically compare arbitrary revisions or silently change an explicit ordered pair.

5. State and asynchronous correctness

Implement and verify distinct presentation states as applicable:

* History loading.
* Empty or insufficient history.
* Ready to select.
* Invalid or incomplete pair.
* Comparison loading.
* Comparison success.
* Supported comparison with no changes.
* Unsupported summary or unavailable comparison.
* Access denied, network failure, and other gateway failures.

Use the existing GatewayResult and retryability contract. Do not fabricate successful or empty results from failures.

A changed revision pair, a new request, a changed project/workspace context, or unmount must prevent an older completion from being presented as the current result. Reuse existing generation/context mechanisms where possible.

If preserving a previous result during refresh, visibly bind it to its actual pair and distinguish it from the pending request. Otherwise clear it. Do not show a previous success as the outcome of a failed new request.

A zero-result display filter is different from a server comparison reporting no changes. A summary with supported=false is different from a supported all-zero summary.

Do not silently truncate gateway results or introduce pagination that the existing contract does not support.

6. Unified interactions and authority

Preserve:

* The single semantic Workspace.
* Existing horizontal Studio navigation and contextual Inspector.
* Existing Selection and current-context command projection.
* Existing read-only query gateways.
* Existing ProductAction/InteractionIntent dispatch where already applicable.

Review UI state, filters and focus are local presentation state. Canonical revision IDs are server identities; they are not Selection lifetime/revision counters.

Do not introduce another command registry, permission cache, Selection store or direct transport bypass.

Backend remains the authorization authority. Unknown or denied access must not become available through UI visibility, feature flags, mock data or Agent actions.

Keep merge resolution and generic canonical Apply unavailable. Do not implement approval, rejection, publication, comments, mentions, visual diff computation or collaborative persistence under this task.

Existing unavailable sections may receive clearer localized explanations. They must not imply implemented capabilities.

7. Accessibility and localization

All new user-facing labels, help, empty states, statuses and accessible names must use the existing neutral en/zh-CN localization system.

Preserve stable IDs and opaque server explanations. Do not translate server authority into a different decision.

Use existing native controls and shared components. Ensure:

* Logical keyboard order and visible focus.
* Associated labels and descriptions.
* Loading and result announcements without excessive live-region repetition .
* Correct existing tab/panel relationships where this task changes them.
* Readable long labels and IDs.
* Usable desktop and narrow layouts.

Do not move focus on every asynchronous result or filter update. Do not introduce a new global keyboard handler.

Physical-device, screen-reader and OS IME behavior may only be claimed if actually tested.

8. Backend requirements and notification inventory

Frontend implementation remains independent of backend development.

Use existing requirements records:

* frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv
* docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md

Append or update a requirement only for a concrete unmet consumer scenario. Reuse existing IDs when appropriate. Record scenario, existing contract, exact gap, permission expectations, failure behavior, mock boundary and integration acceptance.

As a secondary bounded read-only task, inventory notification capability. Do not implement notifications in this task.

Inspect current frontend notification consumers/routes and the available backend notification reference without checking out or altering the active backend worktree.

Known starting points:

* notification-module/
* frontend/src/api/me.ts
* frontend/src/api/admin/notification.ts
* docs/frontend/notification-settings.md
* docs/observability/notification-center.md
* Existing Toast/status components and actual shell entry points.

Distinguish:
A. Ephemeral UI feedback such as Toast.
B. Durable user inbox, unread count and read state.
C. System-generated event notifications.
D. Administrative announcements and targeting.
E. Notification preferences and subscriptions.
F. Email/SMS/webhook/Novu delivery.
G. Browser or operating-system push.

For each, record:

* Exact inspected commit/source identity.
* Backend code present.
* Frontend API wrapper present.
* Routable user interface present.
* Contract alignment established or not established.
* Mock/stub versus actual transport.
* Integration evidence established or not established.
* Concrete gaps.

Specifically verify request parameters, response envelopes and routes. A frontend method name is not proof that the backend endpoint exists or matches it.

Public-reference observations to verify, not assumptions to overwrite current code:

* The inbox service includes listing and read-state operations.
* A frontend inbox wrapper expects a paginated envelope, while the inspected NotificationController returns a list with a limit.
* A frontend read-all wrapper exists; endpoint availability needs confirmation.
* Some local delivery providers return SENT without performing external delivery.
* The notification settings document labels itself a design/contract candidate.

Do not send notifications, call provider delivery/test endpoints, request browser notification permission, read credentials, or trigger real external effects.

Write the inventory into this external task package and record confirmed integration gaps in the existing requirements ledger. Unestablished notification capabilities do not block Review acceptance. Notification UI implementation requires a later separate task.

9. Validation

Validate behavior, not implementation structure alone.

Use meaningful targeted regressions for:

* Invalid and explicit ordered revision selection.
* Current-pair result binding.
* Out-of-order asynchronous completions.
* Project/context changes and unmount.
* Error/retry behavior.
* Unsupported, empty comparison and filtered-empty distinctions.
* Keyboard access, localization and layout.

Reuse existing test infrastructure. Normal failing tests introduced while implementing this authorized scope may be corrected and rerun; preserve meaningful failure records. Do not stop for routine implementation choices.

Run the applicable frontend type, lint, localization and architecture gates. Run the final frontend suite once after the implementation stabilizes when required by the existing gate policy or shared-component impact. Report actual counts; do not require the previous 399 count.

Perform a foc used Chromium smoke of the changed Review flow with deterministic mock HTTP responses through the existing gateway:

* Select and compare revisions.
* Read a result and filter changes.
* Exercise a representative unavailable/error state.
* Check keyboard use and desktop/narrow en/zh-CN presentation.

Use unit tests for controlled race conditions where they provide stronger evidence. Do not build another general browser or lifecycle harness.

No backend tests, prior pagehide replay or validator qualification are needed for this frontend task.

10. Build and preservation

Resolve and record the actual Vite output before building.

Build only into a new external task directory. Do not run an unqualified build command that writes into platform-app/src/main/resources/static.

Do not modify:

* Tracked frontend dist.
* Backend static.
* Dependency manifests or lockfiles.
* Build configuration or tracking policy.

Bind the new build to the new implementation identity. Do not validate changed UI against the accepted prior bundle.

Reuse the established environment and containment. Limit process/port cleanup to task-owned resources.

Observe preservation for the actual frontend scope and prior artifacts. Do not introduce a new whole-machine, multi-workspace or Skill/Memory census.

If a tool denies an operation or an unauthorized protected-path mutation occurs, preserve evidence and stop the affected operation; do not bypass restrictions or restore-and-hide the event.

11. Evidence delivery

Produce an external task package containing:

* Chinese implementation report.
* Baseline/final implementation identities.
* Exact task delta and changed-path hashes.
* Acceptance checklist with evidence references.
* Raw targeted and required gate results.
* Focused browser records and screenshots.
* Build manifest and source/build binding.
* Bounded preservation observations.
* Notification capability inventory.
* Any requirements-ledger delta.

Publish only approved public-safe evidence to the existing media-platform-evidence repository under this new task path. Preserve historical evidence and unrelated task paths.

Use fixed-commit URLs, a manifest and remote byte verification. Keep private configuration, credentials and unrelated local data out of the public package. No manual ZIP upload is required when public evidence is accessible.

Do not change product publication status or claim independent acceptance on behalf of the reviewer.

12. Completion

Finish when the bounded Review implementation, applicable validation and evidence delivery are complete. Do not expand the task to close all frontend governance debt or implement the notification center.

Final response in Chinese must include:
TASK
LANE
FRONTEND_BRANCH
BASELINE_IMPLEMENTATION_TREE
FINAL_IMPLEMENTATION_TREE
PRODUCT_CHANGED_PATHS
DOCUMENTATION_CHANGED_PATHS
REVIEW_UX_RESULT
EXACT_PAIR_AND_STALE_RESULT_HANDLING
LOCALIZATION_AND_ACCESSIBILITY_RESULT
TARGETED_AND_REQUIRED_TEST_RESULTS
FOCUSED_BROWSER_RESULT
MOCK_AND_DEVICE_LIMITS
NOTIFICATION_INVENTORY_RESULT
NEW_OR_UPDATED_BACKEND_REQUIREMENTS
BACKEND_CHANGES
TRACKED_DIST_CHANGES
BACKEND_STATIC_CHANGES
H4_RECONCILIATION_STATUS
FORMAL_SLICE1C_LEDGER_STATUS
PRIOR_ACCEPTED_WORK_REOPENED
PRODUCT_COMMIT_FREEZE_MERGE_PUSH
PRODUCT_PUBLICATION
EVIDENCE_COMMIT_SHA
REVIEW_INDEX_URL
PUBLIC_MANIFEST_SHA256
REMOTE_VERIFICATION
INDEPENDENT_REVIEW=REQUIRED
STOP=YES
