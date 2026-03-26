# This file contains all the identity resources required for admin/operator access to perform migrations

resource "oci_identity_group" "migration_administrators_group" {
  provider       = oci.homeregion
  count          = local.migration_groups_enabled ? 1 : 0
  name           = "${local.prefix}-ocm-administrators-group"
  description    = "Users maintaining connectivity to source environments for the Oracle Cloud Migrations service."
  compartment_id = var.tenancy_ocid
}

resource "oci_identity_policy" "migration_administrators_policy" {
  provider       = oci.homeregion
  count          = local.migration_groups_enabled ? 1 : 0
  name           = "${local.prefix}-ocm-administrators-policy"
  description    = "Allow users to manage components used for migration."
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to manage ocb-environment in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to manage ocb-agent in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to use object-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to manage objects in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to manage ocb-agent-dependency in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to manage ocb-asset-sources in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to manage ocb-discovery-schedules in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to read ocb-workrequests in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to use vaults in compartment id ${oci_identity_compartment.migration_secrets_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to use key-family in compartment id ${oci_identity_compartment.migration_secrets_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to manage secret-family in compartment id ${oci_identity_compartment.migration_secrets_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to manage ocb-inventory in tenancy",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to manage ocb-inventory-asset in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to {OCB_INVENTORY_ASSET_READ} in tenancy",
    "Allow group ${oci_identity_group.migration_administrators_group[0].name} to {COMPARTMENT_INSPECT, COMPARTMENT_READ} in tenancy"
  ]
}
resource "oci_identity_group" "migration_operators_group" {
  provider       = oci.homeregion
  count          = local.migration_groups_enabled ? 1 : 0
  name           = "${local.prefix}-ocm-operators-group"
  description    = "Users performing migrations using the Oracle Cloud Migrations service."
  compartment_id = var.tenancy_ocid
}
resource "oci_identity_policy" "migration_operators_policy" {
  provider       = oci.homeregion
  count          = local.migration_groups_enabled ? 1 : 0
  name           = "${local.prefix}-ocm-operators-policy"
  description    = "Allow users to manage migration projects and launch target assets."
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to manage ocm-migration-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to read ocb-inventory in tenancy",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to manage ocb-inventory-asset in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to read ocb-asset-sources in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to read object-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to manage volume-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to manage orm-stacks in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to manage orm-jobs in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to read metrics in compartment id ${oci_identity_compartment.migration_compartment[0].id} where target.metrics.namespace='ocb_asset'",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to {COMPARTMENT_INSPECT, COMPARTMENT_READ} in tenancy",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to read instance-family in compartment id ${oci_identity_compartment.migration_compartment[0].id}",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to read tag-namespaces in tenancy",
    "Allow group ${oci_identity_group.migration_operators_group[0].name} to use tag-namespaces in tenancy where target.tag-namespace.name='CloudMigrations'",
    ## Additionally required to launch instances and use network any destination compartment.
    # "Allow group ${oci_identity_group.migration_operators_group[0].name} to use virtual-network-family in compartment Production",
    # "Allow group ${oci_identity_group.migration_operators_group[0].name} to read vcns in compartment Production",
    # "Allow group ${oci_identity_group.migration_operators_group[0].name} to read subnets in compartment Production",
    # "Allow group ${oci_identity_group.migration_operators_group[0].name} to read dedicated-vm-hosts in compartment Production",
    # "Allow group ${oci_identity_group.migration_operators_group[0].name} to manage instance-family in compartment Production",
  ]
}
