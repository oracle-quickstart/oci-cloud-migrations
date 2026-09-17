# Bar 5: Storage

**Purpose:** A replication bucket exists for migration data transfer.

**Dependencies:** Bar 2 (Compartment Structure) — bucket lives in Migration compartment.

**Required for:** Scenarios targeting OCI — VMware to OCI, AWS to OCI. Not required for VMware to OLVM.

## Resources

| Resource | Type | Location | Expected state |
|----------|------|----------|---------------|
| Configured replication bucket; default `ocm_replication` | Object Storage Bucket | Migration compartment | Active (no lifecycle_state — existence = active) |

## Validation

**Step 1:** Get the Object Storage namespace for the tenancy.
```
Client: oci.object_storage.ObjectStorageClient
Method: get_namespace
```

**Step 2:** Resolve the expected bucket name from the current stack variable `replication_bucket` or explicit customer configuration. Use `ocm_replication` only when no custom name was selected. If no stack/configuration evidence is available, mark this check `unavailable`; do not guess a name.

**Step 3:** Check if the configured bucket exists.
```
Client: oci.object_storage.ObjectStorageClient
Method: get_bucket
Parameters:
  namespace_name: <tenancy_namespace>
  bucket_name: <configured_replication_bucket>
```
A 200 response means the bucket exists. Verify the returned `compartment_id` matches the Migration compartment OCID. A 404 means it does not exist under that name.

If `get_bucket` requires knowing the compartment, alternatively:
```
Client: oci.object_storage.ObjectStorageClient
Method: list_buckets
Parameters:
  namespace_name: <tenancy_namespace>
  compartment_id: <migration_compartment_ocid>
```
Look for `name` = `<configured_replication_bucket>`.

## Status criteria

| Status | Condition |
|--------|-----------|
| Green | Bucket exists in Migration compartment |
| Yellow | The configured bucket exists in the tenancy namespace but is in the wrong compartment |
| Red | The configured bucket name is absent after a complete read |
| Unavailable | The configured bucket name cannot be resolved, or permissions/coverage prevent a complete read |

## Common failures

- **Bucket exists but in wrong compartment** — customer may have created it manually elsewhere. OCM services expect it in the Migration compartment specifically.
- **Bucket name collision** — Object Storage bucket names are globally unique within a namespace. If the configured name exists in a different compartment, the stack apply will fail. Identify where the existing bucket lives.
- **Migration compartment doesn't exist** — bar 5 is blocked by bar 2. Do not claim that the bucket itself is missing until its required compartment exists. Fix bar 2 first; re-apply recreates the Migration compartment.

## What RMS apply fixes

Creates the bucket named by `replication_bucket` in the Migration compartment when `create_replication_bucket` is true. The current default name is `ocm_replication`. It does not modify an existing bucket's configuration.
