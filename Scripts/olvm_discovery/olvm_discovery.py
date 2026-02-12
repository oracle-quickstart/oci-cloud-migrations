import sys, json, oci, re, base64, requests
from requests.exceptions import RequestException
import tempfile, os, sys
import ovirtsdk4 as sdk
from datetime import datetime, timezone


def auth(profile_name = 'DEFAULT', region = False):
    try:
        config = oci.config.from_file(profile_name=profile_name)
    except oci.exceptions.ProfileNotFound:
        eprint(f'Profile {profile_name} is not found. Authenticate via `oci session authenticate --region=us-phoenix-1 --profile={profile_name}`')
        exit(1)

    if region:
        if len(region) == 3:
            config['region'] = oci.regions.get_region_from_short_name(region)
        else:
            config['region'] = region
    private_key = oci.signer.load_private_key_from_file(config['key_file'])
    token_file = config['security_token_file']
    token = None
    with open(token_file, 'r') as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return (config, signer)

def parse_ocid(ocid):
    pattern = r'^ocid1\.([a-z0-9]+)\.([a-z0-9]+)*\.([a-z0-9\-]+)\.[a-z0-9]{60}'
    match = re.match(pattern, ocid)
    if not match:
        return False
    return {
        'type': match.group(1),
        'realm': match.group(2),
        'region': match.group(3)
    }

def format_asset(at, obj):
    at['displayName'] = obj.name
    at['externalAssetKey'] = obj.id
    return at

def format_storage_domain_asset(at, obj):
    at['assetClassName'] = 'com.oracle.pic.ocb.discovery.model.OlvmStorageDomainAssetDetails'
    at['assetClassVersion'] = '0'
    at['assetDetails'] = {
        'olvmStorageDomain': {
            'storageDomainName': obj.name
        }
    }
    return format_asset(at, obj)

def format_cluster_asset(at, obj):
    at['assetClassName'] = 'com.oracle.pic.ocb.discovery.model.OlvmClusterAssetDetails'
    at['assetClassVersion'] = '0'
    at['assetDetails'] = {
        'olvmCluster': {
            'clusterName': obj.name
        }
    }
    return format_asset(at, obj)

def format_vnic_profile_asset(at, obj):
    at['assetClassName'] = 'com.oracle.pic.ocb.discovery.model.OlvmVnicProfileAssetDetails'
    at['assetClassVersion'] = '0'
    at['assetDetails'] = {
        'olvmVnicProfile': {
            'vnicProfileName': obj.name
        }
    }
    return format_asset(at, obj)

def format_vm_template_asset(at, obj):
    at['assetClassName'] = 'com.oracle.pic.ocb.discovery.model.OlvmTemplateAssetDetails'
    at['assetClassVersion'] = '0'
    at['assetDetails'] = {
        'olvmTemplate': {
            'templateName': obj.name
        }
    }
    return format_asset(at, obj)

def create_asset(payload, config, signer):
    print(f'\tOLVM object {payload['displayName']} .. ', end='')
    #if payload['displayName'] != 'ovirtmgmt':
    #    print('')
    #    return
    url = f'https://cloudbridge.{config["region"]}.oci.oraclecloud.com/20220509/assets/'
    try:
        r = requests.post(url, json=payload, auth=signer)
        r.raise_for_status()
    except RequestException as err:
        print(f'Error occured while injecting to OCM inventory: {err}')
        return
    print(f'OCM inventory asset {r.json()['id']}')
   

if __name__ == '__main__':

    asset_source_id = sys.argv[1]
    region = parse_ocid(asset_source_id)['region']
    config, signer = auth(profile_name = 'DEFAULT',region = region)
    #cloud_bridge_client = oci.cloud_bridge.DiscoveryClient(config, signer=signer)
    url = f'https://cloudbridge.{config["region"]}.oci.oraclecloud.com/20220509/assetSources/{asset_source_id}'
    asset_source = requests.get(url, auth=signer).json()
    print('Got asset source!')
    olvm_endpoint = asset_source['olvmEndpoint']
    inventory_id = asset_source['inventoryId']
    secret_id = asset_source['discoveryCredentials']['secretId']
    compartment_id = asset_source['assetsCompartmentId']
    # Asset Template - at
    at = {
        'assetSourceIds': [asset_source_id],
        'assetType': 'INVENTORY_ASSET',
        'compartmentId': compartment_id,
        'inventoryId': inventory_id,
        'sourceKey': olvm_endpoint,
        'environmentType': 'SOURCE',
        'definedTags': {
            'Oracle-Tags': {
                'CreatedBy': 'Standalone discovery for OLVM',
                'CreatedOn': datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            }
        } 
    }

    secrets_client = oci.secrets.SecretsClient(config, signer=signer)
    secret_response = secrets_client.get_secret_bundle(secret_id = secret_id, stage = 'CURRENT').data
    olvm_secret = json.loads(base64.b64decode(secret_response.secret_bundle_content.content))
    print('Got OVLM secret!')

    tf = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
    tf.write(olvm_secret['certificateString'].encode()); tf.close()

    olvm_conn = sdk.Connection(url=olvm_endpoint, username=olvm_secret['username'], password=olvm_secret['password'], ca_file=tf.name)
    storage_domains=olvm_conn.system_service().storage_domains_service().list()
    print(f'Pulled {len(storage_domains)} storage domains ..  ')
    for domain in storage_domains:
        create_asset(format_storage_domain_asset(at, domain), config, signer)

    clusters = olvm_conn.system_service().clusters_service().list()
    print(f'Pulled {len(clusters)} clusters ..  ')
    for cluster in clusters:
        create_asset(format_cluster_asset(at, cluster), config, signer)
    
    vnic_profiles = olvm_conn.system_service().vnic_profiles_service().list()
    print(f'Pulled {len(vnic_profiles)} vNIC profiles ..  ')
    for vnic_profile in vnic_profiles:
        create_asset(format_vnic_profile_asset(at, vnic_profile), config, signer)

    vm_templates = olvm_conn.system_service().templates_service().list()
    print(f'Pulled {len(vm_templates)} VM templates ..  ')
    for vm_template in vm_templates:
        create_asset(format_vm_template_asset(at, vm_template), config, signer)

    olvm_conn.close()
    os.unlink(tf.name)
