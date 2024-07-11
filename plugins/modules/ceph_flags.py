#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: proxmox_ceph_flags
short_description: Sets global ceph flags
version_added: "2.9.9"

description:
    - "Sets global ceph flags"

options:
    proxmox_cluster_ceph_flags:
        description:
            - API node
        required: true
    cluster_auth:
        description:
            - Authentification information for cluster_node
        required: true
    nobackfill:
        required: false
    nodeep-scrub:
        required: false
    nodown:
        required: false
    noout:
        required: false
    norebalance:
        required: false
    norecover:
        required: false
    noscrub:
        required: false
    notieragent:
        required: false
    noup:
        required: false
    pause:
        required: false
    validate_certs:
        description:
            - weather to validate ssl certs or not

author:
    - Maximilian Hill (mhill@inett.de)
'''

EXAMPELS = '''
- name: Set noout flag
  delegate_to: localhost
  throttle: 1
  proxmox_ceph_wait_for_healthy:
    cluster_node: "{{ ansible_host }}"
    cluster_auth: "{{ proxmox_pve_auth }}"
    validate_certs: false
    noout: true
'''


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
