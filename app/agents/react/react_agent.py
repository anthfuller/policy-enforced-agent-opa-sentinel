from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.telemetry.audit import write_audit
from app.telemetry.logger import log_event

from app.llm.azure_openai_client import get_azure_openai_client, chat_json
from app.mcp.executor import execute_tool


@dataclass
class ReActResult:
    final: Dict[str, Any]
    tool_calls: List[Dict[str, Any]]


class ReActAgent:
    """
    AUTONOMOUS ReAct loop.

    HARD GUARANTEE:
    - The agent CANNOT finalize until it has ATTEMPTED at least one tool call.
    - If the model tries to quit early, the loop FORCES safe exploration.
    """

    def __init__(
        self,
        *,
        name: str,
        system_prompt: str,
        max_steps: int = 10,
        model_deployment_env: str = "AZURE_OPENAI_DEPLOYMENT",
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.deployment = (os.environ.get(model_deployment_env) or "").strip()
        if not self.deployment:
            raise RuntimeError(f"Missing {model_deployment_env}. Set it to your Azure OpenAI deployment name.")

    def _forced_exploration_action(self) -> Dict[str, Any]:
        """
        Non-destructive, safe default exploration.
        This executes even when the user provides no scope.
        """
        return {
            "type": "tool",
            "thought": (
                "The request is underspecified. "
                "Initiating safe exploratory investigation using high-level security telemetry."
            ),
            "tool": {
                "name": "kql_query",
                "args": {
                    "query": "SecurityIncident | where TimeGenerated > ago(30d)",
                    "timespan": "P30D",
                    "max_limit": 100,
                },
            },
        }

    def run(
        self,
        *,
        run_id: str,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ReActResult:
        client = get_azure_openai_client()
        ctx = context or {}

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps({"request": user_request, "context": ctx}, indent=2)},
        ]

        tool_calls: List[Dict[str, Any]] = []
        attempted_tool_calls = 0

        for step in range(1, self.max_steps + 1):
            log_event("react_step_start", {"run_id": run_id, "agent": self.name, "step": step})

            obj = chat_json(client=client, deployment=self.deployment, messages=messages)

            msg_type = obj.get("type")
            thought = obj.get("thought", "")

            if thought:
                write_audit(
                    run_id=run_id,
                    stage="agent_thought",
                    data={"agent": self.name, "step": step, "thought": thought},
                )

            # 🔒 AUTONOMY ENFORCEMENT
            # If the model tries to finalize before ANY tool attempt, force exploration.
            if msg_type == "final" and attempted_tool_calls == 0:
                obj = self._forced_exploration_action()
                msg_type = "tool"

            if msg_type == "tool":
                tool = obj.get("tool") or {}
                if tool.get("name") != "kql_query":
                    raise RuntimeError(f"Agent attempted unsupported tool: {tool.get('name')}")

                args = tool.get("args") or {}
                attempted_tool_calls += 1

                result = execute_tool(run_id=run_id, tool_name="kql_query", args=args)

                tool_calls.append(
                    {
                        "step": step,
                        "tool": tool,
                        "result_meta": {
                            "decision": result.get("decision"),
                            "table": result.get("table"),
                            "rowcount": result.get("rowcount"),
                        },
                    }
                )

                rows = result.get("rows", []) or []
                preview = rows[:10]

                observation = {
                    "decision": result.get("decision"),
                    "reason": result.get("reason"),
                    "table": result.get("table"),
                    "rowcount": result.get("rowcount"),
                    "columns": result.get("columns"),
                    "rows_preview": preview,
                }

                messages.append({"role": "assistant", "content": json.dumps(obj)})
                messages.append({"role": "user", "content": json.dumps({"observation": observation}, indent=2, default=str)})
                continue

            if msg_type == "final":
                final = obj.get("final") or {}
                write_audit(run_id=run_id, stage="agent_final", data={"agent": self.name, "final": final})
                log_event(
                    "react_complete",
                    {
                        "run_id": run_id,
                        "agent": self.name,
                        "steps": step,
                        "attempted_tool_calls": attempted_tool_calls,
                    },
                )
                return ReActResult(final=final, tool_calls=tool_calls)

            raise RuntimeError(f"Invalid ReAct message type: {msg_type}")

        raise RuntimeError(f"{self.name} exceeded max_steps={self.max_steps} without producing a final answer.")
