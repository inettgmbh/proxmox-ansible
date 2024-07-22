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

import time

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

DOCUMENTATION = '''
---
module: ceph_wait_for_healthy
short_description: Waits until ceph health is HEALTH_OK
version_added: "2.9"

description:
    - "Waits until ceph health is HEALTH_OK or no ceph is configured"
    - "Sets fact has_ceph (bool) according to the presence of ceph on the node"

options:

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPELS = '''
- name: Wait for healthy ceph
  delegate_to: localhost
  throttle: 1
  proxmox_ceph_wait_for_healthy:
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
'''


def _ceph_health_from_status(obj):
    for e in obj:
        if e == "health":
            return obj[e]["status"]


def run_module():
    result = dict(
        changed=False,
    )

    mod = PveApiModule(
        supports_check_mode=True
    )

    while True:
        time.sleep(1)

        # Get cluster status
        rc, _out, _err, obj = mod.query_json("get", "/cluster/ceph/status")
        if rc == 0:
            if _ceph_health_from_status(obj) == "HEALTH_OK":
                break
        else:
            mod.fail_json("Unable to get Ceph status")
            break

    mod.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
