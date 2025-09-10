## VMware to OLVM demo (pre-console launch)

### On Console
- Open the console, log in to your tenancy
- On Web URL, append to override to Beta environment
    ```
    ?region=us-phoenix-1&configoverride={"features":{"ocm-use-dev-cp":true}}
    ```
- Run pre-requisite stack to create policies and compartments
- Create Inventory
- Create Source environment in **Migration** Compartment
- Register vCenter Appliance Agent
- Add Agent dependency (VDDK library)
- Create VMware Asset source in **Migration** Compartment. 
    - VMware credentials must be created in **MigrationSecrets** Compartment
    - On Asset source details page, click "Run Discovery" to populate VMware VM Metadata as inventory assets
- Create OLVM replication/discovery credentials in **MigrationSecrets** Compartment
- Ensure *scripts/config.json* is filled out with values corresponding to your environment

### On CLI - Pre-requisite
- Open Terminal, cd to location of script (e.g., cd *~/scripts/oci_wrapper.sh*)
- Install OCI CLI Preview version **3.65.1+preview.1.1351**
- Create an oci session for OCI CLI commands
    ```
    $ oci session authenticate --profile-name DEFAULT --region us-phoenix-1
    ```

### On CLI - Discovery - Create connections and discover assets in external environment
- Create OLVM Asset Source
    ```
    $ ./oci_wrapper.sh discovery asset-source create-olvm
    ```

- Discover OLVM assets
    ```
    $ ./oci_wrapper.sh discovery asset-source discover <OLVM asset source OCID>
    ```


### On CLI - Inventory - View discovered assets in VMware and OLVM
- List VMware VMs and write to file
    ```
    $ ./oci_wrapper.sh inventory asset list vmware-vm > discovered_vms.json
    ```

- List Storage Domains/Cluster/Template/VNIC Profile and write to file
    ```
    $ ./oci_wrapper.sh inventory asset list storage-domain > discovered_storage_domains.json
    $ ./oci_wrapper.sh inventory asset list cluster > discovered_clusters.json
    $ ./oci_wrapper.sh inventory asset list vnic-profile > discovered_vnic_profiles.json
    $ ./oci_wrapper.sh inventory asset list template > discovered_templates.json
    ```


### On CLI - Migration Project - Replicate disks in OLVM
- Create Migration Project
    ```
    $ ./oci_wrapper.sh migration migration create <project name>
    ```

- Add Migration Project OCID to *scripts/config.json*
- Modify discovered_vms.json. Remove from the file any VMs that you do not wish to migrate in this project.
- Initialize Migration Assets
    - View *discovered_storage_domains.json*, pick OCID of storage domain you wish to spin up the disks in. Run:
        ```
        $ ./oci_wrapper.sh migration migration init discovered_vms.json <storage domain inventory asset OCID>
        ```

    - Modify any Migration Asset as needed

- Add Migration Assets to the project
    ```
    $ ./oci_wrapper.sh migration migration-asset create discovered_vms.json
    ```

- Replicate all Migration Assets in the project
    ```
    $ ./oci_wrapper.sh migration migration start-migration-replication
    ```


### On CLI - Migration Plan - Launch VMs in OLVM
- View *discovered_clusters.json*, pick the OCID and write to config.json
- View *discovered_vnic_profiles.json*, pick the OCID and write to config.json
- View *discovered_templates.json*, pick the OCID and write to config.json
- Create Migration Plan
    ```
    $ ./oci_wrapper.sh migration migration-plan create <migration plan name>
    ```
- Add Migration Plan OCID to *scripts/config.json*

- Execute Migration Plan
    ```
    $ ./oci_wrapper.sh migration migration-plan execute
    ```

### On Console - RMS - Launch VMs in OLVM (Cont'd)
- Navigate to Migration Plan, locate RMS Stack.
- Navigate to RMS stack -> Plan -> Apply.

