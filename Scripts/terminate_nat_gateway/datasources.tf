data "oci_identity_tenancy" "tenancy" {
  tenancy_id = var.tenancy_ocid
}

data "oci_identity_compartment" "compartment" {
  id = var.compartment_ocid
}

data "oci_identity_regions" "regions" {
}

data "oci_objectstorage_namespace" "tenancy_namespace" {
  compartment_id = var.tenancy_ocid
}

data "oci_identity_availability_domains" "availability_domains" {
  compartment_id = var.tenancy_ocid
}

data "oci_identity_region_subscriptions" "region_subscriptions" {
  tenancy_id = var.tenancy_ocid
  filter {
    name   = "region_name"
    values = [var.region]
  }
}