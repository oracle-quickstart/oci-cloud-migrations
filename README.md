# Overview
This Terraform implements the [prerequisites](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-get-started.htm#cloud-migration-prerequisites-ocm) needed to use Oracle Cloud Migrations for migrating VMware VM's to Oracle Cloud Infrastructure.

# Deployed Resources

- Compartments - The recommended Migration and MigrationSecrets [compartments](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-get-started.htm#cloud-migration-recommendations-compartments).  
- OCI Vault and Key - The vault used to store [vCenter credentials](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-remote-agent-appliance.htm#cloud-migration-vsphere-privileges).
- Object Storage Bucket - The Object Storage [bucket](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-understand-vm-replication.htm#cloud-migration-replication-bucket) used for transferring vSphere snapshot data into OCI.
- Mandatory Serivce Policies - The mandatory [service policies](https://docs.oracle.com/en-us/iaas/Content/cloud-migration/cloud-migration-servicepolicies.htm) and assoicated dynamic groups needed for OCM serivce components to function.