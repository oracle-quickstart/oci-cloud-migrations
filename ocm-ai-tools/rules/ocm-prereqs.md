---
name: ocm-prereqs
description: Route Oracle Cloud Migrations prerequisite requests to read-only validation or mutation-gated onboarding
metadata:
  owner: ocm
  last_updated: 2026-07-20
---

## Scope

- Apply when a customer asks about OCM readiness, prerequisite failures, prerequisite stack creation, or prerequisite remediation.

## Requirements

- Capture the migration scenario and migration root compartment before evaluating resources.
- Start with `migration-prereqs-validate` unless the customer explicitly requests setup or remediation.
- Invoke `migration-prereqs` for the six-bar validation model and exact resource checks.
- Back every readiness status with live OCI evidence; mark inaccessible checks unavailable.
- Never infer readiness from RMS job history alone.
- Invoke `migration-prereqs-onboard` only for setup or remediation.
- Require explicit confirmation before every Resource Manager state change, including stack create/update, PLAN job creation, APPLY, and DESTROY.
- After Bar 6 is green, report that prerequisites are ready and stop; do not start discovery, planning, or migration execution.

## Required bars

| Scenario | Bars |
|----------|------|
| VMware to OCI | 1, 2, 3, 4, 5, 6 |
| AWS to OCI | 1, 2, 3, 4, 5, 6 |
| VMware to OLVM | 1, 2, 3, 4, 6 |

## Verify

- Validation used only read operations.
- Bar 4 was required for every scenario; only Bar 5 was omitted for VMware to OLVM.
- No downstream migration work started before Bar 6 was green.
