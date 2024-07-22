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
module: vm_cdrom
short_description: Configure cdrom (ide2) of a VM
version_added: "2.9"

description:
    - "Configure cdrom (ide2) of a VM"

options:
    vmid:
        description:
             - Id of the VM to configure
        type: int
        required: true
    device:
        description:
            - Storage device to configure
        type: str
        required: false
        default: ide2
    file:
        description:
            - Path to image in configured storage 
        type: str
        required: true
    storage:
        description:
            - Name of storage containing the CD image
        type: str
        default: None
    media:
        description:
            - media type
        type: str
        default: cdrom

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Remove CD image from Proxmox VE guest
  inett.pve.vm_cdrom:
    vmid: "{{ pve_vmid }}"
    file: none
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
message:
    description: State of subscription after module execution
    type: dict
    contains:
        file:
            type: str
            returned: always
        media:
            type: str
            returned: always
    returned: always
original_message:
    description: State of subscription after module execution
    type: dict
    contains:
        file:
            type: str
            returned: always
        media:
            type: str
            returned: always
'''


import re

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        # VM identification
        vmid=dict(type='int', required=False, default=None),

        # device
        device=dict(type='str', default='ide2'),
        # Media
        file=dict(type='str'),
        storage=dict(type='str', default=None),
        media=dict(type='str', default='cdrom'),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    vm, vm_config = mod.vm_config_get(mod.params['vmid'])

    if mod.params['device'] not in vm_config:
        mod.exit_json( changed=False )
    if mod.params['device'] in PveApiModule.valid_storages():
        update_params = dict()
        file = None
        if mod.params['file'] == 'none':
            file = 'none'
        elif mod.params.get('storage', None) is not None:
            file = "%s:iso/%s" % (mod.params['storage'], mod.params['file'])

        if file is None:
            mod.fail_json(msg="cannot determine file name")

        update_params[mod.params['device']] = dict(
            file=file, media=mod.params.get('media', 'cdrom')
        )
        message = dict({
            k: re.sub(r"^file=", "", PveApiModule.params_dict_to_string(v))
            for (k, v) in update_params.items()
        })

        old_message = dict({k: vm_config[k] for (k, v) in update_params.items()})
        changed = (old_message != message)

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

    mod.fail_json(msg="some unhandled malfunction")


def main():
    run_module()


if __name__ == '__main__':
    main()
