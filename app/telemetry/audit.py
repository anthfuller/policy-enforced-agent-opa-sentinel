import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_FILE = Path("telemetry/audit_log.jsonl")

def write_audit(run_id: str, stage: str, data: dict):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "stage": stage,
        "data": data,
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
