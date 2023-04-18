## Copyright (c) 2019-2022 Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

resource "oci_cloud_bridge_inventory" "Inventory" {
  compartment_id = var.tenancy_ocid
  display_name   = "Inventory"
}