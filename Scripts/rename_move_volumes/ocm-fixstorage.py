import sys
import time
import oci
from ocimodules.functions import login, input_command_line, create_signer, check_oci_version, MyWriter, GetHomeRegion, GetTenantName, SubscribedRegions, GetFullCompartments, GetCompartmentFullPath, findCompartment

# Disable OCI CircuitBreaker feature
oci.circuit_breaker.NoCircuitBreakerStrategy()

#################################################
#           Application Configuration           #
#################################################
min_version_required = "2.88.0"
application_version = "02.06.2026"

##########################################################################
# Main Program
##########################################################################
check_oci_version(min_version_required)

# Check command line parameters
cmd = input_command_line()

# if logging to file, overwrite default print function to also write to file
if cmd.log_file != "":
    writer = MyWriter(sys.stdout, cmd.log_file)
    sys.stdout = writer

#################################################
# oci config and "login" check
######################################################
config, signer = create_signer(cmd.config_profile, cmd.is_instance_principals, cmd.is_delegation_token)
tenant_id = config['tenancy']

login(config, signer)
tenant_name = GetTenantName(config, signer)
print("Tenant Name: {}".format(tenant_name))

if cmd.region:
    config['region'] = cmd.region


#################################################
# Check specified compartment
######################################################
compartment_id = findCompartment(config, signer, cmd.compartment)
if compartment_id == 0:
    print("Compartment not found")
    sys.exit(1)

#################################################
# Resolve compartment
#################################################
compartments = GetFullCompartments(config, signer)
compartment_path = GetCompartmentFullPath(compartments, compartment_id) or compartment_id

print("Compartment: {}".format(compartment_path))

#################################################
# Build volume compartment lookup across accessible compartments
#################################################
def build_volume_compartment_lookup(block_storage_client, compartments, retry_strategy):
    lookup = {}
    for comp in compartments:
        if comp.details.lifecycle_state != "ACTIVE":
            continue
        for list_fn, vol_type in (
            (block_storage_client.list_volumes, "block"),
            (block_storage_client.list_boot_volumes, "boot"),
        ):
            try:
                volumes = oci.pagination.list_call_get_all_results(
                    list_fn,
                    compartment_id=comp.details.id,
                    retry_strategy=retry_strategy
                ).data
                for vol in volumes:
                    lookup[vol.id] = {
                        "compartment_id": vol.compartment_id,
                        "display_name": vol.display_name,
                        "type": vol_type,
                    }
            except oci.exceptions.ServiceError:
                pass
    return lookup


def get_volume_info(block_storage_client, volume_id, volume_lookup, retry_strategy):
    if volume_id in volume_lookup:
        return volume_lookup[volume_id]

    is_boot = ".bootvolume." in volume_id
    try:
        if is_boot:
            vol = block_storage_client.get_boot_volume(volume_id, retry_strategy=retry_strategy).data
        else:
            vol = block_storage_client.get_volume(volume_id, retry_strategy=retry_strategy).data
        return {
            "compartment_id": vol.compartment_id,
            "display_name": vol.display_name,
            "type": "boot" if is_boot else "block",
        }
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def report_mismatch(instance, instance_compartment_path, vol_type, volume_id, volume_name, volume_compartment_path, note=""):
    print("\nMISMATCH - {} Volume{}".format(vol_type, note))
    print("  Instance:      {} ({})".format(instance.display_name, instance.id))
    print("  Instance Comp: {}".format(instance_compartment_path))
    print("  {} Volume:  {} ({})".format(vol_type, volume_name or "unknown", volume_id))
    print("  Volume Comp:   {}".format(volume_compartment_path))


def rename_boot_volume(block_storage_client, volume_id, display_name, retry_strategy):
    block_storage_client.update_boot_volume(
        volume_id,
        oci.core.models.UpdateBootVolumeDetails(display_name=display_name),
        retry_strategy=retry_strategy
    )


def rename_block_volume(block_storage_client, volume_id, display_name, retry_strategy):
    block_storage_client.update_volume(
        volume_id,
        oci.core.models.UpdateVolumeDetails(display_name=display_name),
        retry_strategy=retry_strategy
    )


def move_boot_volume(block_storage_client, volume_id, compartment_id, retry_strategy):
    block_storage_client.change_boot_volume_compartment(
        volume_id,
        oci.core.models.ChangeBootVolumeCompartmentDetails(compartment_id=compartment_id),
        retry_strategy=retry_strategy
    )


def move_block_volume(block_storage_client, volume_id, compartment_id, retry_strategy):
    block_storage_client.change_volume_compartment(
        volume_id,
        oci.core.models.ChangeVolumeCompartmentDetails(compartment_id=compartment_id),
        retry_strategy=retry_strategy
    )

#################################################
# Check compute instance volume compartment mismatches
#################################################
compute_client = oci.core.ComputeClient(config, signer=signer)
block_storage_client = oci.core.BlockstorageClient(config, signer=signer)
retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY

instances = oci.pagination.list_call_get_all_results(
    compute_client.list_instances,
    compartment_id=compartment_id,
    retry_strategy=retry_strategy
).data

active_instances = [i for i in instances if i.lifecycle_state != "TERMINATED"]
print("\nFound {} compute instance(s) in compartment ({} active)".format(
    len(instances), len(active_instances)))

mismatch_count = 0
instance_volumes = []

print("Building volume inventory across accessible compartments...")
volume_lookup = build_volume_compartment_lookup(block_storage_client, compartments, retry_strategy)
print("Indexed {} volume(s)".format(len(volume_lookup)))

for instance in active_instances:
    instance_compartment = instance.compartment_id
    instance_compartment_path = GetCompartmentFullPath(compartments, instance_compartment) or instance_compartment
    mismatched_boot_volume_ids = []
    mismatched_block_volume_ids = []

    boot_attachments = oci.pagination.list_call_get_all_results(
        compute_client.list_boot_volume_attachments,
        compartment_id=compartment_id,
        availability_domain=instance.availability_domain,
        instance_id=instance.id,
        retry_strategy=retry_strategy
    ).data

    for attachment in boot_attachments:
        if attachment.lifecycle_state == "DETACHED":
            continue
        vol_info = get_volume_info(
            block_storage_client, attachment.boot_volume_id, volume_lookup, retry_strategy
        )
        if vol_info is None:
            mismatch_count += 1
            mismatched_boot_volume_ids.append(attachment.boot_volume_id)
            report_mismatch(
                instance, instance_compartment_path, "Boot", attachment.boot_volume_id,
                attachment.display_name, "unknown (volume not accessible)",
                note=" - suspected cross-compartment"
            )
            continue
        if vol_info["compartment_id"] != instance_compartment:
            mismatch_count += 1
            mismatched_boot_volume_ids.append(attachment.boot_volume_id)
            volume_compartment_path = GetCompartmentFullPath(compartments, vol_info["compartment_id"]) or vol_info["compartment_id"]
            report_mismatch(
                instance, instance_compartment_path, "Boot", attachment.boot_volume_id,
                vol_info["display_name"], volume_compartment_path
            )

    volume_attachments = oci.pagination.list_call_get_all_results(
        compute_client.list_volume_attachments,
        compartment_id=compartment_id,
        instance_id=instance.id,
        retry_strategy=retry_strategy
    ).data

    for attachment in volume_attachments:
        if attachment.lifecycle_state == "DETACHED":
            continue
        vol_info = get_volume_info(
            block_storage_client, attachment.volume_id, volume_lookup, retry_strategy
        )
        if vol_info is None:
            mismatch_count += 1
            mismatched_block_volume_ids.append(attachment.volume_id)
            report_mismatch(
                instance, instance_compartment_path, "Block", attachment.volume_id,
                attachment.display_name, "unknown (volume not accessible)",
                note=" - suspected cross-compartment"
            )
            continue
        if vol_info["compartment_id"] != instance_compartment:
            mismatch_count += 1
            mismatched_block_volume_ids.append(attachment.volume_id)
            volume_compartment_path = GetCompartmentFullPath(compartments, vol_info["compartment_id"]) or vol_info["compartment_id"]
            report_mismatch(
                instance, instance_compartment_path, "Block", attachment.volume_id,
                vol_info["display_name"], volume_compartment_path
            )

    if mismatched_boot_volume_ids or mismatched_block_volume_ids:
        instance_volumes.append({
            "instance": instance,
            "mismatched_boot_volume_ids": mismatched_boot_volume_ids,
            "mismatched_block_volume_ids": mismatched_block_volume_ids,
        })

if mismatch_count == 0:
    print("\nNo compartment mismatches found for attached boot and block volumes.")
else:
    print("\nTotal mismatches found: {}".format(mismatch_count))

if cmd.fix:
    if mismatch_count == 0:
        print("\nFix mode enabled: no mismatches to fix.")
    else:
        planned_fixes = []

        for entry in instance_volumes:
            instance = entry["instance"]
            instance_name = instance.display_name
            target_compartment = instance.compartment_id
            target_compartment_path = GetCompartmentFullPath(compartments, target_compartment) or target_compartment

            for boot_volume_id in entry["mismatched_boot_volume_ids"]:
                vol_info = get_volume_info(block_storage_client, boot_volume_id, volume_lookup, retry_strategy)
                current_name = vol_info["display_name"] if vol_info else "unknown"
                current_compartment_path = (
                    GetCompartmentFullPath(compartments, vol_info["compartment_id"]) or vol_info["compartment_id"]
                    if vol_info else "unknown"
                )
                planned_fixes.append({
                    "instance": instance,
                    "volume_type": "boot",
                    "volume_id": boot_volume_id,
                    "current_name": current_name,
                    "new_name": "{} (Boot Volume)".format(instance_name),
                    "current_compartment_path": current_compartment_path,
                    "target_compartment_path": target_compartment_path,
                    "target_compartment_id": target_compartment,
                })

            for block_index, block_volume_id in enumerate(entry["mismatched_block_volume_ids"], start=1):
                vol_info = get_volume_info(block_storage_client, block_volume_id, volume_lookup, retry_strategy)
                current_name = vol_info["display_name"] if vol_info else "unknown"
                current_compartment_path = (
                    GetCompartmentFullPath(compartments, vol_info["compartment_id"]) or vol_info["compartment_id"]
                    if vol_info else "unknown"
                )
                planned_fixes.append({
                    "instance": instance,
                    "volume_type": "block",
                    "volume_id": block_volume_id,
                    "current_name": current_name,
                    "new_name": "{} (Block Volume {:02d})".format(instance_name, block_index),
                    "current_compartment_path": current_compartment_path,
                    "target_compartment_path": target_compartment_path,
                    "target_compartment_id": target_compartment,
                })

        print("\nFix mode enabled: {} mismatched volume(s) will be updated.".format(len(planned_fixes)))
        print("\nPlanned changes:")
        for index, fix in enumerate(planned_fixes, start=1):
            vol_type_label = "Boot" if fix["volume_type"] == "boot" else "Block"
            print("\n  {}. {} volume for instance '{}'".format(index, vol_type_label, fix["instance"].display_name))
            print("     Volume ID:       {}".format(fix["volume_id"]))
            print("     Rename:          '{}' -> '{}'".format(fix["current_name"], fix["new_name"]))
            print("     Move compartment: {} -> {}".format(
                fix["current_compartment_path"], fix["target_compartment_path"]))

        confirm = input("\nApply these changes? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Fix cancelled.")
        else:
            rename_count = 0
            move_count = 0
            fix_errors = 0

            print("\nPhase 1: Renaming mismatched volumes...")
            for fix in planned_fixes:
                try:
                    if fix["volume_type"] == "boot":
                        rename_boot_volume(block_storage_client, fix["volume_id"], fix["new_name"], retry_strategy)
                    else:
                        rename_block_volume(block_storage_client, fix["volume_id"], fix["new_name"], retry_strategy)
                    rename_count += 1
                    print("  Renamed {} volume {} -> '{}'".format(
                        fix["volume_type"], fix["volume_id"], fix["new_name"]))
                except oci.exceptions.ServiceError as e:
                    fix_errors += 1
                    print("  ERROR renaming {} volume {}: {}".format(
                        fix["volume_type"], fix["volume_id"], e.message))

            print("\nPhase 2: Moving mismatched volumes to instance compartments...")
            for fix in planned_fixes:
                try:
                    if fix["volume_type"] == "boot":
                        move_boot_volume(
                            block_storage_client, fix["volume_id"], fix["target_compartment_id"], retry_strategy
                        )
                    else:
                        move_block_volume(
                            block_storage_client, fix["volume_id"], fix["target_compartment_id"], retry_strategy
                        )
                    move_count += 1
                    print("  Moved {} volume {} -> {}".format(
                        fix["volume_type"], fix["volume_id"], fix["target_compartment_path"]))
                except oci.exceptions.ServiceError as e:
                    fix_errors += 1
                    print("  ERROR moving {} volume {}: {}".format(
                        fix["volume_type"], fix["volume_id"], e.message))

            print("\nFix complete: {} volume(s) renamed, {} volume(s) moved, {} error(s)".format(
                rename_count, move_count, fix_errors))

