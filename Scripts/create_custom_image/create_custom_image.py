import oci
import tempfile
import os
import time
import argparse
import sys
import logging
from datetime import datetime, timedelta, timezone
from oci.exceptions import ServiceError

IMAGE_SCHEMA_FIRMWARE_KEY = "Compute.Firmware"
WINDOWS_OS = "WINDOWS"


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def section_separator():
    logging.info("*" * 75)


def get_config_and_signer(profile_location, profile_name):
    config = oci.config.from_file(file_location=profile_location, profile_name=profile_name)
    token_file = config.get('security_token_file')
    if not token_file or not os.path.isfile(os.path.expanduser(token_file)):
        logging.error("Security token file not found: %s", token_file)
        sys.exit(1)
    with open(os.path.expanduser(token_file), 'r') as f:
        token = f.read()
    private_key = oci.signer.load_private_key_from_file(os.path.expanduser(config['key_file']))
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return config, signer


def get_root_compartment_id(start_compartment_id, identity_client):
    current_id = start_compartment_id
    while True:
        compartment = identity_client.get_compartment(current_id).data
        if compartment.compartment_id is None:
            logging.info(f"Root compartment id: {current_id}")
            return compartment.id
        current_id = compartment.compartment_id


def get_capability_version(compute_client):
    response = compute_client.list_compute_global_image_capability_schemas(limit=10)
    if not response.data:
        logging.error("No global image capability schemas found.")
        sys.exit(1)
    logging.info(f"Current capability schema version: {response.data[0].current_version_name}")
    return response.data[0].current_version_name


def get_tag_namespace(identity_client, compartment_id, tag_ns):
    ns = [n for n in identity_client.list_tag_namespaces(compartment_id).data
          if n.name == tag_ns and n.lifecycle_state == "ACTIVE"]
    if not ns:
        raise Exception(f"Tag namespace '{tag_ns}' not found or not active.")
    return ns[0]


def get_tag_key(identity_client, tag_ns_id, tag_key):
    keys = [k for k in identity_client.list_tags(tag_ns_id).data
            if k.name == tag_key and k.lifecycle_state == "ACTIVE"]
    return keys[0] if keys else None


def create_tag_key(identity_client, tag_ns_id, tag_key):
    logging.info(f"Creating tag key '{tag_key}' in namespace.")
    details = oci.identity.models.CreateTagDetails(
        name=tag_key,
        description="Auto-created for OCM custom images",
        is_cost_tracking=False,
        validator=oci.identity.models.EnumTagDefinitionValidator(values=["True"])
    )
    tag = identity_client.create_tag(tag_ns_id, details)
    return tag.data


def upload_empty_file(object_storage_client, namespace, bucket_name, object_name):
    logging.info(f"Creating empty object '{object_name}'...")
    with tempfile.NamedTemporaryFile(delete=False) as tempf:
        tempf.close()
        with open(tempf.name, 'rb') as f:
            object_storage_client.put_object(namespace, bucket_name, object_name, put_object_body=f)
    os.unlink(tempf.name)
    logging.info(f"Empty object created '{object_name}'...")


def create_preauth(object_storage_client, namespace, bucket_name, object_name):
    expiry_time = datetime.now(timezone.utc) + timedelta(weeks=1)
    details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name="temp_par",
        access_type="ObjectRead",
        time_expires=expiry_time,
        object_name=object_name
    )
    par = object_storage_client.create_preauthenticated_request(namespace, bucket_name, details)
    return par.data


def delete_object(object_storage_client, namespace, bucket_name, object_name):
    logging.info(f"Deleting object '{object_name}' in bucket '{bucket_name}' and namespace '{namespace}'...")
    try:
        object_storage_client.delete_object(namespace, bucket_name, object_name)
        logging.info(f"Object '{object_name}' deleted.")
    except ServiceError as e:
        logging.warning(f"Failed to delete object '{object_name}': {e.message}")


def abort_all_upload_requests(object_storage_client, namespace_name, bucket_name):
    logging.info("Abort all upload requests...")
    try:
        response = object_storage_client.list_multipart_uploads(
            namespace_name=namespace_name, bucket_name=bucket_name
        )
    except ServiceError as e:
        if e.status == 404:
            logging.warning(
                f"Failed to fetch UploadRequest in bucket {bucket_name} namespace {namespace_name}, "
                "either bucket does not exist or not authorized"
            )
            return
        else:
            logging.error(
                f"Failed to fetch uploadRequest. httpStatus: {e.status}, bucketName: {bucket_name}, "
                f"namespaceName: {namespace_name}, error: {e.message}"
            )
            return
    if not response.data:
        logging.info(f"No upload requests in bucket {bucket_name} namespace {namespace_name}")
        return
    logging.info(f"Aborting {len(response.data)} upload requests in bucket {bucket_name}")
    for item in response.data:
        try:
            object_storage_client.abort_multipart_upload(
                namespace_name=item.namespace,
                bucket_name=item.bucket,
                object_name=item.object,
                upload_id=item.upload_id
            )
            logging.info(f"Aborted upload {item.upload_id} for object {item.object}")
        except ServiceError as e:
            logging.warning(
                f"Failed to abort uploadRequest. httpStatus: {e.status}, bucketName: {bucket_name}, "
                f"namespaceName: {namespace_name}, error: {e.message}"
            )
    logging.info(f"Aborted upload requests in bucket {bucket_name} namespace {namespace_name}")


def get_tagged_custom_image(compute_client, compartment_id, tag_namespace, tag_key, firmware, operating_system):
    page = None
    while True:
        response = compute_client.list_images(
            compartment_id=compartment_id,
            lifecycle_state=oci.core.models.image.Image.LIFECYCLE_STATE_AVAILABLE,
            operating_system=operating_system,
            page=page
        )
        images = response.data
        for image in images:
            if (image.lifecycle_state == oci.core.models.image.Image.LIFECYCLE_STATE_AVAILABLE and
                    is_tagged_custom_image(image, tag_namespace, tag_key) and
                    is_matching_os(image, operating_system) and
                    is_matching_firmware(compute_client, image, firmware, IMAGE_SCHEMA_FIRMWARE_KEY)):
                logging.info(
                    f"Matching Image found. image id: {image.id} for compartment {compartment_id} "
                    f"and tagNamespace {tag_namespace}, tagKey {tag_key}, firmware {firmware}, "
                    f"operatingSystem {operating_system}."
                )
                return image.id
        page = response.headers.get('opc-next-page')
        if not page:
            break
    logging.info(
        f"No matching BYOI found for compartment {compartment_id} and tagNamespace {tag_namespace}, "
        f"tagKey {tag_key}, firmware {firmware}, operatingSystem {operating_system}."
    )
    return None


def is_tagged_custom_image(image, tag_namespace, tag_key):
    defined_tags = getattr(image, 'defined_tags', None)
    return (
            defined_tags is not None and
            tag_namespace in defined_tags and
            defined_tags[tag_namespace] is not None and
            tag_key in defined_tags[tag_namespace]
    )


def is_matching_firmware(compute_client, image, firmware, image_schema_firmware_key):
    schemas = compute_client.list_compute_image_capability_schemas(image_id=image.id)
    if not schemas.data:
        logging.warning("No capability schema found for this image.")
        return False
    schema_id = schemas.data[0].id
    logging.info(f"Found schema ocid: {schema_id} for custom image {image.id}")
    get_response = compute_client.get_compute_image_capability_schema(schema_id)
    schema_data = getattr(get_response.data, 'schema_data', {})
    descriptor_obj = schema_data.get(image_schema_firmware_key)
    default_value = getattr(descriptor_obj, 'default_value', None)
    if default_value is not None:
        return default_value.lower() == str(firmware).lower()
    else:
        logging.warning(f"Default value is null for schema key '{image_schema_firmware_key}'.")
        return False


def is_matching_os(image, operating_system):
    if operating_system is None:
        logging.info("Operating system is null.")
        return False
    img_os = getattr(image, "operating_system", "")
    return img_os.lower() == operating_system.lower()


def create_custom_image(compute_client, compartment_id, display_name, image_url, os_name, os_version, tag_namespace,
                        tag_key):
    details = oci.core.models.CreateImageDetails(
        compartment_id=compartment_id,
        display_name=display_name,
        image_source_details=oci.core.models.ImageSourceViaObjectStorageTupleDetails(
            operating_system=os_name,
            operating_system_version=os_version,
            source_type="objectStorageTuple",
            bucket_name=image_url['bucket'],
            namespace_name=image_url['namespace'],
            object_name=image_url['object']
        ),
        defined_tags={
            tag_namespace: {
                tag_key: "True"
            }
        },
        launch_mode=oci.core.models.CreateImageDetails.LAUNCH_MODE_PARAVIRTUALIZED
    )
    response = compute_client.create_image(details)
    return response.data


def update_image_capability(compute_client, compartment_id, image_id, default_firmware):
    firmwares = ["BIOS", "UEFI_64"]
    image_schema_firmware_value = oci.core.models.EnumStringImageCapabilitySchemaDescriptor(
        values=firmwares,
        default_value=default_firmware,
        source=oci.core.models.ImageCapabilitySchemaDescriptor.SOURCE_IMAGE
    )
    capability_schema = {
        IMAGE_SCHEMA_FIRMWARE_KEY: image_schema_firmware_value
    }
    schema_version = get_capability_version(compute_client)
    request_details = oci.core.models.CreateComputeImageCapabilitySchemaDetails(
        compartment_id=compartment_id,
        image_id=image_id,
        compute_global_image_capability_schema_version_name=schema_version,
        schema_data=capability_schema
    )
    compute_client.create_compute_image_capability_schema(request_details)


def parse_arguments():
    windows_os_versions = [
        'Server 2022 standard',
        'Server 2022 datacenter',
        'Server 2019 standard',
        'Server 2019 datacenter',
        'Server 2016 datacenter',
        'Server 2016 standard',
        'Server 2012 r2 datacenter',
        'Server 2012 r2 standard',
        'Server 2012 datacenter',
        'Server 2012 standard',
        'Server 2008 r2 datacenter',
        'Server 2008 r2 enterprise',
        'Server 2008 r2 standard'
    ]
    firmware_choices = ['UEFI_64', 'BIOS']
    parser = argparse.ArgumentParser(description="OCI Custom Windows Image Automation Script")
    parser.add_argument('--compartment_id', required=True, help='Migration compartment ID.')
    parser.add_argument('--config_file', default="~/.oci/config")
    parser.add_argument('--config_profile', default="DEFAULT")
    parser.add_argument('--os_version', default='Server 2022 standard', choices=windows_os_versions,
                        help='Windows OS version for the custom image.')
    parser.add_argument('--firmware', required=True, choices=firmware_choices,
                        help='Firmware type for the custom image (default: UEFI_64).')
    parser.add_argument('--bucket_name', required=True,
                        help='Bucket Name used while creating custom zero byte custom image.')
    parser.add_argument('--skip_check_custom_image', action='store_true',
                        help='Skip the check for a custom image and always create a new one')
    return parser.parse_args()


def main():
    setup_logging()
    start_time = time.time()
    try:
        args = parse_arguments()
        config, signer = get_config_and_signer(args.config_file, args.config_profile)
        compartment_id = args.compartment_id
        identity_client = oci.identity.IdentityClient(config, signer=signer)
        object_storage_client = oci.object_storage.ObjectStorageClient(config, signer=signer)
        compute_client = oci.core.ComputeClient(config, signer=signer)
        tag_ns_name = "CloudMigrations"
        tag_key_name = "OcmCustomImage"
        # Step 1: Check if the matching custom image exists
        if not args.skip_check_custom_image:
            custom_image_id = get_tagged_custom_image(compute_client, compartment_id, tag_ns_name, tag_key_name,
                                                      args.firmware, WINDOWS_OS)
            if custom_image_id is not None:
                logging.info("Matching Custom image found, skipping the custom image creation process.")
                return
            logging.info(f"No Matching custom image found in compartment '{compartment_id}' with os type {WINDOWS_OS} "
                         f"and firmware type {args.firmware}. Creating custom image...")
        section_separator()

        # Step 2: Tag Namespace & Key Validation
        tenancy_ocid = get_root_compartment_id(compartment_id, identity_client)
        tag_ns = get_tag_namespace(identity_client, tenancy_ocid, tag_ns_name)
        tag_key = get_tag_key(identity_client, tag_ns.id, tag_key_name)
        if not tag_key:
            create_tag_key(identity_client, tag_ns.id, tag_key_name)
            logging.info(f"Tag key '{tag_key_name}' has been created (Boolean, default true).")
        else:
            logging.info(f"Tag key '{tag_key_name}' already exists in '{tag_ns_name}'.")
        section_separator()

        # Step 3: Bucket & Object
        namespace = object_storage_client.get_namespace(compartment_id=tenancy_ocid).data
        logging.info(f"Namespace '{namespace}' found.")
        object_name = "ocm_migration_custom_image_empty_file.txt"
        upload_empty_file(object_storage_client, namespace, args.bucket_name, object_name)
        section_separator()

        # Step 4: Create Custom Image
        image_url = {'bucket': args.bucket_name, 'namespace': namespace, 'object': object_name}
        image = create_custom_image(
            compute_client,
            compartment_id,
            f"MIGRATION_Custom_Image_{WINDOWS_OS}_{args.os_version}_{args.firmware}".upper(),
            image_url,
            WINDOWS_OS,
            args.os_version,
            tag_ns_name,
            tag_key_name
        )
        logging.info(f"Custom image creation requested: {image.id}")
        section_separator()

        # Step 5: Edit image schema capabilities after image is available
        print("Waiting for image to become AVAILABLE...")
        while True:
            image = compute_client.get_image(image.id).data
            if image.lifecycle_state == "AVAILABLE":
                break
            print(".", end="", flush=True)
            time.sleep(10)
        logging.info(f"Image {image.id} is available.")
        logging.info("Creating custom image capability schema...")
        update_image_capability(compute_client, compartment_id, image.id, args.firmware)
        logging.info(f"Image capabilities updated.")
        section_separator()
        # Cleanup
        delete_object(object_storage_client, namespace, args.bucket_name, object_name)
        logging.info("Cleanup done.")
    except Exception as e:
        logging.error(f"An error occurred executing the code: {e}")
        sys.exit(1)
    finally:
        elapsed_time_minutes = (time.time() - start_time) / 60
        logging.info(f"Script execution completed in {elapsed_time_minutes:.2f} minutes.")


if __name__ == "__main__":
    main()
