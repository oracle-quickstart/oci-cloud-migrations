# Prerequisite Stack Resource Inventory

Complete inventory of OCI resources created by the prerequisite Terraform stack, organized by bar.

## Terraform source

Use one of these customer-facing sources for the prerequisite Terraform:

1. **OCI Console (recommended):** The "Create Prerequisites" button on the Cloud Migrations overview page fetches the current version automatically and opens RMS with the correct source.

2. **Programmatic:** Fetch `metadata.json` from the `prerequisite-scripts` bucket in the OCM service Object Storage namespace. The response contains a `uri` field pointing to the current Terraform zip. Use that URI as the `zipUrl` when creating an RMS stack.
   ```
   Client: ObjectStorageClient
   Method: get_object
   Parameters:
     namespace_name: <ocm_service_namespace>
     bucket_name: prerequisite-scripts
     object_name: metadata.json
   ```
   The service namespace is region-specific and available via the console capabilities API (`ocm-customer-setup-namespace`).

## Terraform files

Key Terraform files in the source:
- `identity_tags.tf` — tag namespace and definitions
- `identity_compartments.tf` — Migration and MigrationSecrets compartments
- `identity_dynamic_groups.tf` — dynamic groups for OCM service principals
- `identity_policies.tf` — IAM policies at tenancy and compartment levels
- `identity_admin_operator_resources.tf` — optional admin/operator groups and policies
- `kms_vault.tf` — KMS vault and key
- `object_storage.tf` — replication bucket
- `validation_checks.tf` — post-apply validation

## Bar 1: Identity Foundation

**Source:** `identity_tags.tf`

| Resource | Name | Type | Location |
|----------|------|------|----------|
| Tag namespace | `CloudMigrations` | `oci_identity_tag_namespace` | Tenancy root |
| Tag | `PrerequisiteVersion` | `oci_identity_tag` | In CloudMigrations |
| Tag | `PrerequisiteResourceLevel` | `oci_identity_tag` | In CloudMigrations |
| Tag | `PrerequisiteForVMware` | `oci_identity_tag` | In CloudMigrations |
| Tag | `PrerequisiteForAWS` | `oci_identity_tag` | In CloudMigrations |
| Tag | `PrerequisiteForOLVM` | `oci_identity_tag` | In CloudMigrations |
| Tag | `SourceEnvironmentType` | `oci_identity_tag` | In CloudMigrations |
| Tag | `SourceEnvironmentId` | `oci_identity_tag` | In CloudMigrations |
| Tag | `SourceAssetId` | `oci_identity_tag` | In CloudMigrations |
| Tag | `MigrationProject` | `oci_identity_tag` | In CloudMigrations |
| Tag | `ServiceUse` | `oci_identity_tag` | In CloudMigrations |

Read `version-compatibility.md` for the current release and compatibility handling.

A `time_sleep` of 70 seconds follows tag creation for IAM propagation.

## Bar 2: Compartment Structure

**Source:** `identity_compartments.tf`

| Resource | Name | Type | Location |
|----------|------|------|----------|
| Compartment | `Migration` | `oci_identity_compartment` | Child of user-selected root |
| Compartment | `MigrationSecrets` | `oci_identity_compartment` | Child of user-selected root |

The "user-selected root" is the compartment the customer specifies when configuring the RMS stack variables.

## Bar 3: Service Authorization

**Source:** `identity_dynamic_groups.tf`, `identity_policies.tf`

### Dynamic groups (tenancy root)

Names are prefixed with `lower(migration_root_compartment_name)` — e.g., `myroot-migration-dg`.

| Resource | Name pattern | Matching rule |
|----------|------|--------------|
| Dynamic group | `{prefix}-migration-dg` | `resource.type = 'ocmmigration'` |
| Dynamic group | `{prefix}-discovery-dg` | `resource.type = 'ocbassetsource'` |
| Dynamic group | `{prefix}-remote-agent-and-plugins-dg` | `resource.type = 'ocbagent'` (VMware to OCI, VMware to OLVM) |
| Dynamic group | `{prefix}-hydration-agent-dg` | All instances in Migration compartment (VMware to OCI, AWS to OCI) |

### Policies — tenancy level

- Consolidated `{prefix}-ocm-tenancy-level-policy`
- Cross-tenancy log upload permissions for migration services, when logging variables are enabled
- Dynamic group permissions for service principals using concrete OCM/OCB resource types from the public service-policy docs
- Tagged with `CloudMigrations` metadata

### Policies — compartment level (migration root)

- Consolidated `{prefix}-ocm-compartment-level-policy`
- Per-dynamic-group permissions scoped to Migration and MigrationSecrets
- Object storage read/write in Migration compartment
- KMS permissions in MigrationSecrets compartment
- Network and compute permissions as required

### Optional: admin/operator groups

**Source:** `identity_admin_operator_resources.tf`

Optional IAM groups and policies for human operators. These are not required for OCM service operation but provide a recommended access model.

## Bar 4: Encryption

**Source:** `kms_vault.tf`

| Resource | Name | Type | Location |
|----------|------|------|----------|
| KMS Vault | `ocm-secrets` | `oci_kms_vault` | MigrationSecrets compartment |
| KMS Key | `ocm-key` | `oci_kms_key` | In `ocm-secrets` vault |

## Bar 5: Storage

**Source:** `object_storage.tf`

| Resource | Name | Type | Location |
|----------|------|------|----------|
| Bucket | Value of `replication_bucket`; default `ocm_replication` | `oci_objectstorage_bucket` | Migration compartment |

## Stack variables

Key variables the customer configures when creating the RMS stack. See `references/stack-variables.md` for the full configuration guide.

| Variable | schema.yaml title | Impact |
|----------|---------|--------|
| `compartment_ocid` | Migration Root Compartment | Scopes all compartment-level resources, prefixes DG/policy names |
| `enabled_migration_scenario` | Enabled Migration Scenario | Primary scenario — determines which DGs and policies are created |
| `primary_prerequisite_stack` | Primary Prerequisite Stack | Whether to create tenancy-level resources (tags, tenancy DGs/policies) |
| `add_vmware_to_oci` | VMware to OCI | Additive scenario toggle |
| `add_aws_to_oci` | AWS to OCI | Additive scenario toggle |
| `add_vmware_to_olvm` | VMware to OLVM | Additive scenario toggle |
| `create_replication_bucket` | Create a new replication bucket? | Bar 5 resources |
| `replication_bucket` | Replication Bucket Name | Default: `ocm_replication` |
| `migration_groups` | Migration Service User Groups | Optional admin/operator IAM groups |
| `remote_agent_logging` | Enable Remote Agent Appliance logging | Cross-tenancy log upload policy |
| `hydration_agent_logging` | Enable Hydration Agent logging | Cross-tenancy log upload policy |
