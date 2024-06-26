## Copyright © 2021, Oracle and/or its affiliates. 
## All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl

terraform {
  required_providers {
    # Recommendation from ORM / OCI provider teams
    oci = {
      version = ">= 4.21.0"
    }
  }
}
