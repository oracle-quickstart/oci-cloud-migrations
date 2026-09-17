# Bar 2: Compartment Structure

**Purpose:** The customer has a dedicated home for migration resources.

**Dependencies:** Bar 1 (Identity Foundation) — compartments are tagged with CloudMigrations tags.

**Required for:** All scenarios (VMware to OCI, AWS to OCI, VMware to OLVM).

## Resources

| Resource | Type | Location | Expected state |
|----------|------|----------|---------------|
| `Migration` | Compartment | Child of customer-selected parent compartment | ACTIVE |
| `MigrationSecrets` | Compartment | Child of customer-selected parent compartment | ACTIVE |

The customer selects a "migration root compartment" when configuring the RMS stack. Both compartments are created as direct children of that root. This is a known pain point — customers sometimes select the wrong compartment or navigate into a child compartment and lose sight of where prereqs were applied.

## Validation

**Step 1:** Identify the customer's migration root compartment. Ask the customer or infer from existing tagged resources.

**Step 2:** List child compartments of the migration root.
```
Client: oci.identity.IdentityClient
Method: list_compartments
Parameters:
  compartment_id: <migration_root_compartment_ocid>
  lifecycle_state: ACTIVE
```
Look for compartments with `name` = `Migration` and `name` = `MigrationSecrets`.

**Step 3:** If found, verify they are tagged with `CloudMigrations.PrerequisiteResourceLevel` = `compartment`.

## Status criteria

| Status | Condition |
|--------|-----------|
| Green | Both `Migration` and `MigrationSecrets` exist, ACTIVE, correctly tagged |
| Yellow | One compartment exists but not the other, or exists but missing tags |
| Red | Neither compartment exists under the specified parent |

## Common failures

- **Compartments exist but under wrong parent** — customer ran the stack with a different root compartment than they're now working in. Ask which compartment they selected during stack creation.
- **Compartments exist but not tagged** — created manually instead of via RMS stack. The stack won't manage them unless it created them. Guide customer to either import into Terraform state or re-create via stack in the correct compartment.
- **MigrationSecrets missing but Migration exists** — partial stack failure. Check RMS job logs for the failure, then re-apply.
- **Migration missing but MigrationSecrets exists** — typical of a failed destroy. The destroy removed `Migration` but failed on `MigrationSecrets` (often because it contains KMS resources with deletion protection). The surviving compartment retains its CloudMigrations tags, which can be used to determine the stack version and scenario. Remediation: re-apply the stack to recreate the missing compartment.
- **Compartment in DELETING state** — someone initiated deletion. Compartment deletion in OCI is asynchronous and may take time. Cannot re-create with same name until deletion completes.

## Compartment scoping note

When `Migration` is missing, mark Storage blocked. When `MigrationSecrets` is missing, mark Encryption blocked. Continue inspecting tenancy- and root-scoped authorization artifacts, but Service Authorization cannot be green until its compartment references can be verified against the required children.

## What RMS apply fixes

Creates both compartments under the configured root if missing. Tags them with CloudMigrations metadata. Does not move existing compartments.
