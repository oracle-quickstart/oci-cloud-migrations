---
name: migration-prereqs-validate
description: Use when a customer needs a read-only assessment of OCM prerequisite readiness from live OCI evidence.
metadata:
  owner: ocm
  last_updated: 2026-08-19
---

## Entry conditions

- OCI CLI access is configured for read operations; OCI MCP tooling is optional.
- The customer can identify or select a migration scenario and migration root compartment.

## Inputs

- Primary scenario: `VMware to OCI`, `AWS to OCI`, or `VMware to OLVM`.
- Optional additive scenarios.
- Migration root compartment name or OCID.
- Optional RMS stack compartment OCID when the stack is stored outside the migration root.
- Configured replication bucket name when no readable current stack supplies it.
- OCI CLI profile and config file when using the detector.
- Customer tenancy OCID when the profile uses operator or delegated access.
- OCI authentication type, region override, and CA certificate bundle path when required by the profile or realm.

## Steps

1. Invoke `migration-prereqs` and use its transport, status, mutation, and output contracts.
2. Collect any missing scenario, additive-scenario, customer-tenancy, root-compartment, OCI profile, config, authentication, region, and CA inputs.
3. Select OCI CLI for the verifier; reserve `invoke_oci_api` for follow-up diagnostics or corroboration using `references/oci-api-reference.md`.
4. Perform the actual tenancy or compartment access preflight required by the skill; stop and report the exact operation if it fails.
5. From the installed `migration-prereqs` skill directory that contains its `SKILL.md`, run `python3 scripts/find_primary_prereq_stack.py --verify --scenario <scenario> --profile <profile> --config-file <config-file> --root-compartment-ocid <root-ocid> --json`; do not resolve `scripts/` relative to this workflow or the user's working directory. Add `--stack-compartment-ocid <ocid>` for each known RMS stack location, `--replication-bucket-name <name>` when required, and the customer-tenancy, authentication, region, and CA arguments required by the skill.
6. Preserve detector warnings and incomplete coverage; never interpret zero candidates as proof that no stack exists when coverage is incomplete.
7. If `primary.latest_job_state` is `FAILED`, fetch logs with the mapped CLI or MCP operation using `primary.latest_job_id` as `--job-id`, then report the first concrete error; if the ID is absent, report job-log evidence as unavailable.
8. Read `verification.bars` and `verification.decision`; load linked bar modules only to explain evidence or the next remediation.
9. Preserve every verifier status and reason code; never independently upgrade `not_ready` or `unknown` to `ready`.
10. Present the skill's five output sections in order with each verifier bar's status, evidence, and next action.
11. Stop at the prerequisite boundary for green; otherwise offer `migration-prereqs-onboard` without invoking it until setup or remediation is explicitly requested.

## Verify

- The operation record contains no `create_*`, `update_*`, `delete_*`, APPLY, PLAN, or DESTROY calls.
- Every required bar has live evidence or an explicit `blocked` or `unavailable` reason.
- The presented decision exactly matches `verification.decision`.
- Every claim whose authority is disputed, unexpected, or determines remediation uses the exact requirement-basis labels from `migration-prereqs`.
- Latest RMS job state is primary; successful history is secondary.
- Bar 4 is required for every scenario; only Bar 5 can be `not_required`.

## Exit criteria

- A bar tracker and ready result were produced for a green assessment.
- A bar tracker and evidence-backed remediation offer were produced for a non-green result.
