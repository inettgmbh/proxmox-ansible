#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: ceph_flags
short_description: Sets global ceph flags
version_added: "2.9"

description:
    - "Sets global ceph flags"

options:
    nobackfill:
        required: false
        type: bool
        default: false
    nodeep-scrub:
        required: false
        type: bool
        default: false
    nodown:
        required: false
        type: bool
        default: false
    noout:
        required: false
        type: bool
        default: false
    norebalance:
        required: false
        type: bool
        default: false
    norecover:
        required: false
        type: bool
        default: false
    noscrub:
        required: false
        type: bool
        default: false
    notieragent:
        required: false
        type: bool
        default: false
    noup:
        required: false
        type: bool
        default: false
    pause:
        required: false
        type: bool
        default: false

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Set flags for Ceph maintenance
  inett.pve.ceph_flags:
    noout: true
    noin: true
    nodown: true
    noup: true
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def _filter_params(module, data, param_list):
    for k in param_list:
        if module.params[k] is not None:
         data[k] = bool(int(module.params[k]))


def run_module():
    module_args = dict(
        # Ceph Flags
        nobackfill=dict(type='bool', required=False, default=False),
        nodeep_scrub=dict(type='bool', required=False, default=False),
        nodown=dict(type='bool', required=False, default=False),
        noin=dict(type='bool', required=False, default=False),
        noout=dict(type='bool', required=False, default=False),
        norebalance=dict(type='bool', required=False, default=False),
        norecover=dict(type='bool', required=False, default=False),
        noscrub=dict(type='bool', required=False, default=False),
        notieragent=dict(type='bool', required=False, default=False),
        noup=dict(type='bool', required=False, default=False),
        pause=dict(type='bool', required=False, default=False)
    )

    result = dict(
        changed=True,
    )

    mod = PveApiModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    mod.params['nodeep-scrub'] = mod.params['nodeep_scrub']

    data = {}
    _filter_params(mod, data, [
        'nobackfill', 'nodeep-scrub', 'nodown', 'noin', 'noout', 'norebalance', 'norecover',
        'noscrub', 'notieragent', 'noup', 'pause'
    ])

    rc, _out, _err = mod.query_api("set", "/cluster/ceph/flags", params=data)

    if rc == 0:
        mod.exit_json(**result)
        return

    mod.fail_json(msg="Failed to query API")


def main():
    run_module()


if __name__ == '__main__':
    main()
