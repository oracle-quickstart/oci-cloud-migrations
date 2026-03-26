resource "oci_objectstorage_bucket" "replication_bucket" {
  count          = var.create_replication_bucket ? 1 : 0
  compartment_id = local.migration_compartment_id
  name           = var.replication_bucket
  namespace      = data.oci_objectstorage_namespace.objectstorage_namespace.namespace

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
