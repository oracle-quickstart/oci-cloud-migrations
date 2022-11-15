## Copyright (c) 2019-2022 Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

resource "oci_identity_policy" "HydrationAgentLoggingPolicy" {
  provider       = oci.homeregion
  name           = "HydrationAgentLoggingPolicy"
  description    = "HydrationAgentLoggingPolicy"
  compartment_id = var.tenancy_ocid
  statements = [
    "Define tenancy OCM-SERVICE AS ocid1.tenancy.oc1..aaaaaaaartv6j5muce2s4djz7rvfn2vwceq3cnue33d72isntnlfmi7huv7q",
    "Endorse dynamic-group ${oci_identity_dynamic_group.HydrationAgentDynamicGroup.name} to { OBJECT_CREATE } in tenancy OCM-SERVICE where all { target.bucket.name = '${var.tenancy_ocid}' }"
  ]
}

resource "oci_identity_policy" "RemoteAgentLoggingPolicy" {
  provider       = oci.homeregion
  name           = "RemoteAgentLoggingPolicy"
  description    = "RemoteAgentLoggingPolicy"
  compartment_id = var.tenancy_ocid
  statements = [
    "Define tenancy OCB-SERVICE as ocid1.tenancy.oc1..aaaaaaaahr2xcduf4knzkzhkzt442t66bpqt3aazss6cy2ll6x4xj3ci7tiq",
    "Endorse dynamic-group ${oci_identity_dynamic_group.RemoteAgentDynamicGroup.name} to { OBJECT_CREATE } in tenancy OCB-SERVICE"
  ]
}