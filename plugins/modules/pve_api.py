#!/usr/bin/python

# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

DOCUMENTATION = r'''
---
module: pve_api

short_description: Access to the pve API

version_added: "0.1.0"

options:
    access:
        description: |
            Type of access.
            options: pvesh | http
            default: "pvesh"
        required: False 
    method:
        description: |
            Method of the API call.
            only method "get" is executed, if check_mode is set
            default: "get"
        type: str 
        required: False
    url:
        type: str
        required: True

author:
    - Maximilian Hill <mhill@inett.de>
'''


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
        mod.fail_json("API query failed",
            changed=(mod.params['method'].lower() != "get"),
            rc=rc, stdout=out, stderr=err, json=obj
        )


def main():
    run_module()


if __name__ == '__main__':
    main()
