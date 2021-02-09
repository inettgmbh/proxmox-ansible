#!/usr/bin/python

# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

from ansible.module_utils.basic import AnsibleModule

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


class PveApiModule(AnsibleModule):
    def __init__(self,
                 url, argument_spec=dict(), supported_methods=list(),
                 **kwargs
                 ):
        self.url = url
        argument_spec.update(dict(
            url=dict(type='str', required=True),
            access=dict(
                choices=['pvesh', 'http'],
                required=False,
                default='pvesh'),
            method=dict(
                type='str',
                required=False,
                default='get'
            ),
        ))
        kwargs['supports_check_mode'] = True
        super(PveApiModule, self).__init__(
            argument_spec=argument_spec, **kwargs
        )
        if self.params['method'].lower() not in supported_methods:
            self.fail_json("Unsupported access mode")

    def get_cmd(self):
        return [
            "pvesh",
            self.params['method'], self.url,
            "--output-format", "json"
        ]

    def query_api(self):
        if self.params['access'] == "pvesh":
            return self.run_command(self.get_cmd())
        else:
            return 1, "", "Access method not supported yet"

    def query_json(self):
        rc, out, err = self.query_api()
        try:
            obj = json.loads(out)
        except:
            obj = None
        return rc, out, err, obj


def run_module():
    mod = PveApiModule("/version", supported_methods=['get'])

    if mod.check_mode and mod.params['method'].lower() != "get":
        mod.exit_json(skipped=True)

    rc, out, err, obj = mod.query_json()

    if rc == 0:
        mod.exit_json(
            changed=(mod.params['method'].lower() != "get"),
            rc=0, stdout=out, stderr=err, json=obj)
    else:
        mod.fail_json(
            changed=(mod.params['method'].lower() != "get"),
            rc=rc, stdout=out, stderr=err, json=obj
        )


def main():
    run_module()


if __name__ == '__main__':
    main()
