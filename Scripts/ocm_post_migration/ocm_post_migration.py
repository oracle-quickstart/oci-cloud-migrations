import oci 
import json
import time
import argparse
import sys

###### Common Functions #######

def wait_for_state(compute_client, response, target_state, max_wait_seconds=3600):
    try:

        # Wait until the resource reaches the target state
        oci.wait_until(
            compute_client,
            response,
            'lifecycle_state',
            target_state,
            max_wait_seconds=max_wait_seconds,
            succeed_on_not_found=False
        )
    except oci.exceptions.ServiceError as e:
        error_message = f"Error waiting for desired state:: {e.code} - {e.message}"
        sys.exit(error_message)

def validate_json_parameters(input_json):
    try:
        # Validate instance_id
        if not isinstance(input_json.get('instance_id'), str):
            raise ValueError('instance_id must be a string')

        # Load and validate OCI configuration
        try:
            config = oci.config.from_file(
                file_location=input_json['config_file'], profile_name=input_json.get('config_profile', 'DEFAULT'))
            oci.config.validate_config(config)
            return config
        except oci.exceptions.ConfigFileNotFound as e:
            print(f"Unable to locate configuration file: {e}")
            raise
        except oci.exceptions.InvalidConfig as e:
            print(f"Invalid configuration: {e}")
            raise
        except oci.exceptions.ProfileNotFound as e:
            print(f"Profile not found: {e}")
            raise

    except ValueError as ve:
        error = f"Error validating input parameters: {ve}"
        sys.exit(error)
    except Exception as e:
        error = f"Unexpected error validating input parameters: {e}"
        sys.exit(error)

def parse_arguments():
    try:
        parser = argparse.ArgumentParser(description="OCI Script for Updating Block Storages on Migrated Instances")
        parser.add_argument("--input_json_file", metavar="input_json_file", type=str,
                            help="Path to the JSON file containing input parameters.")
        return parser.parse_args()
    except Exception as e:
        sys.exit(e)

def section_separator():
    print("*****" *15)
    return ""

########### INSTANCE INFORMATION #########################

def get_instance_info(compute_client, instance_id):
    try:
        get_instance_response = compute_client.get_instance(instance_id=instance_id)

        instance_info = {
            'availability_domain': get_instance_response.data.availability_domain,
            'display_name': get_instance_response.data.display_name,
            'compartment_id': get_instance_response.data.compartment_id,
            'instance_id':get_instance_response.data.id,
        }
        return instance_info
    except Exception as e:
        error_message = f"Error getting compute instance details: {e}"
        sys.exit(error_message)

########### GETTING BLOCK VOLUMES (BOOT & BLOCK) INFORMATION #########################

def get_attached_boot_volume(compute_client, compartment_id, availability_domain,instance_id):
    try:
        list_boot_volume_attachments_response = compute_client.list_boot_volume_attachments(
            availability_domain=availability_domain,
            compartment_id=compartment_id,
            instance_id=instance_id
        )
        for boot_vol in list_boot_volume_attachments_response.data:
            if boot_vol.lifecycle_state == 'ATTACHED':
                return boot_vol.boot_volume_id
    except Exception as e:
        error = f"Error getting attached boot volume: {e}"
        sys.exit(error)

def get_attached_block_volumes(compute_client, compartment_id, availability_domain, instance_id):
    block_volumes = []
    try:
        list_volume_attachments_response = compute_client.list_volume_attachments(
            compartment_id=compartment_id,
            availability_domain=availability_domain,
            instance_id=instance_id
        )

        for block_vol in list_volume_attachments_response.data:
            if block_vol.lifecycle_state == 'ATTACHED':
                volume_info = {
                    "volume_id": block_vol.volume_id,
 
                }
                block_volumes.append(volume_info)

    except oci.exceptions.ServiceError as e:
        print(f"Error getting block volumes. The script will continue: {e}")

    return block_volumes

########### UPDATING BOOT VOLUME NAME #########################

def update_boot_volume_name(blockstorage_client, boot_volume_id,instance_details):
    try:
        updated_boot_display_name = f"{instance_details['display_name']}_BootVolume"

        update_boot_volume_response = blockstorage_client.update_boot_volume(
            boot_volume_id=boot_volume_id,
            update_boot_volume_details=oci.core.models.UpdateBootVolumeDetails(
                display_name=updated_boot_display_name)
        )

        print(f"Update for Boot Volume ID {boot_volume_id} completed successfully. Boot Volume Name updated to {updated_boot_display_name}")

    except oci.exceptions.ServiceError as e:
        error = f"Error updating boot volume name for Boot Volume ID {boot_volume_id}: {e}"
        sys.exit(error)

########### UPDATING BLOCK VOLUME NAMES #########################

def update_block_volume_display_name_with_sequence(blockstorage_client, block_volume_details, instance_details):
    try:
        for index, block_vol in enumerate(block_volume_details, start=1):
            volume_id = block_vol['volume_id']
            sequence_number = index

            # Append the sequence number to the instance display name
            updated_block_display_name = f"{instance_details['display_name']}_BlockVolume_{sequence_number}"

            # Update block volume display name
            update_volume_response = blockstorage_client.update_volume(
                volume_id=volume_id,
                update_volume_details=oci.core.models.UpdateVolumeDetails(
                    display_name=updated_block_display_name)
            )

            print(f"Update for Block Volume ID {volume_id} completed successfully. Block Volume name updated to {updated_block_display_name}")
    except oci.exceptions.ServiceError as e:
        print(f"Error updating block volume display name: {e}. The script will continue.")

########### CHANGING COMPARTMENT #########################

def change_boot_volume_compartment(blockstorage_client, boot_volume_id, compartment_id):
    try:
        change_boot_volume_compartment_response = blockstorage_client.change_boot_volume_compartment(
            boot_volume_id=boot_volume_id,
            change_boot_volume_compartment_details=oci.core.models.ChangeBootVolumeCompartmentDetails(
                compartment_id=compartment_id)
        )

        print(f"Change for Boot Volume ID {boot_volume_id} completed successfully. Boot Volume moved to {compartment_id}")

    except oci.exceptions.ServiceError as e:
        error = f"Error changing the compartment for Boot Volume: {boot_volume_id}: {e}"
        sys.exit(error)


def change_volume_compartment(blockstorage_client, block_volume_details, compartment_id):
    try:
        for block_vol in block_volume_details:
            volume_id = block_vol['volume_id']
            change_volume_compartment_response = blockstorage_client.change_volume_compartment(
                volume_id=volume_id,
                change_volume_compartment_details=oci.core.models.ChangeVolumeCompartmentDetails(
                    compartment_id=compartment_id)
            )

            print(f"Change for Block Volume ID {volume_id} completed successfully. Block Volume moved to {compartment_id}")

    except oci.exceptions.ServiceError as e:
        error = f"Error changing the compartment for Block Volume: {volume_id}: {e}"
        sys.exit(error)


def main():
        try:
            start_time = time.time()

            # Parse command-line arguments
            args = parse_arguments()

            # Print the value of args.input_json_file
            print("Input JSON file:", args.input_json_file)

            # Read input parameters from a JSON file
            with open(args.input_json_file, "r") as file:
                input_params = json.load(file)
            
            print(section_separator())
            print("Validating the input parameters")
            config = validate_json_parameters(input_params)

            # Extract input parameters
            instance_id = input_params.get("instance_id", "")

            # Initialize OCI clients
            compute_client = oci.core.ComputeClient(config)
            blockstorage_client = oci.core.BlockstorageClient(config)
            
            # Capture instance details
            print(section_separator())
            print("Capturing instance details")
            print ("Instance ID:", instance_id)
            instance_details = get_instance_info(compute_client, instance_id)
            print ("Instance Name:",instance_details['display_name'])
            print ("Compartment ID:", instance_details['compartment_id'])

            
            # Capture block and boot volumes details
            boot_volume_details = get_attached_boot_volume(compute_client, instance_details['compartment_id'], instance_details['availability_domain'],instance_id)
            print ("Boot Volume ID:", boot_volume_details)
            block_volume_details = get_attached_block_volumes(compute_client, instance_details['compartment_id'], instance_details['availability_domain'], instance_id)
            print ("Block Volume ID:", block_volume_details)
            
            # Update Boot Volume Name
            print(section_separator())
            print("Performing update for the boot volume and wait for the task to complete")
            update_boot_volume_name (blockstorage_client, boot_volume_details, instance_details)
            change_boot_volume_compartment(blockstorage_client, boot_volume_details, instance_details['compartment_id'])

            #Update Block Volume Name
            print(section_separator())
            print("Performing update for the block volume and wait for the task to complete")
            update_block_volume_display_name_with_sequence(blockstorage_client, block_volume_details, instance_details)
            change_volume_compartment(blockstorage_client, block_volume_details,instance_details['compartment_id'])

            #Time check 
            end_time = time.time()  
            elapsed_time_seconds = end_time - start_time

            # Convert elapsed time to minutes
            elapsed_time_minutes = elapsed_time_seconds / 60

            print(section_separator())
            print(f"Script execution completed in {elapsed_time_minutes:.2f} minutes.")
 
        except Exception as e:
            error = f"An error occurred executing the code: {e}"
            sys.exit(error)

if __name__ == "__main__":
    main()