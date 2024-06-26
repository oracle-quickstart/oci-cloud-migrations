resource "oci_functions_application" "oracle_cloud_migrations_override" {
  compartment_id = var.compartment_ocid
  display_name   = "oracle_cloud_migrations_override"
  subnet_ids     = ["ocid1.subnet.oc1.iad.aaaaaaaaoubnvp662hasqdxr4s4fd3hc5w2bs27jcccxra6i5owf7x5x7bga"]
  syslog_url     = ""
  shape = "GENERIC_ARM"
}

resource "oci_functions_function" "terminate_nat_gateway" {
  depends_on     = [null_resource.terminate_nat_gateway_fn_setup]
  application_id = oci_functions_application.oracle_cloud_migrations_override.id
  display_name   = "terminate_nat_gateway"
  image          = "${local.ocir_docker_repository}/${data.oci_objectstorage_namespace.tenancy_namespace.namespace}/terminate_nat_gateway:${var.terminate_nat_gateway_function_version}"
  memory_in_mbs  = "256"
}