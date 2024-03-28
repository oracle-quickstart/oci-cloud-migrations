# boot_order.py

A simple script, which displays content of the `compute.disks` object of a source asset and adjusts boot order to point onto a specific disk for the target asset to boot from. Takes optional parameter -b/--boot-order with the index of the index of the disk (starting from 0) in `compute.disks` object to boot from. Readied for execution from the Cloud Shell.

Usage:
```

ansokolo@cloudshell:~ (us-ashburn-1)$ python ./boot_order.py
usage: edit_boot_order.py [-h] [-b BOOT_DISK_INDEX] ocid
edit_boot_order.py: error: the following arguments are required: ocid

ansokolo@cloudshell:~ (us-ashburn-1)$ python ./boot_order.py ocid1.ocbinventoryasset.oc1.iad.amaaaaaabkvmyqqa5u2ypgvw5k67be656j45oceyjbd4u4srkax435locshq
[{
  "boot_order": null,
  "location": "[vsanDatastore] 5b69e665-ea2a-6de1-0dfe-b02628368f10/egolenko-new-windows-workload-bootorder_4.vmdk",
  "name": "Hard disk 1",
  "persistent_mode": "persistent",
  "size_in_mbs": 61440,
  "uuid": "6000C29a-03a9-9a90-f23d-89cf4c893316",
  "uuid_lun": null
}, {
  "boot_order": 0,
  "location": "[vsanDatastore] 5b69e665-ea2a-6de1-0dfe-b02628368f10/egolenko-new-windows-workload-bootorder_6.vmdk",
  "name": "Hard disk 2",
  "persistent_mode": "persistent",
  "size_in_mbs": 92160,
  "uuid": "6000C29f-3ef9-9d9b-1264-25375c439e2e",
  "uuid_lun": null
}]


ansokolo@cloudshell:~ (us-ashburn-1)$ python ./boot_order.py ocid1.ocbinventoryasset.oc1.iad.amaaaaaabkvmyqqa5u2ypgvw5k67be656j45oceyjbd4u4srkax435locshq -b 0
[{
  "boot_order": 0,
  "location": "[vsanDatastore] 5b69e665-ea2a-6de1-0dfe-b02628368f10/egolenko-new-windows-workload-bootorder_4.vmdk",
  "name": "Hard disk 1",
  "persistent_mode": "persistent",
  "size_in_mbs": 61440,
  "uuid": "6000C29a-03a9-9a90-f23d-89cf4c893316",
  "uuid_lun": null
}, {
  "boot_order": null,
  "location": "[vsanDatastore] 5b69e665-ea2a-6de1-0dfe-b02628368f10/egolenko-new-windows-workload-bootorder_6.vmdk",
  "name": "Hard disk 2",
  "persistent_mode": "persistent",
  "size_in_mbs": 92160,
  "uuid": "6000C29f-3ef9-9d9b-1264-25375c439e2e",
  "uuid_lun": null
}]
```