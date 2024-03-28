resource "oci_identity_tag_namespace" "migration_tag_namespace" {
  provider       = oci.homeregion
  count          = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  compartment_id = var.tenancy_ocid
  description    = "${local.ocm_migration_tag_namespace} for customer on-boarding and migration metering"
  name           = local.ocm_migration_tag_namespace
}

resource "oci_identity_tag" "version_tag" {
  provider         = oci.homeregion
  count            = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  description      = "Version for customer on-boarding"
  name             = local.version_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
}

resource "oci_identity_tag" "resource_level_tag" {
  provider         = oci.homeregion
  count            = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  description      = "ResourceLevel for customer on-boarding"
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
  count            = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  description      = "VMware use case for customer on-boarding"
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

resource "oci_identity_tag" "cld_use_case_tag" {
  provider         = oci.homeregion
  count            = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  description      = "Cloud use case for customer on-boarding"
  name             = local.cld_use_case_tag
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
  count            = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  description      = "Source environment type tag for migration metering"
  name             = local.source_environment_type_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.cld_use_case_tag
  ]
}

# Migration Metering feature support
resource "oci_identity_tag" "source_environment_id_tag" {
  provider         = oci.homeregion
  count            = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  description      = "Source environment id tag for migration metering"
  name             = local.source_environment_id_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.source_environment_type_tag
  ]
}

# Migration Metering feature support
resource "oci_identity_tag" "source_asset_id_tag" {
  provider         = oci.homeregion
  count            = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  description      = "Source asset id tag for migration metering"
  name             = local.source_asset_id_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.source_environment_id_tag
  ]
}

# Migration Metering feature support
resource "oci_identity_tag" "migration_project_tag" {
  provider         = oci.homeregion
  count            = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  description      = "Migration project tag for migration metering"
  name             = local.migration_project_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.source_asset_id_tag
  ]
}

# Migration Metering feature support
resource "oci_identity_tag" "service_use_tag" {
  provider         = oci.homeregion
  count            = var.create_cloud_migrations_tag_namespace_and_tag_definitions && local.any_migration ? 1 : 0
  description      = "Service use tag for migration metering"
  name             = local.service_use_tag
  tag_namespace_id = oci_identity_tag_namespace.migration_tag_namespace[0].id
  depends_on = [
    oci_identity_tag.migration_project_tag
  ]
}

resource "oci_identity_compartment" "migration_compartment" {
  provider       = oci.homeregion
  count          = local.any_migration ? 1 : 0
  name           = "Migration"
  description    = "Compartment for OCM resources."
  compartment_id = var.compartment_ocid
  enable_delete  = true
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_compartment" "migration_secrets_compartment" {
  provider       = oci.homeregion
  count          = local.any_migration ? 1 : 0
  name           = "MigrationSecrets"
  description    = "Compartment for OCM secrets."
  compartment_id = var.compartment_ocid
  enable_delete  = true
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

# created in root compartment
# this dynamic group is compartment specific
resource "oci_identity_dynamic_group" "migration_dg" {
  provider       = oci.homeregion
  count          = local.any_migration ? 1 : 0
  name           = "${local.prefix}-migration-dg"
  description    = "All ocmmigration resource types."
  compartment_id = var.tenancy_ocid
  matching_rule  = "ALL { resource.type = 'ocmmigration', resource.compartment.id = '${oci_identity_compartment.migration_compartment[0].id}'}"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_dynamic_group" "remote_agent_dg" {
  provider       = oci.homeregion
  count          = local.migration_from_vmware ? 1 : 0
  name           = "${local.prefix}-remote-agent-dg"
  description    = "All ocbagent resource types."
  compartment_id = var.tenancy_ocid
  matching_rule  = "Any { resource.type = 'ocbagent' }"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {}
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_dynamic_group" "discovery_plugin_dg" {
  provider       = oci.homeregion
  count          = local.migration_from_vmware ? 1 : 0
  name           = "${local.prefix}-discovery-plugin-dg"
  description    = "All ocbagent resource types."
  compartment_id = var.tenancy_ocid
  matching_rule  = "Any { resource.type = 'ocbagent' }"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {}
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_dynamic_group" "replication_plugin_dg" {
  provider       = oci.homeregion
  count          = local.migration_from_vmware ? 1 : 0
  name           = "${local.prefix}-replication-plugin-dg"
  description    = "All ocbagent resource types."
  compartment_id = var.tenancy_ocid
  matching_rule  = "Any { resource.type = 'ocbagent' }"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {}
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

# this dynamic group is compartment specific. There is no way to make it not compartment specific.
resource "oci_identity_dynamic_group" "hydration_agent_dg" {
  provider       = oci.homeregion
  count          = local.any_migration ? 1 : 0
  name           = "${local.prefix}-hydration-agent-dg"
  description    = "All instances in the ${oci_identity_compartment.migration_compartment[0].name} compartment."
  compartment_id = var.tenancy_ocid
  matching_rule  = "ALL { instance.compartment.id = '${oci_identity_compartment.migration_compartment[0].id}'}"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_dynamic_group" "asset_source_dg" {
  provider       = oci.homeregion
  count          = 0
  name           = "${local.prefix}-asset-source-dg"
  description    = "All ocbassetsource resource types."
  compartment_id = var.tenancy_ocid
  matching_rule  = "Any { resource.type = 'ocbassetsource' }"
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.cld_defined_tags
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "ocm_tenancy_level_policy_any_migration" {
  provider       = oci.homeregion
  count          = local.any_migration ? 1 : 0
  name           = "${local.prefix}-ocm-tenancy-level-policy-any-migration"
  description    = "Tenancy level policy needed for any migration"
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to read ocb-inventory in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} { INSTANCE_IMAGE_INSPECT, INSTANCE_IMAGE_READ } in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} { INSTANCE_INSPECT } in tenancy where any { request.operation='ListShapes' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} { DEDICATED_VM_HOST_READ } in tenancy where any { request.operation='GetDedicatedVmHost' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} { CAPACITY_RESERVATION_READ } in tenancy where any { request.operation='GetComputeCapacityReservation' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} { ORGANIZATIONS_SUBSCRIPTION_INSPECT } in tenancy where any { request.operation='ListSubscriptions' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to read rate-cards in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to read metrics in tenancy where target.metrics.namespace='ocb_asset'",
    # Migration Metering feature support
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to read tag-namespaces in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to use tag-namespaces in tenancy where target.tag-namespace.name='CloudMigrations'",

    "Allow service ${local.ocb_discovery_service} to read ocb-inventory in tenancy",
    "Allow service ${local.ocb_discovery_service} to { TENANCY_INSPECT } in tenancy"
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "ocm_tenancy_level_policy_vmware_migration" {
  provider       = oci.homeregion
  count          = local.migration_from_vmware ? 1 : 0
  name           = "${local.prefix}-ocm-tenancy-level-policy-vmware-migration"
  description    = "Tenancy level policy needed for VMware migration"
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to manage ocb-inventory in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.discovery_plugin_dg[0].name} to read ocb-inventory in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.replication_plugin_dg[0].name} to { OCB_AGENT_INSPECT, OCB_AGENT_SYNC, OCB_AGENT_READ, OCB_AGENT_DEPENDENCY_INSPECT, OCB_AGENT_DEPENDENCY_READ, OCB_AGENT_KEY_UPDATE, OCB_AGENT_TASK_READ, OCB_AGENT_ASSET_SOURCES_INSPECT, OCB_AGENT_TASK_UPDATE } in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.replication_plugin_dg[0].name} to read ocb-inventory in tenancy",
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[0]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {}
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

# created in customer selected compartment
resource "oci_identity_policy" "migration_service_policy_any_migration" {
  provider       = oci.homeregion
  count          = local.any_migration ? 1 : 0
  name           = "migration-service-policy-any-migration"
  description    = "Migration service policy for any migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to manage instance-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to manage compute-image-capability-schema in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to manage virtual-network-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to manage volume-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to manage object-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} to read ocb-inventory-asset in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.migration_dg[0].name} { OCB_CONNECTOR_READ, OCB_CONNECTOR_DATA_READ, OCB_ASSET_SOURCE_READ, OCB_ASSET_SOURCE_CONNECTOR_DATA_UPDATE } in compartment id ${oci_identity_compartment.migration_compartment[0].id}"
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},

  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "remote_agent_policy_vmware_migration" {
  provider       = oci.homeregion
  count          = local.migration_from_vmware ? 1 : 0
  name           = "remote-agent-policy-vmware-migration"
  description    = "Remote agent policy needed for VMware migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to manage buckets in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to manage object-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} { OCM_REPLICATION_TASK_READ, OCM_REPLICATION_TASK_UPDATE } in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to use ocb-asset-source-connectors in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to use ocb-connectors in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to manage ocb-inventory-asset in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to read secret-family in compartment id ${oci_identity_compartment.migration_secrets_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to use metrics in compartment id ${oci_identity_compartment.migration_compartment[0].id} where target.metrics.namespace='ocb_asset'",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to {OCM_CONNECTOR_INSPECT, OCM_ASSET_SOURCE_READ, OCM_ASSET_SOURCE_CONNECTION_PUSH} in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to {OCB_AGENT_INSPECT, OCB_AGENT_SYNC, OCB_AGENT_READ, OCB_AGENT_DEPENDENCY_INSPECT, OCB_AGENT_DEPENDENCY_READ, OCB_AGENT_KEY_UPDATE, OCB_AGENT_TASK_READ, OCB_AGENT_ASSET_SOURCES_INSPECT, OCB_AGENT_TASK_UPDATE} in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.remote_agent_dg[0].name} to {OCB_ASSET_SOURCE_INSPECT, OCB_ASSET_SOURCE_READ, OCB_ASSET_SOURCE_ASSET_HANDLES_PUSH, OCB_ASSET_SOURCE_CONNECTION_PUSH} in compartment id ${oci_identity_compartment.migration_compartment[0].id}"
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {}
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "discovery_plugin_policy_vmware_migration" {
  provider       = oci.homeregion
  count          = local.migration_from_vmware ? 1 : 0
  name           = "discovery-plugin-policy-vmware-migration"
  description    = "Discovery plugin policy needed for VMware migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.discovery_plugin_dg[0].name} to use ocb-connectors in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.discovery_plugin_dg[0].name} to use ocb-asset-source-connectors in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.discovery_plugin_dg[0].name} to manage ocb-inventory-asset in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.discovery_plugin_dg[0].name} to read secret-family in compartment id ${oci_identity_compartment.migration_secrets_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.discovery_plugin_dg[0].name} to use metrics in compartment id ${oci_identity_compartment.migration_compartment[0].id} where target.metrics.namespace='ocb_asset'"
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {}
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "replication_plugin_policy_vmware_migration" {
  provider       = oci.homeregion
  count          = local.migration_from_vmware ? 1 : 0
  name           = "replication-plugin-policy-vmware-migration"
  description    = "Replication plugin policy needed for VMware migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.replication_plugin_dg[0].name} to { OCM_REPLICATION_TASK_INSPECT, OCM_REPLICATION_TASK_READ, OCM_REPLICATION_TASK_UPDATE, OCM_CONNECTOR_INSPECT, OCM_ASSET_SOURCE_READ, OCM_ASSET_SOURCE_CONNECTION_PUSH } in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.replication_plugin_dg[0].name} to { BUCKET_INSPECT, BUCKET_READ, OBJECTSTORAGE_NAMESPACE_READ, OBJECT_CREATE, OBJECT_DELETE, OBJECT_INSPECT, OBJECT_OVERWRITE, OBJECT_READ } in compartment id ${oci_identity_compartment.migration_compartment[0].id} where all { target.bucket.name='${var.create_replication_bucket ? oci_objectstorage_bucket.replication_bucket[0].name : var.replication_bucket}' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.replication_plugin_dg[0].name} to use ocb-connectors in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.replication_plugin_dg[0].name} to use ocb-asset-source-connectors in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.replication_plugin_dg[0].name} to read ocb-inventory-asset in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.replication_plugin_dg[0].name} to read secret-family in compartment id ${oci_identity_compartment.migration_secrets_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.replication_plugin_dg[0].name} to use metrics in compartment id ${oci_identity_compartment.migration_compartment[0].id} where target.metrics.namespace='ocb_asset'"
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {}
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "discovery_service_policy_any_migration" {
  provider       = oci.homeregion
  count          = local.any_migration ? 1 : 0
  name           = "discovery-service-policy-any-migration"
  description    = "Discovery service policy needed for any migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow service ${local.ocb_discovery_service} to inspect compartments in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow service ${local.ocb_discovery_service} to read ocb-environments in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow service ${local.ocb_discovery_service} to manage ocb-inventory-asset in compartment id ${oci_identity_compartment.migration_compartment[0].id}"
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},

  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "discovery_service_policy_vmware_migration" {
  provider       = oci.homeregion
  count          = local.migration_from_vmware ? 1 : 0
  name           = "discovery-service-policy-vmware-migration"
  description    = "Discovery service policy needed for VMware migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow service ${local.ocb_discovery_service} to read ocb-agents in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {}
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "hydration_agent_policy_any_migration" {
  provider       = oci.homeregion
  count          = local.any_migration ? 1 : 0
  name           = "hydration-agent-policy-any-migration"
  description    = "Hydration agent policy needed for any migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.hydration_agent_dg[0].name} to { OCM_HYDRATION_AGENT_TASK_INSPECT, OCM_HYDRATION_AGENT_TASK_UPDATE, OCM_HYDRATION_AGENT_REPORT_STATUS } in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {},

  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "hydration_agent_policy_vmware_migration" {
  provider       = oci.homeregion
  count          = local.migration_from_vmware ? 1 : 0
  name           = "hydration-agent-policy-vmware-migration"
  description    = "Hydration agent policy needed for VMware migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.hydration_agent_dg[0].name} to read objects in compartment id ${oci_identity_compartment.migration_compartment[0].id}"
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.migration_from_vmware == true ? local.vmware_defined_tags : {}
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "hydration_agent_policy_cld_migration" {
  provider       = oci.homeregion
  count          = 0
  name           = "hydration-agent-policy-cld-migration"
  description    = "Hydration agent policy needed for cloud migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.hydration_agent_dg[0].name} to manage objects in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.hydration_agent_dg[0].name} to read secret-family in compartment id ${oci_identity_compartment.migration_secrets_compartment[0].id}"
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.cld_defined_tags
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}

resource "oci_identity_policy" "asset_source_policy_cld_migration" {
  provider       = oci.homeregion
  count          = 0
  name           = "asset-source-policy-cld-migration"
  description    = "Asset source policy needed for cloud migration"
  compartment_id = var.compartment_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.asset_source_dg[0].name} to use metrics in compartment id ${oci_identity_compartment.migration_compartment[0].id} where target.metrics.namespace='ocb_asset'",
    "Allow dynamic-group ${oci_identity_dynamic_group.asset_source_dg[0].name} to read secret-family in compartment id ${oci_identity_compartment.migration_secrets_compartment[0].id}"
  ]
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    local.cld_defined_tags
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.cld_use_case_tag
  ]
}
