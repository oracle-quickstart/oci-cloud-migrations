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
        error_message = f"Error waiting for desired state:: {e}"
        sys.exit(error_message)

def validate_json_parameters(input_json):
    try:
        # Validate instance_id
        if not isinstance(input_json.get('instance_id'), str):
            raise ValueError('instance_id must be a string')

        # Validate bucket_name
        if not isinstance(input_json.get('bucket_name'), str):
            raise ValueError('bucket_name must be a string')

        # Validate operating_system_version
        if not isinstance(input_json.get('operating_system_version'), str):
            raise ValueError('operating_system_version must be a string')

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
        parser = argparse.ArgumentParser(description="OCI Script for Windows Licensing Fix on Migrated Instances")
        parser.add_argument("--input_json_file", metavar="input_json_file", type=str,
                            help="Path to the JSON file containing input parameters.")
        return parser.parse_args()
    except Exception as e:
        sys.exit(e)

def section_separator():
    print("*****" *15)
    return ""

#############  Stop the compute instance #######

def stop_and_wait_for_instance(compute_client, instance_id):
    try:
        # Get current state
        get_instance_response = compute_client.get_instance(instance_id=instance_id)
        instance_state = get_instance_response.data.lifecycle_state

        if instance_state == 'RUNNING':
            print(f"Stopping instance {instance_id}")
            compute_client.instance_action(instance_id, "SOFTSTOP")

            # Wait until the instance is in the 'STOPPED' state
            wait_for_state(compute_client, get_instance_response, 'STOPPED', max_wait_seconds=1200)
            print(f"Instance {instance_id} is now stopped")
        elif instance_state == 'STOPPED':
            print("Instance already in the stopped state")
        else:
            raise ValueError(f"Error: Instance {instance_id} is in '{instance_state}' state. Expected 'RUNNING'.")

    except oci.exceptions.ServiceError as se:
        error = f"OCI Service Error stopping instance: {se}"
        sys.exit(error)
    except oci.exceptions.RequestException as re:
        error = f"Request Exception stopping instance: {re}"
        sys.exit(error)
    except ValueError as ve:
        error = f"ValueError stopping instance: {ve}"
        sys.exit(error)
    except Exception as e:
        error = f"Unexpected error stopping instance: {e}"
        sys.exit(error)

############  IMAGE CREATION #################
# Create an image using the instance
def create_custom_image(compute_client, compartment_id, image_name, instance_id):
    create_image_details = oci.core.models.CreateImageDetails(
        compartment_id=compartment_id,
        display_name=image_name+"_temp",
        instance_id=instance_id
    )

    try:
        response = compute_client.create_image(create_image_details)
        image_id = response.data.id
        print(f"Custom image creation initiated successfully with ID: {image_id}")
        return image_id
    except oci.exceptions.ServiceError as e:
        error = f"Error creating custom image: {e}"
        sys.exit(error)
########### INSTANCE INFORMATION #########################

def get_vnic_details(compute_client, network_client, compartment_id, instance_id):
    try:
        vnic_details = []
        list_vnic_attachments_response = compute_client.list_vnic_attachments(compartment_id=compartment_id, instance_id=instance_id)
        for attachment in list_vnic_attachments_response.data:
            get_vnic_response = network_client.get_vnic(vnic_id=attachment.vnic_id)
            assign_ipv6_ip = bool(getattr(get_vnic_response.data, 'ipv6_addresses', None))
            nic = {
                'assign_ipv6_ip': assign_ipv6_ip,
                'defined_tags': getattr(get_vnic_response.data, 'defined_tags', None),
                'display_name': getattr(get_vnic_response.data, 'display_name', None),
                'freeform_tags': getattr(get_vnic_response.data, 'freeform_tags', None),
                'hostname_label': getattr(get_vnic_response.data, 'hostname_label', None),
                'ipv6_address_ipv6_subnet_cidr_pair_details': getattr(get_vnic_response.data, 'ipv6_addresses', None),
                'nsg_ids': getattr(get_vnic_response.data, 'nsg_ids', None),
                'private_ip': getattr(get_vnic_response.data, 'private_ip', None),
                'skip_source_dest_check': getattr(get_vnic_response.data, 'skip_source_dest_check', None),
                'subnet_id': getattr(get_vnic_response.data, 'subnet_id', None),
                'vlan_id': getattr(get_vnic_response.data, 'vlan_id', None)
            }
            vnic_details.append(nic)

        return vnic_details

    except oci.exceptions.ServiceError as se:
        error_message = f"OCI Service Error in get_vnic_details: {se}"
        sys.exit(error_message)
    except oci.exceptions.RequestException as re:
        error_message = f"Request Exception in get_vnic_details: {re}"
        sys.exit(error_message)
    except ValueError as ve:
        error_message = f"ValueError in get_vnic_details: {ve}"
        sys.exit(error_message)
    except Exception as e:
        error_message = f"Unexpected error in get_vnic_details: {e}"
        sys.exit(error_message)

def instance_agent_config_to_dict(agent_config):
    return {
        "are_all_plugins_disabled": agent_config.are_all_plugins_disabled,
        "is_management_disabled": agent_config.is_management_disabled,
        "is_monitoring_disabled": agent_config.is_monitoring_disabled,
        "plugins_config": agent_config.plugins_config,  # You might need to handle this attribute accordingly
    }

def object_to_dict(obj):
    if obj is None:
        return None

    # Get all attributes of the object
    attributes = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("__")]

    # Construct a dictionary with attribute names and values
    obj_dict = {attr: getattr(obj, attr) for attr in attributes}

    return obj_dict

def get_instance_info(compute_client, instance_id):
    try:
        get_instance_response = compute_client.get_instance(instance_id=instance_id)

        instance_info = {
            'shape_ocpus': get_instance_response.data.shape_config.ocpus,
            'shape_memory': get_instance_response.data.shape_config.memory_in_gbs,
            'availability_domain': get_instance_response.data.availability_domain,
            'compartment_id': get_instance_response.data.compartment_id,
            'display_name': get_instance_response.data.display_name,
            'shape': get_instance_response.data.shape,
            'instance_id':get_instance_response.data.id,
            'freeform_tags': get_instance_response.data.freeform_tags,
            'fault_domain': get_instance_response.data.fault_domain,
           'is_pv_encryption_in_transit_enabled':  get_instance_response.data.launch_options.is_pv_encryption_in_transit_enabled,
            #Property causing issues with launch instance.
            #'agent_config' :object_to_dict(get_instance_response.data.agent_config),
            'availability_config' :object_to_dict(get_instance_response.data.availability_config),
            'capacity_reservation_id' :get_instance_response.data.capacity_reservation_id,
            'dedicated_vm_host_id' : get_instance_response.data.dedicated_vm_host_id,
            'extended_metadata': object_to_dict(get_instance_response.data.extended_metadata),
            'instance_configuration_id': getattr(get_instance_response.data, 'instance_configuration_id', None),
            #Property doesn't work. Possible bug? 
            #'instance_configuration_id' : get_instance_response.data.get('instance_configuration_id',None),
            'instance_options' :object_to_dict(get_instance_response.data.instance_options),
            'ipxe_script' : get_instance_response.data.ipxe_script,
            'launch_options':object_to_dict(get_instance_response.data.launch_options),
            'metadata' :get_instance_response.data.metadata,
            'platform_config':get_instance_response.data.platform_config,
            'preemptible_instance_config':get_instance_response.data.preemptible_instance_config,
            #This property is causing launch instance failure in some cases. 
            #'source_details':object_to_dict(get_instance_response.data.source_details),
        }
        return instance_info
    except Exception as e:
        error_message = f"Error getting compute instance details: {e}"
        sys.exit(error_message)

def get_instance_details(compute_client, network_client, instance_id):
    instance_info = get_instance_info(compute_client, instance_id)
    compartment_id= instance_info.get('compartment_id', "")
    vnic_details = get_vnic_details(compute_client, network_client, compartment_id, instance_id)
    instance_info["vnic_details"] = vnic_details
    return instance_info

def save_instance_details_to_json(instance_details, output_file):
    with open(output_file, "w") as json_file:
        json.dump(instance_details, json_file, indent=2)


###########  GET STORAGE #######
def get_namespace(object_storage_client):
    try:
        get_namespace_response = object_storage_client.get_namespace()
        return get_namespace_response.data
    except Exception as e:
        error = f"Error getting namespace {e}"
        sys.exit(error)


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

#Continue the script if getting block volume fails. Its non critical for the operation. 
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
                    "display_name": block_vol.display_name,
                    "is_read_only": block_vol.is_read_only,
                    "is_shareable": block_vol.is_shareable,
                    "attachment_type": block_vol.attachment_type,
                }

                if block_vol.attachment_type == 'paravirtualized':
                    volume_info['is_pv_encryption_in_transit_enabled'] = False 
                elif block_vol.attachment_type == 'iscsi':
                    volume_info["encryption_in_transit_type"] = block_vol.encryption_in_transit_type
                    volume_info["is_agent_auto_iscsi_login_enabled"] = block_vol.is_agent_auto_iscsi_login_enabled
                    volume_info["use_chap"] = bool(block_vol.chap_username or block_vol.chap_secret)

                block_volumes.append(volume_info)

    except oci.exceptions.ServiceError as e:
        print(f"Error getting block volumes. The script will continue: {e}")

    return block_volumes

def update_instance_info_with_attached_volumes(instance_info, boot_volume, block_volumes):
    if boot_volume:
        instance_info["boot_volume"] = boot_volume

    if block_volumes:
        instance_info["block_volumes"] = block_volumes

def perform_get_attached_volumes(compute_client, instance_info, compartment_id):
    availability_domain = instance_info.get('availability_domain', '')
    instance_id = instance_info.get('instance_id', '')
    boot_volume = get_attached_boot_volume(compute_client, compartment_id, availability_domain,instance_id)
    block_volumes = get_attached_block_volumes(compute_client, compartment_id, availability_domain, instance_id)
    update_instance_info_with_attached_volumes(instance_info, boot_volume, block_volumes)

#########  Create Block Backups #########
def create_boot_volume_backup(blockstorage_client, instance_info):
    try:
        boot_volume_id= instance_info.get('boot_volume', [])
        create_boot_volume_backup_response = blockstorage_client.create_boot_volume_backup(
            create_boot_volume_backup_details=oci.core.models.CreateBootVolumeBackupDetails(
                boot_volume_id=boot_volume_id
            ),
        )
        backup_id = create_boot_volume_backup_response.data.id
        print(f"Initiated backup creation for Boot Volume ID {boot_volume_id}. Backup ID: {backup_id}")

        # Wait for the backup to complete
        boot_vol_backup_response = blockstorage_client.get_boot_volume_backup(
            boot_volume_backup_id=backup_id
        )
        wait_for_state(blockstorage_client, boot_vol_backup_response, 'AVAILABLE', max_wait_seconds=10000)

        print(f"Backup for Boot Volume ID {boot_volume_id} completed successfully.")
        print(f"Backup created with name: {blockstorage_client.get_boot_volume_backup(boot_volume_backup_id=backup_id).data.display_name}")

    except oci.exceptions.ServiceError as e:
        error = f"Error creating boot volume backup for Boot Volume ID {boot_volume_id}: {e}"
        sys.exit(error)


def create_block_volume_backup(blockstorage_client, instance_info):
    try:
        for block_vol in instance_info.get('block_volumes', []):
            if(block_vol):
                create_block_volume_backup_response = blockstorage_client.create_volume_backup(
                    create_volume_backup_details=oci.core.models.CreateVolumeBackupDetails(
                        volume_id= block_vol["volume_id"]
                    ),
                )
                block_backup_id = create_block_volume_backup_response.data.id
                print(f"Initiated backup creation for Block Volume ID {block_vol['volume_id']}. Backup ID: {block_backup_id}")

                # Wait for the backup to complete
                block_vol_backup_response = blockstorage_client.get_volume_backup(
                    volume_backup_id=block_backup_id
                )
                wait_for_state(blockstorage_client, block_vol_backup_response, 'AVAILABLE', max_wait_seconds=10000)
                print(f"Backup for Block Volume ID  {block_vol['volume_id']} completed successfully.")
                print(f"Backup Name: {blockstorage_client.get_volume_backup(volume_backup_id=block_backup_id).data.display_name}")

    except oci.exceptions.ServiceError as e:
        print(f"Error creating backup for Block Volume ID  {block_vol['volume_id']}: {e}. The script will continue")



########### Upload Image to the object storage ############

def export_image_to_object_storage(core_client, custom_image_id, bucket_name, namespace_name, object_name):
    print(f"Exporting the image {custom_image_id} to the Object storage bucket {bucket_name} with the Object Name {object_name}")
    try:
        export_image_response = core_client.export_image(
            image_id=custom_image_id,
            export_image_details=oci.core.models.ExportImageViaObjectStorageTupleDetails(
                destination_type="objectStorageTuple",
                bucket_name=bucket_name,
                namespace_name=namespace_name,
                object_name=object_name,
                export_format="OCI"
            ),
        )
        # Get the data from the response
        print(f"Image export started with name: {export_image_response.data.display_name}")
        
        print("Waiting for the image export to complete")
        image_response = core_client.get_image(export_image_response.data.id)
        wait_for_state(core_client, image_response, 'AVAILABLE', max_wait_seconds=15000)

        return export_image_response.data

    except oci.exceptions.ServiceError as e:
        error = f"Error exporting image: {e}. The script will exit......"
        sys.exit(error)


######## Import the image with OS details 
def create_image(compute_client, compartment_id, image_name, bucket_name, namespace_name, object_name,operating_system,operating_system_version):
    try:
        create_image_details = oci.core.models.CreateImageDetails(
            compartment_id=compartment_id,
            display_name=image_name,
            image_source_details=oci.core.models.ImageSourceViaObjectStorageTupleDetails(
                source_type="objectStorageTuple",
                bucket_name=bucket_name,
                namespace_name=namespace_name,
                object_name=object_name,
                operating_system=operating_system,
                operating_system_version=operating_system_version
            )
        )
        response = compute_client.create_image(create_image_details)
        print(f"Image import from object storage started with name: {response.data.display_name}")

        # Wait for the image creation task to complete
        print("Waiting for the image import process to complete ")
        image_response = compute_client.get_image(response.data.id)
        wait_for_state(compute_client, image_response, 'AVAILABLE', max_wait_seconds=15000)
        return response.data
    
    except oci.exceptions.ServiceError as e:
        error = f"Error importing image from the object storage: {e}"
        sys.exit(error)


#############  TERMINATE INSTANCE ###########

def terminate_and_wait_for_instance(compute_client, instance_id):
    try:
        print("Terminating the instance to launch a duplicate instance")

        # Terminate the instance
        terminate_instance_response = compute_client.terminate_instance(
            instance_id=instance_id,
            preserve_boot_volume=True
        )

        # Wait until the instance is terminated
        get_terminated_compute_response = compute_client.get_instance(instance_id=instance_id)

        print("Waiting for the instance to terminate")
        wait_for_state(compute_client, get_terminated_compute_response, 'TERMINATED', max_wait_seconds=3600)
        print(f"Instance {instance_id} terminated")
    except Exception as e:
        error = f"Error terminating the instance {e}"
        sys.exit(error)

############## CREATE AND LAUNCH INSTANCE ###############
def get_launch_options(instance_info):
    try:
        launch_options = instance_info.get('launch_options',{})
        return oci.core.models.LaunchOptions(
            boot_volume_type = launch_options.get('_boot_volume_type',""),
            firmware = launch_options.get('_firmware',""),
            is_consistent_volume_naming_enabled = launch_options.get('is_consistent_volume_naming_enabled',""),
            network_type = launch_options.get('network_type',""),
            remote_data_volume_type = launch_options.get('_remote_data_volume_type',""),
        )
    except Exception as e:
        error = f"Error generating launch options in get_launch_options function: {e} "
        sys.exit(error)

def get_instance_source_details(instance_info):
    try:
        source_details = instance_info.get('source_details',{})
        return oci.core.models.InstanceSourceViaBootVolumeDetails(
              boot_volume_id = source_details.get('_boot_volume_id',""),
                source_type = source_details.get('_source_type',"bootVolume")
            )
    except Exception as e:
        error = f"Error generating source details in get_instance_source_details function: {e} "
        sys.exit(error)

def create_launch_instance_details(compartment_id, instance_info, image_id):
    try:
        vnic_details = instance_info.get("vnic_details", [{}])[0]

        return oci.core.models.LaunchInstanceDetails(
            compartment_id=compartment_id,
            availability_domain=instance_info.get('availability_domain', None),
            display_name=instance_info.get('display_name', "") ,
            fault_domain = instance_info.get('fault_domain', ""),
            freeform_tags = instance_info.get('freeform_tags', ""),
            #agent_config = instance_info.get('agent_config', ""),
            availability_config = instance_info.get('availability_config', ""),
            capacity_reservation_id = instance_info.get('capacity_reservation_id', ""),
            dedicated_vm_host_id = instance_info.get('dedicated_vm_host_id', ""),
            extended_metadata = instance_info.get('extended_metadata', ""),
            #Issues with the API for the below param. Looks like a bug! 
            #instance_configuration_id = None ,#instance_info.get('instance_configuration_id', None),
            instance_options = instance_info.get('instance_options', ""),
            ipxe_script = instance_info.get('ipxe_script', ""),
            is_pv_encryption_in_transit_enabled = instance_info.get('is_pv_encryption_in_transit_enabled', ""),
            launch_options = get_launch_options(instance_info), 
            metadata = instance_info.get('metadata',{}),
            platform_config = instance_info.get('platform_config',""),
            preemptible_instance_config = instance_info.get('preemptible_instance_config',""),
            #source_details = get_instance_source_details(instance_info),
            image_id=image_id,
            shape=instance_info.get('shape', None),
            shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                memory_in_gbs=instance_info.get('shape_memory', None),
                ocpus=instance_info.get('shape_ocpus', None)
            ),
            create_vnic_details=oci.core.models.CreateVnicDetails(
                display_name=vnic_details.get('display_name', None),
                freeform_tags=vnic_details.get('freeform_tags', None),
                hostname_label=vnic_details.get('hostname_label', None),
                #ipv6_address_ipv6_subnet_cidr_pair_details= [get_ipv6_details(instance_info)],   
                nsg_ids=vnic_details.get('nsg_ids', None),
                private_ip=vnic_details.get('private_ip', None),
                skip_source_dest_check=vnic_details.get('skip_source_dest_check', True),
                subnet_id=vnic_details.get('subnet_id', None),
                vlan_id=vnic_details.get('vlan_id', None)
            )
        )
    except Exception as e:
        error = f"Error creating launch instance details : {e}"
        sys.exit(error)

def launch_instance(compute_client, launch_instance_details):
    try:
        response = compute_client.launch_instance(launch_instance_details)
        new_instance_id = response.data.id
        print(f"New instance created successfully with ID: {new_instance_id}")
        # Wait until the instance is in the 'RUNNING' state
        get_running_instance_response = compute_client.get_instance(instance_id=new_instance_id)
        
        print("Waiting for the instance to start")
        wait_for_state(compute_client, get_running_instance_response, 'RUNNING', max_wait_seconds=8000)

        print(f"Instance {new_instance_id} is now running")
        return new_instance_id
    except oci.exceptions.ServiceError as e:
        error = f"Error creating new instance: {e}"
        sys.exit(error)

def launch_manual_instance (imported_image_id,compartment_id,compute_client):
    try:
        print("launching the instance manually")
        with open('instance_details.json', "r") as file:
                instance_details = json.load(file)  
        launch_instance_details = create_launch_instance_details(compartment_id, instance_details, imported_image_id)
        new_instance_id = launch_instance(compute_client, launch_instance_details)
        return new_instance_id
    except Exception as e:
        error = f"Error launching the compute instance in function launch_manual_instance {e}"
        sys.exit(error)

#######  Attach Block Volumes to the new instance ########

def attach_block_volumes(compute_client, new_instance_id, instance_details):
    try:
        block_volumes = instance_details.get("block_volumes", None)
        if(block_volumes):
            for volume in block_volumes:
                if volume["attachment_type"] == 'iscsi':
                    print("Attaching iscsi volumes")
                    attach_volume_response = compute_client.attach_volume(
                        attach_volume_details=oci.core.models.AttachIScsiVolumeDetails(
                            display_name=volume["display_name"],
                            encryption_in_transit_type=volume['encryption_in_transit_type'],
                            instance_id=new_instance_id,
                            is_agent_auto_iscsi_login_enabled=volume['is_agent_auto_iscsi_login_enabled'],
                            is_read_only=volume['is_read_only'],
                            is_shareable=volume['is_shareable'],
                            type=volume["attachment_type"],
                            use_chap=volume['use_chap'],
                            volume_id=volume['volume_id']
                        ),
                    )
                    print(f"Volume attachment Name {attach_volume_response.data.display_name} & Lifecycle State is {attach_volume_response.data.lifecycle_state}")
                    print("Waiting for the volume to attach")
                    get_volume_attachment_response = compute_client.get_volume_attachment(volume_attachment_id=attach_volume_response.data.id)
                    wait_for_state(compute_client, get_volume_attachment_response, 'ATTACHED', max_wait_seconds=8000)
                    print("Block volume attached")

                elif volume["attachment_type"] == 'paravirtualized':
                    print("Attaching paravirtualized volumes")
                    attach_volume_response = compute_client.attach_volume(
                        attach_volume_details=oci.core.models.AttachParavirtualizedVolumeDetails(
                            display_name=volume["display_name"],
                            is_pv_encryption_in_transit_enabled=volume['is_pv_encryption_in_transit_enabled'],
                            instance_id=new_instance_id,
                            is_read_only=volume['is_read_only'],
                            is_shareable=volume['is_shareable'],
                            type=volume["attachment_type"],
                            volume_id=volume['volume_id']
                        ),
                    )
                    print(f"Volume attachment Name {attach_volume_response.data.display_name} & Lifecycle State is {attach_volume_response.data.lifecycle_state}")
                    print("Waiting for the volume to attach")
                    get_volume_attachment_response = compute_client.get_volume_attachment(volume_attachment_id=attach_volume_response.data.id)
                    wait_for_state(compute_client, get_volume_attachment_response, 'ATTACHED', max_wait_seconds=8000)
                    print("Block volume attached")

                else:
                    print("Attaching service determined volumes")
                    attach_volume_response = compute_client.attach_volume(
                        attach_volume_details=oci.core.models.AttachServiceDeterminedVolumeDetails(
                            display_name=volume["display_name"],
                            instance_id=new_instance_id,
                            is_read_only=volume['is_read_only'],
                            is_shareable=volume['is_shareable'],
                            volume_id=volume['volume_id']
                        ),
                    )
                    print(f"Volume attachment Name: {attach_volume_response.data.display_name} & Lifecycle State is {attach_volume_response.data.lifecycle_state}")
                    print("Waiting for the volume to attach")
                    get_volume_attachment_response = compute_client.get_volume_attachment(volume_attachment_id=attach_volume_response.data.id)
                    wait_for_state(compute_client, get_volume_attachment_response, 'ATTACHED', max_wait_seconds=8000)
                    print("Block volume attached")
        else:
            print("No block volumes to attach")

    except oci.exceptions.ServiceError as e:
        print(f"Error attaching block volumes. Please proceed with the manual configuration : {e}")

################ Cleanup ###############

def delete_image(compute_client,image_id):
    try:
        delete_image_response = compute_client.delete_image(image_id=image_id)
        return (delete_image_response.headers)
    except oci.exceptions.ServiceError as e:
        print(f"Error deleting custom image. Manual cleanup required: {e}")

def delete_object(object_storage_client,namespace_name,bucket_name,object_name):
    try:
        delete_object_response = object_storage_client.delete_object(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            object_name=object_name
            )
        return (delete_object_response.headers)
    except oci.exceptions.ServiceError as e:
        print(f"Error deleting image from Object Storage. Manual cleanup required: {e}")

def main():
        try:
            start_time = time.time()

            # Parse command-line arguments
            args = parse_arguments()

            # Read input parameters from a JSON file
            with open(args.input_json_file, "r") as file:
                input_params = json.load(file)
            
            print(section_separator())
            print("Validating the input parameters")
            config = validate_json_parameters(input_params)

            # Extract input parameters
            instance_id = input_params.get("instance_id", "")
            bucket_name = input_params.get("bucket_name", "")
            operating_system = "Windows"  
            operating_system_version = input_params.get("operating_system_version", "")
            config_file = input_params.get("config_file", "~/.oci/config")
            config_profile = input_params.get("config_profile", "DEFAULT")

            # Initialize OCI clients
            compute_client = oci.core.ComputeClient(config)
            network_client = oci.core.VirtualNetworkClient(config)
            blockstorage_client = oci.core.BlockstorageClient(config)
            object_storage_client = oci.object_storage.ObjectStorageClient(config)
            
            #namespace 
            namespace_name = get_namespace(object_storage_client)

            # Stop the compute instance
            print(section_separator())
            print("Stopping the compute instance to prevent changes to the data")
            stop_and_wait_for_instance(compute_client, instance_id)
            
            # Capture instance details
            print(section_separator())
            print("Capturing instance details")
            instance_details = get_instance_details(compute_client, network_client, instance_id)
            compartment_id= instance_details.get('compartment_id', "")
            #Generate a custom image name
            image_name =  instance_details["display_name"]
            
            # Create the first image with no OS tag
            print(section_separator())
            print("Capturing a custom image from deployed OS")
            no_os_image = create_custom_image(compute_client, compartment_id, image_name, instance_id)

            # Update JSON with attached boot and block volumes
            print(section_separator())
            print("Capturing attached block storage")
            perform_get_attached_volumes(compute_client, instance_details, compartment_id)
          
            # Backup Boot Volume
            print(section_separator())
            print("Performing boot volume backup and wait for the task to complete")
            create_boot_volume_backup(blockstorage_client, instance_details)

            # Backup Block Volume 
            print(section_separator())
            print("Performing attached block volume backup and wait for the task to complete")
            create_block_volume_backup(blockstorage_client, instance_details)
           
            # Save instance_details to a JSON file
            print(section_separator())
            print("Saving the compute instance details to a JSON file")
            save_instance_details_to_json(instance_details, "instance_details.json")
            print("Instance Details saved to instance_details.json")
        
            # Wait for the 1st image creation process to complete
            print(section_separator())
            print(f"Waiting for the image creation of image id {no_os_image}")
            get_image_response = compute_client.get_image(no_os_image)
            wait_for_state(compute_client, get_image_response, 'AVAILABLE', max_wait_seconds=14400) 

            # Upload the image to object storage
            print(section_separator())
            print("Uploading the image to the object storage")
            export_result = export_image_to_object_storage(compute_client, no_os_image, bucket_name, namespace_name, image_name)

            # Import image from object storage
            print(section_separator())
            print("Importing the image from the Object Storage")
            import_image = create_image(compute_client, compartment_id, image_name, bucket_name, namespace_name, image_name, operating_system, operating_system_version)
        
            # Terminate instance 
            print(section_separator())
            print("Terminating the instance")
            terminate_and_wait_for_instance(compute_client, instance_id)

            #Instance Launch 
            print(section_separator())
            print("Launching the OS tagged image as an Instance")
            launch_instance_details = create_launch_instance_details(compartment_id, instance_details, import_image.id)
            new_instance_id = launch_instance(compute_client, launch_instance_details)
            
            #***If the above lanuch instance function fails. Use the manual launch method below. Only use if the above method fails. 
            #imported_image_id = <OCID of imported image>
            #launch_manual_instance (imported_image_id,compartment_id,compute_client)
            
            # Attach the block volume(s) to the new instance
            print(section_separator())
            print("Attaching block volumes")
            attach_block_volumes(compute_client, new_instance_id, instance_details)

            #Cleanup 
            print(section_separator())
            print(f"Cleaning up the temporary custom image: {no_os_image}")
            delete_image(compute_client,no_os_image)

            print(f"Cleaning up the image object {image_name} in Object storage bucket")
            delete_object(object_storage_client,namespace_name,bucket_name,image_name)
            
            #Time check 
            end_time = time.time()  
            elapsed_time_seconds = end_time - start_time

            # Convert elapsed time to minutes
            elapsed_time_minutes = elapsed_time_seconds / 60

            print(f"Script execution completed in {elapsed_time_minutes:.2f} minutes.")
 
        except Exception as e:
            error = f"An error occurred executing the code: {e}"
            sys.exit(error)

if __name__ == "__main__":
    main()