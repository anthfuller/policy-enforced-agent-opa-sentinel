# Control Mapping

This is a lightweight mapping of the prototype to common AI and security control themes.

## F7-LAS alignment

| F7-LAS layer | Prototype alignment |
|---|---|
| L1 Prompt | System prompt requests bounded KQL and JSON-only responses |
| L3 Planner | ReAct loop plans tool use and observations |
| L4 Tools | Executor mediates KQL tool use |
| L5 External Policy | OPA evaluates allow/deny decisions outside the model |
| L6 Sandbox / Containment | Approved tables, limits, and time filters constrain execution |
| L7 Monitoring | Audit and telemetry capture decisions and outcomes |

## OWASP Top 10 for LLM Applications themes

| Risk theme | Prototype control |
|---|---|
| Prompt injection | Treat model output as untrusted and evaluate before execution |
| Excessive agency | Restrict tool use and require policy approval |
| Sensitive information disclosure | Limit approved tables, time scope, and row counts |
| Insecure output handling | Do not execute model output directly |
| Supply chain / component risk | Keep policy external and reviewable |

## MITRE ATLAS themes

| Theme | Prototype relevance |
|---|---|
| AI-enabled action misuse | Tool execution is mediated by policy |
| Data exposure through AI systems | Query boundaries reduce exposure risk |
| Model behavior manipulation | Prompt manipulation does not bypass external policy |

## NIST AI RMF-style functions

| Function | Prototype relevance |
|---|---|
| Govern | External policy defines allowed behavior |
| Map | Threat model documents risks and boundaries |
| Measure | Audit events record policy decisions |
| Manage | PEP/PDP blocks unsafe actions and supports reviewability |
