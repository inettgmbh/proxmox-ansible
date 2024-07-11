#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import yaml

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


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
