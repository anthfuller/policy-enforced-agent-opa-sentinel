from app.agents.react.react_agent import ReActAgent

def main():
    agent = ReActAgent(
        name="SentinelAgent",

system_prompt=(
    "You are a security investigation agent.\n"
    "All KQL queries MUST include a TimeGenerated filter such as | where TimeGenerated > ago(7d).\n"
    "Return JSON only.\n"
    "Every response MUST include a top-level key named 'type'.\n"
    "\n"
    "Valid responses:\n"
    "\n"
    "TO USE TOOL:\n"
    "{"
    "\"type\":\"tool\","
    "\"tool\":{"
    "\"name\":\"kql_query\","
    "\"args\":{"
    "\"query\":\"<KQL>\","
    "\"timespan\":\"P7D\","
    "\"max_limit\":100"
    "}"
    "}"
    "}\n"
    "\n"
    "TO FINISH:\n"
    "{"
    "\"type\":\"final\","
    "\"final\":{"
    "\"summary\":\"<short summary>\""
    "}"
    "}\n"
    "\n"
    "No markdown. No explanations."
)
    )

    prompt = (
        "Collect baseline data from SecurityIncident, SecurityAlert, "
        "SigninLogs, and AzureActivity for the last 7 days, then summarize findings."
    )

    result = agent.run(
        user_request=prompt,
        run_id="react-test-001",
    )

    print("\n=== FINAL RESULT ===")
    print(result)


if __name__ == "__main__":
    main()