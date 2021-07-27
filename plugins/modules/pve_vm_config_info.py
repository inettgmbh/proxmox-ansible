#!/usr/bin/python

# Copyright: (c) 2020, inett Gmbh <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        vmid=dict(type=int, required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    node = mod.vm_locate(mod.params['vmid'])

    _rc, out, err, vm_config = mod.query_json('get', "/nodes/%s/qemu/%s/config" % (node, mod.params['vmid']))
    mod.exit_json(changed=False, stdout=out, stderr=err, ansible_facts=dict(pve_vm_config=vm_config))


def main():
    run_module()


if __name__ == '__main__':
    main()
