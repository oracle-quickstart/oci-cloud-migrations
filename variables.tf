## Copyright (c) 2019-2022 Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "region" {}

variable "replication_bucket" {
  default = "ocm_replication"
}

variable "migration_compartment" {
  default = "Migration"
}

variable "migration_secrets_compartment" {
  default = "MigrationSecrets"
}