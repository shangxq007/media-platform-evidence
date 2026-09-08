# Controller interim source observations — writer still active

Not an acceptance report; verify against final writer bytes before correction.

1. In initial new `source.ts` real `hasExpectedProjection`, explicitly exclude `TEST_ONLY_RENDER_ACCESS_KEY` from host-agreed SERVER keys as well as `UNAGREED_RENDER_QUERY_LABEL` and surface visibility. A host could otherwise relabel the test key as HOST_AGREED+SERVER. Current Owner explicitly says testkey is not authorization. Add a focused negative test if not already covered.
2. In SCOPE_AND_SOURCE_MAP.md instruction conflict record, `independent controller review/freeze remains required` must say independent review required but product freeze remains forbidden/separate. No permission to freeze is implied by controller review.

3. Initial RenderDetail only renders `progressText`; on invalid finite range (fixture 140 frames / 100 frames) it hides all supplied value/unit/total fields and only says Invalid supplied progress. Owner requires supplied value/unit/total/stage in detail. Keep a visible raw value/unit/total/totalUnit row or summary for supplied finite values, with invalid/no-derived-percent reason and no clamping. Add a meaningful assertion that 140/100 is represented as source values but never 100%/140% derived progress.

4. Initial component tests isolate pending principal/tenant/session/project, but do not yet directly exercise ready/pending access-binding/source-adapter replacement, explicit owner retirement under StrictMode, or an unmount-late completion. Owner explicitly requires access/source change isolation and retirement ready/pending under actual StrictMode. Add focused non-vacuous behavior assertions: establish data or pending read, replace access binding/access status or adapter, assert old data/dialog removed and signal aborted, resolve/reject old request late, assert no restoration; test explicit retirement with StrictMode ready and pending states. Preserve existing identifiers rather than another wholesale rewrite. Preserve predecessor's meaningful adapter-replacement/unmount and initial denied/unknown no-query coverage (new direct assertions may replace old identities, but behavior must not vanish). Ordinary runtime corrections remain authorized.

Controller will re-read final bytes and run exact-tree gates, so ongoing writer fixes may already supersede these observations.
