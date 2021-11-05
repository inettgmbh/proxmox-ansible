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
        state=dict(type=str, required=True),
        group=dict(type=str, required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    ha_params = dict(
        sid=mod.params['vmid'],
        state=mod.params['state'],
    )
    if mod.params.get('group', None) is not None:
        ha_params['group'] = mod.params['group']

    _rc, out, err, vm_config = mod.query_json(
        'create', "/cluster/ha/resources",
        params=ha_params,
    )
    mod.exit_json(changed=False, stdout=out, stderr=err)


def main():
    run_module()


if __name__ == '__main__':
    main()
