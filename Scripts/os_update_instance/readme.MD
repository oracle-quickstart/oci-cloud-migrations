
# OCI Compute instances OS & OS version update script 
This Python script automates the OS and OS version update process of an existing compute instance. This script was specifically written to help address the Windows licensing issues for a OCM migrated images. 
##### The script performs the following steps:

- Stop Compute Instance:
Stops the compute instance to prevent any new changes during the migration process.

- Create Custom Image:
Creates a custom image of the stopped compute instance.

- Capture Configuration Details:
Captures vNIC, storage, and instance configuration details and saves them to a JSON file.

- Backup Volumes:
Backs up any boot or block volumes attached to the compute instance.

- Upload Image to Object Storage:
Uploads the created image to the specified Object Storage bucket and tags the image with the OS and OS version.

- Import Image from Object Storage:
Imports the tagged image back into the custom images from the Object Storage bucket.

- Terminate Compute Instance:
Terminates the original compute instance, preserving the boot volume.

- Launch New Compute Instance:
Launches a new compute instance from the OS-tagged custom image.

- Attach Block Volumes:
Attaches any block volumes that were originally attached to the compute instance.

- Cleanup temp images
Delete the temp custom image and image uploaded to the object storage 

## Input Parameters JSON
Ensure to provide the necessary input parameters in a JSON file. Here is an example:

JSON
```sh
{
    "instance_id": "ocid1.instance.oc1.ap-tokyo-1.anxhiljrp77apcqcxxxxx",
    "bucket_name": "OCM_Migration_Bucket",
    "operating_system_version": "Server 2022 Standard",
    "config_file": "~/.oci/config",
    "config_profile": "DEFAULT"
}
```

### How to Run
Save the input parameters in a JSON file (e.g., input_params.json).
Execute the script with the following command:
```sh
python update_OS_instance.py --input_json_file input_params.json

```



### This script does NOT perform the following steps:

- Replace the need to consider the broader environment and dependencies between VMs and services.
- Stop/disable running services within a VM (as a result does not ensure consistent "recovery" of the replacement VM (e.g. see point below about additional block volumes).
- Address Windows successfully mounting additional block volumes attached to VMs (this requires manual intervention within the VM).
- Guarantee consistent state between the VM and the broader environment (application consistency).
- Does not address GUIDs/incarnations associated with the VM (it creates a new VM).
- Does not address MAC address differences (i.e. new vNICs).
- Does not add IPv6 details. 
- Does not copy ephemeral and reserved public IPs assigned to the non-billing orignal instance. 


### Notes
- The script uses the OCI SDK for Python. Make sure to install the necessary dependencies before running the script.
- It's recommended to review the script and customize it according to your specific requirements before execution.

### Disclaimer:
This script is provided for experimental purposes only and should not be used in production. It is provided to assist your development or administration efforts and provided “AS IS” and is NOT supported by Oracle Corporation. The script has been tested in a test environment and appears to work as intended. You should always run new scripts on a test environment and validate and modify the same as per your requirements before using on your application environment.

