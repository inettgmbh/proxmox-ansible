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
module: proxmox_auth
short_description: Pulls a ticket and saves auth info in to `proxmox_pve_auth`
version_added: "2.9.9"

description:
    - "Authenticates against a proxmox node"
    - "Caches authentification info"

options:
    node_name:
        descirption:
            - name of the node to authenticate agains
        required: true
    node_addr:
        description:
            - IP address of the node to authenticate against
        required: true
    node_user:
        description:
            - Username to use
        required: true
    node_pass:
        description:
            - Password to use
        required: false
    validate_certs:
        description:
            - weather to validate ssl certs or not

author:
    - Maximilian Hill (mhill@inett.de)
'''

EXAMPELS = '''
- delegate_to: localhost
  proxmox_auth:
    node_name: "{{ inventory_hostname }}"
    node_addr: "{{ ansible_host }}"
    node_user: "{{ ansible_user }}@pam"
    node_pass: "{{ ansible_password }}"
    validate_certs: false
'''

import json
import time
import subprocess
import platform

from json.decoder import JSONDecodeError
from urllib.parse import urlencode

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
import ansible.module_utils.six.moves.http_cookies as cookies


def host_reachable(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0


def run_module():
    module_args = dict(
        node_addr=dict(type='str', required=True),
        node_name=dict(type='str', required=True),
        node_user=dict(type='str', required=True),
        node_pass=dict(type='str', required=True, no_log=True),
        validate_certs=dict(type='bool', required=False, default=True)
    )

    result = dict(
        changed=False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    node_api_url = "https://"+module.params['node_addr']+":8006/api2/json"
    bc = cookies.BaseCookie()

    try:
        o_info_f = open("/tmp/"+module.params["node_name"]+".ticket", "r")
        authinfo = json.loads(o_info_f.read())
        facts = {
            'proxmox_pve_auth': authinfo
        }
        if not host_reachable(module.params['node_addr']):
            module.exit_json(**result, ansible_facts=facts)
        (ai_ticket_c, _t) = bc.value_encode(authinfo["ticket"])
        (val_resp, val_info) = fetch_url(module,
            node_api_url+"/version", timeout=5,
            headers={
                'Cookie': 'PVEAuthCookie='+ai_ticket_c
            }
        )
        if val_info["status"] == 200:
            version_info = json.loads(val_resp.read().decode('utf8'))
            facts['proxmox_pve_version'] = version_info["data"]["version"]
            module.exit_json(**result, ansible_facts=facts)
    except FileNotFoundError:
        pass

    (auth_resp, auth_info) = fetch_url(module,
        node_api_url+"/access/ticket",
        method="POST",
        data=urlencode([
            ('username', module.params["node_user"]),
            ('password', module.params["node_pass"])
        ])
    )
    if auth_info["status"] != 200:
        module.fail_json(msg="unable to authenticate")

    authinfo = json.loads(auth_resp.read())["data"]
    (ai_ticket_c, _t) = bc.value_encode(authinfo["ticket"])
    (val_resp, val_info) = fetch_url(module,
        node_api_url+"/version",
        headers={
            'Cookie': 'PVEAuthCookie='+ai_ticket_c
        }
    )
    if val_info["status"] == 200:
        result["changed"] = True
        f = open("/tmp/"+module.params["node_name"]+".ticket", "w")
        f.write(json.dumps(authinfo))
        f.close()
        facts = {
            'proxmox_pve_auth': authinfo,
            'proxmox_pve_version': json.loads(val_resp.read())["data"]["version"]
        }
        module.exit_json(**result, ansible_facts=facts)


def main():
    run_module()


if __name__ == '__main__':
    main()
