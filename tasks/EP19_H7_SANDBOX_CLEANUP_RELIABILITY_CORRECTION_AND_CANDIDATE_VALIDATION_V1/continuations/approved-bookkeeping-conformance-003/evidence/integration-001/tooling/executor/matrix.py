"""Read the authoritative 29 entries. Regeneration never adds or drops gates."""
import argparse,json
from pathlib import Path
from bindings import build
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with a.output.open('x') as f:json.dump(build(a.run),f,indent=2);f.write('\n')
