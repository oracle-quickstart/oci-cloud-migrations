resource "oci_objectstorage_bucket" "ReplicationBucket" {
  compartment_id = oci_identity_compartment.Migration.id
  name           = var.replication_bucket
  namespace      = data.oci_objectstorage_namespace.objectstorage_namespace.namespace
}