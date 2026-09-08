from pathlib import Path
import json,datetime
ROOT=Path(__file__).parent
T=json.loads((ROOT/'TREE_BINDING.json').read_text())['FINAL_EXACT_IMPLEMENTATION_TREE']
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
