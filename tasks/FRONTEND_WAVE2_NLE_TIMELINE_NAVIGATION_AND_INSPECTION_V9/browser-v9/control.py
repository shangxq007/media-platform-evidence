from datetime import datetime, timezone
T='a90af5baccf94a437b67e69fb1897328572a0209'
def now(): return datetime.now(timezone.utc).isoformat()
