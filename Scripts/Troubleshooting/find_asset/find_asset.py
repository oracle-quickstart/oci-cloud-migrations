import oci
import json
import sys
import os

def get_all_compartments(items):
    output = {}
    for compartment in items:
        output[compartment['id']]= {
               'parent': compartment['compartment_id'],
               'name': compartment['name']
        }
    return output

def get_name(ocid):
    output = comp_list[ocid]['name']
    if comp_list[ocid]['parent'] in comp_list.keys():
        output = get_name(comp_list[ocid]['parent']) + '\\' + output
    return output

asset = str(sys.argv[1])
tenancy_id = os.environ.get('OCI_TENANCY')
config = oci.config.from_file()
identity_client = oci.identity.IdentityClient(config)
compartments = json.loads(str(identity_client.list_compartments(compartment_id=tenancy_id,compartment_id_in_subtree=True,access_level="ANY",limit=1000).data))
cloud_migrations_client = oci.cloud_migrations.MigrationClient(config)
comp_list = get_all_compartments(compartments)
found_assets = []
for compartment in compartments:
    print(f"Scanning compartment {get_name(compartment['id'])}")
    try:
        migrations_in_compartment = json.loads(str(cloud_migrations_client.list_migrations(limit=1000, compartment_id=compartment['id']).data.items))
    except oci.exceptions.ServiceError as e:
        print(f"\tUnable to list migration projects. Status: {e.status}, code: {e.code}, message: {e.message}")
        continue
    for migration in migrations_in_compartment:
        print(f"\tMigration: {migration['display_name']}")
        migration_assets = json.loads(str(cloud_migrations_client.list_migration_assets(limit=1000, migration_id=migration['id']).data.items))
        for migration_asset in migration_assets:
            source_asset = migration_asset['source_asset_data']
            if source_asset['displayName'] == asset or source_asset['externalAssetKey'] == asset or source_asset['id'] == asset:
                    found_assets.append(migration_asset)
                    print('\033[92m' + f"Found compartment: {get_name(compartment['id'])}, migration project: {migration['id']}, state: {migration['lifecycle_state']}, "\
                          + f"migration asset:{migration_asset['id']}, state: {migration_asset['lifecycle_state']}" + '\033[0m')