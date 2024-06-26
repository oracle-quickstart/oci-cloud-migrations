## Copyright © 2021, Oracle and/or its affiliates. 
## All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl

variable "tenancy_ocid" {}
variable "region" {}

variable "compartment_ocid" {
  type        = string
  description = "The compartment that resources will be deployed in."
}

variable "subnet_ocid" {
  type        = string
  description = "Subnet used to launch the function."
}

variable "ocir_repo_name" {
  type    = string
  default = "oracle_cloud_migrations_override"
}

variable "ocir_user_name" {
  type        = string
  description = "User name that will push docker images to the container registry."
  validation {
    condition     = length(var.ocir_user_name) > 0
    error_message = "Required."
  }
}

variable "ocir_password" {
  type        = string
  description = "Auth Token for the user that will push docker images to the container registry."
  sensitive   = true
  validation {
    condition     = length(var.ocir_password) > 0
    error_message = "Required."
  }
}

variable "terminate_nat_gateway_function_version" {
  type    = string
  default = "1.0.0"
}
