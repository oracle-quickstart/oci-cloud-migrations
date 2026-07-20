output "prerequisite_stack_version" {
  description = "Version of the prerequisite stack that was applied."
  value       = local.version_value
}

output "prerequisite_stack_mode" {
  description = "Whether this run was a primary stack (creates IAM, tags, compartments) or secondary (reuses existing tenancy-level resources)."
  value       = local.primary_prerequisite_stack ? "primary" : "secondary"
}

output "migration_root_compartment_id" {
  description = "The parent compartment under which the Migration and MigrationSecrets compartments were created or found."
  value       = var.compartment_ocid
}

output "migration_compartment_id" {
  description = "OCID of the Migration compartment, whether created by this stack or found from a prior run."
  value       = local.migration_compartment_id
}

output "migration_secrets_compartment_id" {
  description = "OCID of the MigrationSecrets compartment, whether created by this stack or found from a prior run."
  value       = local.migration_secrets_compartment_id
}

output "tag_namespace_id" {
  description = "OCID of the CloudMigrations tag namespace created by this stack. Empty for secondary stacks."
  value       = try(oci_identity_tag_namespace.migration_tag_namespace[0].id, "")
}

output "dynamic_group_ids" {
  description = "JSON map of dynamic group name to OCID for groups created by this stack. Empty for secondary stacks."
  value = jsonencode(merge(
    { for dg in oci_identity_dynamic_group.migration_dg : dg.name => dg.id },
    { for dg in oci_identity_dynamic_group.remote_agent_and_plugins_dg : dg.name => dg.id },
    { for dg in oci_identity_dynamic_group.discovery_dg : dg.name => dg.id },
    { for dg in oci_identity_dynamic_group.hydration_agent_dg : dg.name => dg.id }
  ))
}

output "policy_ids" {
  description = "JSON map of policy name to OCID for IAM policies created by this stack. Empty for secondary stacks."
  value = jsonencode(merge(
    { for p in oci_identity_policy.ocm_tenancy_level_policy : p.name => p.id },
    { for p in oci_identity_policy.ocm_compartment_level_policy : p.name => p.id }
  ))
}

output "enabled_scenarios" {
  description = "Comma-separated list of migration scenarios enabled by this prerequisite stack."
  value = join(", ", compact([
    local.migration_from_vmware_to_oci ? "VMware to OCI" : "",
    local.migration_from_vmware_to_olvm ? "VMware to OLVM" : "",
    local.migration_from_aws_to_oci ? "AWS to OCI" : ""
  ]))
}

output "kms_vault_id" {
  description = "OCID of the KMS vault created in MigrationSecrets for migration credential storage."
  value       = try(oci_kms_vault.ocm_secrets[0].id, "")
}

output "kms_key_id" {
  description = "OCID of the KMS key created for migration secret encryption."
  value       = try(oci_kms_key.ocm_key[0].id, "")
}

output "replication_bucket_name" {
  description = "Name of the Object Storage replication bucket, if created by this stack."
  value       = try(oci_objectstorage_bucket.replication_bucket[0].name, "")
}
