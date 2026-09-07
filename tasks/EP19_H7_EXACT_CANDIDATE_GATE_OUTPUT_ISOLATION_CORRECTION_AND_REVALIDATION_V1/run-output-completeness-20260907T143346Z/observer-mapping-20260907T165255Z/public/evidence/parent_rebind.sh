#!/usr/bin/env bash
# Local fixture qualification only. No parent/product gates are invoked here.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
ep19_observer_attempt="${1:-$PWD/parent-rebind-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
exec python3 -B bind_qualification.py --out "$ep19_observer_attempt"
