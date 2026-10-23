# Bar 4: Encryption

**Purpose:** Customer data at rest is encrypted with a customer-managed key.

**Dependencies:** Bar 2 (Compartment Structure) — vault lives in MigrationSecrets compartment.

**Required for:** All scenarios — VMware to OCI, AWS to OCI, VMware to OLVM. Encryption supports remote login credentials used in all source environments.

**Requirement basis:** Bar 4 being mandatory for every scenario is `OCM policy`. The current stack creating a dedicated vault and key with no KMS opt-out is the `Published prerequisite-stack contract`. Do not label KMS as a `Product/API requirement` unless current public product documentation explicitly establishes that requirement.

## Resources

| Resource | Type | Location | Expected state |
|----------|------|----------|---------------|
| `ocm-secrets` | KMS Vault | MigrationSecrets compartment | ACTIVE |
| `ocm-key` | KMS Key | In `ocm-secrets` vault | ENABLED |

## Validation

**Step 1:** List vaults in the MigrationSecrets compartment.
```
Client: oci.key_management.KmsVaultClient
Method: list_vaults
Parameters:
  compartment_id: <migration_secrets_compartment_ocid>
```
Look for a vault with `display_name` = `ocm-secrets` and `lifecycle_state` = `ACTIVE`.

**Step 2:** If vault found, list keys in it. The KmsManagementClient requires the vault's `management_endpoint` as its service endpoint — pass this via the `endpoint` parameter to `invoke_oci_api`.
```
Client: oci.key_management.KmsManagementClient
Method: list_keys
Parameters:
  compartment_id: <migration_secrets_compartment_ocid>
Endpoint: <vault.management_endpoint from step 1>
```
Look for a key with `display_name` = `ocm-key` and `lifecycle_state` = `ENABLED`.

## Status criteria

| Status | Condition |
|--------|-----------|
| Green | Vault exists + ACTIVE, key exists + ENABLED |
| Yellow | Vault exists but key is missing, DISABLED, or PENDING_DELETION |
| Red | MigrationSecrets exists, but the vault does not exist there |

## Common failures

- **Vault exists but key was scheduled for deletion** — KMS keys have a waiting period before actual deletion. If still in PENDING_DELETION, customer can cancel the deletion. If already deleted, re-apply stack to create a new key.
- **Vault is in CREATING state** — vault provisioning can take a few minutes. Wait and re-check.
- **Customer wants to reuse existing vault** — the stack creates a new vault. Reusing an existing vault requires manual Terraform state manipulation, which is not recommended via this workflow. Note the limitation.
- **MigrationSecrets compartment doesn't exist** — bar 4 is blocked by bar 2. Do not claim that the vault itself is missing until its required compartment exists. Fix bar 2 first.
- **Vault and key fully deleted after failed DESTROY** — a DESTROY job may schedule vault deletion (7-30 day waiting period for keys). The DESTROY fails because it can't immediately remove MigrationSecrets while the vault is in PENDING_DELETION. Months later, the key waiting period expires, the vault deletes, but MigrationSecrets remains as an orphaned compartment with no vault inside. Re-apply creates a new vault and key.

## Cost note

KMS vaults have ongoing costs. This is a known customer concern. The stack creates a dedicated vault for isolation; reusing an existing vault is tracked as a future improvement.

## What RMS apply fixes

Creates the vault and key if missing. Does not modify existing vaults or keys — KMS resources are append-only in Terraform.
