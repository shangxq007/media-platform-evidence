# EP19 bookkeeping V3 adapter — advisory source conformance review

**Result: concrete conformance defects identified. Not final independent acceptance.**

Owner verbatim SHA-256 verified: `4f431b08fda1066719b63d9753f5db202f5c1191371c33d9d99fed66dd5b01ff`. Read the complete Owner decision and both incorporated local proposals. References below are relative to K, except proposal line references which are relative to the prior continuation-review-001. No implementation or integration changes.

## Evidence assessment

The green-009 receipts enumerate 71 unique controls, zero failures/errors/skips; native log says 71 tests / OK. The qualification-linked process/result/log/diff hashes and current source bindings match. This confirms receipt consistency, not this reviewer executing tests or full contract coverage. build_qualification.py:123-127 stamps every area PASS from overall unittest success, so those area labels do not establish independent exhaustive coverage. No full 29-gate driver was reviewed.

## Findings

### AR001 — HIGH — Strict scope and ancestor coverage are not implemented by this adapter

**Source:** `tooling/executor/observe.py:119-127`; `tooling/executor/bookkeeping_v3.py:202-232,495-507`; `tooling/executor/capture.py:147-172`

**Contract:** Owner 46,77,111,131,211; ledger proposal 202-204,243-259,292-301.

**Deterministic reasoning counterexample (not executed):** With eligible alpha and an existing ineligible beta directory, change beta/support.txt in place. The root entry set and alpha manifest stay equal; the observer watches root and alpha directories, not beta; directory watches are not recursive. No event or capture covers beta/support.txt, and default strict_input_integrity=True allows PASS. Memory and external strict objects are also absent. chmod an ancestor above skills similarly changes no compared ancestor row. This is a concrete adapter coverage gap, not a claim that an unreviewed outer integration cannot supply coverage.

**Repair direction:** Capture and bind the full independent strict inventory and required ancestor identities/entry sets, with continuous coverage; require an authenticated strict result rather than default True. Package manifests currently retain only path/hash, not strict metadata or directory identity.

**Why existing qualification misses it:** Tests 369-380 cover only eligible alpha; test 413 only supplies a false flag.

### AR002 — HIGH — Usage temporary-file lifecycle is widened beyond V2

**Source:** `tooling/executor/observe.py:39-48,68-104`; `tooling/executor/bookkeeping_v3.py:495-505`

**Contract:** Owner 72-79; narrow proposal 33,59.

**Deterministic reasoning counterexample (not executed):** Move a temp named .usage_abc12_3z.tmp out of skills to an unobserved directory. Its MOVED_FROM event is accepted with any cookie, no matching MOVED_TO is required, and final absence passes. Likewise an externally supplied file renamed to .usage.json is accepted with MOVED_TO without a paired approved temp source. No visible-temp mode 0600, owner/group/dev/nlink check exists in the reducer. These are event/lifecycle violations even when usage endpoint bytes are legal.

**Repair direction:** Restore exact V2 rename pairing, scope and visible-temp metadata checks; do not treat every event bearing an approved temp name as resolved.

**Why existing qualification misses it:** Atomic replacement positive 120-129 supplies the valid pair; no negative unpaired/cross-boundary temp test exists.

### AR003 — HIGH — Ledger timestamps are bounded by caller values, not actual capture time

**Source:** `tooling/executor/boundary.py:89-99,117-119`; `tooling/executor/bookkeeping_v3.py:368-382`

**Contract:** Owner 119; ledger proposal 147 and 330.

**Deterministic reasoning counterexample (not executed):** Engine(policy) defaults window_end to datetime.max. An otherwise valid appended row dated 2099-01-01T00:00:00+00:00 passes at a 2026 boundary with matching modify/close events. Even an explicit future end permits future timestamps before that time has occurred. No observed wall-clock rollback check exists; time.time_ns fields are recorded without comparison.

**Repair direction:** Bind start to the actual protected start and end to actual boundary capture time; reject wall-clock rollback, without adding a 3600-second cap.

**Why existing qualification misses it:** Fixture 66-70 injects a two-day window; timestamp negative 341-343 checks only a value beyond that injected end.

### AR004 — MEDIUM — Ledger parser accepts forbidden carriage-return framing

**Source:** `tooling/executor/bookkeeping_v3.py:181-195,416-430,81-103`

**Contract:** Owner 119; ledger proposal 208 explicitly says no CR.

**Deterministic reasoning counterexample (not executed):** Take any otherwise valid ledger record and encode JSON followed by CR LF. bytes.splitlines(keepends=True) retains CR LF; line.endswith(LF) passes; line[:-1] still contains CR, which json.loads accepts as trailing whitespace. A CR used as JSON whitespace inside the object before the ending LF is likewise not explicitly prohibited. The accepted schema forbids CR.

**Repair direction:** Reject CR bytes in ledger framing explicitly, including original-prefix framing as applicable; keep usage parsing separate.

**Why existing qualification misses it:** Existing malformed/UTF8/half-line tests do not include CRLF.

### AR005 — HIGH — An unchanged boundary after an approved usage change is falsely rejected

**Source:** `tooling/executor/bookkeeping_v3.py:311-353`; `tooling/executor/boundary.py:123,131-135,179-180`; `tooling/executor/observe.py:82-83`

**Contract:** Owner 88-98,190-201; narrow proposal 37-39.

**Deterministic reasoning counterexample (not executed):** Baseline usage count is 1. At COMMAND it legally becomes 2 with covered usage events and passes. At the next GATE no usage write occurs and count remains 2. evaluate_usage compares against the original policy baseline, still returns OLD_STRICT_REJECT; usage_variation remains true and the empty new event batch triggers USAGE_VARIATION_WITHOUT_COVERED_EVENT. The same occurs immediately after approved baseline variation. The session advances ledger only.

**Repair direction:** Retain old-strict differences against original baseline, but compute per-boundary event requirements from a separately retained previous successful real usage capture.

**Why existing qualification misses it:** Tests 101-118 check one variation only; all-eight-phases test 94-99 uses fully unchanged input.

### AR006 — HIGH — Caller assertions and replayed bundles can manufacture complete PASS

**Source:** `tooling/executor/boundary.py:70-99,101-119,137-160,178-187`; `tooling/executor/bookkeeping_v3.py:303-308`; `tooling/executor/executor_adapter.py:38-42,65-71`

**Contract:** Owner 81-101,142-143,228-238,260-267.

**Deterministic reasoning counterexample (not executed):** Call RunAdapter with no binding; retain a prior coherent bundle, then pass it to baseline(bundle=old_bundle) without observer or evidence_dir. Defaults claim coverage and strict integrity. There is no fresh capture, byte/hash/source-ID recomputation, capture-age check, mandatory evidence, or mandatory expected binding. Changing all capture IDs and their matching dictionary values together also passes coherence equality. Supplying just binding schema plus ledger_use and no expected fields bypasses candidate/source/Owner validation. This is a public adapter fail-open trust boundary, not a claim of malicious code injection into a protected executor.

**Repair direction:** Separate fixture injection from production APIs. Require actual bound captures, observer continuity, complete strict inventory, exact immutable runtime binding and durable evidence before PASS; never default missing attestations to success.

**Why existing qualification misses it:** Tests 382-386 mutate only one side of the ID comparison; stale-binding tests provide the expected candidate themselves; no missing binding/replayed bundle control.

### AR007 — HIGH — Candidate binding accepts fabricated qualification and incomplete dependency evidence

**Source:** `tooling/qualification/candidate_binding.py:56-73,74-92`; `tooling/qualification/test_approved_contract.py:521-535`; `tooling/qualification/build_qualification.py:123-136`

**Contract:** Owner 142-143,212,219-220,228-238,260-267.

**Deterministic reasoning counterexample (not executed):** A qualification object containing only schema, result=PASS and current source_binding passes candidate_binding.build; its process/result/log receipt paths, hashes, control identities, fresh count and per-area coverage need not exist. The positive test at 525-527 constructs exactly that object. A dependency document containing schema/result/ledger_role also passes when consumers and dynamic readers are omitted because missing defaults are empty. No actual consumer/source closure is validated here. Output does not bind a policy/eligible map, wrapper/init or exclusive runtime directories.

**Repair direction:** Require and verify actual receipt/hash/control closure and complete dependency evidence; include every required binding or explicitly defer them to a mandatory checked final binding stage.

**Why existing qualification misses it:** The purported actual builder positive demonstrates the minimal forged PASS payload rather than fresh qualification provenance. Existing green-009 is real internally consistent evidence, but the builder does not require it.

### AR008 — HIGH — Evidence-write exceptions do not poison the run and session advances before durability

**Source:** `tooling/executor/boundary.py:178-187`; `tooling/executor/executor_adapter.py:65-83`

**Contract:** Owner 101,167,212,284-289; ledger proposal 286,303.

**Deterministic reasoning counterexample (not executed):** With an otherwise valid baseline, give evidence_dir an existing regular file. Engine updates its ledger session, then write_evidence raises BoundaryReject. RunAdapter.boundary never reaches its decision != PASS branch, so BOOKKEEPING_FAILURE.json is not written. The same adapter can then call preflight() without evidence_dir: _require_live sees only its consumed marker and permits PASS. A valid ledger suffix consumed by the failed evidence write has also already advanced the session.

**Repair direction:** Latch failure on exceptions as well as explicit rejection, update accepted session only after durable evidence, and prohibit further phases after any failed formal acceptance.

**Why existing qualification misses it:** Evidence failure test 418-422 uses Engine directly; namespace failure test 434-447 tests only returned REJECT, not exceptions.

### AR009 — HIGH — Attempt/failure namespace markers are not crash-durable directory entries

**Source:** `tooling/executor/executor_adapter.py:22-34,45-56,73-83`; `tooling/executor/boundary.py:46-64`; `tooling/qualification/policy_builder.py:41-50`

**Contract:** Owner 167,269,284-289; ledger proposal 292-293,303.

**Deterministic reasoning counterexample (not executed):** The marker file is fsynced, but its containing directory (and a newly created run directory parent) is never fsynced before baseline capture. A power-loss recovery may retain file data but lose the new directory entry; a subsequent adapter then sees neither consumed nor failure marker and admits another baseline. Similarly private evidence file data is fsynced but its private directory entry is not. Also policy_builder captures authoritative policy baseline inputs before RunAdapter.baseline consumes its namespace; this sequencing is left to the caller.

**Repair direction:** Fsync the directories needed to durably publish namespace markers before the first authoritative baseline capture, and failure markers before returning failure. Place policy capture inside the same consumed/covered lifecycle; fsync private evidence directory.

**Why existing qualification misses it:** No crash-order or directory-fsync qualification exists; tests check live filesystem presence only. Crash outcome is a permitted filesystem failure window, not an executed crash test.

### AR010 — MEDIUM — Capture/event resource budgets are not enforced across actual acquisition

**Source:** `tooling/executor/capture.py:53-65,82-100,147-168`; `tooling/executor/bookkeeping_v3.py:202-222`; `tooling/executor/observe.py:140-174,68-73`; `tooling/qualification/test_approved_contract.py:495-519`

**Contract:** Owner 153-165; ledger proposal 218-222.

**Deterministic reasoning counterexample (not executed):** capture_file checks elapsed time before an attempt and after the entire read, not inside its read loop. A continuously growing usage file has no byte cap and can keep returning chunks beyond five seconds without reaching the clock check. Observer drain likewise appends without checking pending_events_max and can drain indefinitely while events arrive; only the later reducer notices excess. The three-attempt allowance resets for usage, lock, ledger and every manifest file rather than being a shared per-boundary retry budget; two failed reads then success on usage, followed by two failed reads then success on lock are accepted if total time fits.

**Repair direction:** Check deadlines and event count during acquisition, fail closed immediately on actual excess, and make the intended per-boundary attempt accounting explicit/shared. Ordinary reads of different required files must remain possible; do not confuse the number of files with retry rounds.

**Why existing qualification misses it:** Generic enforce_limit exact/over checks at 495-501 only prove a numeric helper. Actual tests cover record count and reducer event list, but not sustained acquisition, cumulative retry consumption, or full-size fixtures for every declared cap.

## Supported implementation observations (static, not acceptance)

- Exact lock predicate compares all nine captured metadata fields and empty content; direct classifier requires mask 8/cookie 0. Native observer strips IN_ISDIR at observe.py:172, so its stored event is not literally the unmodified mask; no separate exploit finding is made without a producible regular-file case.
- Usage mutable field list is exactly view_count/use_count/last_viewed_at/last_used_at; bool counters, membership changes and strict nested type/value changes reject.
- Ledger checks both original and previous byte prefixes, historical ID collisions, new record ID uniqueness, eight keys, action patch/edit, empty evidence, nonempty equal sorted unique complete bound manifests. Single-file capture uses same-descriptor stat/read/stat and final path metadata equality. These protections do not cure the scope, lifecycle or caller-input gaps above.
- Hidden ledger overwrite-restore/truncate-regrow remains the explicitly accepted observational LIMIT. It is not a defect, and no new approval or 3600-second cap is requested. Historical writer remains UNKNOWN / NOT_ESTABLISHED.

## Review boundaries

- No tests, probes, formal gate, baseline or shared bookkeeping reads executed.
- No integration-001 content read; full 29-gate driver integration is outside this review.
- V2 source not independently reviewed; four-field and lifecycle comparison uses incorporated approved narrow proposal. Previous-capture usage monotonicity is not independently asserted as a separate defect.
- Local approved proposal copies reviewed and hashed; remote fixed commit payload not independently fetched.
- Historical writer remains UNKNOWN / NOT_ESTABLISHED.
- Ledger hidden overwrite-restore/truncate-regrow is Owner-accepted LIMIT, not a finding. No 3600-second cap is required.
- Scope is partial advisory static review, not independent final acceptance or a new approval prerequisite.

Source hashes are recorded before/after in this directory; input hashes cover proposals and green-009 receipts. Source-hash comparison is recorded separately. Only this review directory is written.
