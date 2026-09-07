# Baseline native reproduction
Baseline exact tree a8dc8bd3a0e4119e0a3a6bc8cdd18ed9ff789f72; original build reused, 8 emitted files hash-matched prior remote-verification manifest. No baseline rebuild/product edit.

browser-baseline-01: runner path relocation error before browser start; fixture exec missing path; NOT product RED. Root-relative venv lookup corrected, original failed directory retained.
browser-baseline-02: native script exit 1; harness_error=null. 58 assertions:24 passed,34 failed. These are assertions, NOT 34 independent defects. In particular pending-late-does-not-reopen lacks a successful close precondition because Escape already failed: dependency consequence, not evidence of reopening. Exact raw observations retained.

Natural trusted Tab/Enter disabled the focused single-read button and activeElement became BODY. All immediate success retains 3 rows and count=1 but Escape from BODY does not close. Controlled pending, failed, invalid/rejected outcomes and reconciliation failure show same loss. No direct BODY focus or DOM blur injected. Existing read-all transfers to the active filter; Unread after successful row removal restores focus. Native Tab from BODY happened to re-enter a valid dialog control, so universal Tab failure is NOT claimed.

The immediate case used the original production simulated fixture with no adapter injection. Delayed cases wrap only the explicit simulated source adapter via external React-fiber inspection to control promises. Same object/contract and unmodified bundle; resolution by CDP Runtime.evaluate is test assistance, whereas Tab/Enter/Escape are trusted inputs. Browser has CDP focus emulation; viewport/locale helpers disclosed; no physical-device/OS/screen-reader claim.
