resource "oci_kms_vault" "OCMSecrets" {
  display_name   = "OCMSecrets"
  compartment_id = oci_identity_compartment.MigrationSecrets.id
  vault_type     = "DEFAULT"
}

resource "oci_kms_key" "MainKey" {
  compartment_id = oci_identity_compartment.MigrationSecrets.id
  display_name   = "MainKey"
  key_shape {
    algorithm = "AES"
    length    = "32"
  }
  management_endpoint = oci_kms_vault.OCMSecrets.management_endpoint
}