#!/usr/bin/python

# Copyright: (c) 2021, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import re

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        # VM identification
        vmid=dict(type='int', required=True),
        # node=dict(type='str', required=False),

        # configuration
        update=dict(type='dict', default=dict()),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=False)

    vm, vm_config = mod.vm_config_get(mod.params['vmid'])

    if len(mod.params.get('update', {})) > 0:
        _vm, _vm_config = mod.vm_config_set(
            mod.params['vmid'],
            digest=vm_config.get('digest', None),
            config=mod.params.get('update', {}),
            vm=vm,
        )

    mod.exit_json(
        changed=True,
    )
    return


def main():
    run_module()


if __name__ == '__main__':
    main()
