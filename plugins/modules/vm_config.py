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
        # node=dict(type='str', required=False),

        # configuration
        update=dict(type='dict', default=dict()),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=False)

    change = False

    vm, vm_config = mod.vm_config_get(mod.params['vmid'])

    old_config = vm_config.copy()
    old_config.pop('digest')

    delete = mod.params.get('update', {}).get('delete', [])
    for d in delete:
        if d in old_config:
            change = True
            break

    if not change:
        for d in mod.params.get('update', {}).keys():
            if mod.params['update'][d] != old_config.get(d, ""):
                change = True
                break

    if (len(mod.params.get('update', {})) > 0) and change:
        _vm, new_config = mod.vm_config_set(
            mod.params['vmid'],
            digest=vm_config.get('digest', None),
            config=mod.params.get('update', {}),
            vm=vm,
        )
        new_config.pop('digest')
        mod.exit_json( changed = (old_config != new_config) )

    mod.exit_json(
        changed=False,
    )
    return


def main():
    run_module()


if __name__ == '__main__':
    main()

