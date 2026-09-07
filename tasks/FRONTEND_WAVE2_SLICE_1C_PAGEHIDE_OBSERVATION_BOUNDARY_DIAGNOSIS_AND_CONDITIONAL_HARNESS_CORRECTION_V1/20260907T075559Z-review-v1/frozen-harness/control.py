from pathlib import Path
import json,datetime
from scope_check import check
ROOT=Path(__file__).parent
T=json.loads((ROOT/'TREE_BINDING.json').read_text())['FINAL_EXACT_IMPLEMENTATION_TREE']
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def tripwire(label):return check(label)
