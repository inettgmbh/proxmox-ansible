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
---
module: vm_network
short_description: Configure VM network
version_added: "2.9"

description:
    - "Configure VM network"
    - "At the moment only adding/changing is possible"

options:
    vmid:
        description:
             - Id of the VM to configure
        type: int
        required: true
    net:
        description:
            - Network configuration
            - Key of dict is the number of the virual NIC
            - Value is a dict
        type: dict
        required: false
        default: {}

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Network
  delegate_to: "{{ pve_target_node }}"
  inett.pve.vm_network:
    vmid: 100
    net:
      0: {"bridge": "vmbr1", "firewall": true, "tag": 10, "gw": "172.23.65.254", "s_net": 24, "ip": "172.23.65.163" }
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
message:
    description: Changed network config
    type: dict
    returned: always
original_message:
    description: Original network config to be changed
    type: dict
    returned: always
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

import copy
import sys




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
        if len(n.get('trunks', [])) > 0:
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

        if len(update_params["ipconfig%s" % k]) == 0:
            update_params.pop("ipconfig%s" % k, None)

    # message = dict({
    #     k: re.sub(r"^file=", "", PveApiModule.params_dict_to_string(v))
    #     for (k, v) in update_params.items()
    # })
    message = update_params;

    old_message = dict({k: vm_config.get(k, None) for (k, v) in update_params.items()})

    try:
        msg_cmp_a = copy.deepcopy(old_message)
        msg_cmp_b = copy.deepcopy(message)
        for k, v in msg_cmp_a.items():
            if k.startswith("net") and v is not None:
                if "macaddr" in v.keys():
                    v.pop("macaddr")
                if "virtio" in v.keys():
                    v.update({"model": "virtio"})
                    v.pop("virtio")
                if "firewall" in v.keys():
                    v.update({"firewall": bool(int(v.get("firewall")))})
                if "tag" in v.keys():
                    v.update({"tag": int(v.get("tag"))})
        for k, v in msg_cmp_b.items():
            if k.startswith("net") and v is not None:
                if "virtio" in v.keys():
                    v.update({"model": "virtio"})
                    v.pop("virtio")
                if "macaddr" in v.keys():
                    v.pop("macaddr")
    except:
        mod.fail_json(msg="preparation for comparison failed", error=sys.exec_info()[0],
                key=k, value=v, msg_cmp_a=msg_cmp_a, msg_cmp_b=msg_cmp_b
        )

    # remove elements, that didn't change
    for k, v in msg_cmp_b.items():
        if v == msg_cmp_a.get(k, None):
            update_params.pop(k, None)

    changed = (msg_cmp_a != msg_cmp_b)

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
        original_message=old_message,
        msg_cmp_a=msg_cmp_a,
        msg_cmp_b=msg_cmp_b,
    )
    return

    mod.fail_json(msg="some unhandled malfunction")


def main():
    run_module()


if __name__ == '__main__':
    main()

