resource "oci_objectstorage_bucket" "replication_bucket" {
  count = (var.create_replication_bucket && local.any_migration) || (var.create_replication_bucket && !local.primary_prerequisite_stack) ? 1 : 0
  compartment_id = (
    local.primary_prerequisite_stack ?
    oci_identity_compartment.migration_compartment[0].id :
    data.oci_identity_compartments.existing_migration_compartment.compartments[0].id
  )
  name      = var.replication_bucket
  namespace = data.oci_objectstorage_namespace.objectstorage_namespace.namespace
  defined_tags = merge({
    "${local.ocm_migration_tag_namespace}.${local.version_tag}"        = local.version_value,
    "${local.ocm_migration_tag_namespace}.${local.resource_level_tag}" = local.resource_level_values[1]
    },
    var.migration_from_vmware == true ? local.vmware_defined_tags : {},
    var.migration_from_aws == true ? local.aws_defined_tags : {},
  )
  depends_on = [
    oci_identity_tag_namespace.migration_tag_namespace,
    oci_identity_tag.version_tag,
    oci_identity_tag.resource_level_tag,
    oci_identity_tag.vmware_use_case_tag,
    oci_identity_tag.aws_use_case_tag
  ]
}