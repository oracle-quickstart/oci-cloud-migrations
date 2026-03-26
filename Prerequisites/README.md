# Overview
This Terraform implements the [prerequisites](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-get-started.htm#cloud-migration-prerequisites-ocm) needed to use Oracle Cloud Migrations for migrating VMware VMs, AWS EC2 instances, or OLVM VMs to Oracle Cloud Infrastructure.

# Deployed Resources

- Compartments - The recommended Migration and MigrationSecrets [compartments](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-get-started.htm#cloud-migration-recommendations-compartments).
- OCI Vault and Key - The vault used to store [vCenter credentials](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-remote-agent-appliance.htm#cloud-migration-vsphere-privileges).
- Object Storage Bucket - The Object Storage [bucket](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-understand-vm-replication.htm#cloud-migration-replication-bucket) used for transferring snapshot data into OCI.
- Mandatory Service Policies - The mandatory [service policies](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-servicepolicies.htm) and associated dynamic groups needed for OCM service components to function.
- Tags - Tag namespace and tag definitions needed for prerequisites and for migration metering.

# References

- [Deploy Required Migration Prerequisites](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-deploy-overview.htm)
- [Oracle Cloud Migrations Service Policies](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-servicepolicies.htm)
- [Getting Started with Oracle Cloud Migrations](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-get-started.htm)
