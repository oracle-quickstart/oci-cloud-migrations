resource "oci_events_rule" "oracle_cloud_migrations_nat_gateway" {
  actions {
    actions {
      action_type = "FAAS"
      function_id = oci_functions_function.terminate_nat_gateway.id
      is_enabled  = "true"
    }
  }
  compartment_id = var.compartment_ocid
  condition      = "{\"eventType\":[\"com.oraclecloud.virtualnetwork.createroutetable\",\"com.oraclecloud.virtualnetwork.updateroutetable\"],\"data\":{\"compartmentId\":[\"${data.oci_identity_compartment.compartment.id}\"]}}"
  display_name   = "route_table_update"
  is_enabled     = "true"
}