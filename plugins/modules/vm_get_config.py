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
module: vm_get_config
short_description: Fetch configuration of a VM
version_added: "2.9"

description:
    - "Fetch configuration of a VM"
    - |
        The raw configuration as returned by the Proxmox VE API will be
        returned as `pve_vm_config_raw`. A parsed representation will
        be returned as `pve_vm_config`.

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
- name: Get VM config
  delegate_to: pve01
  inett.pve.vm_get_config:
    vmid: 100
  register: _vm_get_config
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
stdout:
    description: stdout of clone Proxmox VE CLI command
    type: str
    returned: always
stderr:
    description: stderr of clone Proxmox VE CLI command
    type: str
    returned: always
pve_vm_config_raw:
    description: raw Proxmox VE VM configuration
    type: dict
    returned: always
pve_vm_config:
    description: Proxmox VE VM configuration with parsed values
    type: dict
    returned: always
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        vmid=dict(type=int, required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    node = mod.vm_locate(mod.params['vmid'])

    _rc, out, err, vm_config_raw = mod.query_json(
            'get',
            "/nodes/%s/qemu/%s/config" % (node, mod.params["vmid"])
    )
    vm_config = mod.vm_config_get(mod.params["vmid"])

    mod.exit_json(changed=False, stdout=out, stderr=err, 
        pve_vm_config_raw=vm_config_raw,
        pve_vm_config=vm_config,
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
