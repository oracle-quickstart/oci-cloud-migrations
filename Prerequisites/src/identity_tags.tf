# This file contains all the tagging resources required for service functionalities

resource "oci_identity_tag_namespace" "migration_tag_namespace" {
  provider       = oci.homeregion
  count          = local.tags_enabled ? 1 : 0
  compartment_id = var.tenancy_ocid
  description    = "${local.ocm_migration_tag_namespace} for customer on-boarding and migration tagging."
  name           = local.ocm_migration_tag_namespace
}

resource "oci_identity_tag" "version_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Version for customer on-boarding."
  name             = local.version_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
}

resource "oci_identity_tag" "resource_level_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "ResourceLevel for customer on-boarding."
  name             = local.resource_level_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  validator {
    validator_type = "ENUM"
    values         = local.resource_level_values
  }
  depends_on = [
    oci_identity_tag.version_tag
  ]
}

resource "oci_identity_tag" "vmware_use_case_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "VMware use case for customer on-boarding."
  name             = local.vmware_use_case_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  validator {
    validator_type = "ENUM"
    values         = [local.use_case_enabled_tag_value]
  }
  depends_on = [
    oci_identity_tag.resource_level_tag
  ]
}

resource "oci_identity_tag" "aws_use_case_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "AWS use case for customer on-boarding."
  name             = local.aws_use_case_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  validator {
    validator_type = "ENUM"
    values         = [local.use_case_enabled_tag_value]
  }
  depends_on = [
    oci_identity_tag.vmware_use_case_tag
  ]
}

resource "oci_identity_tag" "olvm_use_case_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "OLVM use case for customer on-boarding."
  name             = local.olvm_use_case_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  validator {
    validator_type = "ENUM"
    values         = [local.use_case_enabled_tag_value]
  }
  depends_on = [
    oci_identity_tag.vmware_use_case_tag
  ]
}

# Migration Metering feature support
resource "oci_identity_tag" "source_environment_type_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Source environment type for migration tagging."
  name             = local.source_environment_type_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.aws_use_case_tag
  ]
}

# Migration Metering feature support
resource "oci_identity_tag" "source_environment_id_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Source environment id for migration tagging."
  name             = local.source_environment_id_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.source_environment_type_tag
  ]
}

# Migration Metering feature support
resource "oci_identity_tag" "source_asset_id_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Source asset id for migration tagging."
  name             = local.source_asset_id_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.source_environment_id_tag
  ]
}

# Migration Metering feature support
resource "oci_identity_tag" "migration_project_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Migration project for migration tagging."
  name             = local.migration_project_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.source_asset_id_tag
  ]
}

# Migration Metering feature support
resource "oci_identity_tag" "service_use_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Service use for migration tagging."
  name             = local.service_use_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.migration_project_tag
  ]
}

resource "time_sleep" "tags_availability_delay" {
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.aws_use_case_tag,
    oci_identity_tag.source_environment_type_tag,
    oci_identity_tag.source_environment_id_tag,
    oci_identity_tag.source_asset_id_tag,
    oci_identity_tag.migration_project_tag,
    oci_identity_tag.service_use_tag
  ]
  create_duration = local.tags_enabled ? "70s" : "0s"
}
