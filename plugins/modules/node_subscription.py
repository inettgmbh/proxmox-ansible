#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: node_subscription
short_description: Checks subscription of a node
version_added: "2.9"

description:
    - "Checks the subscription key of a Proxmox VE node"

options:
    state:
        description:
            - 'present' if license not be set or removed
            - 'absent' if license should be set
        choices: ['absent', 'present']
        default: 'present'
        required: false
    node:
        description:
            - Proxmox VE Node maintenance state should be set
        type: str
        required: false
        default: Node the module is run on
    key:
        description:
            - Weather maintenance mode should be enabled 
        type: str
        required: false
        default: false
    https_proxy:
        description:
            - HTTP(S) Proxy to use for license check
        type: str
        required: false
        default: None

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES= r'''
- name: Remove key from Proxmox VE node
  inett.pve.node_subscription:
    state: absent
- name: Set key on Proxmox VE node
  inett.pve.node_subscription:
    state: present
    key: pve1b-********
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
message:
    description: State of subscription after module execution
    type: dict
    contains:
        subscription_present:
            type: bool
            returned: always
        subscription_active:
            type: bool
            returned: always
        valid:
            type: bool
            returned: always
    returned: always
original_message:
    description: State of subscription after module execution
    type: dict
    contains:
        subscription_present:
            type: bool
            returned: always
        subscription_active:
            type: bool
            returned: always
        valid:
            type: bool
            returned: always
original_message:
    description: State of subscription after module execution
    type: dict
'''


from datetime import datetime

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def __clean_state(in_state=dict()):
    if ('key' in in_state) and (in_state['key'] is not None):
        in_state['key'] = '******'
    return in_state


def run_module():
    arg_spec = dict(
        state=dict(
            choices=['absent', 'present'],
            required=False, default='present'
        ),
        node=dict(type='str', required=False, default=None),
        key=dict(type='str', no_log=True, required=False, default=None),
        update=dict(type='bool', required=False, default=False),
        https_proxy=dict(type='str', required=False, default=None),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    ansible_facts = dict()
    cluster = dict()
    nodes = dict()

    if mod.params['node'] is None:
        node = mod.get_local_node()
    else:
        node = mod.params['node']

    if mod.params['update']:
        _rc, _out, _err, = mod.query_api(
            'create', '/nodes/'+node+'/subscription',
            https_proxy=mod.params['https_proxy'],
            fail="Updating subscription info failed",
        )

    _rc, out, err, obj = mod.query_json(
        'get', '/nodes/'+node+'/subscription',
        fail="Getting subscription status failed",
    )
    old_state = dict(
        subscription_present=(obj['status'].lower() != "notfound"),
        subscription_active=(obj['status'].lower() == "active"),
        valid=(
            (obj['status'].lower() != "notfound")
            and (
                datetime.strptime(obj['nextduedate'], '%Y-%m-%d') >= datetime.now()
            )
        ),
        key=obj.get('key', None),
    )
    target = dict(
        subscription_present=(mod.params['state'] == 'present'),
        subscription_active=(mod.params['state'] == 'present'),
        valid=(mod.params['state'] == 'present'),
        key=mod.params['key'],
    )
    changed = False
    for k in target:
        changed |= (old_state.get(k, None) != target[k])

    # early exit in check_mode
    if mod.check_mode or (not changed):
        mod.exit_json(
            changed=changed,
            original_message=__clean_state(old_state),
            message=__clean_state(target)
        )

    # check mode only for now
    mod.fail_json(msg="This module cannot change anything yet")


def main():
    run_module()


if __name__ == '__main__':
    main()
