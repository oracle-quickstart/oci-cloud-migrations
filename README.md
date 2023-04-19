# Overview
This Terraform implements the [prerequisites](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-get-started.htm#cloud-migration-prerequisites-ocm) needed to use Oracle Cloud Migrations for migrating VMware VM's to Oracle Cloud Infrastructure.

# Deployed Resources

- Compartments - The recommended Migration and MigrationSecrets [compartments](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-get-started.htm#cloud-migration-recommendations-compartments).  
- OCI Vault and Key - The vault used to store [vCenter credentials](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-remote-agent-appliance.htm#cloud-migration-vsphere-privileges).
- Object Storage Bucket - The Object Storage [bucket](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-understand-vm-replication.htm#cloud-migration-replication-bucket) used for transferring vSphere snapshot data into OCI.
- Mandatory Service Policies - The mandatory [service policies](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-servicepolicies.htm) and associated dynamic groups needed for OCM service components to function.
- Oracle Cloud Bridge Inventory - The [Inventory](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-inventory.htm) used to store discovered assets for migration.
- Tag Namespace and Tags - The tag namespace and tags used by Oracle Cloud Migrations to keep track of [migrated resources](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-get-started.htm#cloud-migration-prerequisites-ocm).