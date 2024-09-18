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
short_description: Returns the health of Ceph
version_added: "2.9"

description:
    - "Returns the health of Ceph"

options:

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPELS = '''
- name: Get the health of Ceph
  inett.pve.ceph_health_info:
  register: ceph_health
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
health:
    description: Ceph health
    type: str
'''


def _ceph_health_from_status(obj):
    if ("health" in obj) and ("status" in obj["health"]):
        return obj["health"]["status"]


def run_module():
    result = dict(
        changed=False,
    )

    mod = PveApiModule(
        supports_check_mode=True
    )

    rc, _out, _err, obj = mod.query_json("get", "/cluster/ceph/status")
    if rc == 0:
        result["health"] = _ceph_health_from_status(obj)
        mod.exit_json(**result)
    else:
        mod.fail_json("Unable to get Ceph status")



def main():
    run_module()


if __name__ == '__main__':
    main()
