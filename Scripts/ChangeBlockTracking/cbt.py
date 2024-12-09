from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import ssl
import argparse
import configparser

# Read configuration from config.ini.example
config = configparser.ConfigParser()
config.read('config.ini')
vc_host = config.get('vCenter', 'host')
vc_user = config.get('vCenter', 'user')
vc_password = config.get('vCenter', 'password')

# Disable SSL certificate verification
ssl_context = ssl._create_unverified_context()


def connect_to_vc(vc_host, vc_user, vc_password, ssl_context):
    try:
        return SmartConnect(host=vc_host, user=vc_user, pwd=vc_password, sslContext=ssl_context)
    except vim.fault.InvalidLogin:
        raise SystemExit("Invalid username/password")
    except Exception as e:
        raise SystemExit(str(e))


def get_vm_by_name(content, vm_name):
    obj_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    for vm in obj_view.view:
        if vm.name == vm_name:
            obj_view.Destroy()
            return vm
    obj_view.Destroy()
    return None


def get_folder(content, folder_name):
    obj_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Folder], True)
    for f in obj_view.view:
        if f.name == folder_name:
            obj_view.Destroy()
            return f
    obj_view.Destroy()
    return None

def get_vms_in_folder(folder):
    vm_list = []
    for child in folder.childEntity:
        if isinstance(child, vim.VirtualMachine):
            vm_list.append(child)
        elif isinstance(child, vim.Folder):
            vm_list.extend(get_vms_in_folder(child))  # Recursively add VMs from subfolders
    return vm_list

def display_cbt_info(vm):
    print(f"VM: {vm.name}")
    if vm.config.changeTrackingEnabled:
        print("  CBT is enabled")
    else:
        print("  CBT is disabled")
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            print(f"  Disk: {device.deviceInfo.label} - {device.backing.diskMode}")
            if device.backing.changeId:
                print(f"    CBT Enabled: Yes")
            else:
                if vm.config.changeTrackingEnabled:
                    print(f"    CBT Enabled: No - VM possibly needs a reboot?")
                else:
                    print(f"    CBT Enabled: No")
            disk_mode = device.backing.diskMode
            if "independent" in disk_mode:
                print(f"    Warning: Disk '{device.deviceInfo.label}' on VM '{vm.name}' is configured as '{disk_mode}'. Snapshots may not work as expected.")

def enable_cbt_on_vm(vm, args):
    print(f"Enabling CBT for VM: {vm.name}")
    spec = vim.vm.ConfigSpec()
    spec.changeTrackingEnabled = True
    device_changes = []

    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            disk_mode = device.backing.diskMode
            if "independent" in disk_mode:
                print(
                    f" - Warning: Disk '{device.deviceInfo.label}' on VM '{vm.name}' is configured as '{disk_mode}'. Snapshots may not work as expected.")
                if disk_mode == "independent_persistent" and args.dependent:
                    print (f" - Converting disk '{device.deviceInfo.label}' to dependent-persistent disk mode")
                    device.backing.diskMode = "persistent"
            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            disk_spec.device = device
            disk_spec.device.backing.changeId = ""
            device_changes.append(disk_spec)

    spec.deviceChange = device_changes
    task = vm.ReconfigVM_Task(spec)
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        pass
    if task.info.state == vim.TaskInfo.State.success:
        print(f" - Completed successfully")
    else:
        print(f" - Failed: {task.info.error.msg}")


def main():
    parser = argparse.ArgumentParser(description="Get or Set Change Block Tracking (CBT) on a VM or all VMs in a folder.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--vm_name", help="The name of the virtual machine")
    group.add_argument("--vm_folder", help="The path of the folder containing VMs")
    parser.add_argument("--enable", action='store_true', help="Enable Change Block tracking")
    parser.add_argument("--dependent", action='store_true', help="Convert independent-persistent disk to dependent-persistent")
    args = parser.parse_args()

    service_instance = connect_to_vc(vc_host, vc_user, vc_password, ssl_context)
    content = service_instance.RetrieveContent()

    if args.vm_name:
        vm = get_vm_by_name(content, args.vm_name)
        if vm:
            if args.enable:
                enable_cbt_on_vm(vm, args)
            else:
                display_cbt_info(vm)
        else:
            print(f"VM '{args.vm_name}' not found")
    elif args.vm_folder:
        folder = get_folder(content, args.vm_folder)
        vms = get_vms_in_folder(folder)
        if vms:
            for vm in vms:
                if args.enable:
                    enable_cbt_on_vm(vm, args)
                else:
                    display_cbt_info(vm)
        else:
            print(f"No VMs found in folder '{args.vm_folder}'")

    else:
        print("No VM name or VM folder path provided!")

    Disconnect(service_instance)


if __name__ == "__main__":
    main()
