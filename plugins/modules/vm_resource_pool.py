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
module: vm_resource_pool
short_description: Assign VM to a resource pool
version_added: "2.9"

description:
    - "Assign VM to a resource pool"

options:
    vmid:
        description:
             - Id of the VM to configure
        type: int
        required: true
    pool:
        description:
            - Resource pool the VM should be in
            - The resource pool MUST already exist
        type: str
        required: true

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Configure Resource Pool
  inett.pve.vm_resource_pool:
    vmid: "{{ pve_vmid }}"
    pool: "{{ pve_vm_resource_pool }}"
  delegate_to: "{{ pve_target_node }}"

'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
stdout:
    description: Stdout of clone Proxmox VE CLI command
    type: str
    returned: always
stderr:
    description: Stderr of clone Proxmox VE CLI command
    type: str
    returned: always
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        vmid=dict(type=int, required=True),
        pool=dict(type=str, required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    node = mod.vm_locate(mod.params['vmid'])

    _rc, out, err = mod.query_api(
        'set', "/pools/%s" % (mod.params['pool']),
        params=dict(
            vms=[ str(mod.params['vmid']) ],
        ),
    )
    mod.exit_json(changed=True, stdout=out, stderr=err)


def main():
    run_module()


if __name__ == '__main__':
    main()
