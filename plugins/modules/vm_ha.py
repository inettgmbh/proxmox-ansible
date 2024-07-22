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
module: vm_ha
short_description: Configure HA a VM
version_added: "2.9"

description:
    - "Configure HA a VM"
    - "At the moment a HA group MUST be configured"

options:
    vmid:
        description:
             - Id of the VM to configure
        type: int
        required: true
    state:
        description:
            - Target state in HA config (running, stopped, ignored, disabled)
        type: str
        required: true
    group:
        description:
            - Name of the HA group the VM should be in
        type: int
        required: true

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Add guest to resource pool pool
  delegate_to: "{{ pve_target_node }}"
  inett.pve.vm_resource_pool:
    vmid: "{{ pve_vmid }}"
    pool: "{{ pve_vm_resource_pool }}"
  when: pve_vm_resource_pool is defined
'''

RETURN = r'''

'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        vmid=dict(type=int, required=True),
        state=dict(type=str, required=True),
        group=dict(type=str, required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=False)

    node = mod.vm_locate(mod.params['vmid'])

    _rc, out, err, vm_config = mod.query_json(
        'create', "/cluster/ha/resources",
        params=dict(
            sid=mod.params['vmid'],
            state=mod.params['state'],
            group=mod.params['group'],
        ),
    )
    mod.exit_json(changed=False, stdout=out, stderr=err)


def main():
    run_module()


if __name__ == '__main__':
    main()
