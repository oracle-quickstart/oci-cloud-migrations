resource "oci_objectstorage_bucket" "replication_bucket" {
  count          = var.create_replication_bucket && local.any_migration ? 1 : 0
  compartment_id = oci_identity_compartment.migration_compartment[0].id
  name           = var.replication_bucket
  namespace      = data.oci_objectstorage_namespace.objectstorage_namespace.namespace
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