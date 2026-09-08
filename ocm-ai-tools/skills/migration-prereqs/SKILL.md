---
name: migration-prereqs
description: Use when a customer asks whether an OCI tenancy is ready for Oracle Cloud Migrations, reports a prerequisite failure, requests prerequisite setup or remediation, or refreshes a readiness handoff after its migration root or scenario changes. Do not use for modifying the prerequisite Terraform source or for downstream migration execution.
metadata:
  owner: ocm
  last_updated: 2026-07-23
  audience: customers, operators
---

## When to use

- Validate whether the required OCM resources exist and are usable.
- Diagnose a yellow, red, blocked, or unavailable prerequisite bar.
- Guide RMS prerequisite stack creation or remediation through `migration-prereqs-onboard`.

## When not to use

- Do not modify the prerequisite Terraform source.
- Do not perform discovery, planning, replication, or migration execution.
- Do not treat a successful historical RMS job as current readiness evidence.

## Operating posture

- Use `validate` mode by default. Keep it read-only.
- Enter `onboard` mode only when the customer explicitly requests setup or remediation; use `migration-prereqs-onboard` when the workflow is installed.
- Treat setup intent as permission to prepare a proposal, not as approval for any Resource Manager mutation.
- Capture migration scenario and root compartment before evaluating resources.
- Back every status with OCI API, CLI, SDK, or MCP evidence.
- Mark a check `unavailable` when permission or coverage prevents evaluation; never convert unavailable evidence to green.
- Route resource creation and remediation through the RMS stack; do not create prerequisite resources through ad hoc APIs.
- Require explicit confirmation before stack create/update, PLAN job creation, APPLY, and DESTROY.

When installed as a standalone Agent Skill, execute the validation model and mutation contract in this file directly. When the pack workflows are available, use `migration-prereqs-validate` and `migration-prereqs-onboard` as entry points; they enforce the same contracts.

## Requirement basis

Label a claim when its authority is disputed, unexpected, or determines a remediation decision:

- `Product/API requirement`: behavior required by current public OCI product documentation or API contracts.
- `Published prerequisite-stack contract`: behavior of the current published prerequisite Terraform source or schema.
- `Observed service behavior`: current tenancy state, API responses, detector coverage, RMS jobs, or job logs.
- `OCM policy`: this skill's safety, evidence, and workflow rules.

Use these labels verbatim; do not paraphrase or substitute one basis for another.

Do not turn stack behavior or OCM policy into a product requirement. Live resources determine readiness; RMS ownership is not required when manually managed resources satisfy every required check.

## Required context

- OCI access with read permissions for validation and write permissions for approved remediation.
- OCI CLI configured for the target tenancy. The detector and standalone skill require the `oci` executable.
- One primary scenario: `VMware to OCI`, `AWS to OCI`, or `VMware to OLVM`.
- The selected migration root compartment.
- The customer tenancy OCID when the authenticated profile belongs to an operator or delegated-access tenancy.
- When the OCI profile requires them: authentication type, region override, and CA certificate bundle path.

## Transport contract

- Use OCI CLI as the portable baseline. Build one global prefix and use it for every call: `oci --profile <profile> --config-file <config-file> [--auth <auth>] [--region <region>] [--cert-bundle <path>]`.
- Prove access with a real read before evaluating bars. For a tenancy-root target, call `iam tenancy get --tenancy-id <root-ocid>`; for a compartment target, call `iam compartment get --compartment-id <root-ocid>`.
- Stop and report the exact failed operation when the preflight fails. A command catalog or method-list response does not prove authentication or authorization.
- Run `scripts/find_primary_prereq_stack.py --verify --scenario <scenario> --root-compartment-ocid <ocid> --json` with OCI CLI in every transport mode. Add `--stack-compartment-ocid <ocid>` for each known RMS stack location and `--replication-bucket-name <name>` when no readable stack supplies the configured name.
- Treat `verification.decision` as the readiness verdict. Explain its evidence and next action; never upgrade `not_ready` or `unknown` to `ready`.
- Use OCI MCP tooling only for follow-up diagnostics or corroboration. Neither an API invocation nor method discovery replaces the verifier or changes its verdict.

## Validation model

The deterministic verifier validates the bars in dependency order:

1. Read live identity evidence and classify Bar 1 against `references/version-compatibility.md` and `bars/identity-foundation.md`.
2. Read the selected root's live child compartments and classify Bar 2 from `bars/compartment-structure.md`.
3. Block checks whose required compartment is absent; do not infer the contained resource state.
4. Read dynamic groups and policies and classify Bar 3 by matching-rule and policy content, not policy names alone.
5. Read the vault and key and classify Bar 4 for every scenario.
6. Resolve the configured replication bucket, read it, and classify Bar 5 for VMware-to-OCI and AWS-to-OCI; use `not_required` for VMware-to-OLVM.
7. Compute Bar 6 from the required bar statuses.

Use the linked bar modules to explain a result or remediation. Do not independently recompute a different status from the same evidence.

## Scenario matrix

| Scenario | Required bars | Primary value | Additive toggle |
|----------|---------------|---------------|-----------------|
| VMware to OCI | 1, 2, 3, 4, 5, 6 | `enabled_migration_scenario = "VMware to OCI"` | `add_vmware_to_oci` |
| AWS to OCI | 1, 2, 3, 4, 5, 6 | `enabled_migration_scenario = "AWS to OCI"` | `add_aws_to_oci` |
| VMware to OLVM | 1, 2, 3, 4, 6 | `enabled_migration_scenario = "VMware to OLVM"` | `add_vmware_to_olvm` |

Use `enabled_migration_scenario` for the primary scenario. Use `add_*` only for additional scenarios on the same stack.

## Status contract

- `green`: every required check passed with live evidence.
- `yellow`: resources exist but are partial, stale, or misconfigured.
- `red`: required resources are confirmed missing or failed.
- `blocked`: a failed dependency prevents the check.
- `unavailable`: permissions, authentication, or incomplete scan coverage prevented the check.
- `not_required`: use only for Bar 5 with VMware-to-OLVM.

Use `yellow` only when observed evidence proves a partial, stale, or misconfigured state. If any required sub-check cannot be read, mark the bar `unavailable` even when earlier sub-checks passed; do not infer the unread state.

Bar 6 is green only when every required bar is green. Any proven required red or blocked bar makes the decision `not_ready`, even when another required bar is unavailable. Otherwise, any unavailable required bar makes the decision `unknown`.

## RMS evidence

- Use `scripts/find_primary_prereq_stack.py --verify --scenario <scenario> --root-compartment-ocid <ocid> --json` after the customer selects a root.
- When the RMS stack is stored outside the selected migration root and its compartment is known, add `--stack-compartment-ocid <stack-compartment-ocid>`. Repeat the option for multiple known locations.
- Use `--scan-all-compartments` only when the stack location is unknown and tenancy-wide accessible RMS discovery is needed.
- When the profile tenancy differs from the customer tenancy, add `--tenancy-ocid <customer-tenancy-ocid>`; never substitute the profile tenancy for the customer target.
- For session-authenticated profiles, add `--auth security_token`; for a region override, add `--region <region>`; for a private realm CA, add `--cert-bundle <path>`.
- Preserve detector warnings, `coverage_complete`, `requested_scan_complete`, and `coverage_limitations` in the assessment.
- Fetch the latest job for each candidate stack.
- Present the latest operation, state, and timestamp before historical context.
- When `primary.latest_job_state` is `FAILED`, fetch logs with `primary.latest_job_id` and quote the first concrete error. If the ID is absent, report job-log evidence as unavailable. Do not turn that observation into a broader root cause unless independent live evidence confirms it; otherwise state that the cause is unconfirmed.
- Use `verification.bars` as the live-resource assessment; RMS status corroborates but does not replace its bar evidence.
- Treat detector `variable_model` as a family signal. Use `prereq_version` only when it came from resource defined tags.

## Mutation contract

- Present a gate with these fields: `MUTATION`, `Target`, `Action`, `Expected outcome`, `Plan or changes`, and `Cleanup or rollback`.
- Name the exact Resource Manager API operation and job operation; never use a generic approval request.
- Wait for explicit confirmation immediately before stack create/update plus PLAN.
- Present the completed plan before requesting separate APPLY confirmation.
- Describe DESTROY as a cleanup attempt, not guaranteed rollback: KMS deletion is scheduled and non-empty or manually managed resources can remain.
- Re-run read-only validation after each approved mutation.

## Output contract

- Use these headings in order: `Mode and Scope`, `Readiness`, `RMS Evidence`, `Decision`, and `Next Action`.
- Under `Mode and Scope`, state the operating mode, scenario, root compartment, and whether real calls were made.
- Under `Readiness`, present Bar 1 through Bar 6 with status, evidence, and next action.
- Under `RMS Evidence`, include detector coverage and the latest RMS job status, or state that neither is available.
- Under `Decision`, render `verification.decision` as `ready`, `not ready`, or `unknown` and identify the deciding reason code. Do not upgrade the verifier's decision.
- When a downstream handoff contract is installed, replace `Next Action` with `Handoff` for a green result.
- Otherwise, use `Next Action` for the single next prerequisite action; on green, report readiness and stop at the prerequisite boundary.

## Verify

- Every required bar has live evidence or an explicit blocked/unavailable reason.
- The rendered bar statuses and decision match `verification.bars` and `verification.decision`.
- Bar 4 is required for all scenarios; Bar 5 alone is scenario-conditional.
- Validation performed no state-changing calls.
- Every Resource Manager mutation was preceded by its own explicit gate.
- A green result reports readiness and stops at the prereq boundary.

## Failure modes

- If OCI access fails, report the failed operation and stop; do not infer resource state.
- If RMS discovery coverage is incomplete, preserve the limitation and do not treat zero candidates as proof of absence; keep the verifier's live-resource decision unchanged.
- If the latest RMS job failed, report its log evidence before proposing remediation.
- If resources were created outside RMS, validate them by behavior and configuration; do not require stack ownership for green status.
