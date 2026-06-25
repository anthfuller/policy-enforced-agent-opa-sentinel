# Architecture

This prototype demonstrates a policy-enforced AI agent pattern for Microsoft Sentinel / Log Analytics.

## Control flow

```text
1. User asks for a security investigation
2. ReAct agent proposes a KQL tool call
3. PEP intercepts the tool call before execution
4. PEP extracts table, limit, query, and time-filter context
5. PDP evaluates the request through OPA
6. Policy returns ALLOW or DENY
7. Allowed requests execute against Sentinel / Log Analytics
8. Denied requests are blocked and audited
9. Audit and telemetry records preserve the decision trail
```

## Key boundaries

### Model boundary

The model can propose a query, but its output is not trusted. The model is not the enforcement point.

### Tool boundary

The PEP mediates all tool use. It decides whether a proposed action can proceed based on policy output.

### Policy boundary

OPA evaluates policy outside the model. This keeps governance separate from prompting and model behavior.

### Data boundary

Microsoft Sentinel / Log Analytics is only reached after policy evaluation. Broad or unsafe KQL is blocked before execution.

## Why this matters

Prompt-only guardrails are not enough when AI systems can call tools or access security data. Enforcement must happen at the execution boundary.

This pattern supports:

- bounded KQL execution
- fail-closed policy behavior
- auditable tool use
- separation of model reasoning and policy enforcement
- human-review extension points for higher-risk actions

## Production hardening considerations

This prototype is intentionally small. A production implementation would need:

- managed identity and least-privilege workspace access
- hardened policy lifecycle management
- secure secret handling
- policy testing and CI checks
- centralized logging and monitoring
- strong tenant and customer data boundaries
- human approval for high-risk actions
- change control around allowed tools and tables
