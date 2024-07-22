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
'''

RETURN = r'''

'''


import json
import yaml

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


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
    old_config.pop('digest', None)

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

    update_params = mod.params.get('update', {})

    for k, n in update_params.pop('net', {}).items():
        update_params["net%s" % k] = n
        if n.get('model', None) is None:
            update_params["net%s" % k]['model'] = 'virtio'
        if n.get('tag', None) is not None:
            update_params["net%s" % k]['tag'] = int(n.get('tag'))
        if len(n.get('trunks', [])) > 0:
            update_params["net%s" % k]['trunks'] = n.get('trunks')

        update_params["ipconfig%s" % k] = dict()

        ip4 = n.get('ip', None)
        net4 = n.get('s_net', None)
        ip4 = ip4 if net4 is None else "%s/%s" % (ip4, net4)
        if net4 is not None:
            update_params["net%s" % k].pop('s_net', None)
        if ip4 is not None:
            update_params["net%s" % k].pop('ip', None)
            update_params["ipconfig%s" % k].update(dict(ip=ip4))
        gw4 = n.get('gw', None)
        if gw4 is not None:
            update_params["net%s" % k].pop('gw', None)
            update_params["ipconfig%s" % k].update(dict(gw=gw4))
        ip6 = n.get('ip6', None)
        net6 = n.get('s_net6', None)
        ip6 = ip6 if net6 is None else "%s/%s" % (ip6, net6)
        if net6 is not None:
            update_params["net%s" % k].pop('s_net6', None)
        if ip6 is not None:
            update_params["net%s" % k].pop('ip6', None)
            update_params["ipconfig%s" % k].update(dict(ip6=ip6))
        gw6 = n.get('gw6', None)
        if gw6 is not None:
            update_params["net%s" % k].pop('gw6', None)
            update_params["ipconfig%s" % k].update(dict(gw6=gw6))

        if len(update_params["ipconfig%s" % k]) == 0:
            update_params.pop("ipconfig%s" % k, None)

    description = update_params.pop('description', None)

    if isinstance(description, dict) and description is not None:
        for k, v in description.items():
            if isinstance(v, str):
                description[k] = v.strip()
        description = yaml.dump(
            description,
            default_flow_style=False,
        )

    if description is not None:
        description = "\n\n".join(description.split("\n"))
        update_params['description'] = description

    if (len(update_params) > 0) and change:
        _vm, new_config = mod.vm_config_set(
            mod.params['vmid'],
            digest=vm_config.get('digest', None),
            config=update_params,
            vm=vm,
        )
        new_config.pop('digest', None)
        mod.exit_json( changed = (old_config != new_config) )

    mod.exit_json(
        changed=False,
    )
    return


def main():
    run_module()


if __name__ == '__main__':
    main()

