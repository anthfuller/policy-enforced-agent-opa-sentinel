package sentinel

# Default-deny policy for policy-mediated KQL execution.
default allow := false

approved_tables := {
  "SecurityIncident",
  "SecurityAlert",
  "SigninLogs",
  "AzureActivity"
}

blocked_patterns := [
  "externaldata",
  "invoke",
  "evaluate",
  ".export",
  "set query_datascope",
  "search *"
]

allow if {
  startswith(input.action, "kql.read.")
  input.table in approved_tables
  input.has_time_filter == true
  input.limit <= 500
  not contains_blocked_pattern(lower(input.query))
}

contains_blocked_pattern(query) if {
  some pattern in blocked_patterns
  contains(query, pattern)
}
