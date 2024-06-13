resource "oci_logging_log_group" "oracle_cloud_migrations_logs" {
  compartment_id = var.compartment_ocid
  description    = "oracle_cloud_migrations_logs"
  display_name   = "oracle_cloud_migrations_logs"
}

resource "oci_logging_log" "oracle_cloud_migrations_nat_gateway" {
  configuration {
    compartment_id = var.compartment_ocid
    source {
      category    = "ruleexecutionlog"
      resource    = oci_events_rule.oracle_cloud_migrations_nat_gateway.id
      service     = "cloudevents"
      source_type = "OCISERVICE"
    }
  }
  display_name       = "oracle_cloud_migrations_nat_gateway"
  is_enabled         = "true"
  log_group_id       = oci_logging_log_group.oracle_cloud_migrations_logs.id
  log_type           = "SERVICE"
  retention_duration = "30"
}