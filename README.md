# proxmox-ansible

## usage

VMs are part of the inventory in the form of normal hosts, but contained 
special groups, configured with variables.


### groups

* `pve_nodes` must contain Proxmox VE nodes
* `pve_vms` all vms to be deployed/removed must be inside this group

### playbooks

* `vms_setup`: basic setup for VMs

### roles

* `inett.pve.pve_cluster_group`: gather facts about Proxmox VE nodes and 
  group them by cluster name
* `inett.pve.pve_vm_prepare_facts`: assigns VMs to target nodes, set and merge 
  some facts
* `inett.pve.pve_vms`: set up VMs and group them by target state
* `inett.pve.pve_vm_disks`: resize and create SCSI disks
* `inett.pve.pve_vm_cloudinit`: ensure state of cloud-init drive
* `inett.pve.pve_vms_finish`: wait for VMs (timeout if `pve_vm_wait` is an 
  integer, connection (Linux) if `pve_vm_wait` is set to "connect") and 
  finish setup

### variables

#### pve_nodes

`pve_vm_storage` and `pve_efivars_storage` are automatically merged by the 
role `inett.pve.pve_vm_prepare_facts` from the target node to the VM.

#### pve_vms

* `pve_vmid` (Integer, **required**): ID of VM
* `pve_vm_state` (running|stopped|absent, **required**): target state for VM
* `pve_vm_memory` (Integer, 1024): size of VM RAM in bytes
* `pve_vm_cpu` (dict): 
  * `cores` (Integer (4)): number of cores
  * `vcpus` (Integer (4)): number of virtual cpus
  * `limit` (Integer (4)): CPU limit
* `pve_vm_storage` (String): default storage for VM resources
* `pve_vm_scsi` (dict):
  * 0:
    * `storage` (String, `{{ pve_vm_storage }}`)
* `pve_vm_setup_iso` (dict):
  * `storage` (String ('cephfs'))
  * `image_name` (String, **required**)
  * `media` (String ('cdrom'))
* `pve_vm_remove_install_media` (Boolean (true)): remove media in `ide1` 
  after VM setup  
* `pve_target_cluster` (String): Name of the target cluster for VM related tasks
* `pve_target_node` (String): Inventory name of target Proxmox VE node 
  (overrides `pve_target_cluster`)
