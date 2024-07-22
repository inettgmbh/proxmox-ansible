#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: vm_description
short_description: Change Description of a VM or Template
version_added: "2.9"

description:
    - "Change Description of a VM or Template"
    - |
        If description is a dictionary or list, it will be converted to yaml.
        If a value of the dict or an element of the list is not a string, said
        value will be converted to json.

options:
    vmid:
        description:
             - Id of the VM to configure
        type: int
        required: true
    description:
        description:
            - Description of VM
            - May be an string, dictionary or list
        type: raw
        required: false

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Set VM description
  delegate_to: "{{ pve_target_node }}"
  inett.pve.vm_description:
    vmid: "{{ pve_vmid }}"
    description: "{{ pve_vm_notes }}"
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
message:
    description: State of subscription after module execution
    type: dict
    returned: always
original_message:
    description: State of subscription after module execution
    type: dict
    returned: always
'''


import yaml

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        # VM identification
        vmid=dict(type='int'),

        description=dict(type='raw', required=False, default=None),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    vm, vm_config = mod.vm_config_get(mod.params['vmid'])

    description = mod.params.get('description', None)

    if isinstance(description, dict) and description is not None:
        for k, v in description.items():
            if isinstance(v, str):
                description[k] = v.strip()
        description = yaml.dump(description,
                default_flow_style=False,
        )
        description = "\n\n".join(description.split("\n"))

    update_params = {
        'description': description
    }

    old_message = dict({k: vm_config.get(k, None) for (k, v) in update_params.items()})
    message = old_message.copy()
    message.pop('digest', None)
    message.update(update_params)
    changed = (old_message != message)

    if update_params['description'] is None:
        update_params.pop('description')
        update_params['delete'] = ['description']

    if changed:
        mod.vm_config_set(
            mod.params['vmid'],
            node=vm['node'],
            digest=vm_config.get('digest', None),
            config=update_params,
            vm=vm
        )

    mod.exit_json(
        changed=changed,
        message=message,
        original_message=old_message
    )
    return


def main():
    run_module()


if __name__ == '__main__':
    main()
