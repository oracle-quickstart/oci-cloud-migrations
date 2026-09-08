# Prerequisite Stack Version Compatibility

Load this reference before assigning version status or configuring an RMS stack.

## Current baseline

- Current release: `2.4`.
- Minimum compatible resource and variable model: `2.3`.
- Read the exact deployed version from `CloudMigrations.PrerequisiteVersion` on stack-created resources. Variables identify a model family, not an exact release.

## Compatibility table

| Observed version | Handling |
|---|---|
| `2.4` | Current. Validate all required bars from live resource evidence. |
| `2.3` | Compatible six-bar and variable model. When either logging toggle is enabled, verify the cross-tenancy logging statements resolve to the correct service tenancy for the customer's realm. |
| Earlier than `2.3` | Legacy model. Mark the identity foundation yellow and guide the customer to update the stack source and variables. |
| Later than `2.4`, conflicting, or unreadable | Unverified. Report the observed value, validate resources without guessing, and do not claim current-version compatibility. |

## Stable v2.3+ model

- Ten `CloudMigrations` tag definitions: version, resource level, three scenario tags, and five metering tags.
- Primary scenario variable `enabled_migration_scenario` plus `add_*` toggles.
- Primary/secondary ownership through `primary_prerequisite_stack`.
- Consolidated tenancy- and compartment-level policy names.
- KMS vault and key required for all scenarios; no KMS opt-out.
- Replication bucket required only for VMware-to-OCI and AWS-to-OCI.

## v2.4 delta

- `ocm-service-tenancy-ocid` and `ocb-service-tenancy-ocid` are optional overrides with empty defaults.
- The stack resolves service tenancy values for the customer's realm when optional agent logging is enabled.
- Leave overrides empty unless Oracle provides a realm-specific value. Never copy service tenancy OCIDs into this pack or customer output.

## Unaccounted-for versions

When `CloudMigrations.PrerequisiteVersion` is newer than `2.4`, conflicts with another observed value, or cannot be read:

- Report the exact observed value and evidence source.
- Mark compatibility as `unverified`; do not claim current-version compatibility.
- Continue checks supported by live resource evidence.
- Do not infer behavior from tag counts, variable names, or historical stack jobs.
- Do not recommend an upgrade solely from this table. Follow the newer release's documented upgrade guidance and review a successful PLAN before APPLY.
- If the resource or evidence model differs, stop at the prerequisite boundary and state that version-specific compatibility is unverified.
