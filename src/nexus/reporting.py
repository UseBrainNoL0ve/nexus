import json
from datetime import datetime, timezone

from nexus.core.models import SystemSnapshot


def snapshot_to_json(snapshot: SystemSnapshot) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot.to_dict(),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
