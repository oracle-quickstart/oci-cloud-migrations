provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  region           = var.region
}

# ## Required for IAM resource creation. IAM resource must be created in the tenancy home region.
provider "oci" {
  alias            = "homeregion"
  tenancy_ocid     = var.tenancy_ocid
  region           = local.home_region
}

locals {
  region_map = {
    for r in data.oci_identity_regions.regions.regions :
    r.key => r.name
  }

  home_region = lookup(local.region_map, data.oci_identity_tenancy.tenancy.home_region_key)
}
