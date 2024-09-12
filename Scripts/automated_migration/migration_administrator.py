import oci
import json
import base64
import time

BOAT = True

## BOAT Authentication
if BOAT:
        config = oci.config.from_file(profile_name='m360')
        token_file = config['security_token_file']
        token = None
        with open(token_file, 'r') as f:
                token = f.read()
        private_key = oci.signer.load_private_key_from_file(config['key_file'])
        tenancy_id = config['tenancy']
        signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
        inventory_client = oci.cloud_bridge.InventoryClient({'region': config['region']}, signer=signer)
        inventory_composite_client = oci.cloud_bridge.InventoryClientCompositeOperations(inventory_client)
        agent_client = oci.cloud_bridge.OcbAgentSvcClient({'region': config['region']}, signer=signer)
        agent_composite_client = oci.cloud_bridge.OcbAgentSvcClientCompositeOperations(agent_client)
        discovery_client = oci.cloud_bridge.DiscoveryClient({'region': config['region']}, signer=signer)
        vault_client = oci.key_management.KmsVaultClient({'region': config['region']}, signer=signer)
        secret_client = oci.vault.VaultsClient({'region': config['region']}, signer=signer)
        identity_client = oci.identity.IdentityClient({'region': config['region']}, signer=signer)
        object_client = oci.object_storage.ObjectStorageClient({'region': config['region']}, signer=signer)
else:
        ## CloudShell
        config = oci.config.from_file()
        tenancy_id = config['tenancy']
        inventory_client = oci.cloud_bridge.InventoryClient(config)
        inventory_composite_client = oci.cloud_bridge.InventoryClientCompositeOperations(inventory_client)
        agent_client = oci.cloud_bridge.OcbAgentSvcClient(config)
        agent_composite_client = oci.cloud_bridge.OcbAgentSvcClientCompositeOperations(agent_client)
        discovery_client = oci.cloud_bridge.DiscoveryClient(config)
        vault_client = oci.key_management.KmsVaultClient(config)
        secret_client = oci.vault.VaultsClient(config)
        identity_client = oci.identity.IdentityClient(config)
        object_client = oci.object_storage.ObjectStorageClient(config)

print("Finding migration compartments.")
migration_compartment = identity_client.list_compartments(
    compartment_id=migration_root_compartment_id,
    name='Migration').data[0]
migration_secrets_compartment = identity_client.list_compartments(
    compartment_id=migration_root_compartment_id,
    name='MigrationSecrets').data[0]
print("Done.")

print("Creating Source Environment.")
source_environment = agent_composite_client.create_environment_and_wait_for_state(
    oci.cloud_bridge.models.CreateEnvironmentDetails(
        display_name = lab_name_prefix + "_source_environment",
        compartment_id = migration_compartment.id
    ),
    [oci.cloud_bridge.models.Environment.LIFECYCLE_STATE_ACTIVE]
).data
print("Done.")

print("Creating Agent Dependency.")
object_storage_namespace = object_client.get_namespace(compartment_id=tenancy_id).data
# agent_dependency = agent_composite_client.create_agent_dependency_and_wait_for_state(
#     oci.cloud_bridge.models.CreateAgentDependencyDetails(
#         display_name = lab_name_prefix + "_vddk",
#         compartment_id = migration_compartment.id,
#         dependency_name = 'VDDK',
#         namespace = object_storage_namespace,
#         bucket = 'ocm_replication',
#         object_name = vddk_filename
#     ),
#     [oci.cloud_bridge.models.AgentDependency.LIFECYCLE_STATE_ACTIVE]
# )
# print("Done.")

agent_dependency = agent_client.create_agent_dependency(
    oci.cloud_bridge.models.CreateAgentDependencyDetails(
        display_name = lab_name_prefix + "_vddk",
        compartment_id = migration_compartment.id,
        dependency_name = 'VDDK',
        namespace = object_storage_namespace,
        bucket = 'ocm_replication',
        object_name = vddk_filename
    )
).data
vddk_test = 0
while True:
    vddk_status = agent_client.get_agent_dependency(agent_dependency_id=agent_dependency.id).data
    vddk_test += 1
    time.sleep(1)
    if vddk_status.lifecycle_state == 'ACTIVE':
        print("Done. " + str(vddk_test) + "s")
        break
    if vddk_test > 30:
        print("ERROR: Agent Dependency not created. Last state: " + vddk_status.lifecycle_state)
        exit(1)

print("Adding Agent Dependency to Source Environment.")
vddk = oci.cloud_bridge.models.AddAgentDependencyDetails(agent_dependency_id=agent_dependency.id)
source_environment_dependency = agent_client.add_agent_dependency(
    environment_id=source_environment.id,
    add_agent_dependency_details=vddk
)
print("Done.")

print("Creating Inventory.")
# inventory = inventory_composite_client.create_inventory_and_wait_for_state(
#     oci.cloud_bridge.models.CreateInventoryDetails(
#         display_name = lab_name_prefix + "_inventory",
#         compartment_id = tenancy_id
#     ),
#     [oci.cloud_bridge.models.Inventory.LIFECYCLE_STATE_CREATING,oci.cloud_bridge.models.Inventory.LIFECYCLE_STATE_ACTIVE]
# )
# print("Done.") 

# inventory_create = inventory_client.create_inventory(
#     oci.cloud_bridge.models.CreateInventoryDetails(
#         display_name = lab_name_prefix + "_inventory",
#         compartment_id = tenancy_id
#     )
# )
 
inventory = inventory_client.list_inventories(compartment_id=tenancy_id).data.items[0]
inventory_test = 0
while True:
    inventory_status = inventory_client.get_inventory(inventory_id=inventory.id).data
    inventory_test += 1
    time.sleep(1)
    if inventory_status.lifecycle_state == 'ACTIVE':
        print("Done. " + str(inventory_test) + "s")
        break
    if inventory_test > 30:
        print("ERROR: Inventory not created. Last state: " + inventory_status.lifecycle_state)
        exit(1)

print("Storing credentials in Vault.")
ocm_vault = vault_client.list_vaults(compartment_id=migration_secrets_compartment.id).data[0]

if BOAT:
    key_client = oci.key_management.KmsManagementClient(
        {'region': config['region']},
        signer=signer,
        service_endpoint=ocm_vault.management_endpoint
    )
else:
    key_client = oci.key_management.KmsManagementClient(
        config,
        service_endpoint=ocm_vault.management_endpoint
    )
ocm_key = key_client.list_keys(compartment_id=migration_secrets_compartment.id).data[0]

print("Creating discovery credentials.")
discovery_credentials_string = json.dumps(discovery_credentials)
discovery_credentials_string_bytes = discovery_credentials_string.encode("ascii") 
discovery_credentials_base64_bytes = base64.b64encode(discovery_credentials_string_bytes) 
discovery_credentials_base64_string = discovery_credentials_base64_bytes.decode("ascii") 

discovery_secret_details = oci.vault.models.CreateSecretDetails(
    compartment_id = migration_secrets_compartment.id,
    secret_name = lab_name_prefix + 'discovery',
    vault_id = ocm_vault.id,
    key_id = ocm_key.id,
    secret_content = oci.vault.models.Base64SecretContentDetails(
        content_type = "BASE64",
        stage = "CURRENT",
        content = discovery_credentials_base64_string
    )
)
discovery_secret = secret_client.create_secret(create_secret_details=discovery_secret_details).data

print("Creating replication credentials.")
replication_credentials_string = json.dumps(replication_credentials)
replication_credentials_string_bytes = replication_credentials_string.encode("ascii") 
replication_credentials_base64_bytes = base64.b64encode(replication_credentials_string_bytes) 
replication_credentials_base64_string = replication_credentials_base64_bytes.decode("ascii") 

replication_secret_details = oci.vault.models.CreateSecretDetails(
    compartment_id = migration_secrets_compartment.id,
    secret_name = lab_name_prefix + 'replication',
    vault_id = ocm_vault.id,
    key_id = ocm_key.id,
    secret_content = oci.vault.models.Base64SecretContentDetails(
        content_type="BASE64",
        stage="CURRENT",
        content = replication_credentials_base64_string
    )
)

replication_secret = secret_client.create_secret(create_secret_details=replication_secret_details).data
print("Done.")

print("Creating Asset Source.")
asset_source_details = oci.cloud_bridge.models.CreateVmWareAssetSourceDetails(
    type = "VMWARE",
    display_name = lab_name_prefix + '_asset_source',
    compartment_id = migration_compartment.id,
    assets_compartment_id = migration_compartment.id,
    environment_id = source_environment.id,
    inventory_id = inventory.id,
    vcenter_endpoint = vcenter_sdk,
    discovery_credentials = oci.cloud_bridge.models.AssetSourceCredentials(
        type = 'BASIC',
        secret_id = discovery_secret.id
    ),
    replication_credentials = oci.cloud_bridge.models.AssetSourceCredentials(
        type = 'BASIC',
        secret_id = replication_secret.id
    ),
    are_historical_metrics_collected = True,
    are_realtime_metrics_collected = True
)
asset_source = discovery_client.create_asset_source(asset_source_details).data
print("Done.")
print("Asset Source OCID: " + asset_source.id)