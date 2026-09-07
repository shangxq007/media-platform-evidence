"""Compatibility entrypoint for the integrated run-owned executor."""
import sys
from runner import main
if __name__=="__main__":
 sys.argv.insert(1,'preflight')
 raise SystemExit(main())
