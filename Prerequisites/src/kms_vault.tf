resource "oci_kms_vault" "ocm_secrets" {
  display_name   = "ocm-secrets"
  count          = local.any_migration ? 1 : 0
  compartment_id = oci_identity_compartment.migration_secrets_compartment[0].id
  vault_type     = "DEFAULT"
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

resource "oci_kms_key" "ocm_key" {
  compartment_id = oci_identity_compartment.migration_secrets_compartment[0].id
  count          = local.any_migration ? 1 : 0
  display_name   = "ocm-key"
  key_shape {
    algorithm = "AES"
    length    = "32"
  }
  management_endpoint = oci_kms_vault.ocm_secrets[0].management_endpoint
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