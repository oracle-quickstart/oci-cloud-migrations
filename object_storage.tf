## Copyright (c) 2019-2022 Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

resource "oci_objectstorage_bucket" "ReplicationBucket" {
  compartment_id = oci_identity_compartment.Migration.id
  name           = var.replication_bucket
  namespace      = data.oci_objectstorage_namespace.objectstorage_namespace.namespace
}