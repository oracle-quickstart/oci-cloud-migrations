$labvcenter = 'vcenter-ocmlab.sddc.iad.oci.oraclecloud.com'

function main {
    #Set-CBT
    #Set-CBT-Batch
    #List-All-CBT-Enabled
    #List-All-CBT-Disabled
    #Create-Lab-VMs
}

function Connect-Vcenter {
    Connect-VIServer -Server $labvcenter
}

function Set-CBT {
    param (
        [string]$vmName,
        [bool]$cbtSetting
    )
    $vmTarget = Get-vm $vmName | get-view
    $vmConfigSpec = New-Object VMware.Vim.VirtualMachineConfigSpec
    $vmConfigSpec.changeTrackingEnabled = $cbtSetting
    $vmTarget.reconfigVM($vmConfigSpec)
}

function Set-CBT-Batch {
    param (
        [bool]$enableCBT,
        [array]$VMs
    )
    $enableCBT = $true
    foreach ( $vmName in $VMs){
        # Get current CBT setting.
        $currentCBT = (Get-VM -Name $vmName).ExtensionData.Config.ChangeTrackingEnabled
        if ( $currentCBT -ne $enableCBT) {
            Set-CBT -vmName $vmName -cbtSetting $enableCBT
        }
    }
}

function List-All-CBT-Enabled {
    # Find VMs where Change Block Tracking is Enabled
    Get-VM| Where-Object{$_.ExtensionData.Config.ChangeTrackingEnabled -eq $true} | sort
}

function List-All-CBT-Disabled {
    # Find VMs where Change Block Tracking is Disabled
    Get-VM| Where-Object{$_.ExtensionData.Config.ChangeTrackingEnabled -eq $false} | sort
}

function Create-Lab-VMs {
    param (
        [array]$vms,
        [array]$users,
        [string]$workloadFolder,
        [string]$esxihostfqnd,
        [string]$datastore
    )

    foreach ($user in $users){

        New-Folder -Name "$user" -Location $workloadFolder
        $Folder = Get-Folder "$user"
        $vmHost = Get-VMHost $esxihostfqnd
        $dataStore = Get-Datastore $datastore

        foreach ($vm in $vms){
            $templateName = $vm + "_template"
            $Template = Get-Template -Name $templateName
            $workloadVM = $vm + "_" + $user

            New-VM -Name $workloadVM -Template $Template -VMHost $vmHost -Datastore $dataStore -Location $Folder -RunAsync
        }
    }
<#
#Get-vm "win2016-000"| get-view

        if ( $workloadVM like 'ol*' ) {
            Start-VM -Name $workloadVM -RunAsync
        }

#Get-VM| Where-Object{$_.Name -like 'ol*'} | Start-VM
#>

}

$connectedCount = $global:DefaultVIServers.Count

if ($connectedCount -eq 0 ) {
    Connect-Vcenter
}

main