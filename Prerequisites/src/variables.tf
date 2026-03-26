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

variable "enabled_migration_scenario" {
  type        = string
  description = "Enabled migration scenario selection. Valid values: VMware to OCI, VMware to OLVM, AWS to OCI."
  default     = ""

  validation {
    condition     = (!var.primary_prerequisite_stack) || contains(["VMware to OCI", "VMware to OLVM", "AWS to OCI"], var.enabled_migration_scenario)
    error_message = "Primary prerequisite stacks require selecting a valid enabled_migration_scenario (VMware to OCI, VMware to OLVM, AWS to OCI)."
  }
}

variable "add_vmware_to_oci" {
  type        = bool
  description = "Enable VMware VM to OCI migrations in addition to the primary scenario."
  default     = false
}

variable "add_vmware_to_olvm" {
  type        = bool
  description = "Enable VMware VM to OLVM migrations in addition to the primary scenario."
  default     = false
}

variable "add_aws_to_oci" {
  type        = bool
  description = "Enable AWS EC2 to OCI migrations in addition to the primary scenario."
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

  validation {
    condition = (!var.primary_prerequisite_stack) || (!var.remote_agent_logging) || (
      contains(["VMware to OCI", "VMware to OLVM"], var.enabled_migration_scenario) ||
      var.add_vmware_to_oci ||
      var.add_vmware_to_olvm
    )
    error_message = "remote_agent_logging can only be enabled when a VMware scenario is enabled (VMware to OCI or VMware to OLVM)."
  }
}
variable "hydration_agent_logging" {
  type        = bool
  description = "Create service policies allowing Hydration Agents to upload logs."
  default     = false

  validation {
    condition = (!var.primary_prerequisite_stack) || (!var.hydration_agent_logging) || (
      contains(["VMware to OCI", "AWS to OCI"], var.enabled_migration_scenario) ||
      var.add_vmware_to_oci ||
      var.add_aws_to_oci
    )
    error_message = "hydration_agent_logging can only be enabled when a migration to OCI scenario is enabled (VMware to OCI or AWS to OCI)."
  }
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
