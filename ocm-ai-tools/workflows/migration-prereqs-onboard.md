---
name: migration-prereqs-onboard
description: Guide OCM prerequisite creation or remediation through Resource Manager with a gate before every state-changing operation.
metadata:
  owner: ocm
  last_updated: 2026-07-21
---

## Entry conditions

- The customer explicitly requested prerequisite setup or remediation.
- OCI access permits the requested Resource Manager operations.
- Production mutations require the customer's own change-control process; this workflow does not waive it.

## Inputs

- A fresh `migration-prereqs-validate` assessment or enough context to run one.
- Primary and additive migration scenarios.
- Migration root compartment.
- Existing stack OCID for remediation, if present.

## Steps

1. Invoke `migration-prereqs-validate` when no fresh assessment was handed off.
2. If Bar 6 is green, report that prerequisites are ready and stop without mutation.
3. Ask whether the customer will use the RMS prerequisite stack or their own infrastructure process.
4. If the customer selects self-managed creation, present exact requirements from the non-green bar modules and stop until the customer reports completion.
5. For the RMS path, load `references/version-compatibility.md`, `references/stack-variables.md`, and `references/rms-guide.md`, then confirm every variable value, including `compartment_ocid`, `enabled_migration_scenario`, `primary_prerequisite_stack`, additive toggles, `create_replication_bucket`, `replication_bucket`, `migration_groups`, logging toggles, and any explicitly provided service-tenancy override.
6. State that the current stack exposes no KMS opt-out; declining KMS leaves Bar 4 red and ends the RMS path.
7. Determine the preparation operation: `create_stack` plus PLAN for a fresh start, or `update_stack` plus PLAN for remediation.
8. Present a `MUTATION` gate with `Target`, `Action`, `Expected outcome`, `Plan or changes`, and `Cleanup or rollback`, naming the stack, compartment, exact preparation operations, confirmed variables, expected Resource Manager records, and cleanup limitations.
9. Wait for explicit confirmation of that preparation mutation; the earlier request to set up prerequisites is not confirmation for this gate.
10. After confirmation, execute the exact CLI or MCP stack create/update operation from `references/rms-guide.md` with the confirmed source and variables.
11. Execute the exact CLI or MCP PLAN operation from `references/rms-guide.md` for the resulting stack.
12. Poll the PLAN with the mapped CLI or MCP get-job operation until it is `SUCCEEDED` or `FAILED`.
13. If PLAN failed, fetch `get_job_logs`, report the first concrete error, and stop.
14. Fetch and present the completed plan, including every create, update, replace, and delete action.
15. Present a separate `MUTATION` gate with `Target`, `Action`, `Expected outcome`, `Plan or changes`, and `Cleanup or rollback`, naming the stack, APPLY action, reviewed PLAN job, affected resources and compartments, expected result, and cleanup limitations.
16. Wait for explicit APPLY confirmation; preparation confirmation does not authorize APPLY.
17. After confirmation, execute the exact CLI or MCP APPLY operation from `references/rms-guide.md` with the reviewed PLAN job ID.
18. Poll APPLY with the mapped CLI or MCP get-job operation until it is `SUCCEEDED` or `FAILED`.
19. If APPLY failed, fetch `get_job_logs`, report the first concrete error, and stop before proposing another mutation.
20. Invoke `migration-prereqs-validate` with fresh API calls.
21. If Bar 6 is green, report that prerequisites are ready and stop at the prereq boundary.
22. If any required bar remains non-green, report the remaining evidence and wait for the customer to choose the next remediation action.

## Mutation gate format

- Label: `MUTATION`.
- Target: exact RMS stack and compartment.
- Action: exact API operation and job operation.
- Expected outcome: Resource Manager records for preparation; listed OCI resources for APPLY.
- Plan or changes: complete confirmed variables for preparation; every reviewed create, update, replace, and delete for APPLY.
- Cleanup or rollback: DESTROY is a separate mutation and only a cleanup attempt; KMS deletion is scheduled, and non-empty or manually managed resources can remain.
- Approval: require an explicit response to this gate immediately before execution.

## Verify

- Each `create_stack`, `update_stack`, PLAN, APPLY, or DESTROY call has a preceding explicit gate in the execution record.
- APPLY references the reviewed PLAN job.
- No prerequisite resources were created through ad hoc service API calls.
- Final status comes from fresh validation, not APPLY state alone.

## Exit criteria

- Bar 6 is green and readiness was reported; or
- The workflow stopped with evidence, no unapproved mutation, and a customer-owned next decision.
