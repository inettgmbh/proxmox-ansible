#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: vm_locate_info
short_description: Clone VM or Template
version_added: "2.14"

description:
    - "Clone VM or Template"

options:
    vmid:
        description:
             - Id of the new VM
        type: int
        required: false
        default: New VMID from API

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Clone VM
  inett.pve.vm_locate_info:
    vmid: 101
  delegate_to: pve01
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
node:
    description: Returns node the VM is running on. Returns Null if VM isn't found
    type: str
    returned: always
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        vmid=dict(type="int", required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=False)

    vmid = mod.params['vmid']

    node = mod.vm_locate(vmid)

    if node is None:
        mod.fail_json(msg="VM not found")
    else:
        rc, _out, _err, _obj = mod.query_json('set', f'/nodes/{node}/qemu/{vmid}/cloudinit')
        if rc != 0:
            mod.fail_json(msg=f"Failed to refresh cloud init")

        mod.exit_json(
            changed=False, vmid=vmid, node=node,
        )
    return


def main():
    run_module()


if __name__ == "__main__":
    main()