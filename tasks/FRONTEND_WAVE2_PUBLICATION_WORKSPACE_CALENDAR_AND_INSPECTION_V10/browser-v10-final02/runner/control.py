from datetime import datetime, timezone
T='afc966ad4872e6dd65997281c75fe49e7aaed376'
def now(): return datetime.now(timezone.utc).isoformat()
