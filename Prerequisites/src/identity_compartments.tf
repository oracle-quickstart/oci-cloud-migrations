# This file contains all the compartment resources required for service functionalities

resource "oci_identity_compartment" "migration_compartment" {
  provider       = oci.homeregion
  count          = local.iam_enabled ? 1 : 0
  name           = "Migration"
  description    = "Compartment for OCM resources."
  compartment_id = var.compartment_ocid
  enable_delete  = true
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
    local.migration_from_aws == true ? local.aws_defined_tags : {},
    local.migration_to_olvm == true ? local.olvm_defined_tags : {}
  )
  depends_on = [time_sleep.tags_availability_delay]
}

resource "oci_identity_compartment" "migration_secrets_compartment" {
  provider       = oci.homeregion
  count          = local.iam_enabled ? 1 : 0
  name           = "MigrationSecrets"
  description    = "Compartment for OCM secrets."
  compartment_id = var.compartment_ocid
  enable_delete  = true
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
    local.migration_from_aws == true ? local.aws_defined_tags : {},
    local.migration_to_olvm == true ? local.olvm_defined_tags : {}
  )
  depends_on = [time_sleep.tags_availability_delay]
}
