# Prerequisite Stack Variables

Variables the customer configures when creating or updating the RMS stack. Read `version-compatibility.md` for the current release and supported variable-model families.

## Required variables

### Migration Root Compartment (`compartment_ocid`)

The parent compartment under which `Migration` and `MigrationSecrets` are created. All compartment-level policies, KMS vault, and storage bucket are scoped here. Dynamic group and policy names are prefixed with `lower(compartment_name)`.

This is the most common source of customer errors. Ask the customer:
- "Where do you want your migration resources to live?"
- "Do you have an existing organizational compartment for cloud migration work?"

If unsure, the tenancy root works but a dedicated compartment is recommended for isolation.

**Failure if wrong:** All bars may show red when checking the wrong compartment. The customer's resources exist but in a different location than expected.

### Enabled Migration Scenario (`enabled_migration_scenario`)

Primary scenario enum. One of:
- "VMware to OCI"
- "AWS to OCI"
- "VMware to OLVM"

Determines which dynamic groups, IAM policies, and scenario-dependent resources are created. Ask: "What platform are you migrating FROM, and what is the target?"

### Primary Prerequisite Stack (`primary_prerequisite_stack`)

Boolean. Default: true.

When true, the stack creates tenancy-level resources: the `CloudMigrations` tag namespace (Bar 1), tenancy-level dynamic groups, and tenancy-level IAM policies. When false, these are skipped — the stack only creates compartment-level resources (compartments, compartment-scoped policies, KMS, storage).

Set to false when the customer already has tenancy-level resources from a prereq stack in another compartment. A tenancy only needs one primary stack; additional compartment roots share the tenancy-level foundation.

## Additive scenario variables

These enable multiple migration scenarios on a single stack. The primary scenario is set by `enabled_migration_scenario`; additive booleans extend it.

| Variable | Title | Default |
|----------|-------|---------|
| `add_vmware_to_oci` | VMware to OCI | Follows primary scenario |
| `add_aws_to_oci` | AWS to OCI | false |
| `add_vmware_to_olvm` | VMware to OLVM | false |

When an additive scenario is enabled, the stack creates the dynamic groups and policies required for that scenario in addition to the primary.

### KMS vault and key

The v2.3+ variable model exposes no KMS enable/disable variable. When `MigrationSecrets` is available, the stack creates the `ocm-secrets` vault and `ocm-key`. Bar 4 is required for all scenarios because OCM stores migration credentials through this path.

State the KMS cost before plan review. If the customer declines KMS, stop the RMS path and report Bar 4 red; do not mark it not required.

## Scenario-dependent variables

### Replication bucket (`create_replication_bucket` / `replication_bucket`)

Controls whether to create the bucket named by `replication_bucket` in the Migration compartment (Bar 5). Default: enabled for OCI-targeted scenarios (VMware to OCI, AWS to OCI). Not required for VMware to OLVM.

`replication_bucket` sets the bucket name. Default: `ocm_replication`.

### Migration Service User Groups (`migration_groups`)

Boolean. Controls whether to create optional IAM groups for human administrators and operators. These are not required for OCM service operation but provide a recommended access model.

Enable if the customer wants predefined IAM groups for their migration team. Skip if they manage access through existing organizational groups.

### Logging variables

| Variable | Title | Default |
|----------|-------|---------|
| `remote_agent_logging` | Enable Remote Agent Appliance logging | false |
| `hydration_agent_logging` | Enable Hydration Agent logging | false |

When enabled, the stack creates IAM policies that allow Remote Agent Appliances and Hydration Agents to upload logs to OCM service tenancies. Recommended for troubleshooting visibility.

## Detecting variable models

Stack variables identify a model family, not the exact deployed release. Read the exact version from `CloudMigrations.PrerequisiteVersion` on a stack-created resource.

| Signal | Variable model |
|--------|---------|
| `migration_from_vmware`, `migration_from_aws` (booleans) | v2.1 |
| `enabled_migration_scenario` (enum) | v2.3+ |
| `primary_migration_scenario` | Transitional pre-v2.3 rename |

v2.1 stacks are missing: `enabled_migration_scenario`, `primary_prerequisite_stack`, `add_*` additive booleans, and the `PrerequisiteForOLVM` tag. Upgrade path: update the RMS stack to the current source, map the legacy variables to the current model, then review PLAN before APPLY.

**v2.1 → current-model variable mapping:**

| v2.1 variable | v2.1 value | Current-model equivalent |
|---------------|-----------|-----------------|
| `migration_from_vmware = true` | VMware scenario enabled | `enabled_migration_scenario = "VMware to OCI"` |
| `migration_from_aws = true` | AWS scenario enabled | `enabled_migration_scenario = "AWS to OCI"` |
| Both `migration_from_vmware` and `migration_from_aws` true | Multi-scenario | Set primary to whichever is primary, enable the other via `add_vmware_to_oci` or `add_aws_to_oci` |
| `migration_groups = true` | Admin/operator groups | `migration_groups = true` (unchanged) |
| `remote_agent_logging = true` | RA logging | `remote_agent_logging = true` (unchanged) |
| `hydration_agent_logging = true` | HA logging | `hydration_agent_logging = true` (unchanged) |
| (not present) | — | `primary_prerequisite_stack = true` (new, default true) |
| (not present) | — | `add_vmware_to_olvm = false` (new scenario, default false) |

The detector reports `variable_model` from these signals and reports `prereq_version` only when it observes the version tag on a surviving prerequisite compartment. Preserve a null or conflicting version result instead of converting the variable-model family into an exact release.

## Variable configuration order

1. Migration scenario (required — determines which other variables apply)
2. Migration root compartment (required — most error-prone variable)
3. Primary vs secondary stack (`primary_prerequisite_stack`)
4. Additive scenarios (if multi-platform)
5. KMS (required for every scenario) and storage (required for OCI targets)
6. Human operator access (`migration_groups`) — optional stack-created groups; customers may use existing organizational groups instead. OCM service dynamic groups and policies are separate Bar 3 requirements.
7. Logging (truly optional — `remote_agent_logging`, `hydration_agent_logging`)
