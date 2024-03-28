data "oci_identity_tenancy" "customer_tenancy" {
  tenancy_id = var.tenancy_ocid
}

data "oci_identity_compartment" "customer_compartment" {
  id = var.compartment_ocid
}

locals {
  # Prefix that will be used to create all resources outside of this two compartments (Migration and MigrationSecrets)
  version_value               = "1.0"
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
  cld_use_case_tag            = "PrerequisiteForCLD"
  resource_level_values = [
    "tenancy",
    "compartment"
  ]
  migration_from_vmware      = true
  use_case_enabled_tag_value = "true"
  ocb_discovery_service = "ocb-discovery"
  any_migration              = local.migration_from_vmware
  vmware_defined_tags = {
    "${local.ocm_migration_tag_namespace}.${local.vmware_use_case_tag}" = local.use_case_enabled_tag_value
  }
  cld_defined_tags = {
    "${local.ocm_migration_tag_namespace}.${local.cld_use_case_tag}" = local.use_case_enabled_tag_value
  }

}

data "oci_identity_regions" "regions" {
}

data "oci_objectstorage_namespace" "objectstorage_namespace" {
  compartment_id = var.tenancy_ocid
}
