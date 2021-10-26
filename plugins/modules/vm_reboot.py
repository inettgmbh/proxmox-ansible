#!/usr/bin/python

# Copyright: (c) 2021, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


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

