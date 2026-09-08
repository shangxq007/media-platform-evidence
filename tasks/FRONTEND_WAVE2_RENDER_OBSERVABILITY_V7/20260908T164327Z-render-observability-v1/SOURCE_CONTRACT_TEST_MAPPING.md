# Source → executed test / browser map

Exact implementation `414d6ed80f6d4c01699d56403a043b84b390d1e7`. Raw expanded identities in validation/TEST_IDENTITY_ACCOUNTING.json. This map is not a claim of exhaustive input-space proof.

## source.ts:parseRenderSnapshot/validateRelationships/progressSchema/deriveProgressPercent

Executed identities in `frontend/src/product/render-browser/source.test.ts`:

- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "searches only supplied ID/name, uses source-supported statuses, and sorts stably by name then ID"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "derives percent only for matching finite units and valid ranges without clamping invalid values"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "accepts safe task, attempt, failure, progress and bounded Artifact metadata as one owned snapshot"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves missing, empty, bounded, denied, unavailable, unknown and stale Artifact states without inventing history"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "classifies broken attempt and Artifact task links as invalid relationships"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "rejects malformed ownership, duplicate identities, foreign Projects, invalid source times, unsafe failures and excess bounds"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing unavailable receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing denied receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing unknown receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing unsupported receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing error receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing stale receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["Render source, identity and access boundaries"], "accepts only an exact host-agreed SERVER binding and never treats Operations visibility as query permission"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["Render source, identity and access boundaries"], "keys principal, tenant, session, Project and complete access projection ownership"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["Render source, identity and access boundaries"], "requires explicit fixture identity, performs no transport or storage access, and has a distinct test-only binding"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["Render source, identity and access boundaries"], "defaults unavailable without transport and does not invent a Project or identity"]` — passed

## source.ts:sourceDisposition/hasExpectedProjection/renderScopeIsValid/contextKey; fixture.ts:createRendersFixture

Executed identities in `frontend/src/product/render-browser/source.test.ts`:

- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "searches only supplied ID/name, uses source-supported statuses, and sorts stably by name then ID"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "derives percent only for matching finite units and valid ranges without clamping invalid values"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "accepts safe task, attempt, failure, progress and bounded Artifact metadata as one owned snapshot"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves missing, empty, bounded, denied, unavailable, unknown and stale Artifact states without inventing history"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "classifies broken attempt and Artifact task links as invalid relationships"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "rejects malformed ownership, duplicate identities, foreign Projects, invalid source times, unsafe failures and excess bounds"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing unavailable receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing denied receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing unknown receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing unsupported receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing error receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["bounded Render observability projection"], "preserves safe nondisclosing stale receipts"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["Render source, identity and access boundaries"], "accepts only an exact host-agreed SERVER binding and never treats Operations visibility as query permission"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["Render source, identity and access boundaries"], "keys principal, tenant, session, Project and complete access projection ownership"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["Render source, identity and access boundaries"], "requires explicit fixture identity, performs no transport or storage access, and has a distinct test-only binding"]` — passed
- `["frontend/src/product/render-browser/source.test.ts", ["Render source, identity and access boundaries"], "defaults unavailable without transport and does not invent a Project or identity"]` — passed

## RenderBrowser.tsx:RenderBrowser/RenderBrowserSession/load/cancel; Selection owner integration

Executed identities in `frontend/src/product/render-browser/RenderBrowser.test.tsx`:

- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "uses explicit provider injection and remains usable through StrictMode adapter registration replay"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "shows supplied summary data, opaque unknown status, valid progress and current-snapshot disclosure without actions"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "searches ID/name, filters only source-supported literal statuses, sorts stably and keeps Reset focusable"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "opens read-only task/attempt/failure/Artifact metadata and restores launcher focus without exposing URLs"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "distinguishes missing attempts/Artifacts from empty and bounded inspectable metadata"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retains mismatched progress units and missing totals literally without deriving a percentage"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "uses one stable Refresh/Cancel/Retry control, preserves filters, drops cancelled replies and never steals moved focus"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe unavailable receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe denied receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe unknown receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe unsupported receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe error receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe stale receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "distinguishes invalid relationships from invalid returned content and never retains stale detail"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "shows detail-not-found after a successful refresh removes the inspected Render"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending valid reply on principalId change"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending valid reply on tenantId change"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending valid reply on sessionId change"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending valid reply on projectId change"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending read under StrictMode Selection ownership and rejects its late success"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires pending reads on access/source replacement and unmount"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears ready data and detail on access, agreed binding and adapter replacement under StrictMode"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "never queries initially denied or unknown access, including a host-relabelled test key"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "rebinds only to a fresh pageshow Selection owner after clearing ready data"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "is unavailable with no injected source and localizes the complete workflow in Chinese"]` — passed

## RenderBrowser.tsx:RenderDetail/ArtifactDetail/FailureDetail; shared InteractionDialog, localization

Executed identities in `frontend/src/product/render-browser/RenderBrowser.test.tsx`:

- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "uses explicit provider injection and remains usable through StrictMode adapter registration replay"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "shows supplied summary data, opaque unknown status, valid progress and current-snapshot disclosure without actions"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "searches ID/name, filters only source-supported literal statuses, sorts stably and keeps Reset focusable"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "opens read-only task/attempt/failure/Artifact metadata and restores launcher focus without exposing URLs"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "distinguishes missing attempts/Artifacts from empty and bounded inspectable metadata"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retains mismatched progress units and missing totals literally without deriving a percentage"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "uses one stable Refresh/Cancel/Retry control, preserves filters, drops cancelled replies and never steals moved focus"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe unavailable receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe denied receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe unknown receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe unsupported receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe error receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears old content for a safe stale receipt and keeps retry available"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "distinguishes invalid relationships from invalid returned content and never retains stale detail"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "shows detail-not-found after a successful refresh removes the inspected Render"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending valid reply on principalId change"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending valid reply on tenantId change"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending valid reply on sessionId change"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending valid reply on projectId change"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires a pending read under StrictMode Selection ownership and rejects its late success"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "retires pending reads on access/source replacement and unmount"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "clears ready data and detail on access, agreed binding and adapter replacement under StrictMode"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "never queries initially denied or unknown access, including a host-relabelled test key"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "rebinds only to a fresh pageshow Selection owner after clearing ready data"]` — passed
- `["frontend/src/product/render-browser/RenderBrowser.test.tsx", ["RenderBrowser observability workflow"], "is unavailable with no injected source and localizes the complete workflow in Chinese"]` — passed

## app/routeTree.tsx:existing operations/renders registration; AppShell and interaction/localization regression suites

Executed identities in `frontend/src/app/routeTree.test.tsx`:

- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "registers every implemented page and preserved legacy link exactly once"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "restores Workspace, Project, and surface identity from a creative deep link and fails unauthorized commands closed"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "remounts the ProjectFrame subtree when same-route Workspace or Project parameters change"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "integrates the disposable sketch on the Workflow route while invoke remains unavailable"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "reaches the post-H7 edit route and loads explicit canonical HEAD authority"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "renders the Workspace to Projects entry without synthesizing a Project selection"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "routes the existing Projects destination to the fail-closed recent-project browser without using Workspace home as its source"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "routes Operations renders to the fail-closed source browser and leaves Storage behavior unchanged"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "registers the Project Production consumer with exact route scope and no implicit fixture or request"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "handles Workspace API errors without inventing an empty state"]` — passed
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "preserves the historical default API export alongside the additive platform client"]` — passed

## Guard mechanisms and blind spots

Unchanged frontend-architecture-guard inventories governed source paths against both current ledger inputs and checks forbidden authority/import/mutation patterns. Unchanged Node controls execute positive and negative cases; 120/120 passed. This is static structural enforcement, not backend authorization/integration proof. Typecheck and lint are separate from executed Vitest behavior; browser uses built output rather than test DOM.

## Predecessor identity disposition

748 baseline identities retained exactly; 49 removed and 41 new, all confined to the two Render suites. The full before/after test files are exported as source endpoints. Old five-field/ID-profile-only filter, unknown-status rejection, fixed proposed real binding, and URL fixture expectations are intentionally superseded by this authorized feature. Old expanded schema-negative cases are consolidated into bounded behavior loops; the exact old parameterized instance set was not executed unchanged on V7. No skip or fixed total was added.

The final native assertions, expressions, their passing values and timestamps are in browser/NATIVE_CHECKS.json. Native pointer/key activation is distinct from DOM locale/locator/scroll assistance and explicit fixture outcome injection, all in browser/ASSISTANCE.json.
