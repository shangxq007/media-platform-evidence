from datetime import datetime, timezone
T='ea4798924207d4004c92910815a42753e4ab9724'
def now(): return datetime.now(timezone.utc).isoformat()
