## Copyright © 2021, Oracle and/or its affiliates. 
## All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl

resource "oci_identity_compartment" "Migration" {
  provider       = oci.homeregion
  name           = "Migration"
  description    = "Compartment for OCM resources."
  compartment_id = var.tenancy_ocid
  enable_delete  = false
}
resource "oci_identity_compartment" "MigrationSecrets" {
  provider       = oci.homeregion
  name           = "MigrationSecrets"
  description    = "Compartment for OCM secrets."
  compartment_id = var.tenancy_ocid
  enable_delete  = false
}

resource "oci_identity_dynamic_group" "MigrationDynamicGroup" {
  provider       = oci.homeregion
  name           = "MigrationDynamicGroup"
  description    = "All ocmmigration resource types in the ${oci_identity_compartment.Migration.name} compartment."
  compartment_id = var.tenancy_ocid
  matching_rule  = "All { resource.type = 'ocmmigration', resource.compartment.id = '${oci_identity_compartment.Migration.id}' }"
}

resource "oci_identity_dynamic_group" "RemoteAgentDynamicGroup" {
  provider       = oci.homeregion
  name           = "RemoteAgentDynamicGroup"
  description    = "All ocbagent resource types."
  compartment_id = var.tenancy_ocid
  matching_rule  = "Any { resource.type = 'ocbagent' }"
}

resource "oci_identity_dynamic_group" "DiscoveryPluginDynamicGroup" {
  provider       = oci.homeregion
  name           = "DiscoveryPluginDynamicGroup"
  description    = "All ocbagent resource types."
  compartment_id = var.tenancy_ocid
  matching_rule  = "Any { resource.type = 'ocbagent' }"
}

resource "oci_identity_dynamic_group" "ReplicationPluginDynamicGroup" {
  provider       = oci.homeregion
  name           = "ReplicationPluginDynamicGroup"
  description    = "All ocbagent resource types."
  compartment_id = var.tenancy_ocid
  matching_rule  = "Any { resource.type = 'ocbagent' }"
}

resource "oci_identity_dynamic_group" "HydrationAgentDynamicGroup" {
  provider       = oci.homeregion
  name           = "HydrationAgentDynamicGroup"
  description    = "All all instances in the ${oci_identity_compartment.Migration.name} compartment."
  compartment_id = var.tenancy_ocid
  matching_rule  = "ALL { instance.compartment.id = '${oci_identity_compartment.Migration.id}'}"
}

resource "oci_identity_policy" "MigrationServicePolicy" {
  provider       = oci.homeregion
  name           = "MigrationServicePolicy"
  description    = "MigrationServicePolicy"
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} to manage instance-family in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} to manage compute-image-capability-schema in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} to manage virtual-network-family in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} to manage volume-family in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} to manage object-family in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} to read ocb-inventory in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} to read ocb-inventory-asset in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} { OCB_CONNECTOR_READ, OCB_CONNECTOR_DATA_READ, OCB_ASSET_SOURCE_READ, OCB_ASSET_SOURCE_CONNECTOR_DATA_UPDATE } in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} { INSTANCE_IMAGE_INSPECT, INSTANCE_IMAGE_READ } in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} { INSTANCE_INSPECT } in tenancy where any { request.operation='ListShapes' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} { DEDICATED_VM_HOST_READ } in tenancy where any { request.operation='GetDedicatedVmHost' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} { CAPACITY_RESERVATION_READ } in tenancy where any { request.operation='GetComputeCapacityReservation' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} { ORGANIZATIONS_SUBSCRIPTION_INSPECT } in tenancy where any { request.operation='ListSubscriptions' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} to read rate-cards in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.MigrationDynamicGroup.name} to use metrics in tenancy where target.metrics.namespace='ocb_asset'"

  ]
}

resource "oci_identity_policy" "RemoteAgentPolicy" {
  provider       = oci.homeregion
  name           = "RemoteAgentPolicy"
  description    = "RemoteAgentPolicy"
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to manage buckets in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to manage object-family in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} { OCM_REPLICATION_TASK_READ, OCM_REPLICATION_TASK_UPDATE } in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to use ocb-asset-source-connectors in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to use ocb-connectors in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to manage ocb-inventory in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to manage ocb-inventory-asset in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to read secret-family in compartment ${oci_identity_compartment.MigrationSecrets.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to use metrics in compartment ${oci_identity_compartment.Migration.name} where target.metrics.namespace='ocb_asset'",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to {OCM_CONNECTOR_INSPECT, OCM_ASSET_SOURCE_READ, OCM_ASSET_SOURCE_CONNECTION_PUSH} in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to {OCB_AGENT_INSPECT, OCB_AGENT_SYNC, OCB_AGENT_READ, OCB_AGENT_DEPENDENCY_INSPECT, OCB_AGENT_DEPENDENCY_READ, OCB_AGENT_KEY_UPDATE, OCB_AGENT_TASK_READ, OCB_AGENT_ASSET_SOURCES_INSPECT, OCB_AGENT_TASK_UPDATE} in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to {OCB_ASSET_SOURCE_INSPECT, OCB_ASSET_SOURCE_READ, OCB_ASSET_SOURCE_ASSET_HANDLES_PUSH, OCB_ASSET_SOURCE_CONNECTION_PUSH} in compartment ${oci_identity_compartment.Migration.name}"

  ]
}

resource "oci_identity_policy" "DiscoveryPluginPolicy" {
  provider       = oci.homeregion
  name           = "DiscoveryPluginPolicy"
  description    = "DiscoveryPluginPolicy"
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.DiscoveryPluginDynamicGroup.name} to use ocb-connectors in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.DiscoveryPluginDynamicGroup.name} to use ocb-asset-source-connectors in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.DiscoveryPluginDynamicGroup.name} to read ocb-inventory in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.DiscoveryPluginDynamicGroup.name} to manage ocb-inventory-asset in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.DiscoveryPluginDynamicGroup.name} to read secret-family in compartment ${oci_identity_compartment.MigrationSecrets.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.DiscoveryPluginDynamicGroup.name} to use metrics in compartment ${oci_identity_compartment.Migration.name} where target.metrics.namespace='ocb_asset'"
  ]
}

resource "oci_identity_policy" "ReplicationPluginPolicy" {
  provider       = oci.homeregion
  name           = "ReplicationPluginPolicy"
  description    = "ReplicationPluginPolicy"
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.ReplicationPluginDynamicGroup.name} to { OCB_AGENT_INSPECT, OCB_AGENT_SYNC, OCB_AGENT_READ, OCB_AGENT_DEPENDENCY_INSPECT, OCB_AGENT_DEPENDENCY_READ, OCB_AGENT_KEY_UPDATE, OCB_AGENT_TASK_READ, OCB_AGENT_ASSET_SOURCES_INSPECT, OCB_AGENT_TASK_UPDATE } in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.ReplicationPluginDynamicGroup.name} to { OCM_REPLICATION_TASK_INSPECT, OCM_REPLICATION_TASK_READ, OCM_REPLICATION_TASK_UPDATE, OCM_CONNECTOR_INSPECT, OCM_ASSET_SOURCE_READ, OCM_ASSET_SOURCE_CONNECTION_PUSH } in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.ReplicationPluginDynamicGroup.name} to { BUCKET_INSPECT, BUCKET_READ, OBJECTSTORAGE_NAMESPACE_READ, OBJECT_CREATE, OBJECT_DELETE, OBJECT_INSPECT, OBJECT_OVERWRITE, OBJECT_READ } in compartment ${oci_identity_compartment.Migration.name} where all { target.bucket.name='${oci_objectstorage_bucket.ReplicationBucket.name}' }",
    "Allow dynamic-group ${oci_identity_dynamic_group.ReplicationPluginDynamicGroup.name} to use ocb-connectors in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.ReplicationPluginDynamicGroup.name} to use ocb-asset-source-connectors in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.ReplicationPluginDynamicGroup.name} to manage ocb-inventory in tenancy",
    "Allow dynamic-group ${oci_identity_dynamic_group.ReplicationPluginDynamicGroup.name} to manage ocb-inventory-asset in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.ReplicationPluginDynamicGroup.name} to read secret-family in compartment ${oci_identity_compartment.MigrationSecrets.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.ReplicationPluginDynamicGroup.name} to use metrics in compartment ${oci_identity_compartment.Migration.name} where target.metrics.namespace='ocb_asset'"

  ]
}

resource "oci_identity_policy" "DiscoveryServicePolicy" {
  provider       = oci.homeregion
  name           = "DiscoveryServicePolicy"
  description    = "DiscoveryServicePolicy"
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow service ocb-discovery to read ocb-environment in compartment ${oci_identity_compartment.Migration.name}",
    "Allow service ocb-discovery to read ocb-agents in compartment ${oci_identity_compartment.Migration.name}",
    "Allow service ocb-discovery to read ocb-inventory in tenancy",
    "Allow service ocb-discovery to manage ocb-inventory-asset in compartment ${oci_identity_compartment.Migration.name}",
    "Allow service ocb-discovery to { TENANCY_INSPECT } in tenancy"
  ]
}

resource "oci_identity_policy" "HydrationAgentPolicy" {
  provider       = oci.homeregion
  name           = "HydrationAgentPolicy"
  description    = "HydrationAgentPolicy"
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.HydrationAgentDynamicGroup.name} to { OCM_HYDRATION_AGENT_TASK_INSPECT, OCM_HYDRATION_AGENT_TASK_UPDATE, OCM_HYDRATION_AGENT_REPORT_STATUS } in compartment ${oci_identity_compartment.Migration.name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.HydrationAgentDynamicGroup.name} to read objects in compartment ${oci_identity_compartment.Migration.name}"
  ]
}

