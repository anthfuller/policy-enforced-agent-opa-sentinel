from pathlib import Path
import uuid
import json

from app.coordinator.coordinator import CoordinatorAgent
from app.investigator.investigator import InvestigatorAgent
from app.telemetry.audit import write_audit


def correlate(incident_file, alert_file, output_file):
    output_file.write_text("[]", encoding="utf-8")
    return []


# ---- validation helpers ----

def _abort(run_id: str, reason: str, details: dict | None = None):
    write_audit(
        run_id=run_id,
        stage="validation_failed",
        data={"reason": reason, "details": details or {}},
    )
    raise RuntimeError(reason)


def validate_baseline_evidence(run_id: str, run_dir: Path):
    evidence_dir = run_dir / "evidence"
    required = [
        "securityincident.json",
        "securityalert.json",
        "signinlogs.json",
        "azureactivity.json",
    ]
    missing = [f for f in required if not (evidence_dir / f).exists()]
    if missing:
        _abort(run_id, "baseline_evidence_missing", {"missing_files": missing})


def validate_security_alerts(run_id: str, run_dir: Path):
    sa_file = run_dir / "evidence" / "securityalert.json"
    data = json.loads(sa_file.read_text(encoding="utf-8"))

    if int(data.get("rowcount", 0)) == 0:
        write_audit(
            run_id=run_id,
            stage="validation_warning",
            data={
                "reason": "zero_alerts",
                "details": {"table": "SecurityAlert"},
            },
        )


def validate_correlation(run_id: str, run_dir: Path):
    corr_file = run_dir / "correlated_facts.json"
    if not corr_file.exists():
        _abort(run_id, "correlation_missing", {})

    facts = json.loads(corr_file.read_text(encoding="utf-8"))
    if not facts:
        write_audit(
            run_id=run_id,
            stage="validation_warning",
            data={"reason": "correlation_empty", "details": {}},
        )
        return

    missing_alerts = [f for f in facts if f.get("status") == "MISSING_ALERT"]
    if missing_alerts:
        _abort(run_id, "correlation_missing_alerts", {"count": len(missing_alerts)})


# ---- ORCHESTRATOR ----

class Orchestrator:
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.investigator = InvestigatorAgent()

    def run(self, user_request: str):
        run_id = str(uuid.uuid4())
        run_dir = Path("runs") / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        write_audit(run_id=run_id, stage="run_started", data={"request": user_request})

        # 1. Plan
        plan_obj = self.coordinator.handle_request(user_request, run_id)
        plan = plan_obj["plan"]

        # 2. Execute
        self.investigator.investigate(plan, run_id=run_id)

        # 3. Validation
        validate_baseline_evidence(run_id, run_dir)
        validate_security_alerts(run_id, run_dir)

        # 4. Correlate
        correlate(
            incident_file=run_dir / "evidence" / "securityincident.json",
            alert_file=run_dir / "evidence" / "securityalert.json",
            output_file=run_dir / "correlated_facts.json",
        )

        # 5. Validate correlation
        validate_correlation(run_id, run_dir)

        write_audit(run_id=run_id, stage="run_completed", data={"status": "OK"})

        return {
            "run_id": run_id,
            "status": "completed",
        }