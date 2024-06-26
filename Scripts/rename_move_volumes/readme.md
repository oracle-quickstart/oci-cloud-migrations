
# OCI Compute Instances Block Storage Update 
This Python script automates the process of assigning display names and compartments for the boot and block volumes of an existing compute instance. Specifically designed to resolve post-migration issues with Oracle Cloud Infrastructure (OCI) migrated images using OCM (Oracle Cloud Migration) Tool RMS stack, the script addresses a challenge where a migrated image, when spun up using the OCM RMS stack, is assigned random names for its boot and block volumes. These names are difficult to correlate with the associated OCI compute instance. Additionally, the OCM RMS stack places the boot and block volumes in a migration compartment rather than the correct compartment.

##### The script performs the following steps:

- Capture Configuration Details:
Captures instance configuration and block storage/s details.

- Modify the Boot and Block Volume Display Name:
Modify the display names of the boot and block volume/s attached to the compute instance to match the compute instance name.

- Update the Boot and Block Volume Compartment:
Move the boot and block volume/s to the compartment where the compute instance resides.

## Input Parameters JSON
Ensure to provide the necessary input parameters in a JSON file. Here is an example:

JSON
```sh
{
    "instance_id": "ocid1.instance.XXXXX",
    "config_file": "<OCI Config File e.g. ~/.oci/config>",
    "config_profile": "<OCI Config Profile name e.g. DEFAULT>"
}
```

### How to Run
Save the input parameters in a JSON file (e.g., input_params.json).
Execute the script with the following command:
```sh
python rename_move_volumes.py --input_json_file input_params.json

```

### Notes
- The script uses the OCI SDK for Python. Make sure to install the necessary dependencies before running the script.
- It's recommended to review the script and customize it according to your specific requirements before execution.

### Disclaimer:
This script is provided for experimental purposes only and should not be used in production. It is provided to assist your development or administration efforts and provided “AS IS” and is NOT supported by Oracle Corporation. The script has been tested in a test environment and appears to work as intended. You should always run new scripts on a test environment and validate and modify the same as per your requirements before using on your application environment.
