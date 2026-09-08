# Bar 1: Identity Foundation

**Purpose:** The tenancy is tagged and identifiable to OCM services.

**Dependencies:** None — this is the foundation bar.

**Required for:** All scenarios (VMware to OCI, AWS to OCI, VMware to OLVM).

## Resources

| Resource | Type | Location | Expected state |
|----------|------|----------|---------------|
| `CloudMigrations` | Tag namespace | Tenancy root compartment | ACTIVE |
| `PrerequisiteVersion` | Tag definition | In `CloudMigrations` namespace | Compatible value from `references/version-compatibility.md` |
| `PrerequisiteResourceLevel` | Tag definition | In `CloudMigrations` namespace | Enum: `tenancy`, `compartment` |
| `PrerequisiteForVMware` | Tag definition | In `CloudMigrations` namespace | Boolean tag |
| `PrerequisiteForAWS` | Tag definition | In `CloudMigrations` namespace | Boolean tag |
| `PrerequisiteForOLVM` | Tag definition | In `CloudMigrations` namespace | Boolean tag |
| `SourceEnvironmentType` | Tag definition | In `CloudMigrations` namespace | Metering tag |
| `SourceEnvironmentId` | Tag definition | In `CloudMigrations` namespace | Metering tag |
| `SourceAssetId` | Tag definition | In `CloudMigrations` namespace | Metering tag |
| `MigrationProject` | Tag definition | In `CloudMigrations` namespace | Metering tag |
| `ServiceUse` | Tag definition | In `CloudMigrations` namespace | Metering tag |

The metering tags are used by OCM service instrumentation. Their presence supports the v2.3+ identity shape; it does not prove the rest of the stack applied or that the tenancy is ready. A missing metering tag indicates an older or partial identity setup.

The Terraform waits 70 seconds after tag creation for IAM propagation. Do not treat that timer as readiness evidence; re-read the namespace and tag definitions and use their live state.

## Validation

**Step 1:** List tag namespaces in the tenancy root compartment.
```
Client: oci.identity.IdentityClient
Method: list_tag_namespaces
Parameters:
  compartment_id: <tenancy_root_ocid>
```
Look for a namespace with `name` = `CloudMigrations` and `lifecycle_state` = `ACTIVE`.

**Step 2:** If namespace found, list tag definitions within it.
```
Client: oci.identity.IdentityClient
Method: list_tags
Parameters:
  tag_namespace_id: <CloudMigrations_namespace_ocid>
```
Check for the presence of `PrerequisiteVersion`, `PrerequisiteResourceLevel`, and scenario tags.

**Step 3:** Determine the stack version. The `PrerequisiteVersion` tag definition exists as a namespace entry, but its value is applied as a defined tag on resources created by the stack. To check version:
- If compartments exist (Bar 2), read their `defined_tags` for `CloudMigrations.PrerequisiteVersion`
- If no compartments exist, count and identify tag definitions to infer version:
  - v2.1 tags (4-5): `PrerequisiteVersion`, `PrerequisiteResourceLevel`, `PrerequisiteForVMware`, `PrerequisiteForAWS` (some v2.1 deploys may also include a 5th tag depending on Terraform version)
  - v2.3+ tags (10): `PrerequisiteVersion`, `PrerequisiteResourceLevel`, `PrerequisiteForVMware`, `PrerequisiteForAWS`, `PrerequisiteForOLVM`, plus 5 metering tags (`SourceEnvironmentType`, `SourceEnvironmentId`, `SourceAssetId`, `MigrationProject`, `ServiceUse`)

Load `references/version-compatibility.md` and classify the observed value. Do not infer an exact release from the tag-definition count or stack variables.

## Status criteria

| Status | Condition |
|--------|-----------|
| Green | Namespace exists, ACTIVE, all 10 tags present (5 prerequisite + 5 metering), and the observed version is compatible per `version-compatibility.md` |
| Yellow | Namespace exists and readable evidence proves the version is legacy, version tags conflict, or the tag set is partial |
| Red | Namespace does not exist or is not ACTIVE |

If namespace or tag-definition coverage is unreadable, use the parent skill's `unavailable` status instead of yellow.

## Common failures

- **Namespace exists but is INACTIVE/DELETING** — someone retired it manually. Customer needs to re-create via RMS stack apply.
- **Legacy version** — guide the customer to update the RMS stack source and review PLAN before APPLY.
- **Newer or conflicting version** — report the observed values and validate resources without guessing; do not claim current-version compatibility.
- **Scenario tags missing** — stack was applied before the scenario tag feature was added. Update + re-apply resolves this.
- **Tags exist but namespace name differs** — customer may have created a custom namespace. OCM services specifically look for `CloudMigrations`. The custom namespace does not satisfy prerequisites.

## What RMS apply fixes

Creates the `CloudMigrations` namespace and all tag definitions if missing. Updates tag definitions if the stack source has a newer version. Does not delete manually-added tags.
