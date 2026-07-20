data "oci_identity_tenancy" "customer_tenancy" {
  tenancy_id = var.tenancy_ocid
}

data "oci_identity_compartment" "customer_compartment" {
  id = var.compartment_ocid
}

data "oci_identity_compartments" "existing_migration_compartment" {
  compartment_id = var.compartment_ocid
  access_level   = "ANY"
  name           = "Migration"
  state          = "ACTIVE"
}

data "oci_identity_compartments" "existing_migration_secrets_compartment" {
  compartment_id = var.compartment_ocid
  access_level   = "ANY"
  name           = "MigrationSecrets"
  state          = "ACTIVE"
}

data "oci_identity_tag_namespaces" "existing_migration_tag_namespace" {
  provider       = oci.homeregion
  compartment_id = var.tenancy_ocid
  state          = "ACTIVE"
}

data "oci_identity_dynamic_groups" "existing_dynamic_groups" {
  provider       = oci.homeregion
  compartment_id = var.tenancy_ocid
  state          = "ACTIVE"
}

data "oci_identity_policies" "existing_tenancy_policies" {
  provider       = oci.homeregion
  compartment_id = var.tenancy_ocid
  state          = "ACTIVE"
}

data "oci_identity_policies" "existing_compartment_policies" {
  provider       = oci.homeregion
  compartment_id = var.compartment_ocid
  state          = "ACTIVE"
}

locals {
  # Prefix that will be used to create all resources outside of this two compartments (Migration and MigrationSecrets)
  version_value               = "2.4"
  prefix                      = lower(data.oci_identity_compartment.customer_compartment.name)
  ocm_migration_tag_namespace = "CloudMigrations"
  version_tag                 = "PrerequisiteVersion"
  resource_level_tag          = "PrerequisiteResourceLevel"
  source_environment_type_tag = "SourceEnvironmentType"
  source_environment_id_tag   = "SourceEnvironmentId"
  source_asset_id_tag         = "SourceAssetId"
  migration_project_tag       = "MigrationProject"
  service_use_tag             = "ServiceUse"
  vmware_use_case_tag         = "PrerequisiteForVMware"
  aws_use_case_tag            = "PrerequisiteForAWS"
  olvm_use_case_tag           = "PrerequisiteForOLVM"
  resource_level_values = [
    "tenancy",
    "compartment"
  ]
  use_case_enabled_tag_value                    = "true"
  primary_prerequisite_stack                    = var.primary_prerequisite_stack
  existing_migration_compartment_exists         = length(data.oci_identity_compartments.existing_migration_compartment.compartments) > 0
  existing_migration_secrets_compartment_exists = length(data.oci_identity_compartments.existing_migration_secrets_compartment.compartments) > 0
  existing_migration_tag_namespace_exists = length([
    for namespace in data.oci_identity_tag_namespaces.existing_migration_tag_namespace.tag_namespaces :
    namespace.name if namespace.name == local.ocm_migration_tag_namespace
  ]) > 0
  migration_compartment_available             = local.primary_prerequisite_stack || local.existing_migration_compartment_exists
  migration_secrets_compartment_available     = local.primary_prerequisite_stack || local.existing_migration_secrets_compartment_exists
  migration_compartment_name_conflict         = local.iam_enabled && local.existing_migration_compartment_exists
  migration_secrets_compartment_name_conflict = local.iam_enabled && local.existing_migration_secrets_compartment_exists
  migration_tag_namespace_collision           = local.tags_enabled && local.existing_migration_tag_namespace_exists

  migration_compartment_id = try(
    oci_identity_compartment.migration_compartment[0].id,
    data.oci_identity_compartments.existing_migration_compartment.compartments[0].id,
    ""
  )

  migration_secrets_compartment_id = try(
    oci_identity_compartment.migration_secrets_compartment[0].id,
    data.oci_identity_compartments.existing_migration_secrets_compartment.compartments[0].id,
    ""
  )

  scenario_vmware_to_oci  = "VMware to OCI"
  scenario_vmware_to_olvm = "VMware to OLVM"
  scenario_aws_to_oci     = "AWS to OCI"

  migration_from_vmware_to_oci  = (var.enabled_migration_scenario == local.scenario_vmware_to_oci) || var.add_vmware_to_oci
  migration_from_vmware_to_olvm = (var.enabled_migration_scenario == local.scenario_vmware_to_olvm) || var.add_vmware_to_olvm
  migration_from_aws_to_oci     = (var.enabled_migration_scenario == local.scenario_aws_to_oci) || var.add_aws_to_oci

  any_migration         = local.migration_from_vmware_to_oci || local.migration_from_aws_to_oci || local.migration_from_vmware_to_olvm
  migration_from_vmware = local.migration_from_vmware_to_oci || local.migration_from_vmware_to_olvm
  migration_from_aws    = local.migration_from_aws_to_oci
  migration_to_oci      = local.migration_from_vmware_to_oci || local.migration_from_aws_to_oci
  migration_to_olvm     = local.migration_from_vmware_to_olvm

  iam_enabled              = local.primary_prerequisite_stack && local.any_migration
  tags_enabled             = local.iam_enabled && var.create_cloud_migrations_tag_namespace_and_tag_definitions
  migration_groups_enabled = local.iam_enabled && var.migration_groups
  vmware_migration_enabled = local.iam_enabled && local.migration_from_vmware
  migration_to_oci_enabled = local.iam_enabled && local.migration_to_oci
  expected_dynamic_group_names = compact([
    local.iam_enabled ? "${local.prefix}-migration-dg" : "",
    local.vmware_migration_enabled ? "${local.prefix}-remote-agent-and-plugins-dg" : "",
    local.iam_enabled ? "${local.prefix}-discovery-dg" : "",
    local.migration_to_oci_enabled ? "${local.prefix}-hydration-agent-dg" : ""
  ])
  existing_dynamic_group_names = [
    for dynamic_group in data.oci_identity_dynamic_groups.existing_dynamic_groups.dynamic_groups :
    dynamic_group.name
  ]
  conflicting_dynamic_group_names = [
    for name in local.expected_dynamic_group_names :
    name if contains(local.existing_dynamic_group_names, name)
  ]
  expected_policy_names = compact([
    local.iam_enabled ? "${local.prefix}-ocm-tenancy-level-policy" : "",
    local.iam_enabled ? "${local.prefix}-ocm-compartment-level-policy" : ""
  ])
  existing_tenancy_policy_names = [
    for policy in data.oci_identity_policies.existing_tenancy_policies.policies :
    policy.name
  ]
  existing_compartment_policy_names = [
    for policy in data.oci_identity_policies.existing_compartment_policies.policies :
    policy.name
  ]
  conflicting_policy_names = [
    for name in local.expected_policy_names :
    name if contains(local.existing_tenancy_policy_names, name) || contains(local.existing_compartment_policy_names, name)
  ]
  vmware_defined_tags = {
    "${local.ocm_migration_tag_namespace}.${local.vmware_use_case_tag}" = local.use_case_enabled_tag_value
  }
  aws_defined_tags = {
    "${local.ocm_migration_tag_namespace}.${local.aws_use_case_tag}" = local.use_case_enabled_tag_value
  }
  olvm_defined_tags = {
    "${local.ocm_migration_tag_namespace}.${local.olvm_use_case_tag}" = local.use_case_enabled_tag_value
  }
}

data "oci_identity_regions" "regions" {
}

data "oci_objectstorage_namespace" "objectstorage_namespace" {
  compartment_id = var.tenancy_ocid
}
