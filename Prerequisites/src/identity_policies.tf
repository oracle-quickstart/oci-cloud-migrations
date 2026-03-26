# This file contains all the policy resources required for service functionalities

locals {
  migration_dg_name                = try(oci_identity_dynamic_group.migration_dg[0].name, "")
  discovery_dg_name                = try(oci_identity_dynamic_group.discovery_dg[0].name, "")
  remote_agent_and_plugins_dg_name = try(oci_identity_dynamic_group.remote_agent_and_plugins_dg[0].name, "")
  hydration_agent_dg_name          = try(oci_identity_dynamic_group.hydration_agent_dg[0].name, "")

  # Tenancy level policy statements
  hydration_agent_logging_define_statements = [
    "Define tenancy OCM-SERVICE AS ${var.ocm-service-tenancy-ocid}"
  ]
  remote_agent_logging_define_statements = [
    "Define tenancy OCB-SERVICE as ${var.ocb-service-tenancy-ocid}"
  ]
  hydration_agent_logging_endorse_statements = [
    "Endorse dynamic-group ${local.hydration_agent_dg_name} to { OBJECT_CREATE } in tenancy OCM-SERVICE where all { target.bucket.name = '${var.tenancy_ocid}' }"
  ]
  remote_agent_logging_endorse_statements = [
    "Endorse dynamic-group ${local.remote_agent_and_plugins_dg_name} to { OBJECT_CREATE } in tenancy OCB-SERVICE"
  ]
  migration_dg_tenancy_level_any_migration_statements = [
    "Allow dynamic-group ${local.migration_dg_name} to read ocb-inventory in tenancy",
    "Allow dynamic-group ${local.migration_dg_name} to { INSTANCE_INSPECT } in tenancy where any { request.operation='ListShapes' }",
    "Allow dynamic-group ${local.migration_dg_name} to { DEDICATED_VM_HOST_READ } in tenancy where any { request.operation='GetDedicatedVmHost' }",
    "Allow dynamic-group ${local.migration_dg_name} to { CAPACITY_RESERVATION_READ } in tenancy where any { request.operation='GetComputeCapacityReservation' }",
    "Allow dynamic-group ${local.migration_dg_name} to { ORGANIZATIONS_SUBSCRIPTION_INSPECT } in tenancy where any { request.operation='ListSubscriptions' }",
    "Allow dynamic-group ${local.migration_dg_name} to read rate-cards in tenancy",
    "Allow dynamic-group ${local.migration_dg_name} to read metrics in tenancy where target.metrics.namespace='ocb_asset'",
    # Migration Metering feature support
    "Allow dynamic-group ${local.migration_dg_name} to read tag-namespaces in tenancy",
    "Allow dynamic-group ${local.migration_dg_name} to use tag-namespaces in tenancy where target.tag-namespace.name='CloudMigrations'"
  ]
  discovery_dg_tenancy_level_any_migration_statements = [
    "Allow dynamic-group ${local.discovery_dg_name} to read ocb-inventory in tenancy",
    "Allow dynamic-group ${local.discovery_dg_name} to { TENANCY_INSPECT } in tenancy"
  ]
  remote_agent_and_plugins_dg_tenancy_level_vmware_migration_statements = [
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to manage ocb-inventory in tenancy",
    # For replication plugin
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to { OCB_AGENT_INSPECT, OCB_AGENT_SYNC, OCB_AGENT_READ, OCB_AGENT_DEPENDENCY_INSPECT, OCB_AGENT_DEPENDENCY_READ, OCB_AGENT_KEY_UPDATE, OCB_AGENT_TASK_READ, OCB_AGENT_ASSET_SOURCES_INSPECT, OCB_AGENT_TASK_UPDATE } in tenancy"
  ]

  # Compartment level policy statements
  migration_dg_compartment_level_any_migration_statements = [
    "Allow dynamic-group ${local.migration_dg_name} to manage instance-family in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.migration_dg_name} to manage compute-image-capability-schema in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.migration_dg_name} to manage virtual-network-family in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.migration_dg_name} to manage volume-family in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.migration_dg_name} to manage object-family in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.migration_dg_name} to read ocb-inventory-asset in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.migration_dg_name} to { OCB_CONNECTOR_READ, OCB_CONNECTOR_DATA_READ, OCB_ASSET_SOURCE_READ, OCB_ASSET_SOURCE_CONNECTOR_DATA_UPDATE } in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.migration_dg_name} to { INSTANCE_IMAGE_INSPECT, INSTANCE_IMAGE_READ } in compartment id ${local.migration_compartment_id}"
  ]
  remote_agent_and_plugins_dg_compartment_level_vmware_migration_statements = [
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to manage buckets in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to manage object-family in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to { OCM_REPLICATION_TASK_INSPECT, OCM_REPLICATION_TASK_READ, OCM_REPLICATION_TASK_UPDATE } in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to use ocb-asset-source-connectors in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to use ocb-connectors in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to manage ocb-inventory-asset in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to read secret-family in compartment id ${local.migration_secrets_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to use metrics in compartment id ${local.migration_compartment_id} where target.metrics.namespace='ocb_asset'",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to { OCM_CONNECTOR_INSPECT, OCM_ASSET_SOURCE_READ, OCM_ASSET_SOURCE_CONNECTION_PUSH} in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to { OCB_AGENT_INSPECT, OCB_AGENT_SYNC, OCB_AGENT_READ, OCB_AGENT_DEPENDENCY_INSPECT, OCB_AGENT_DEPENDENCY_READ, OCB_AGENT_KEY_UPDATE, OCB_AGENT_TASK_READ, OCB_AGENT_ASSET_SOURCES_INSPECT, OCB_AGENT_TASK_UPDATE, OCB_AGENT_UPDATE_COMMAND_CREATE} in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to { OCB_ASSET_SOURCE_INSPECT, OCB_ASSET_SOURCE_READ, OCB_ASSET_SOURCE_ASSET_HANDLES_PUSH, OCB_ASSET_SOURCE_CONNECTION_PUSH} in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.remote_agent_and_plugins_dg_name} to { BUCKET_INSPECT, BUCKET_READ, OBJECTSTORAGE_NAMESPACE_READ, OBJECT_CREATE, OBJECT_DELETE, OBJECT_INSPECT, OBJECT_OVERWRITE, OBJECT_READ } in compartment id ${local.migration_compartment_id}"
  ]
  discovery_dg_compartment_level_any_migration_statements = [
    "Allow dynamic-group ${local.discovery_dg_name} to read ocb-environment in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.discovery_dg_name} to manage ocb-inventory-asset in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.discovery_dg_name} to inspect compartments in compartment id ${local.migration_compartment_id}"
  ]
  discovery_dg_compartment_level_vmware_migration_statements = [
    "Allow dynamic-group ${local.discovery_dg_name} to read ocb-agents in compartment id ${local.migration_compartment_id}"
  ]
  discovery_dg_compartment_level_service_discovery_migration_statements = [
    "Allow dynamic-group ${local.discovery_dg_name} to use metrics in compartment id ${local.migration_compartment_id} where target.metrics.namespace='ocb_asset'",
    "Allow dynamic-group ${local.discovery_dg_name} to read secret-family in compartment id ${local.migration_secrets_compartment_id}"
  ]
  hydration_agent_dg_compartment_level_any_migration_statements = [
    "Allow dynamic-group ${local.hydration_agent_dg_name} to { OCM_HYDRATION_AGENT_TASK_INSPECT, OCM_HYDRATION_AGENT_TASK_UPDATE, OCM_HYDRATION_AGENT_REPORT_STATUS } in compartment id ${local.migration_compartment_id}"
  ]
  hydration_agent_dg_compartment_level_vmware_migration_statements = [
    "Allow dynamic-group ${local.hydration_agent_dg_name} to read objects in compartment id ${local.migration_compartment_id}"
  ]
  hydration_agent_dg_compartment_level_aws_migration_statements = [
    "Allow dynamic-group ${local.hydration_agent_dg_name} to manage objects in compartment id ${local.migration_compartment_id}",
    "Allow dynamic-group ${local.hydration_agent_dg_name} to read secret-family in compartment id ${local.migration_secrets_compartment_id}"
  ]
}

# Consolidated Tenancy Level Policy
resource "oci_identity_policy" "ocm_tenancy_level_policy" {
  provider       = oci.homeregion
  count          = local.iam_enabled ? 1 : 0
  name           = "${local.prefix}-ocm-tenancy-level-policy"
  description    = "Tenancy level policy for migrations."
  compartment_id = var.tenancy_ocid
  statements = concat(
    # DEFINE statements must be at the beginning
    # DEFINE statement for hydration_agent_logging
    var.hydration_agent_logging ? local.hydration_agent_logging_define_statements : [],
    # DEFINE statement for remote_agent_logging
    var.remote_agent_logging && local.migration_from_vmware ? local.remote_agent_logging_define_statements : [],

    # ENDORSE statement for hydration_agent_logging
    var.hydration_agent_logging && local.migration_to_oci ? local.hydration_agent_logging_endorse_statements : [],
    # ENDORSE statement for remote_agent_logging
    var.remote_agent_logging && local.migration_from_vmware ? local.remote_agent_logging_endorse_statements : [],

    # Statements for ocm_tenancy_level_policy_any_migration
    local.migration_dg_tenancy_level_any_migration_statements,
    local.discovery_dg_tenancy_level_any_migration_statements,

    # Statements for ocm_tenancy_level_policy_vmware_migration
    local.migration_from_vmware ? local.remote_agent_and_plugins_dg_tenancy_level_vmware_migration_statements : []
  )
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

# created in customer selected compartment
# Consolidated Compartment Level Policy
resource "oci_identity_policy" "ocm_compartment_level_policy" {
  provider       = oci.homeregion
  count          = local.iam_enabled ? 1 : 0
  name           = "${local.prefix}-ocm-compartment-level-policy"
  description    = "Compartment level policy for migrations."
  compartment_id = var.compartment_ocid
  statements = concat(
    # Statements for migration_service_policy_any_migration
    local.migration_dg_compartment_level_any_migration_statements,
    # Statements for remote_agent_policy_vmware_migration, discovery_plugin_policy_vmware_migration and replication_plugin_policy_vmware_migration
    local.migration_from_vmware ? local.remote_agent_and_plugins_dg_compartment_level_vmware_migration_statements : [],
    # Statements for discovery_service_policy_any_migration
    local.discovery_dg_compartment_level_any_migration_statements,
    # Statements for discovery_service_policy_vmware_migration
    local.migration_from_vmware ? local.discovery_dg_compartment_level_vmware_migration_statements : [],
    # Statements for discovery_service_policy_service_discovery_migration
    local.migration_from_aws || local.migration_to_olvm ? local.discovery_dg_compartment_level_service_discovery_migration_statements : [],
    # Statements for hydration_agent_policy_any_migration
    local.migration_to_oci ? local.hydration_agent_dg_compartment_level_any_migration_statements : [],
    # Statements for hydration_agent_policy_vmware_migration
    local.migration_from_vmware_to_oci ? local.hydration_agent_dg_compartment_level_vmware_migration_statements : [],
    # Statements for hydration_agent_policy_aws_migration
    local.migration_from_aws ? local.hydration_agent_dg_compartment_level_aws_migration_statements : []
  )
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
