import oci
import os
import sys
from sys import exit

DEBUG = False

tenancy_id = os.environ.get('OCI_TENANCY')

auth_type = "KEY"

if (auth_type == "DT"):
	## Delegation Token
	config = oci.config.from_file()
	token_file = config['security_token_file']
	token = None
	with open(token_file, 'r') as f:
		token = f.read()
	private_key = oci.signer.load_private_key_from_file(config['key_file'])
	tenancy_id = config['tenancy']
	signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
	compute_client = oci.core.ComputeClient({'region': config['region']}, signer=signer)
	blockstorage_client = oci.core.BlockstorageClient({'region': config['region']}, signer=signer)
	cloud_migrations_client = oci.cloud_migrations.MigrationClient({'region': config['region']}, signer=signer)
	identity_client = oci.identity.IdentityClient({'region': config['region']}, signer=signer)
	resource_search_client = oci.resource_search.ResourceSearchClient({'region': config['region']}, signer=signer)
elif (auth_type == "CS"):
	## CloudShell
	config = oci.config.from_file()
	compute_client = oci.core.ComputeClient(config)
	blockstorage_client = oci.core.BlockstorageClient(config)
	cloud_migrations_client = oci.cloud_migrations.MigrationClient(config)
	identity_client = oci.identity.IdentityClient(config)
	resource_search_client = oci.resource_search.ResourceSearchClient(config)
else:
	config = oci.config.from_file()
	signer = oci.signer.Signer(
		tenancy=config["tenancy"],
		user=config["user"],
		fingerprint=config["fingerprint"],
		private_key_file_location=config.get("key_file"),
		pass_phrase=oci.config.get_config_value_or_default(config, "pass_phrase"),
		private_key_content=config.get("key_content")
	)
	compute_client = oci.core.ComputeClient(config=config, signer=signer)
	blockstorage_client = oci.core.BlockstorageClient(config=config, signer=signer)
	cloud_migrations_client = oci.cloud_migrations.MigrationClient(config=config, signer=signer)
	identity_client = oci.identity.IdentityClient(config=config, signer=signer)
	resource_search_client = oci.resource_search.ResourceSearchClient(config=config, signer=signer)

VOLUME_FILTER = ("G_","Hydration")

def confirm():
	answer = input("[Y]es or [N]o: ")
	if answer.strip().lower() not in ('y', 'n'):
		print("Invalid Option. Please Enter a Valid Option.")
		return confirm() 
	return answer

def get_boot_volume_attachments(compartment_id):
	results = []
	for availability_domain in availability_domains:
		attachments = compute_client.list_boot_volume_attachments(
			compartment_id=compartment_id,
			availability_domain=availability_domain).data
		for attachment in attachments:
			if attachment.lifecycle_state == "ATTACHED":
				results.append(attachment)
	return results

def get_data_volume_attachments(compartment_id):
	results = []
	attachments = compute_client.list_volume_attachments(compartment_id=compartment_id).data
	for attachment in attachments:
		if attachment.lifecycle_state == "ATTACHED":
			results.append(attachment)
	return results

## Search for Migration compartment ##
try:
	migration_compartment_id = str(sys.argv[1])
except:
	print("No Migration compartment OCID provided.")
	print("Searching for Migration compartments.")
	search_migration_compartments_response = resource_search_client.search_resources(
    	search_details=oci.resource_search.models.StructuredSearchDetails(
       		type="Structured",
        	query="query compartment resources where name = \"Migration\" &&  lifecycleState == \"ACTIVE\""),
    	tenant_id=config["tenancy"]).data.items
	
if len(search_migration_compartments_response) == 0:
	print("No Migration compartments found. Please specify a compartment OCID and try again.")
	exit()
elif len(search_migration_compartments_response) > 1:
	print ("Multiple Migraiton compartments found. Please select a compartment.")
	compartment_ids = []
	count = 0 
	for count, compartment in enumerate(search_migration_compartments_response, start=1):
		print("[" + str(count) + "]", compartment.identifier)
		compartment_ids.append(compartment)
	selected_compartment = int(input("Compartment number: "))
	if not 1 <= selected_compartment < len(compartment_ids)+1:
		print("Invalid compartment selection. Please try again.")
		exit()
	migration_compartment_id = compartment_ids[selected_compartment-1].identifier
else:
	print ("Migraiton compartment found.")
	migration_compartment_id = search_migration_compartments_response[0].identifier

migration_compartment = identity_client.get_compartment(compartment_id=migration_compartment_id).data

## Find Compute ##
# Volume attachments exist in the same compartment as the compute instance it is attached to.
# Search for all compute instances.
all_compartments = []
compute_compartments = set()

print("Searching for compute compartments.")
search_resources_response = resource_search_client.search_resources(
    search_details=oci.resource_search.models.StructuredSearchDetails(
        type="Structured",
        query="query instance resources"),
    tenant_id=config["tenancy"]).data.items

if DEBUG:
	print("Found " + str(len(search_resources_response)) + " compute instances.")

# Build a unique list of compute compartments.

for result in search_resources_response:
	compute_compartments.add(result.compartment_id)
# Collect compartment details for compute compartments.
# Not necessary but used to print compartment name.
if DEBUG:
	print("Found " + str(len(compute_compartments)) + " compute compartmens.")
for compute_compartment in compute_compartments:
	all_compartments.append(identity_client.get_compartment(compartment_id=compute_compartment).data)

if DEBUG:
	print("Captured details for " + str(len(all_compartments)) + " compute compartments.")

## Find Volume Attachments ##
boot_volume_attachments = []
attached_boot_volumes = set()
data_volume_attachments = []
attached_data_volumes = set()

# Boot volumes calls require availability domain.
availability_domains = identity_client.list_availability_domains(compartment_id=config["tenancy"]).data

print("Collecting boot and data volume attachments.")
for compartment in all_compartments:
	if DEBUG: print("Searching compartment for attachments - " + compartment.name)
	boot_attachments = get_boot_volume_attachments(compartment.id)
	data_attachments = get_data_volume_attachments(compartment.id)
	if len(boot_attachments) != 0:
		if DEBUG: print ("Found " + str(len(boot_attachments)) + " boot volume attachments.")
		for boot_attachment in boot_attachments:
			boot_volume_attachments.append(boot_attachment)
			# Track attached volume for quick-lookup delete.
			attached_boot_volumes.add(boot_attachment.boot_volume_id)
	if len(data_attachments) != 0:
		if DEBUG: print ("Found " + str(len(data_attachments)) + " data volume attachments.")
		for data_attachment in data_attachments:
			data_volume_attachments.append(data_attachment)
			# Track attached volume for quick-lookup delete.
			attached_data_volumes.add(data_attachment.volume_id)

## Find Boot and Data Volumes ##
print("Collecting boot volumes in the " + migration_compartment.name + " compartment.")

# Collect boot volumes in the compartment.
boot_volumes = blockstorage_client.list_boot_volumes(compartment_id=migration_compartment.id).data

# Collect data volumes in the compartment.
print("Collecting data volumes in the " + migration_compartment.name + " compartment.")
data_volumes = blockstorage_client.list_volumes(compartment_id=migration_compartment.id,lifecycle_state="AVAILABLE").data

## Delete Unattached Boot Volumes ##
found_unattached_boot = False
for boot_volume in boot_volumes:
	# Boot volume list does not include lifecycle filter.
	if boot_volume.lifecycle_state != "AVAILABLE":
		continue
	if (not boot_volume.display_name.startswith(VOLUME_FILTER)) and (boot_volume.id not in attached_boot_volumes):
		found_unattached_boot = True
		try:
			migration_asset = cloud_migrations_client.get_migration_asset(migration_asset_id=boot_volume.freeform_tags["migrationAssetId"]).data
		except:
			migration_asset = oci.cloud_migrations.models.MigrationAsset(
				display_name = "UNKNOWN_MIGRATION_ASSET"
			)
		print("Delete unattached boot volume ("+ boot_volume.display_name + ") for " + migration_asset.display_name + "?")
		if confirm().lower() == 'y':
			blockstorage_client.delete_boot_volume(boot_volume_id=boot_volume.id)

if not found_unattached_boot:
	print("No unattached BOOT VOLUMES found in the " + migration_compartment.name + " compartment.")

## Delete Unattached Data Volumes ##
found_unattached_data = False
for data_volume in data_volumes:
	if (not data_volume.display_name.startswith(VOLUME_FILTER)) and (data_volume.id not in attached_data_volumes):
		found_unattached_data = True
		migration_asset = cloud_migrations_client.get_migration_asset(migration_asset_id=data_volume.freeform_tags["migrationAssetId"]).data
		print("Delete unattached data volume ("+ data_volume.display_name + ") for " + migration_asset.display_name + "?")
		if confirm().lower() == 'y':
			blockstorage_client.delete_volume(volume_id=data_volume.id)

if not found_unattached_data:
	print("No unattached DATA VOLUMES found in the " + migration_compartment.name + " compartment.")