# Browser harness attempts

smoke-01: missing task-local TREE_BINDING.json required by reused control.py; fixture never started; no browser or product correction.

smoke-02: three initial native keyboard checks passed. The harness incorrectly required a native disabled Compare button to retain focus during a request; Chromium naturally blurs disabled controls. No product focus handler moved it. Replaced this assertion with a stronger user-directed focus test: deterministic mock delay, native Shift+Tab to To revision while pending, and unchanged focus when the result arrives. Original failure and screenshot retained. Product identity and build unchanged.

smoke-03: all 39 UI checks passed. An overbroad final harness assertion expected no POST at all. Existing, unchanged shell auth bootstrap made four POSTs to the localhost fixture /api/v1/dev/auth/token; all were denied with 403, no credential or token response, no forwarding. No Review/canonical/notification mutation occurred. The final harness distinguishes these exact denied local bootstrap attempts from prohibited product mutations, asserts every response remains denied and all read endpoints are the exact expected local mocks. The fixture does not grant auth or bypass any restriction. Product/source/build are unchanged; this is not a tool-policy denial. Original run exit 1 and all raw requests remain.
