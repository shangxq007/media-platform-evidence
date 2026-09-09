from datetime import datetime, timezone
T='37d003fc4f55faf166cd836a6ea93d77eb8b6a1e'
def now(): return datetime.now(timezone.utc).isoformat()
