# Bar 3: Service Authorization

**Purpose:** OCM migration services can authenticate and act on the customer's behalf.

**Dependencies:** The selected migration root. Missing child compartments do not block IAM inspection, but this bar cannot be green until policy and matching-rule compartment references can be verified against the required children.

**Required for:** All scenarios (VMware to OCI, AWS to OCI, VMware to OLVM).

## Resources

### Dynamic groups (tenancy root)

Dynamic group names are prefixed with `lower(migration_root_compartment_name)`. For example, if the migration root is `cloud-migrations`, the groups are `cloud-migrations-migration-dg`, `cloud-migrations-discovery-dg`, etc. When validating, match the suffix pattern and verify the prefix corresponds to the migration root compartment.

| Resource (suffix) | Matching rule | Scenarios |
|----------|--------------|-----------|
| `{prefix}-migration-dg` | resource.type = `ocmmigration` | All |
| `{prefix}-discovery-dg` | resource.type = `ocbassetsource` | All |
| `{prefix}-remote-agent-and-plugins-dg` | resource.type = `ocbagent` | VMware to OCI, VMware to OLVM |
| `{prefix}-hydration-agent-dg` | All instances in Migration compartment | VMware to OCI, AWS to OCI |

### IAM policies

**Tenancy-level policy (expected name and key statements):**

Policy names also use the `{prefix}` pattern derived from the migration root compartment name. The v2.3+ stack family consolidates service statements into one tenancy-level policy; validate the statement content, not a legacy one-policy-per-service shape.

| Policy name pattern | Key permissions | Dynamic group |
|---|---|---|
| `{prefix}-ocm-tenancy-level-policy` | read `ocb-inventory`, compute/capacity/rate-card/metrics reads, tag namespace reads/uses, optional cross-tenancy log upload | `{prefix}-migration-dg` |
| `{prefix}-ocm-tenancy-level-policy` | read `ocb-inventory`, tenancy inspect | `{prefix}-discovery-dg` |
| `{prefix}-ocm-tenancy-level-policy` | manage `ocb-inventory`, `OCB_AGENT_*` / `OCB_AGENT_DEPENDENCY_*` permissions, optional remote-agent log upload | `{prefix}-remote-agent-and-plugins-dg` |

**Compartment-level policies (in migration root):**

| Policy name pattern | Key permissions | Scoped to |
|---|---|---|
| `{prefix}-ocm-compartment-level-policy` | Compute, network, volume, object storage, image, connector, and inventory permissions | Migration |
| `{prefix}-ocm-compartment-level-policy` | Secret-family read, KMS use, and credential-access permissions | MigrationSecrets |
| `{prefix}-ocm-compartment-level-policy` | Hydration-agent task permissions for migration-to-OCI scenarios | Migration |

**Logging policies (optional, tenancy-level):**

When `remote_agent_logging` or `hydration_agent_logging` is enabled, additional tenancy-level policies allow the corresponding agents to upload logs to OCM service tenancies. These are cross-tenancy log upload permissions — distinct from the base service authorization policies above.

Validation approach: match current-family policies by the `-ocm-tenancy-level-policy` and `-ocm-compartment-level-policy` suffixes, then verify statements reference the correct dynamic groups and compartment OCIDs. The prefix should correspond to `lower(migration_root_compartment_name)`. Policy names may vary between stack versions — the key signal is that statements reference the expected dynamic groups and grant the expected resource-type permissions from the public OCM service-policy docs.

For logging enabled on a v2.3 stack, load `references/version-compatibility.md` and verify that the cross-tenancy statements target the correct service tenancy for the customer's realm. If that cannot be verified, mark this bar yellow.

If logging policies are absent but the customer enabled logging variables, status is yellow (non-critical but recommended).

## Validation

**Step 1:** List dynamic groups at tenancy root.
```
Client: oci.identity.IdentityClient
Method: list_dynamic_groups
Parameters:
  compartment_id: <tenancy_root_ocid>
```
Check for expected dynamic group names and verify `lifecycle_state` = `ACTIVE`. Verify matching rules reference the correct resource types.

**Step 2:** List policies at tenancy root.
```
Client: oci.identity.IdentityClient
Method: list_policies
Parameters:
  compartment_id: <tenancy_root_ocid>
```
Match against expected tenancy-level policy name patterns from the table above. For each found policy, read its statements and verify they reference the expected dynamic groups by name.

**Step 3:** List policies in the migration root compartment.
```
Client: oci.identity.IdentityClient
Method: list_policies
Parameters:
  compartment_id: <migration_root_compartment_ocid>
```
Match against expected compartment-level policy name patterns. Verify statements reference the correct dynamic groups AND the correct Migration/MigrationSecrets compartment OCIDs.

**Step 4:** Cross-check dynamic group matching rules against compartment OCIDs.
For `hydration-agent-dg`, verify the matching rule references the Migration compartment OCID (not a stale or wrong compartment). For `remote-agent-and-plugins-dg`, verify the resource type matches the scenario.

## Status criteria

| Status | Condition |
|--------|-----------|
| Green | All expected dynamic groups exist + ACTIVE, policies at both tenancy and compartment levels present and reference correct groups/compartments |
| Yellow | Dynamic groups exist but policies are incomplete or reference stale group/compartment OCIDs |
| Red | Dynamic groups missing or no OCM-related policies found |

## Common failures

- **Dynamic groups exist but matching rules reference wrong compartment** — stack was applied with a different migration root, then customer changed compartments. Re-apply with correct variables.
- **Policies exist but are stale** — policy statements from an older prereq version may not include permissions required by newer OCM features. Update stack source and re-apply.
- **Manually-created policies conflict** — customer added custom policies that duplicate or contradict stack-managed ones. Safe to have both, but may cause confusion. Note in assessment.
- **Custom IAM (non-stack policies)** — some organizations use centralized IAM rather than the RMS stack. Validate by content, not name:
  - Dynamic groups present with correct matching rules (resource type + compartment OCID) but non-standard names → **green**. Names don't matter; matching rules do.
  - Policy statements grant the required resource-type permissions to the correct dynamic groups but use non-standard policy names → **green**.
  - Policy statements exist but reference wrong compartment OCIDs or wrong dynamic group names → **yellow**. Report the mismatch.
  - Required permissions missing entirely → **red**.
  - Public documentation for required policy statements: VMware — https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-servicepolicies.htm / AWS — https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-servicepolicies-aws.htm

## What RMS apply fixes

Creates dynamic groups and policies if missing. Updates policy statements if stack source has newer version. Does not delete manually-created policies or groups.
