"""
Safe OPA demo for policy-enforced Sentinel KQL decisions.

This demo does not require Azure OpenAI, Microsoft Sentinel, or live workspace credentials.
It sends two sample policy inputs to the local OPA PDP endpoint and prints the decisions.

Prerequisite:
    opa run --server policy.rego
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import requests

OPA_URL = os.environ.get("OPA_URL", "http://localhost:8181/v1/data/sentinel/allow")
ROOT = Path(__file__).resolve().parents[1]


def load_sample(name: str) -> Dict[str, Any]:
    with (ROOT / "samples" / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_sample(label: str, filename: str) -> Dict[str, Any]:
    payload = load_sample(filename)
    response = requests.post(OPA_URL, json=payload, timeout=5)
    response.raise_for_status()
    result = response.json()
    allowed = bool(result.get("result", False))

    decision = {
        "label": label,
        "decision": "ALLOW" if allowed else "DENY",
        "opa_result": result,
        "input": payload.get("input", {}),
    }
    return decision


def main() -> None:
    print("=== Safe OPA policy demo ===")
    print(f"OPA endpoint: {OPA_URL}")
    print("No Sentinel or Azure OpenAI connection is used.\n")

    for label, filename in [
        ("bounded_query", "input-allowed.json"),
        ("unbounded_query", "input-denied.json"),
    ]:
        try:
            decision = evaluate_sample(label, filename)
        except requests.RequestException as exc:
            raise SystemExit(
                "Could not reach OPA. Start it from the repo root with:\n"
                "  opa run --server policy.rego\n\n"
                f"Details: {exc}"
            ) from exc

        print(json.dumps(decision, indent=2))
        print()


if __name__ == "__main__":
    main()
