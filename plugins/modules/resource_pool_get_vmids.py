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
module: resource_pool_get_vmids
short_description: get VMs in resource pool
version_added: "2.9"

description:
    - "get VMs in resource pool"

options:
    pool:
        description:
            - Resource pool to get VMs of
        type: str
        required: true

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Configure Resource Pool
  inett.pve.vm_resource_pool:
    pool: "{{ pve_vm_resource_pool }}"
  delegate_to: "{{ pve_target_node }}"

'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
vms:
    description: Stdout of clone Proxmox VE CLI command
    type: list
    returned: always
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        pool=dict(type=str, required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    _rc, _out, _err, obj = mod.query_json(
        'get', "/pools/%s" % (mod.params['pool']),
    )

    vms = []
    for members_el in obj["members"]:
        if "vmid" in members_el:
            vms.append(members_el["vmid"])

    mod.exit_json(changed=False, vms=vms)


def main():
    run_module()


if __name__ == '__main__':
    main()
