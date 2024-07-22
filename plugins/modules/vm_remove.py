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
module: vm_remove
short_description: Remove a VM
version_added: "2.9"

description:
    - "Reboot a VM"
    - "MAY only work after a few retries when HA is configured"

options:
    vmid:
        description:
             - Id of the VM to remove
        type: int
        required: true

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Remove VM
  delegate_to: "{{ pve_target_node }}"
  inett.pve.vm_remove:
    vmid: "{{ pve_vmid }}"
  reties: 3
  delay: 10
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
failed:
    description: Returns true if API calls failed
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
        vmid=dict(type='int', required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=False)

    vmid = None
    if ('vmid' in mod.params) and (mod.params['vmid'] is not None):
        vmid = mod.params['vmid']

    existing, vmid = mod.vmid_magic(vmid)

    if not existing:
        mod.exit_json(changed=False)
        return

    vm_info = mod.vm_info(mod.params.get("vmid"))
    vm_node = mod.vm_locate(mod.params.get("vmid"))

    if vm_info['status'] != 'stopped':
        _rc, _out, _err = mod.query_api(
            'create', "/nodes/%s/qemu/%d/status/stop" % (vm_node, mod.params.get('vmid')),
            fail='failed to stop VM'
        )
    rc, out, err = mod.query_api(
        'delete', "/nodes/%s/qemu/%d" % (vm_node, mod.params.get('vmid')),
        params=dict(purge=True),
    )
    mod.exit_json(
        changed=(rc == 0), failed=(rc != 0), stdout=out, stderr=err
    )


def main():
    run_module()


if __name__ == '__main__':
    main()