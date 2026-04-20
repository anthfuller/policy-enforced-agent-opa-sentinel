# Policy-Enforced AI Agent for Microsoft Sentinel  
**ReAct + Open Policy Agent (OPA) + Code-Based PEP + Audit Telemetry**

## Overview

This repository demonstrates a **policy-enforced AI agent pattern** for Microsoft Sentinel.

The main idea is straightforward:

> **LLM-generated KQL is untrusted and must be externally governed before execution.**

Instead of allowing the model to directly query security data, this prototype places a **code-based Policy Enforcement Point (PEP)** between the agent and the execution layer. That PEP sends execution context to an external **Policy Decision Point (PDP)** implemented with **Open Policy Agent (OPA)**. Only approved queries are allowed to reach Microsoft Sentinel / Log Analytics.

This design shows a practical security pattern for AI-assisted security operations:

- the **LLM generates** investigative KQL
- the **PEP intercepts and mediates** execution
- the **PDP evaluates policy**
- **Sentinel executes only approved queries**
- **audit and telemetry** record what happened

---

## What This Repository Demonstrates

This prototype is meant to show a control pattern, not just an architecture concept.

It demonstrates that:

- **LLM output is not a trust boundary**
- generated KQL should be treated as **untrusted output**
- **policy must live outside the model**
- tool use should be **mediated, evaluated, and auditable**
- security controls should govern **execution**, not just prompting

---

## Architecture

```text
User Prompt / External Content
           ↓
     ReAct LLM Agent
           ↓
   Code-Based PEP
           ↓
      OPA as PDP
           ↓
Microsoft Sentinel / Log Analytics
           ↓
    Audit + Telemetry
```

### Control Model

- **LLM Agent**: proposes KQL based on the investigation goal
- **PEP**: intercepts every tool request before execution
- **PDP (OPA)**: evaluates the request and returns **ALLOW** or **DENY**
- **Sentinel**: executes only policy-approved KQL
- **Telemetry / Audit**: captures decisions, tool usage, and outcomes

---

## Repository Structure

```text
policy-enforced-ai-agent-react-opa-sentinel/
├── app/
│   ├── agents/
│   │   ├── react/
│   │   │   └── react_agent.py
│   │   └── soc/
│   │       └── react_soc_agent.py
│   ├── llm/
│   │   └── azure_openai_client.py
│   ├── mcp/
│   │   ├── executor.py
│   │   └── tools.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   ├── pdp/
│   │   └── pdp.py
│   └── telemetry/
│       ├── audit.py
│       └── logger.py
├── main.py
├── README.md
├── LICENSE
└── supporting files/directories as applicable
```

---

## Key Components

### `app/agents/react/react_agent.py`
Implements the autonomous ReAct loop.

Key characteristics:
- forces at least one tool attempt before finalization
- treats model output as untrusted
- records thought/final events to audit telemetry
- supports iterative `Thought -> Action -> Observation -> Final` behavior

### `app/agents/soc/react_soc_agent.py`
Wraps the ReAct pattern for a SOC investigation scenario.

It applies:
- Sentinel-focused prompting
- bounded table access expectations
- time-bounded query requirements
- evidence-oriented output for analyst use

### `app/llm/azure_openai_client.py`
Creates the Azure OpenAI client and enforces JSON-formatted model responses.

### `app/mcp/executor.py`
Acts as the effective **Policy Enforcement Point (PEP)**.

Responsibilities include:
- intercepting tool execution requests
- deriving table/query context
- ensuring limits are applied
- calling the PDP for allow/deny evaluation
- executing KQL only when policy allows
- writing audit events for both denied and executed actions

### `app/mcp/tools.py`
Builds tool-driven KQL from contract definitions.

This module expects supporting contract files, including a tool contract JSON file.

### `app/pdp/pdp.py`
Acts as the **Policy Decision Point (PDP)** by sending evaluation requests to OPA.

It returns:
- `ALLOW` when policy approves the action
- `DENY` when policy blocks the action
- `DENY` on OPA failure, which is the safer default

### `app/telemetry/audit.py`
Writes structured audit records to a JSONL audit log.

### `app/telemetry/logger.py`
Emits structured telemetry/logging events for runtime visibility.

### `app/orchestrator/orchestrator.py`
Contains a broader orchestration pattern for planning, evidence gathering, validation, and correlation.

---

## Security Pattern

This repository centers on a simple but important rule:

> **The model can propose. The system decides.**

That separation matters because prompt instructions alone are not enforcement.

A useful AI security pattern is:

1. Let the model generate candidate actions or queries
2. Treat those outputs as untrusted
3. Intercept every execution attempt
4. Evaluate policy externally
5. Allow only constrained, auditable actions

---

## Example Enforcement Logic

### Unsafe Query Example
```kql
SigninLogs
| summarize count()
```

Why this is unsafe:
- no bounded time filter
- can become overly broad depending on table size

### Safer Query Example
```kql
SigninLogs
| where TimeGenerated > ago(7d)
| take 100
```

Why this is safer:
- bounded by time
- bounded by result size
- easier to evaluate against policy

---

## Alignment to F7-LAS Concepts

This prototype aligns with several core control ideas:

### Layer 4 — Tool Mediation
The model does not directly query Sentinel. Tool use is mediated by code.

### Layer 5 — External Policy Enforcement
OPA acts as an external decision point. Policy is outside the model.

### Layer 7 — Telemetry and Audit
Allow/deny decisions and execution outcomes are logged for traceability.

This repository is focused on **control, mediation, and observability**, not on claiming the model itself is secure.

---

## Prerequisites

Typical prerequisites include:

- Python 3.10+
- Azure OpenAI deployment
- Microsoft Sentinel / Log Analytics workspace
- Open Policy Agent (OPA)
- Azure identity and monitor query dependencies

---

## Environment Variables

Set the required Azure OpenAI and Sentinel variables before running:

```bash
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_API_VERSION=2024-05-01-preview
AZURE_OPENAI_DEPLOYMENT=<deployment-name>
LOGS_WORKSPACE_ID=<workspace-id>
```

Depending on your environment, equivalent workspace variable names may also be supported by the code.

---

## How to Run

### 1. Start OPA (PDP)
OPA runs locally on the laptop for this demo.

```bash
cd C:\opa
opa version
opa run --server policy.rego
```

Expected behavior:

```text
Listening on localhost:8181
```

If your policy entrypoint is configured as shown in the code, PDP evaluation is expected at:

```text
http://localhost:8181/v1/data/sentinel/allow
```

### 2. Run the Agent

```bash
cd C:\Users\Anthony\Downloads\policy-enforced-ai-agent-react-opa-sentinel
python main.py
```

### What the Demo Does

- ReAct agent generates KQL
- PEP (`executor.py`) intercepts the request
- PDP (OPA) evaluates the request
- `ALLOW` → Sentinel query runs
- `DENY` → blocked and audited

### Optional Demo Clarity
For a cleaner live demo, you can show both outcomes:

- one compliant KQL path that is allowed
- one unsafe KQL path that is denied
- the resulting audit / telemetry output

---

## Expected Runtime Behavior

A normal run should look like this:

1. user request is sent to the ReAct agent
2. agent proposes a KQL tool action
3. executor intercepts the request
4. context is sent to OPA
5. OPA returns **ALLOW** or **DENY**
6. approved queries execute against Sentinel
7. telemetry and audit logs capture the decision and outcome
8. the agent returns a final result based on observations

---

## Current State of the Repository

This repository is best described as a **working prototype demonstrating an external policy-enforcement pattern**.

It already shows the key security control idea well:
- ReAct-style generation
- execution mediation
- external policy decisioning
- Sentinel query path
- telemetry and audit logging

At the same time, some supporting assets may still need alignment depending on the version of the repo, such as:
- policy files
- contract files
- runtime folders
- any older orchestration imports or modules

That means this repo should be presented honestly as a **prototype demonstrating an enforcement pattern**, not as a finished production platform.

---

## Recommended Next Improvements

To make the repository stronger for technical reviewers, consider adding or tightening:

- explicit `requirements.txt`
- included `contracts/` assets
- included `policy/` files
- a minimal runnable end-to-end demo scenario
- one blocked KQL example and one allowed KQL example with sample output
- a short architecture image that precisely labels:
  - LLM Agent
  - PEP
  - PDP
  - Sentinel
  - Audit/Telemetry

---

## Why This Matters

Many AI security discussions stop at prompting, guardrails, or model behavior.

This repository focuses on something more operational:

> **external enforcement of model-generated actions**

That matters because when AI starts touching security data, detections, or downstream tools, the real control boundary should be outside the model.

---

## Disclaimer

This repository is a **prototype / demo implementation** intended to illustrate a security architecture pattern.

It is **not** a production-ready security product.

---

## Summary

This project shows a practical pattern for:

- AI-assisted security investigations
- external policy enforcement
- policy-mediated KQL execution
- auditable control of LLM-generated actions

In plain terms:

> **The model is not the control plane. Policy is.**
