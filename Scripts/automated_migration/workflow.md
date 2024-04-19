# Automated Migration Workflow

1. Tenancy Admin - Login to tenancy and deploy prerequisites. Upload VDDK to ocm_replication bucket. Setup Migration users.
2. VMware Admin - Create Discovery and Replication credentials. Determine Remote Agent Appliance network connectivity. 
3. Script - Run migration_adminsitrator.py
4. VMware Admin and Migration Administrator - Register agent. Refresh Asset Source.
5. Script - Run migration_operator.py to start replication.
6. Script - Run migration_cutover.py to clone and create stack.
