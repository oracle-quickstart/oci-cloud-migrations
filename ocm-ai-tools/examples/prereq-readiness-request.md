# Example: Prerequisite Readiness Request

Use this shape when asking an AI assistant to validate OCM prerequisite readiness.

```text
I want to validate Oracle Cloud Migrations prerequisites for my tenancy.

Migration scenario: VMware to OCI
Migration root compartment: <compartment name or OCID>
OCI profile: <profile name>

Use the OCM AI tools in this repository. Start with read-only validation only. Report each prerequisite bar as green, yellow, red, or blocked. Back every status with the OCI call or command result used to verify it. If any bar is not green, explain the next step and ask before starting any setup or remediation workflow.
```

Expected response shape:

| Bar | Status | Evidence | Next step |
|-----|--------|----------|-----------|
| 1 Identity Foundation | Green/yellow/red | API, CLI, SDK, or MCP result | Required action or none |
| 2 Compartment Structure | Green/yellow/red | API, CLI, SDK, or MCP result | Required action or none |
| 3 Service Authorization | Green/yellow/red/blocked | API, CLI, SDK, or MCP result | Required action or none |
| 4 Encryption | Green/yellow/red/blocked | API, CLI, SDK, or MCP result | Required action or none |
| 5 Storage | Green/yellow/red/blocked/not required | API, CLI, SDK, or MCP result | Required action or none |
| 6 End-to-End Ready | Green/yellow/red | Composite of required bars | Proceed or remediate |
