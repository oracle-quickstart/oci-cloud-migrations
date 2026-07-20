locals {
  realm = try(lower(split(".", var.tenancy_ocid)[2]), "")

  ocm_service_tenancy_ocids_by_realm = {
    oc1 = "ocid1.tenancy.oc1..aaaaaaaartv6j5muce2s4djz7rvfn2vwceq3cnue33d72isntnlfmi7huv7q"
  }

  ocb_service_tenancy_ocids_by_realm = {
    oc1 = "ocid1.tenancy.oc1..aaaaaaaahr2xcduf4knzkzhkzt442t66bpqt3aazss6cy2ll6x4xj3ci7tiq"
  }

  ocm_service_tenancy_ocid = trimspace(var.ocm-service-tenancy-ocid) != "" ? trimspace(var.ocm-service-tenancy-ocid) : lookup(local.ocm_service_tenancy_ocids_by_realm, local.realm, "")
  ocb_service_tenancy_ocid = trimspace(var.ocb-service-tenancy-ocid) != "" ? trimspace(var.ocb-service-tenancy-ocid) : lookup(local.ocb_service_tenancy_ocids_by_realm, local.realm, "")
}
