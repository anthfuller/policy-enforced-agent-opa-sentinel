# Threat Model

This threat model focuses on AI-assisted security investigation where an LLM can propose KQL queries for Microsoft Sentinel / Log Analytics.

## Assets

- Sentinel / Log Analytics data
- Security incidents and alerts
- Sign-in and identity telemetry
- Cloud activity logs
- KQL execution capability
- Policy decision records
- Audit logs

## Trust assumptions

- LLM-generated output is untrusted
- User prompts and external content may be malicious or manipulated
- Tool execution must be mediated by code
- Policy must be evaluated outside the model
- Policy failure should deny execution by default

## Primary threats

| Threat | Description | Control in prototype |
|---|---|---|
| Prompt injection | A prompt causes the model to generate unsafe KQL | PEP intercepts every query before execution |
| Overbroad query | Query lacks time or result boundaries | OPA requires time filter and max limit |
| Unauthorized table access | Query targets a disallowed table | OPA checks approved table list |
| Sensitive data exposure | Query retrieves too much security data | Limit and table constraints reduce blast radius |
| Tool abuse | Model tries to use unsupported tools | ReAct agent and executor restrict tool paths |
| Policy bypass | Model attempts unsafe KQL syntax or patterns | OPA blocks dangerous patterns |
| Missing audit trail | Actions occur without reviewability | Audit log records decisions and outcomes |
| PDP failure | OPA is unavailable or returns an error | PDP fails closed with DENY |

## Out of scope

This prototype does not fully implement:

- production identity hardening
- complete KQL parsing
- tenant isolation
- policy lifecycle approval workflow
- advanced data-loss prevention
- full model evaluation pipeline
- enterprise monitoring and alerting

## Design principle

The model is never treated as the control plane. Policy enforcement occurs outside the model at the execution boundary.
