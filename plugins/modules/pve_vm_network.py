#!/usr/bin/python

# Copyright: (c) 2021, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        state=dict(
            choices=['absent', 'running', 'stopped'],
            required=False, default='stopped'
        ),

        # VM identification
        vmid=dict(type='int', required=False, default=None),

        # Network configuration
        net=dict(
            type='dict', required=False, default={},  # elements='dict'
        ),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)
    vm, vm_config = mod.vm_config_get(mod.params['vmid'])
    update_params = dict()

    for k, n in mod.params.get('net', dict()).items():
        update_params["net%s" % k] = n
        if n.get('model', None) is None:
            update_params["net%s" % k]['model'] = 'virtio'
        if n.get('tag', None) is not None:
            update_params["net%s" % k]['tag'] = int(n.get('tag'))
        if len(n.get('trunks', [])) is not 0:
            update_params["net%s" % k]['trunks'] = n.get('trunks')

        update_params["ipconfig%s" % k] = dict()

        ip4 = n.get('ip', None)
        net4 = n.get('s_net', None)
        ip4 = ip4 if net4 is None else "%s/%s" % ( ip4, net4 )
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
        ip6 = ip6 if net6 is None else "%s/%s" % ( ip6, net6 )
        if net6 is not None:
            update_params["net%s" % k].pop('s_net6', None)
        if ip6 is not None:
            update_params["net%s" % k].pop('ip6', None)
            update_params["ipconfig%s" % k].update(dict(ip6=ip6))
        gw6 = n.get('gw6', None)
        if gw6 is not None:
            update_params["net%s" % k].pop('gw6', None)
            update_params["ipconfig%s" % k].update(dict(gw6=gw6))

        if len(update_params["ipconfig%s" % k]) is 0:
            update_params.pop("ipconfig%s" % k, None)

    # message = dict({
    #     k: re.sub(r"^file=", "", PveApiModule.params_dict_to_string(v))
    #     for (k, v) in update_params.items()
    # })
    message = update_params;

    old_message = dict({k: vm_config.get(k, None) for (k, v) in update_params.items()})
    changed = (old_message != message)

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

    mod.fail_json(msg="some unhandled malfunction")


def main():
    run_module()


if __name__ == '__main__':
    main()

