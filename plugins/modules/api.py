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

DOCUMENTATION = r'''
---
module: api
short_description: Access to the pve API
version_added: "2.9"

options:
    method:
        description: |
            Method of the API call.
            only method "get" is executed, if check_mode is set
            default: "get"
        type: str 
        required: false
    url:
        type: str
        required: True

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: Query API
  inett.pve.api:
    url: /cluster/resources
    mathod: get
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
rc:
    description: Return code of API command execution
    type: int
stdout:
    description: Stdout of API command execution
    type: str
stderr:
    description: Stderr of API command execution
    type: str
parsed_stdout:
    description: Stderr parsed as JSON
    type: any
'''

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    mod = PveApiModule(argument_spec=dict(
        url=dict(type='str', required=True),
        method=dict(
            type='str',
            required=False,
            default='get',
        ),
    ))

    if mod.check_mode and mod.params['method'].lower() != "get":
        mod.exit_json(skipped=True)

    rc, out, err, obj = mod.query_json(
        mod.params['method'].lower(),
        mod.params['url'].lower(),
        access=mod.params['access'].lower(),
    )

    if rc == 0:
        mod.exit_json(
            changed=(mod.params['method'].lower() != "get"),
            rc=0, stdout=out, stderr=err, json=obj)
    else:
        mod.fail_json(msg="API query failed",
            changed=(mod.params['method'].lower() != "get"),
            rc=rc, stdout=out, stderr=err, json=obj
        )


def main():
    run_module()


if __name__ == '__main__':
    main()
