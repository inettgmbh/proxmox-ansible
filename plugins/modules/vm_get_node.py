#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: vm_get_node
short_description: Fetch node a VM is running on 
version_added: "2.9"

description:
    - "Fetch node a VM is running on"
    - "The hypervisor node will be returned as `node`"

options:
    vmid:
        description:
             - Id of the VM to configure
        type: int
        required: true

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Get name of the Proxmox VE node a guest is running on
  delegate_to: pve01
  inett.pve.vm_get_node:
    vmid: 100
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
node:
    description: Proxmox VE node the VM is running on
    type: str
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        vmid=dict(type=int, required=True),
        access=dict(
            choices=['pvesh', 'http'], required=False, default='pvesh'
        ),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    vm_info = mod.vm_info(mod.params["vmid"])
    mod.exit_json(changed=False, node=vm_info["node"])


def main():
    run_module()


if __name__ == '__main__':
    main()
