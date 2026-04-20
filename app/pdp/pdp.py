"""
Stage2 PDP (Layer 5): External policy evaluation via OPA.
Authoritative decision point for ALL tool executions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import fnmatch
import yaml
import requests

from app.telemetry.audit import write_audit
from app.telemetry.logger import log_event


POLICY_DIR = Path(__file__).resolve().parents[2] / "policy" / "policies"


@dataclass
class Decision:
    decision: str  # ALLOW | DENY | HITL
    reason: str
    policy_id: Optional[str] = None
    rule_id: Optional[str] = None


def _load_yaml_policies() -> List[Dict[str, Any]]:
    policies: List[Dict[str, Any]] = []
    if not POLICY_DIR.exists():
        return policies

    for p in sorted(POLICY_DIR.glob("*.y*ml")):
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            doc = yaml.safe_load(f) or {}
            doc["_source_file"] = str(p)
            policies.append(doc)

    return policies


def _action_matches(action: str, patterns: List[str]) -> bool:
    for pat in patterns:
        if pat == "*" or fnmatch.fnmatch(action, pat):
            return True
    return False


def evaluate(action: str, context: Dict[str, Any], run_id: str) -> Dict[str, str]:
    payload = {
        "input": {
            "action": action,
            "table": context.get("table"),
            "query": context.get("query", ""),
            "limit": context.get("limit"),
            "has_time_filter": context.get("has_time_filter", False),
        }
    }

    try:
        resp = requests.post(
            "http://localhost:8181/v1/data/sentinel/allow",
            json=payload,
            timeout=3,
        )
        resp.raise_for_status()
        allowed = resp.json().get("result", False)
    except Exception as e:
        decision = "DENY"
        reason = f"opa_error: {str(e)}"

        write_audit(
            run_id=run_id,
            stage="pdp_decision",
            data={
                "action": action,
                "decision": decision,
                "reason": reason,
            },
        )

        log_event(
            "pdp_decision",
            {
                "run_id": run_id,
                "action": action,
                "decision": decision,
            },
        )

        return {"decision": decision, "reason": reason}

    decision = "ALLOW" if allowed else "DENY"
    reason = "policy_allowed" if allowed else "policy_denied"

    write_audit(
        run_id=run_id,
        stage="pdp_decision",
        data={
            "action": action,
            "decision": decision,
            "reason": reason,
        },
    )

    log_event(
        "pdp_decision",
        {
            "run_id": run_id,
            "action": action,
            "decision": decision,
        },
    )

    return {"decision": decision, "reason": reason}