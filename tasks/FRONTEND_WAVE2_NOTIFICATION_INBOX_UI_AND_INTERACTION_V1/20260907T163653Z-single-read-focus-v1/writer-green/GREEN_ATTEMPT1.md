# First GREEN attempt: preserved helper failure

- Exit: 1
- Total tests: 77
- Passed: 75
- Failed: 2
- Pending/todo: 0

Both failures are the two parameters of the original `reconciles disabled-button focus loss, moved-away=%s (modeled browser blur)` test. Its modeled helper path unconditionally toggled and blurred the single-read button, then expected BODY. After the intended synchronous transfer, that button no longer owns focus, so calling `blur()` on it correctly leaves the active filter focused. This is a modeled-helper incompatibility, not a remaining product-focus failure.

Per the Owner instruction, the failed JSON is preserved as `green-focused.json`. The helper is corrected to model browser blur only if the exact disabled read button still owns `document.activeElement`; the original test title and original BODY assertion text remain unchanged inside that applicable branch.
