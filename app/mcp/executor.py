from __future__ import annotations

import os
import re
from datetime import timedelta
from typing import Any, Dict, Optional, List

from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient

from app.mcp.tools import build_query
from app.pdp.pdp import evaluate
from app.telemetry.audit import write_audit
from app.telemetry.logger import log_event


_TABLE_TOKEN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(\||$)")
_LIMIT_RE = re.compile(r"\|\s*(take|limit)\s+\d+\b", re.IGNORECASE)
_TIMEFILTER_HINT_RE = re.compile(r"\b(TimeGenerated|timestamp)\b.*\bago\(", re.IGNORECASE)


def _infer_table(query: str) -> str:
    q = query.strip()
    if q.lower().startswith("search"):
        return "TableDiscovery"

    if q.lower().startswith("union"):
        m = re.search(r"union\s+([^|]+)", q, re.IGNORECASE)
        if m:
            first = m.group(1).strip().split(",")[0].strip()
            first = re.split(r"\s", first)[0]
            return re.sub(r"[^A-Za-z0-9_]", "", first) or "Unknown"
        return "Unknown"

    m = _TABLE_TOKEN_RE.match(q)
    return m.group(1) if m else "Unknown"


def _ensure_limit(query: str, max_limit: int) -> str:
    if _LIMIT_RE.search(query):
        return query
    return f"{query}\n| take {max_limit}"


def _timespan_from_args(args: Dict[str, Any]) -> timedelta:
    ts = (args.get("timespan") or args.get("time_range") or "P1D").strip()
    m = re.fullmatch(r"P(\d+)D", ts, re.IGNORECASE)
    if m:
        return timedelta(days=int(m.group(1)))
    m = re.fullmatch(r"PT(\d+)H", ts, re.IGNORECASE)
    if m:
        return timedelta(hours=int(m.group(1)))
    return timedelta(days=1)


def _get_workspace_id() -> str:
    workspace_id = (
        os.environ.get("LOGS_WORKSPACE_ID")
        or os.environ.get("WORKSPACE_ID")
        or os.environ.get("SENTINEL_WORKSPACE_ID")
    )
    if not workspace_id:
        raise RuntimeError(
            "Missing LOGS_WORKSPACE_ID (or WORKSPACE_ID or SENTINEL_WORKSPACE_ID) environment variable"
        )
    return workspace_id


def _extract_columns(table) -> List[str]:
    cols = []
    for c in (table.columns or []):
        if hasattr(c, "name"):
            cols.append(c.name)
        else:
            cols.append(str(c))
    return cols


def execute(
    tool_name: str,
    *,
    run_id: str,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    built = build_query(tool_name, params=params)

    action = built["action"]

    decision = evaluate(
        action=action,
        context={
            "limit": built["limit"],
            "has_time_filter": built["has_time_filter"],
            "table": built["table"],
        },
        run_id=run_id,
    )

    if decision["decision"] != "ALLOW":
        write_audit(
            run_id=run_id,
            stage="tool_denied",
            data={"tool": tool_name, "action": action, **decision},
        )
        return {
            "tool": tool_name,
            "action": action,
            "decision": "DENY",
            "reason": decision.get("reason"),
        }

    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    workspace_id = _get_workspace_id()

    result = client.query_workspace(
        workspace_id=workspace_id,
        query=built["query"],
        timespan=_timespan_from_args(params or {}),
    )

    rows: List[List[Any]] = []
    columns: List[str] = []
    rowcount = 0

    if result and result.tables:
        t = result.tables[0]
        columns = _extract_columns(t)
        rows = [list(r) for r in t.rows]
        rowcount = len(rows)

    log_event(
        "mcp_tool_executed",
        {
            "run_id": run_id,
            "tool": tool_name,
            "table": built["table"],
            "rowcount": rowcount,
        },
    )

    write_audit(
        run_id=run_id,
        stage="tool_executed",
        data={
            "tool": tool_name,
            "action": action,
            "table": built["table"],
            "rowcount": rowcount,
        },
    )

    return {
        "tool": tool_name,
        "action": action,
        "decision": "ALLOW",
        "query": built["query"],
        "table": built["table"],
        "rowcount": rowcount,
        "columns": columns,
        "rows": rows,
    }


def execute_tool(*, run_id: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:

    if tool_name != "kql_query":
        return execute(tool_name, run_id=run_id, params=args)

    query = (args.get("query") or "").strip()
    if not query:
        raise ValueError("kql_query requires args.query")

    table = _infer_table(query)
    action = f"kql.read.{table}"

    max_limit = int(args.get("max_limit") or 500)
    query = _ensure_limit(query, max_limit=max_limit)
    has_time_filter = bool(_TIMEFILTER_HINT_RE.search(query))

    decision = evaluate(
        action=action,
        context={
            "limit": max_limit,
            "has_time_filter": has_time_filter,
            "table": table,
            "query": query,
        },
        run_id=run_id,
    )

    if decision["decision"] != "ALLOW":
        write_audit(
            run_id=run_id,
            stage="tool_denied",
            data={
                "tool": tool_name,
                "action": action,
                "table": table,
                "query": query,
                **decision,
            },
        )
        return {
            "tool": tool_name,
            "action": action,
            "table": table,
            "decision": "DENY",
            "reason": decision.get("reason"),
        }

    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    workspace_id = _get_workspace_id()
    timespan = _timespan_from_args(args)

    log_event(
        "kql_query_execute",
        {
            "run_id": run_id,
            "table": table,
            "timespan_hours": timespan.total_seconds() / 3600.0,
        },
    )

    result = client.query_workspace(
        workspace_id=workspace_id,
        query=query,
        timespan=timespan,
    )

    rows: List[List[Any]] = []
    columns: List[str] = []
    rowcount = 0

    if result and result.tables:
        t = result.tables[0]
        columns = _extract_columns(t)
        rows = [list(r) for r in t.rows]
        rowcount = len(rows)

    write_audit(
        run_id=run_id,
        stage="tool_executed",
        data={"tool": tool_name, "action": action, "table": table, "rowcount": rowcount},
    )

    return {
        "tool": tool_name,
        "action": action,
        "decision": "ALLOW",
        "query": query,
        "table": table,
        "rowcount": rowcount,
        "columns": columns,
        "rows": rows,
    }