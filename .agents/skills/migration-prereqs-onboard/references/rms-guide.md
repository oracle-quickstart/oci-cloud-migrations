# RMS Stack Guide for Prerequisites

Use this reference only from the mutation-gated onboarding workflow.

## Transport selection

- Use `<oci-prefix>` to mean the fully resolved global CLI prefix from `oci-api-reference.md`.
- Use the CLI operation as the portable baseline.
- When OCI MCP tooling is available, `invoke_oci_api` may perform the paired SDK operation shown below.
- Preserve the same gate, target, complete variable map, reviewed plan, and job identifier across transports.

## Customer source

- Prefer the Cloud Migrations **Create Prerequisites** flow in the OCI Console.
- For programmatic setup, resolve the current Terraform URI from the OCM prerequisite metadata described in `stack-resources.md`.
- Never invent variable names from Console labels; use the exact Terraform variables below.

## Current variable model

| Variable | Required behavior |
|----------|-------------------|
| `tenancy_ocid` | Customer tenancy OCID |
| `compartment_ocid` | Selected migration root compartment OCID |
| `enabled_migration_scenario` | `VMware to OCI`, `AWS to OCI`, or `VMware to OLVM` |
| `add_vmware_to_oci` | Additive VMware-to-OCI toggle |
| `add_aws_to_oci` | Additive AWS-to-OCI toggle |
| `add_vmware_to_olvm` | Additive VMware-to-OLVM toggle |
| `primary_prerequisite_stack` | Create tenancy-level resources when `true` |
| `create_replication_bucket` | Create the bucket when required and not supplied by the customer |
| `replication_bucket` | Bucket name; defaults to `ocm_replication` |
| `create_cloud_migrations_tag_namespace_and_tag_definitions` | Create tags unless an existing primary stack owns them |
| `migration_groups` | Create optional human operator groups |
| `remote_agent_logging` | Enable Remote Agent log-upload policies |
| `hydration_agent_logging` | Enable Hydration Agent log-upload policies |
| `ocb-service-tenancy-ocid` | Optional service-tenancy override; leave empty unless Oracle provides a realm-specific value |
| `ocm-service-tenancy-ocid` | Optional service-tenancy override; leave empty unless Oracle provides a realm-specific value |

Read `version-compatibility.md` before configuring a stack. The current source has no KMS toggle. It creates `ocm-secrets` and `ocm-key` when `MigrationSecrets` is available. A customer who declines KMS does not satisfy Bar 4.

## Fresh stack preparation

Before `create_stack`, use the onboarding workflow's stack-preparation `MUTATION` gate. After the stack is created, use a separate PLAN `MUTATION` gate immediately before creating the PLAN job.

CLI:

```text
<oci-prefix> resource-manager stack create --compartment-id <rms-stack-compartment-ocid> --display-name <confirmed-display-name> --config-source <terraform-zip-path> --variables file://<variables-json-path>
```

MCP/API equivalent:

```text
Client: oci.resource_manager.ResourceManagerClient
Method: create_stack
Parameters:
  create_stack_details:
    compartment_id: <rms_stack_compartment_ocid>
    display_name: <confirmed_display_name>
    config_source: <confirmed_current_prerequisite_source>
    variables:
      tenancy_ocid: <tenancy_ocid>
      compartment_ocid: <migration_root_compartment_ocid>
      enabled_migration_scenario: <scenario>
      primary_prerequisite_stack: <true_or_false>
      add_vmware_to_oci: <true_or_false>
      add_aws_to_oci: <true_or_false>
      add_vmware_to_olvm: <true_or_false>
      create_replication_bucket: <true_or_false>
      replication_bucket: <bucket_name>
      create_cloud_migrations_tag_namespace_and_tag_definitions: <true_or_false>
      migration_groups: <true_or_false>
      remote_agent_logging: <true_or_false>
      hydration_agent_logging: <true_or_false>
      ocb-service-tenancy-ocid: <empty_unless_oracle_provides_override>
      ocm-service-tenancy-ocid: <empty_unless_oracle_provides_override>
```

CLI PLAN:

```text
<oci-prefix> resource-manager job create-plan-job --stack-id <stack-ocid>
```

```text
Client: oci.resource_manager.ResourceManagerClient
Method: create_job
Parameters:
  create_job_details:
    stack_id: <stack_ocid>
    job_operation: PLAN
```

Both calls mutate Resource Manager state. PLAN does not change prerequisite resources, but it creates a job record and requires its own separate PLAN gate.

## Existing stack preparation

Before `update_stack`, present the exact source and variable delta in the stack-preparation `MUTATION` gate.

CLI:

```text
<oci-prefix> resource-manager stack update --stack-id <stack-ocid> --config-source <terraform-zip-path> --variables file://<variables-json-path>
```

MCP/API equivalent:

```text
Client: oci.resource_manager.ResourceManagerClient
Method: update_stack
Parameters:
  stack_id: <stack_ocid>
  update_stack_details:
    config_source: <confirmed_current_prerequisite_source>
    variables: <complete_confirmed_variable_map>
```

After update, present the separate PLAN `MUTATION` gate, then create a PLAN job with the same call shape as the fresh path.

## Plan review

CLI:

```text
<oci-prefix> resource-manager job get --job-id <plan-job-ocid>
```

MCP/API equivalent:

```text
Client: oci.resource_manager.ResourceManagerClient
Method: get_job
Parameters:
  job_id: <plan_job_ocid>
```

- Wait for `SUCCEEDED` or `FAILED`.
- On failure, run `<oci-prefix> resource-manager job get-job-logs --job-id <plan-job-ocid> --all` or the mapped `get_job_logs` API call, then stop.
- On success, present all creates, updates, replacements, and deletes before requesting APPLY approval.

## Apply

Present a separate APPLY `MUTATION` gate after plan review.

CLI:

```text
<oci-prefix> resource-manager job create-apply-job --stack-id <stack-ocid> --execution-plan-strategy FROM_PLAN_JOB_ID --execution-plan-job-id <reviewed-plan-job-ocid>
```

MCP/API equivalent:

```text
Client: oci.resource_manager.ResourceManagerClient
Method: create_job
Parameters:
  create_job_details:
    stack_id: <stack_ocid>
    job_operation: APPLY
    apply_job_plan_resolution:
      plan_job_id: <reviewed_plan_job_ocid>
```

Poll with `<oci-prefix> resource-manager job get --job-id <apply-job-ocid>` or `get_job`. If APPLY fails, fetch job logs and stop before another mutation.

## Cleanup limitations

- Never describe DESTROY as guaranteed rollback.
- Require a separate `MUTATION` gate before DESTROY.
- Expect KMS keys and vaults to enter scheduled or pending deletion states.
- Expect non-empty compartments, retained buckets, dependencies, or manually managed resources to block complete cleanup.
- Re-run prerequisite validation and inventory residual resources after DESTROY.

## Stack discovery and failure evidence

Run:

```bash
python3 scripts/find_primary_prereq_stack.py --verify --scenario <scenario> --profile <profile> --config-file <config-file> --root-compartment-ocid <root-ocid> --json
```

When the stack is stored outside the migration root and its compartment is known, add `--stack-compartment-ocid <stack-compartment-ocid>`. Repeat it for multiple known locations. Use `--scan-all-compartments` only when the stack location is unknown. When the profile tenancy differs from the customer tenancy, add `--tenancy-ocid <customer-tenancy-ocid>`; do not scan the profile tenancy as a substitute. For session authentication, add `--auth security_token`. Add `--region <region>` when the profile does not select the target region. Add `--cert-bundle <path>` when the realm requires a private CA bundle.

- Preserve `warnings`, `coverage_scope`, `coverage_complete`, `requested_scan_complete`, and `coverage_limitations`.
- If no candidate is found with incomplete coverage, supply each known RMS stack compartment or rerun with `--scan-all-compartments`.
- For a candidate, call `list_jobs` sorted newest first.
- For a failed newest job, call `get_job_logs` and report the first concrete error.
