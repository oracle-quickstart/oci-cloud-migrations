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

locals {
  # Prefix that will be used to create all resources outside of this two compartments (Migration and MigrationSecrets)
  version_value               = "2.1"
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
  resource_level_values = [
    "tenancy",
    "compartment"
  ]
  use_case_enabled_tag_value = "true"
  primary_prerequisite_stack = var.primary_prerequisite_stack
  any_migration              = var.migration_from_vmware || var.migration_from_aws
  vmware_defined_tags = {
    "${local.ocm_migration_tag_namespace}.${local.vmware_use_case_tag}" = local.use_case_enabled_tag_value
  }
  aws_defined_tags = {
    "${local.ocm_migration_tag_namespace}.${local.aws_use_case_tag}" = local.use_case_enabled_tag_value
  }

}

data "oci_identity_regions" "regions" {
}

data "oci_objectstorage_namespace" "objectstorage_namespace" {
  compartment_id = var.tenancy_ocid
}
