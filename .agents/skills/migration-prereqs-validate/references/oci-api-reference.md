# OCI Operation Reference for Prerequisite Validation

Use this mapping for the validation calls required by the bar modules. OCI CLI is the verifier transport. OCI MCP tooling may corroborate or diagnose an individual API read, but it does not replace the verifier or change its verdict. The bar modules describe the readiness criteria.

## Shared CLI context

Start every command with the same resolved global options:

```text
oci --profile <profile> --config-file <config-file> [--auth <auth>] [--region <region>] [--cert-bundle <path>]
```

Do not silently drop an authentication type, region override, or CA bundle supplied by the customer. Use `--auth security_token` for a session-authenticated profile.

## Access preflight

Make one actual read against the selected root before evaluating bars:

| Selected root type | CLI suffix | MCP client and method |
|---|---|---|
| Tenancy OCID | `iam tenancy get --tenancy-id <root-ocid>` | `oci.identity.IdentityClient.get_tenancy(tenancy_id=<root-ocid>)` |
| Compartment OCID | `iam compartment get --compartment-id <root-ocid>` | `oci.identity.IdentityClient.get_compartment(compartment_id=<root-ocid>)` |

For MCP, call `invoke_oci_api`; a successful `list_client_operations` response proves only that a method is discoverable. It does not prove authentication, authorization, or access to the selected root.

## Validation operations

| Evidence | CLI suffix | MCP client and method | Required parameters |
|---|---|---|---|
| Tag namespaces | `iam tag-namespace list --compartment-id <tenancy-ocid> --all` | `oci.identity.IdentityClient.list_tag_namespaces` | `compartment_id` |
| Tag definitions | `iam tag list --tag-namespace-id <namespace-ocid> --all` | `oci.identity.IdentityClient.list_tags` | `tag_namespace_id` |
| Child compartments | `iam compartment list --compartment-id <root-ocid> --lifecycle-state ACTIVE --all` | `oci.identity.IdentityClient.list_compartments` | `compartment_id`, `lifecycle_state=ACTIVE` |
| Dynamic groups | `iam dynamic-group list --compartment-id <tenancy-ocid> --all` | `oci.identity.IdentityClient.list_dynamic_groups` | `compartment_id` |
| Policies | `iam policy list --compartment-id <policy-scope-ocid> --all` | `oci.identity.IdentityClient.list_policies` | `compartment_id` |
| KMS vaults | `kms management vault list --compartment-id <migration-secrets-ocid> --all` | `oci.key_management.KmsVaultClient.list_vaults` | `compartment_id` |
| KMS keys | `kms management key list --endpoint <vault-management-endpoint> --compartment-id <migration-secrets-ocid> --all` | `oci.key_management.KmsManagementClient.list_keys` | `compartment_id`; construct the client with the vault management endpoint |
| Object Storage namespace | `os ns get` | `oci.object_storage.ObjectStorageClient.get_namespace` | None |
| Configured bucket | `os bucket get --namespace-name <namespace> --bucket-name <configured-name>` | `oci.object_storage.ObjectStorageClient.get_bucket` | `namespace_name`, `bucket_name` |
| Buckets in Migration | `os bucket list --namespace-name <namespace> --compartment-id <migration-ocid> --all` | `oci.object_storage.ObjectStorageClient.list_buckets` | `namespace_name`, `compartment_id` |

For Bar 5, resolve `<configured-name>` from the current stack variable `replication_bucket` or explicit customer configuration. Use `ocm_replication` only as the current default when no custom name was selected. If the name cannot be resolved, the check is unavailable.

## Resource Manager evidence

Run `scripts/find_primary_prereq_stack.py --verify --scenario <scenario>` for stack discovery, ranking, live bar evidence, and the readiness verdict. It performs the CLI reads using the same profile, config, authentication, region, and CA inputs. Pass `--stack-compartment-ocid` for a known separate RMS location; use `--scan-all-compartments` only when its location is unknown.

For follow-up reads:

| Evidence | CLI suffix | MCP client and method |
|---|---|---|
| Stack details | `resource-manager stack get --stack-id <stack-ocid>` | `oci.resource_manager.ResourceManagerClient.get_stack` |
| Jobs | `resource-manager job list --stack-id <stack-ocid> --sort-by TIMECREATED --sort-order DESC --all` | `oci.resource_manager.ResourceManagerClient.list_jobs` |
| Job | `resource-manager job get --job-id <job-ocid>` | `oci.resource_manager.ResourceManagerClient.get_job` |
| Job logs | `resource-manager job get-job-logs --job-id <job-ocid> --all` | `oci.resource_manager.ResourceManagerClient.get_job_logs` |

Use `references/rms-guide.md` for mutation-gated stack and job operations. Do not infer readiness from RMS history without validating live resources.
