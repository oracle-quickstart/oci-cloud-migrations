variable "tenancy_ocid" {
  type        = string
  description = "OCI tenancy OCID for the customer tenancy where the prerequisite stack runs. This is provided by Resource Manager and is not intended to be changed manually."
}

variable "compartment_ocid" {
  type        = string
  description = "Migration Root Compartment OCID. The stack creates or reuses the Migration and MigrationSecrets child compartments under this parent compartment. Leave this aligned with the compartment where you create the stack unless you intentionally want Oracle Cloud Migrations working compartments created somewhere else."
}

variable "replication_bucket" {
  type        = string
  description = "Name of the Object Storage bucket used for Oracle Cloud Migrations replication data. Leave the default to let the stack create the standard bucket name, or change it only when you need to reuse an existing bucket or follow a tenancy-specific naming convention."
  default     = "ocm_replication"
}

variable "create_replication_bucket" {
  type        = bool
  description = "Creates the replication bucket required for VMware-to-OCI and AWS-to-OCI data transfer flows. Leave this enabled for the default setup. Disable it only when you already have an approved existing bucket and want the stack to reuse the name specified by replication_bucket."
  default     = true
}

variable "create_cloud_migrations_tag_namespace_and_tag_definitions" {
  type        = bool
  description = "Creates the CloudMigrations tag namespace and tag definitions used to label prerequisite resources and migration assets. Leave this enabled for a primary stack unless the namespace already exists and should be reused."
  default     = true
}

variable "enabled_migration_scenario" {
  type        = string
  description = "Primary migration scenario enabled by this prerequisite stack. Choose the scenario that best matches the customer's first planned migration path. Additional scenarios can be enabled with the add_* toggles below."
  default     = ""

  validation {
    condition     = contains(["", "VMware to OCI", "VMware to OLVM", "AWS to OCI"], var.enabled_migration_scenario)
    error_message = "Valid values: VMware to OCI, VMware to OLVM, AWS to OCI."
  }
}

variable "add_vmware_to_oci" {
  type        = bool
  description = "Also enable the VMware to OCI prerequisites in addition to the primary scenario selected above. Use this when the same tenancy needs to support more than one migration path."
  default     = false
}

variable "add_vmware_to_olvm" {
  type        = bool
  description = "Also enable the VMware to OLVM prerequisites in addition to the primary scenario selected above. Use this only for customers participating in the VMware to OLVM flow."
  default     = false
}

variable "add_aws_to_oci" {
  type        = bool
  description = "Also enable the AWS to OCI prerequisites in addition to the primary scenario selected above. Use this when the tenancy needs to support both AWS and another migration scenario."
  default     = false
}

variable "primary_prerequisite_stack" {
  type        = bool
  description = "Controls whether this run creates the shared tenancy-level prerequisite resources such as IAM policies, dynamic groups, and the CloudMigrations tag namespace. Leave this enabled for the first prerequisite stack in a tenancy. Disable it only when those global resources already exist and this run should reuse them."
  default     = true
}

variable "migration_groups" {
  type        = bool
  description = "Creates example IAM groups and policies for migration administrators and migration operators. Enable this only when you want the stack to provision those customer-facing operator groups in addition to the service prerequisites."
  default     = false
}
variable "remote_agent_logging" {
  type        = bool
  description = "Creates cross-tenancy policies that allow Remote Agent Appliances used in VMware-based migrations to upload service logs. Enable this only when the customer needs appliance log collection for VMware migrations."
  default     = false

}
variable "hydration_agent_logging" {
  type        = bool
  description = "Creates cross-tenancy policies that allow Hydration Agents to upload service logs for migration-to-OCI workflows. Enable this only when the customer needs hydration agent log collection for VMware-to-OCI or AWS-to-OCI migrations."
  default     = false

}

variable "ocb-service-tenancy-ocid" {
  type        = string
  description = "Optional Oracle Cloud Bridge service tenancy OCID override for the Remote Agent Appliance logging policy. Leave blank in OC1; provide the realm-specific value when enabling this logging policy in another realm."
  default     = ""
  nullable    = false

  validation {
    condition     = var.ocb-service-tenancy-ocid == "" || can(regex("^ocid1\\.tenancy\\.[a-z0-9]+\\.\\.[a-z0-9]+$", var.ocb-service-tenancy-ocid))
    error_message = "The Oracle Cloud Bridge service tenancy override must be empty or a tenancy OCID."
  }
}

variable "ocm-service-tenancy-ocid" {
  type        = string
  description = "Optional Oracle Cloud Migrations service tenancy OCID override for the Hydration Agent logging policy. Leave blank in OC1; provide the realm-specific value when enabling this logging policy in another realm."
  default     = ""
  nullable    = false

  validation {
    condition     = var.ocm-service-tenancy-ocid == "" || can(regex("^ocid1\\.tenancy\\.[a-z0-9]+\\.\\.[a-z0-9]+$", var.ocm-service-tenancy-ocid))
    error_message = "The Oracle Cloud Migrations service tenancy override must be empty or a tenancy OCID."
  }
}
