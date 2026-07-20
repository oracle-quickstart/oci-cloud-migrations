resource "oci_identity_tag_namespace" "migration_tag_namespace" {
  provider       = oci.homeregion
  count          = local.tags_enabled ? 1 : 0
  compartment_id = var.tenancy_ocid
  description    = "Shared tag namespace used by Oracle Cloud Migrations to label prerequisite resources and migration assets created in the customer tenancy."
  name           = local.ocm_migration_tag_namespace
}

resource "oci_identity_tag" "version_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Tag that records which prerequisite stack version created or manages a resource."
  name             = local.version_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
}

resource "oci_identity_tag" "resource_level_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Tag that distinguishes tenancy-level prerequisite resources from compartment-level prerequisite resources."
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
  description      = "Tag that marks prerequisite resources needed for VMware migration scenarios."
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
  description      = "Tag that marks prerequisite resources needed for AWS to OCI migration scenarios."
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
  description      = "Tag that marks prerequisite resources needed for VMware to OLVM migration scenarios."
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

resource "oci_identity_tag" "source_environment_type_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Tag used by migration metering to record the source environment type for a migrated asset."
  name             = local.source_environment_type_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.aws_use_case_tag
  ]
}

resource "oci_identity_tag" "source_environment_id_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Tag used by migration metering to record the source environment identifier for a migrated asset."
  name             = local.source_environment_id_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.source_environment_type_tag
  ]
}

resource "oci_identity_tag" "source_asset_id_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Tag used by migration metering to record the source asset identifier for a migrated workload."
  name             = local.source_asset_id_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.source_environment_id_tag
  ]
}

resource "oci_identity_tag" "migration_project_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Tag used by migration metering to associate resources with an Oracle Cloud Migrations project."
  name             = local.migration_project_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.source_asset_id_tag
  ]
}

resource "oci_identity_tag" "service_use_tag" {
  provider         = oci.homeregion
  count            = local.tags_enabled ? 1 : 0
  description      = "Tag used by migration metering to classify how Oracle Cloud Migrations is using a tagged resource."
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
