resource "oci_identity_dynamic_group" "migration_dg" {
  provider       = oci.homeregion
  count          = local.iam_enabled ? 1 : 0
  name           = "${local.prefix}-migration-dg"
  description    = "Dynamic group for Oracle Cloud Migrations service resources that operate on migration assets in the Migration compartment."
  compartment_id = var.tenancy_ocid
  matching_rule  = "ALL { resource.type = 'ocmmigration', resource.compartment.id = '${oci_identity_compartment.migration_compartment[0].id}'}"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
    local.migration_from_aws == true ? local.aws_defined_tags : {},
    local.migration_to_olvm == true ? local.olvm_defined_tags : {}
  )
  depends_on = [time_sleep.tags_availability_delay]
}

resource "oci_identity_dynamic_group" "remote_agent_and_plugins_dg" {
  provider       = oci.homeregion
  count          = local.vmware_migration_enabled ? 1 : 0
  name           = "${local.prefix}-remote-agent-and-plugins-dg"
  description    = "Dynamic group for Remote Agent Appliances and related plugins used by VMware migration and replication workflows."
  compartment_id = var.tenancy_ocid
  matching_rule  = "Any { resource.type = 'ocbagent' }"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
    local.migration_to_olvm == true ? local.olvm_defined_tags : {}
  )
  depends_on = [time_sleep.tags_availability_delay]
}

resource "oci_identity_dynamic_group" "discovery_dg" {
  provider       = oci.homeregion
  count          = local.iam_enabled ? 1 : 0
  name           = "${local.prefix}-discovery-dg"
  description    = "Dynamic group for Oracle Cloud Migrations discovery resources that inventory source environments and report discovered assets."
  compartment_id = var.tenancy_ocid
  matching_rule  = "Any { resource.type = 'ocbassetsource' }"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
    local.migration_from_aws == true ? local.aws_defined_tags : {},
    local.migration_to_olvm == true ? local.olvm_defined_tags : {}
  )
  depends_on = [time_sleep.tags_availability_delay]
}

resource "oci_identity_dynamic_group" "hydration_agent_dg" {
  provider = oci.homeregion
  # If migrating to OLVM instead of OCI, don't create hydration agent dynamic group
  count          = local.migration_to_oci_enabled ? 1 : 0
  name           = "${local.prefix}-hydration-agent-dg"
  description    = "Dynamic group for Hydration Agent instances launched in the Migration compartment for migration-to-OCI workflows."
  compartment_id = var.tenancy_ocid
  matching_rule  = "ALL { instance.compartment.id = '${oci_identity_compartment.migration_compartment[0].id}'}"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
    local.migration_from_aws == true ? local.aws_defined_tags : {}
  )
  depends_on = [time_sleep.tags_availability_delay]
}
