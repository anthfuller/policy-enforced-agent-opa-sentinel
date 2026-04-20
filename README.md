# Sentinel Policy-Enforced ReAct Agent (Demo)

## Overview

## Repository Structure

```text
sentinel-policy-enforced-evidence-main/
├── app/
│   ├── agents/
│   │   └── react/
│   │       └── react_agent.py
│   ├── llm/
│   │   └── azure_openai_client.py
│   ├── mcp/
│   │   ├── executor.py
│   │   └── tools.py
│   ├── pdp/
│   │   └── pdp.py
│   └── telemetry/
│       ├── audit.py
│       └── logger.py
├── contracts/
│   ├── tables_contract.json
│   └── tools_contract.json
├── runs/
├── telemetry/
│   └── audit_log.jsonl
├── main.py
├── README.md
└── requirements.txt

This project demonstrates a **policy-governed AI agent** for Microsoft Sentinel.

It proves that:

> **LLM-generated queries are untrusted and must be governed by external policy before execution.**

## Architecture

```text
User Prompt
   ↓
ReAct Agent (LLM)
   ↓
PEP (executor.py)
   ↓
PDP (OPA)
   ↓
Microsoft Sentinel (KQL)
   ↓
Audit Logs
```

## Key Components

### ReAct Agent
- Generates KQL queries dynamically using Azure OpenAI
- Can adapt strategy across runs

### PEP (Policy Enforcement Point)
- Implemented in `executor.py`
- Intercepts all tool calls
- Sends context to policy engine

### PDP (Policy Decision Point)
- Implemented using **Open Policy Agent (OPA)**
- Evaluates:
  - Table access
  - Query safety (for example, required `TimeGenerated` filter)
  - Limits

### Microsoft Sentinel
- Executes KQL queries only if policy allows

### Telemetry
- Logs all decisions (`ALLOW` / `DENY`)
- Provides audit trail

## Alignment to F7-LAS (Conceptual)

This demo aligns to key principles from the F7-LAS model:

- **Layer 4 (Tool Mediation)**  
  The agent cannot directly execute queries. All tool calls are mediated.

- **Layer 5 (Policy Enforcement - PDP/PEP)**  
  Open Policy Agent (OPA) acts as the Policy Decision Point (PDP).  
  The executor functions as a Policy Enforcement Point (PEP).

- **Layer 7 (Telemetry & Audit)**  
  All actions, decisions, and outcomes are logged for traceability.

This implementation focuses on **enforcement and control**, not model intelligence.

## What This Demonstrates

- LLMs do **not inherently follow security constraints**
- Policies must be enforced **outside the model**
- Queries can be:
  - Generated dynamically
  - Evaluated consistently
  - Allowed or denied deterministically

## Prerequisites

- Python 3.10+
- Azure OpenAI deployment
- Microsoft Sentinel workspace
- OPA installed

## Environment Variables

Set the following:

```bash
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>
LOGS_WORKSPACE_ID=<sentinel-workspace-id>
```

## How to Run

### 1. Start OPA (PDP)

```bash
cd C:\opa
opa run --server policy.rego
```

OPA will listen on:

```text
http://localhost:8181
```

### 2. Run the Agent

```bash
cd C:\Users\Anthony\Downloads\sentinel-policy-enforced-evidence-main
python main.py
```

## Expected Behavior

- Agent generates KQL queries
- PEP intercepts requests
- PDP evaluates policy
- Queries are:
  - **Allowed** if compliant
  - **Denied** if unsafe

## Example Policy Enforcement

### DENY (no time filter)

```kql
SigninLogs
| summarize count()
```

### ALLOW (time bounded)

```kql
SigninLogs
| where TimeGenerated > ago(7d)
```

## Security Model

| Component | Responsibility |
|----------|----------------|
| LLM | Generate queries |
| PEP | Enforce execution control |
| PDP (OPA) | Decide allow/deny |
| Sentinel | Execute only approved queries |

## Key Insight

> **The model is not trusted. The system enforces trust.**

## Future Enhancements

- Identity-aware policies (Entra ID integration)
- Field-level redaction
- Tool-level authorization
- AI Gateway integration
- Advanced threat scenarios

## Disclaimer

This is a **demo architecture**, not a production system.

## Summary

This project shows a **real, working pattern** for:

- Agentic AI
- External policy enforcement
- Secure query execution
