#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        vmid=dict(type=int, required=True),
        access=dict(
            choices=['pvesh', 'http'], required=False, default='pvesh'
        ),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    vm_info = mod.vm_info(mod.params["vmid"])
    mod.exit_json(changed=False, node=vm_info["node"])


def main():
    run_module()


if __name__ == '__main__':
    main()
