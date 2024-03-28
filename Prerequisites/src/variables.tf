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