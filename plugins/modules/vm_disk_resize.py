#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, inett Gmbh <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: vm_disk_resize
short_description: Resize configured block device of a VM
version_added: "2.9"

description:
    - "Resize configured block device of a VM"
    - "Only growing it is possible in Proxmox VE"

options:
    vmid:
        description:
             - Id of the VM to configure
        type: int
        required: true
    disk:
        description:
            - Config key of the device to be resized
        type: str
        required: true
    size:
        description:
            - New size of block device in GB
        type: int
        required: true

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: resize disks
  delegate_to: "{{ pve_target_node }}"
  inett.pve.vm_disk_resize:
    vmid: 100
    disk: "scsi0"
    size: 200
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
stdout:
    description: stdout of clone Proxmox VE CLI command
    type: str
stderr:
    description: stderr of clone Proxmox VE CLI command
    type: str
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        vmid=dict(type=int, required=True),
        disk=dict(type=str, required=True),
        size=dict(type=int, required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=False)

    node = mod.vm_locate(mod.params['vmid'])

    _rc, out, err, vm_config = mod.query_json(
        'set', "/nodes/%s/qemu/%d/resize" % (node, mod.params['vmid']),
        params=dict(
            disk=mod.params['disk'],
            size="%dG" % mod.params['size'],
        ),
    )
    mod.exit_json(changed=False, stdout=out, stderr=err)


def main():
    run_module()


if __name__ == '__main__':
    main()
