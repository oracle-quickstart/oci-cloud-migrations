resource "oci_identity_dynamic_group" "OracleCloudMigrationsFunctionDynamicGroup" {
  provider       = oci.homeregion
  name           = "OracleCloudMigrationsFunctionDynamicGroup"
  description    = "All functions in the ${data.oci_identity_compartment.compartment.name} compartment."
  compartment_id = var.tenancy_ocid
  matching_rule  = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"
}


resource "oci_identity_policy" "OracleCloudMigrationsFunctionPolicy" {
  provider       = oci.homeregion
  name           = "OracleCloudMigrationsFunctionPolicy"
  description    = "Policy for NAT Gateway Termination."
  compartment_id = var.tenancy_ocid
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.OracleCloudMigrationsFunctionDynamicGroup.name} to manage virtual-network-family in compartment id ${data.oci_identity_compartment.compartment.id}"
    ]
}
