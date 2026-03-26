# This file contains all the dynamic_group resources required for service functionalities

# created in root compartment
# this dynamic group is compartment specific
resource "oci_identity_dynamic_group" "migration_dg" {
  provider       = oci.homeregion
  count          = local.iam_enabled ? 1 : 0
  name           = "${local.prefix}-migration-dg"
  description    = "All ocmmigration resource types."
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

# For remote-agent and (discovery, replication) plugins
resource "oci_identity_dynamic_group" "remote_agent_and_plugins_dg" {
  provider       = oci.homeregion
  count          = local.vmware_migration_enabled ? 1 : 0
  name           = "${local.prefix}-remote-agent-and-plugins-dg"
  description    = "All ocbagent resource types."
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
  description    = "All ocbassetsource resource types."
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

# this dynamic group is compartment specific. There is no way to make it not compartment specific.
resource "oci_identity_dynamic_group" "hydration_agent_dg" {
  provider = oci.homeregion
  # If migrating to OLVM instead of OCI, don't create hydration agent dynamic group
  count          = local.migration_to_oci_enabled ? 1 : 0
  name           = "${local.prefix}-hydration-agent-dg"
  description    = "All instances in the ${oci_identity_compartment.migration_compartment[0].name} compartment."
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
