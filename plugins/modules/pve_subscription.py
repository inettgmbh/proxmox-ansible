#!/usr/bin/python

# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from datetime import datetime

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


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
