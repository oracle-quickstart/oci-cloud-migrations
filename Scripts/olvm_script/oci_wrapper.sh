#!/bin/zsh

# Wrapper script to execute OCI CLI commands for cloud-migrations and cloud-bridge


# Feature List

# Discovery (Create/List/Refresh)
## Create OLVM|VMware asset sources
## List OLVM|VMware asset sources
## Refresh OLVM|VMware asset sources

# Inventory (List Only)
## List OLVM Inventory assets (storage domain, cluster, templates, VNIC Profiles)
## List VMware Inventory assets

# Migration (Create/Init/List/Update)
## Create Migration project
## Initialize migration project info
## Bulk add migration assets to project
## Replicate migration assets in project
## Create Migration plan
## Execute Migration plan

setopt shwordsplit

# FIXED VARIABLES
auth="--config-file $HOME/.oci/config --profile DEFAULT --auth security_token"
cm_beta="--endpoint "https://cloudmigration.us-phoenix-1.oci.oc-test.com""
cb_beta="--endpoint "https://cloudbridge.us-phoenix-1.oci.oc-test.com""

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Dynamically load all required IDs / endpoints from config.json so that
# this wrapper script does not hard-code tenancy-specific values.
#
# Requires: jq (https://stedolan.github.io/jq/)
# ---------------------------------------------------------------------------

CONFIG_FILE="$(dirname "$0")/config.json"

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Config file not found: $CONFIG_FILE" >&2
  exit 1
fi

# Initialize config.json variables
tenant_id=$(jq -r '.tenant_id'            "$CONFIG_FILE")
mig_cmpt=$(jq -r '.mig_cmpt'              "$CONFIG_FILE")
mig_secret_cmpt=$(jq -r '.mig_secret_cmpt' "$CONFIG_FILE")
env_id=$(jq -r '.env_id'                  "$CONFIG_FILE")

olvm_discovery_secret=$(jq -r '.olvm_discovery_secret'   "$CONFIG_FILE")
olvm_replication_secret=$(jq -r '.olvm_replication_secret' "$CONFIG_FILE")
vcenter_discovery_secret=$(jq -r '.vcenter_discovery_secret' "$CONFIG_FILE")
vcenter_replication_secret=$(jq -r '.vcenter_replication_secret' "$CONFIG_FILE")

olvm_endpoint=$(jq -r '.olvm_endpoint'     "$CONFIG_FILE")
vcenter_endpoint=$(jq -r '.vcenter_endpoint' "$CONFIG_FILE")

migration_id=$(jq -r '.migration_id'       "$CONFIG_FILE")
migration_plan_id=$(jq -r '.migration_plan_id' "$CONFIG_FILE")

cluster_id=$(jq -r '.cluster_id'           "$CONFIG_FILE")
vnic_profile_id=$(jq -r '.vnic_profile_id' "$CONFIG_FILE")
template_id=$(jq -r '.template_id'         "$CONFIG_FILE")

# Dummy vars. TODO: Replace with lookup
vol_AD="gfwo:PHX-AD-1"
snapshot_bucket="ocmlab06"


# Preserve script name; in zsh the FUNCTION_ARGZERO option can cause `$0`
# inside a function to expand to the function's name (“usage”).  Capture the
# real script name here for consistent help text.
script_name=./$(basename "$0")

usage() {
  echo "Usage: $script_name [discovery|inventory|migration] [command] [sub-command/options]"
  echo "Example: $script_name inventory inventory list"
}

# Require at least 3 arguments: category, resource and action
if [[ $# -lt 3 ]]; then
  echo "Error: expected at least 3 arguments (category, resource, action)." >&2
  usage
  exit 1
fi

category=$1
resource=$2
action=$3
shift
shift
shift
args=$@


oci_session_init() {
  oci session authenticate --profile-name "DEFAULT" --region "us-phoenix-1"
}

# -----------------------------------------------------------------
# Check if the file (first argument) exists
# -----------------------------------------------------------------
check_file_exists() {
  local filename=$1
  if [ ! -f "$filename" ]; then
    echo "Error: $filename does not exist"
    exit 1
  fi
  echo "$filename exists"
}

# -----------------------------------------------------------------
# Retrieve Cloud Bridge inventory OCID with error handling
# -----------------------------------------------------------------
get_inventory_id() {
  local inventory_json
  inventory_json=$(oci cloud-bridge inventory inventory list \
                   --compartment-id $tenant_id $auth $cb_beta 2>/dev/null)
  if [[ $? -ne 0 ]]; then
    echo "Error: failed to retrieve inventory list for tenant $tenant_id" >&2
    exit 1
  fi
  local id
  id=$(echo "$inventory_json" | jq -r '.data.items[0].id // empty')
  if [[ -z "$id" ]]; then
    echo "Error: no inventory found in compartment $tenant_id" >&2
    exit 1
  fi
  echo "$id"
}

# Start of the script
case $category in
  discovery)
    if [[ "$resource" != "asset-source" ]]; then
      echo "Error: Only asset-source resource is supported"
      exit 1
    fi
    inventory_id=$(get_inventory_id)
    case $action in
      list)
        action+=" --compartment-id $mig_cmpt --lifecycle-state ACTIVE"
        oci cloud-bridge discovery $resource $action $auth $cb_beta
      ;;
      create-olvm)
        # action=" create --compartment-id $mig_cmpt --assets-compartment-id $mig_cmpt \
        #         --inventory-id $inventory_id --environment-id $env_id \
        #         --discovery-credentials {\"type\":\"BASIC\",\"secretId\":\"$olvm_discovery_secret\"} \
        #         --replication-credentials {\"type\":\"BASIC\",\"secretId\":\"$olvm_replication_secret\"} \
        #         --olvm-endpoint $olvm_endpoint --type OLVM --environment-type DESTINATION"
        oci raw-request --http-method POST --target-uri "https://cloudbridge.us-phoenix-1.oci.oc-test.com/20220509/assetSources" \
        --request-body "{
          \"type\": \"OLVM\",
          \"compartmentId\": \"$mig_cmpt\",
          \"environmentId\": \"$env_id\",
          \"inventoryId\": \"$inventory_id\",
          \"assetsCompartmentId\": \"$mig_cmpt\",
          \"discoveryScheduleId\": null,
          \"olvmEndpoint\": \"$olvm_endpoint\",
          \"discoveryCredentials\": {
            \"type\": \"BASIC\",
            \"secretId\": \"$olvm_discovery_secret\"
          },
          \"replicationCredentials\": {
            \"type\": \"BASIC\",
            \"secretId\": \"$olvm_replication_secret\"
          },
          \"environmentType\": \"DESTINATION\"
        }" $auth
      ;;
      create-vcenter)
        action=" create --compartment-id $mig_cmpt --assets-compartment-id $mig_cmpt \
                --inventory-id $inventory_id --environment-id $env_id \
                --discovery-credentials {\"type\":\"BASIC\",\"secretId\":\"$vcenter_discovery_secret\"} \
                --vcenter-endpoint $vcenter_endpoint --type VMWARE --environment-type SOURCE"
        oci cloud-bridge discovery $resource $action $auth $cb_beta
      ;;
      discover)
        action=" refresh --asset-source-id $args"
        oci cloud-bridge discovery $resource $action $auth $cb_beta
      ;;
      get-work-request)
        oci cloud-bridge common work-request get --work-request-id $args $auth $cb_beta
      ;;
      *)
        echo "Error: Invalid action. "
        exit 1
      ;;
    esac
  ;;
  inventory)
    if [[ "$action" != "list" ]]; then
      echo "Only LIST action is supported"
      exit 1
    fi
    case $resource in
      inventory)
        action+=" --compartment-id $tenant_id"
        oci cloud-bridge inventory $resource $action $auth $cb_beta
      ;;
      asset)
        action+=" --compartment-id $mig_cmpt --all --lifecycle-state ACTIVE"
        result=$(oci cloud-bridge inventory $resource $action $auth $cb_beta)

        case $args in
          vmware-vm)
            # List "VMware VMs"
            echo $result | jq '[.data.items[] 
            | select(."asset-type" == "VMWARE_VM") 
            | {"id": ."id", "display-name": ."display-name", "external-asset-key": ."external-asset-key"}]'
          ;;
          storage-domain)
            # List "Storage Domains"
            echo $result | jq '[.data.items[] 
            | select(."asset-class-name" != null and (."asset-class-name" 
            | contains("StorageDomain"))) | {"id": ."id", "display-name": ."display-name", "external-asset-key": ."external-asset-key" }] '
          ;;
          cluster)
            # List "Clusters"
            echo $result | jq '[.data.items[] | 
            select(."asset-class-name" != null and (."asset-class-name" 
            | contains("Cluster"))) 
            | {"id": ."id", "display-name": ."display-name", "external-asset-key": ."external-asset-key" }]'
          ;;
          template)
            # List "Templates"
            echo $result | jq '[.data.items[] | 
            select(."asset-class-name" != null and (."asset-class-name" 
            | contains("Template"))) 
            | {"id": ."id", "display-name": ."display-name", "external-asset-key": ."external-asset-key" }]'
          ;;
          vnic-profile)
            # List "VNIC Profiles"
            echo $result | jq '[.data.items[] | 
            select(."asset-class-name" != null and (."asset-class-name" 
            | contains("VnicProfile"))) 
            | {"id": ."id", "display-name": ."display-name", "external-asset-key": ."external-asset-key" }]'
          ;;
          *)
            echo "Error: Invalid inventory asset type. Please use 'vmware-vm', 'storage-domain', 'cluster', 'template', or 'vnic-profile'."
            exit 1
          ;;
        esac
      ;;
      *)
        echo "Error: Invalid resource type. Please use 'inventory', or 'asset'."
        exit 1
      ;;
    esac
  ;;
  migration)
    case $resource in
      migration)
        case $action in
          list)
            action+=" --compartment-id $mig_cmpt --all"
          ;;
          create)
            action+=" --compartment-id $mig_cmpt --display-name $args --migration-type OLVM"
          ;;
          init)
            filename=$1
            storage_domain_asset=$2
            tmpfile=$(mktemp)
            check_file_exists "$filename"
            jq --arg nv "$storage_domain_asset" 'map(. + {"storage-domain-asset-id": $nv})' "$filename" > "$tmpfile" && mv "$tmpfile" "$filename"
            exit 0
          ;;
          start-migration-replication)
            action+=" --migration-id $migration_id"
          ;;
          *)
            echo "Error: Invalid action. "
            exit 1
          ;;
        esac
      ;;
      migration-asset)
        case $action in
          create)
            filename=$args
            check_file_exists "$filename"
            echo "Creating migration assets based on information in $filename"
            while IFS= read -r line; do
              if [ "$(echo "$line" | jq 'has("storage-domain-asset-id")')" = "false" ]; then
                echo "Error: Storage Domain not initialized. Run ./oci_wrapper.sh migration migration init <json file> <storage domain OCID> first."
                exit 1
              fi
              id=$(echo "$line" | jq -r '.id')
              display_name=$(echo "$line" | jq -r '."display-name"')
              external_asset_key=$(echo "$line" | jq -r '."external-asset-key"')
              storage_domain_asset=$(echo "$line" | jq -r '."storage-domain-asset-id"')

              action+=" --inventory-asset-id $id --migration-id $migration_id \
              --availability-domain $vol_AD --replication-compartment-id $mig_cmpt \
              --snap-shot-bucket-name $snapshot_bucket \
              --replication-location {\"replicationLocationType\":\"OLVM_STORAGE_DOMAIN\",\"metadata\":{\"storageDomainAssetId\":\"$storage_domain_asset\"}}"

              oci raw-request --http-method POST --target-uri "https://cloudmigration.us-phoenix-1.oci.oc-test.com/20220919/migrationAssets" \
              --request-body "{
                \"displayName\": \"$display_name\",
                \"inventoryAssetId\": \"$id\",
                \"availabilityDomain\": \"$vol_AD\",
                \"migrationId\": \"$migration_id\",
                \"replicationCompartmentId\": \"$mig_cmpt\",
                \"snapShotBucketName\": \"$snapshot_bucket\",
                \"replicationLocationDetail\": {
                  \"replicationLocationType\": \"OLVM_STORAGE_DOMAIN\",
                  \"metadata\":{
                     \"storageDomainAssetId\": \"$storage_domain_asset\"
                  }
                }
              }" $auth
              oci cloud-migrations $resource $action $auth $cm_beta
              echo "\n"
              action="create "
            done < <(jq -c '.[]' $filename)

            exit 0
          ;;
          *)
            echo "Error: Invalid action."
            exit 1
        esac
      ;;
      migration-plan)
        case $action in
          create)
            action+=" --display-name $args --compartment-id $mig_cmpt --migration-id $migration_id 
            --strategies [{\"resourceType\":\"CPU\",\"strategyType\":\"AS_IS\"}]
            --target-environments [{\"targetEnvironmentType\":\"OLVM_TARGET_ENV\",\"clusterAssetId\":\"$cluster_id\",\"vnicProfileAssetId\":\"$vnic_profile_id\",\"olvmTemplates\":{\"OracleLinux7(64-bit)\":\"$template_id\"}}]"
          ;;
          execute)
            action+=" --migration-plan-id $migration_plan_id"
          ;;
          *)
            echo "Error: Invalid action."
            exit 1
          ;;
        esac
      ;;
      *)
        echo "Invalid resource. Please use 'migration', 'migration-asset', or 'migration-plan'"
        exit 1
      ;;
    esac
    oci cloud-migrations $resource $action $auth $cm_beta
  ;;
  *)
    echo "Invalid category. Please use 'discovery', 'inventory', or 'migration'."
    usage
    exit 1
  ;;
esac
