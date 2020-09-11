#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: proxmox_cluster_membership
short_description: Manages the membership of a proxmox node
version_added: "2.9.9"

description:
    - "Let a node join a proxmox cluster"

options:
    cluster_node:
        description:
            - A node of the cluster to join
            - Cluster will be created if it doesn't exist
        required: true
    cluster_name:
        description:
            - The name of the cluster, in case it have to be created
            - Only required, if the cluster doesn't already exist
        required: false
    node:
        description:
            - Node to join the cluster
        required: true
    cluster_ticket:
        description:
            - A valid ticket for the api of cluster_node
        required: true
    node_ticket:
        description:
            - A valid ticket for the api of node
        required: true
    node_root_password:
        description:
            - Password for root@pam
        required: true
    validate_certs:
        description:
            - weather to validate ssl certs or not

author:
    - Maximilian Hill (mhill@inett.de)
'''

EXAMPELS = '''
- name: join a existing cluster
  proxmox_cluster_membership:
    cluster_node: resolvable_hostname / ip_address
    node: resolvable_hostname / ip_address
    cluster_ticket: TICKET
    node_ticket: TICKET
    node_root_password: PASSWORD

- name: create a new cluster if necessary and join
  proxmox_cluster_membership:
    cluster_node: IP_ADDRESS
    cluster_name: CLUSTER_NAME
    node: IP_ADDRESS
    cluster_ticket: TICKET
    node_ticket: TICKET
    node_root_password: PASSWORD
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

    (auth_resp, auth_info) = fetch_url(module, node_api_url+"/access/ticket", method="POST", data=urlencode([
        ('username', module.params["node_user"]),
        ('password', module.params["node_pass"])
    ]))
    if auth_info["status"] != 200:
        module.fail_json(msg="unable to authenticate")

    authinfo = json.loads(auth_resp.read())["data"]
    (ai_ticket_c, _t) = bc.value_encode(authinfo["ticket"])
    (val_resp, val_info) = fetch_url(module, node_api_url+"/version", headers={
        'Cookie': 'PVEAuthCookie='+ai_ticket_c
    })
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
