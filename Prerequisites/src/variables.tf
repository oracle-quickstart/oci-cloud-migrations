variable "tenancy_ocid" {
  type        = string
  description = "Your tenancy OCID."
}

variable "compartment_ocid" {
  type        = string
  description = "Your Oracle Cloud Migrations compartment OCID."
}

variable "replication_bucket" {
  type        = string
  description = "The name of the Object Storage bucket where Oracle Cloud Migrations replication snapshots will be stored. If not specified, name \"ocm_replication\" is going to be used."
  default     = "ocm_replication"
}

variable "create_replication_bucket" {
  type        = bool
  description = "Whether an object storage bucket for storing Oracle Cloud Migrations replication snapshots should be created. Uncheck this checkbox if you want to use an existing object storage bucket for this purpose. The name of the replication bucket is defined by the value of \"replication_bucket\" variable."
  default     = true
}

variable "create_cloud_migrations_tag_namespace_and_tag_definitions" {
  type        = bool
  description = "Whether the CloudMigrations tag namespace and associated tag definitions should be created. Uncheck this checkbox if these resources have already been created."
  default     = true
}
variable "migration_from_aws" {
  type        = bool
  description = "Whether the resources needed for AWS migration should be created. Check this checkbox if you are going to migrate from AWS."
  default     = false
}

variable "migration_from_vmware" {
  type        = bool
  description = "Whether the resources needed for VMware migration should be created. Check this checkbox if you are going to migrate from VMware."
  default     = false
}

variable "primary_prerequisite_stack" {
  type        = bool
  description = "Deploy tenancy-level resource required for Oracle Cloud Migrations."
  default     = true
}

variable "migration_groups" {
  type        = bool
  description = "Create base policies for migration administrators and operators."
  default     = false
}
variable "remote_agent_logging" {
  type        = bool
  description = "Create service policies allowing Remote Agent Appliances to upload logs."
  default     = false
}
variable "hydration_agent_logging" {
  type        = bool
  description = "Create service policies allowing Hydration Agents to upload logs."
  default     = false
}

variable "ocb-service-tenancy-ocid" {
  type        = string
  description = "Realm OCID of the Oracle Cloud Bridge service tenancy."
  default     = "ocid1.tenancy.oc1..aaaaaaaahr2xcduf4knzkzhkzt442t66bpqt3aazss6cy2ll6x4xj3ci7tiq"
}

variable "ocm-service-tenancy-ocid" {
  type        = string
  description = "Realm OCID of the Oracle Cloud Migrations service tenancy."
  default     = "ocid1.tenancy.oc1..aaaaaaaartv6j5muce2s4djz7rvfn2vwceq3cnue33d72isntnlfmi7huv7q"
}