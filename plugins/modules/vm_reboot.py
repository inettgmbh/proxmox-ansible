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
module: vm_reboot
short_description: Reboot a VM
version_added: "2.9"

description:
    - "Reboot a VM"

options:
    vmid:
        description:
             - Id of the VM to reboot
        type: int
        required: true

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Reboot VM
  delegate_to: pve01
  inett.pve.vm_reboot:
    vmid: 100
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        # VM identification
        vmid=dict(type='int', required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=False)
    node = mod.vm_locate(mod.params['vmid'])

    mod.query_api(
        'create', "/nodes/%s/qemu/%d/status/reboot" % (node, mod.params['vmid']),
    )

    mod.exit_json(
        changed=True,
    )
    return


def main():
    run_module()


if __name__ == '__main__':
    main()

