#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r'''

'''

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        # VM identification
        vmid=dict(type='int'),

        tag=dict(type='list', required=False, default=None, elements='string'),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    vm, vm_config = mod.vm_config_get(mod.params['vmid'])

    tag = mod.params.get('tag', None)

    update_params = {
        'tag': tag
    }

    old_message = dict({k: vm_config.get(k, None) for (k, v) in update_params.items()})
    message = old_message.copy()
    message.pop('digest', None)
    message.update(update_params)
    changed = (old_message != message)

    if update_params['tag'] is None:
        update_params.pop('tag')
        update_params['delete'] = ['tag']

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
