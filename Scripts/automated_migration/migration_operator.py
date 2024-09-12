import oci

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
        migration_client = oci.cloud_migrations.MigrationClient({'region': config['region']}, signer=signer)
        migration_composite_client = oci.cloud_migrations.MigrationClientCompositeOperations(migration_client)
        inventory_client = oci.cloud_bridge.InventoryClient({'region': config['region']}, signer=signer)
        inventory_composite_client = oci.cloud_bridge.InventoryClientCompositeOperations(inventory_client)
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

print("Creating Migration Project.")
current_migration_projects = migration_client.list_migrations(compartment_id=migration_compartment_id).data
project_count = len(current_migration_projects.items)
migration_project = migration_composite_client.create_migration_and_wait_for_state(
     oci.cloud_migrations.models.CreateMigrationDetails(
          display_name = lab_name_prefix + "_migration_project_" + str(project_count + 1).zfill(3),
          compartment_id = migration_compartment_id
     ),
     [oci.cloud_migrations.models.Migration.LIFECYCLE_STATE_ACTIVE]
).data
print("Done.")

print("Adding Migration Asset to Migration Project.")
inventory_asset = inventory_client.list_assets(compartment_id=migration_compartment_id,display_name=migration_asset).data.items[0]
migration_asset = migration_composite_client.create_migration_asset_and_wait_for_state(
        oci.cloud_migrations.models.CreateMigrationAssetDetails(
                availability_domain = availability_domain,
                inventory_asset_id = inventory_asset.id,
                migration_id = migration_project.id,
                replication_compartment_id = migration_compartment_id,
                snap_shot_bucket_name = replication_bucket_name
        ),
        [oci.cloud_migrations.models.WorkRequest.STATUS_SUCCEEDED]
).data
print("Done.")

print("Creating Migration Plan.")
target_environment = oci.cloud_migrations.models.VmTargetEnvironment(
        target_environment_type = oci.cloud_migrations.models.TargetEnvironment.TARGET_ENVIRONMENT_TYPE_VM_TARGET_ENV,
        preferred_shape_type = "VM",
        target_compartment_id = production_compartment_id,
        vcn = production_vcn,
        subnet = production_subnet
)

plan_strategy = oci.cloud_migrations.models.ResourceAssessmentStrategy(
        resource_type = oci.cloud_migrations.models.ResourceAssessmentStrategy.RESOURCE_TYPE_ALL,
        strategy_type = oci.cloud_migrations.models.ResourceAssessmentStrategy.STRATEGY_TYPE_AS_IS
)

plan_details = oci.cloud_migrations.models.CreateMigrationPlanDetails(
        compartment_id = migration_compartment_id,
        display_name = lab_name_prefix + "_migration_project_" + plan_strategy.strategy_type,
        migration_id = migration_project.id,
        strategies = [plan_strategy],
        target_environments =[target_environment]
)

migration_plan = migration_composite_client.create_migration_plan_and_wait_for_state(
        create_migration_plan_details = plan_details,
        wait_for_states = [oci.cloud_migrations.models.WorkRequest.STATUS_SUCCEEDED]
).data
print("Done.")

print("Starting Migration Asset replication.")
asset_replication = migration_composite_client.start_asset_replication_and_wait_for_state(
        migration_asset_id = migration_asset.resources[0].identifier,
        wait_for_states = [oci.cloud_migrations.models.WorkRequest.STATUS_IN_PROGRESS]
).data
print("Done.")


