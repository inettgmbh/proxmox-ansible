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
from urllib.parse import urlencode

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
import ansible.module_utils.six.moves.http_cookies as cookies


def run_module():
    module_args = dict(
        cluster_node=dict(type='str', required=True),
        cluster_name=dict(type='str', required=False, default=""),
        cluster_auth=dict(type='dict', required=True, no_log=True),
        node=dict(type='str', required=True),
        node_auth=dict(type='dict', required=True, no_log=True),
        node_root_password=dict(type='str', required=True, no_log=True),
        validate_certs=dict(type='bool', required=False, default=True)
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    cluster_name = module.params['cluster_name']
    cluster_node = module.params['cluster_node']

    module.params['validate_certs'] = (module.params['validate_certs'] == "True")

    cluster_api_url = "https://"+module.params['cluster_node']+":8006/api2/json"

    node_api_url = "https://"+module.params['node']+":8006/api2/json"

    bc = cookies.BaseCookie()

    t_cc, _t = bc.value_encode(module.params['cluster_auth']['ticket'])
    t_nc, _t = bc.value_encode(module.params['node_auth']['ticket'])

    cluster_headers = {
        'Cookie': 'PVEAuthCookie='+t_cc,
        'CSRFPreventionToken':
            module.params['cluster_auth']['CSRFPreventionToken']
    }

    node_headers = {
        'Cookie': 'PVEAuthCookie='+t_nc,
        'CSRFPreventionToken':
            module.params['node_auth']['CSRFPreventionToken']
    }

    # Get cluster status
    cl_resp, cl_info = fetch_url(module,
        cluster_api_url+"/cluster/status",
        method="GET",
        headers=cluster_headers
    )
    if cl_info["status"] != 200:
        module.fail_json(msg='cannot fetch cluster status')
    cluster_status = json.loads(cl_resp.read().decode('utf8'))

    # Get node cluster status
    ncl_resp, ncl_info = fetch_url(module,
        node_api_url+"/cluster/status",
        method="GET",
        headers=node_headers
    )
    if ncl_info["status"] != 200:
        ncl_resp, ncl_info = fetch_url(module,
            node_api_url+"/cluster/status",
            method="GET",
            headers=cluster_headers
        )
        if ncl_info["status"] == 200:
            result["changed"] = True
        else:
            module.fail_json(msg='cannot fetch node cluster_status')
    node_cluster_status = json.loads(ncl_resp.read().decode('utf8'))

    cluster_exists = False
    for v in cluster_status["data"]:
        if v["type"] == "cluster":
            cluster_exists = True
            cluster_name = v["name"]

    node_in_cluster = False
    for v in node_cluster_status["data"]:
        if v["type"] == "cluster":
            node_in_cluster = True
            result["original_message"] = v["name"]

    if node_in_cluster == True:
        if result["original_message"] == cluster_name:
            result["message"] = cluster_name
            module.exit_json(**result)
        else:
            module.fail_json(msg='Node already in another cluster')

    result["message"] = cluster_name
    result["changed"] = (result["message"] != result["original_message"])
    if module.check_mode:
        module.exit_json(**result)

    if (cluster_exists == False) and (module.params['cluster_node'] == module.params['node']) and (result["changed"] == True):
        cluster_create_data = {
            'clustername': cluster_name,
            'link0': cluster_node
        }
        ccd = urlencode(cluster_create_data)
        clc_resp, clc_info = fetch_url(module,
            cluster_api_url+"/cluster/config?"+ccd, method="POST",
            headers=cluster_headers
        )
        if clc_info["status"] != 200:
            module.fail_json(msg="Unable to create new cluster\n"+module.jsonify(clc_info))
        time.sleep(15)

        module.exit_json(**result)

    # Join `node` into cluster
    if (
                (module.params['cluster_node'] != module.params['node'])
            and (result["changed"] == True)
        ):
        # Get join information from `cluster_node`
        clgjd_resp, clgjd_info = fetch_url(module,
            cluster_api_url+"/cluster/config/join",
            method="GET",
            headers=cluster_headers
        )
        if clgjd_info["status"] != 200:
            module.fail_json(msg="Failed to get cluster join info", kwargs={"exception": clgjd_info})
        join_req = json.loads(clgjd_resp.read().decode('utf8'))
        join_data = {
            'fingerprint': join_req["data"]["nodelist"][0]["pve_fp"],
            'hostname': cluster_node,
            'password': module.params['node_root_password']
        }
        join_data_url=urlencode(join_data)

        # Join cluster
        clj_resp, clj_info = fetch_url(module,
            node_api_url+"/cluster/config/join?"+join_data_url,
            method="POST",
            headers=node_headers
        )
        if clj_info["status"] != 200:
            clj_kwargs = {
                "exception": clj_resp.read().decode('utf8')
            }
            module.fail_json(msg='Error joining cluster', kwargs=clj_kwargs)
        time.sleep(15)

        # Get node cluster status
        ncl_resp, ncl_info = fetch_url(module,
            node_api_url+"/cluster/status",
            method="GET",
            headers=cluster_headers
        )
        if ncl_info["status"] != 200:
            module.fail_json(msg='cannot fetch node cluster_status')
        node_cluster_status = json.loads(ncl_resp.read().decode('utf8'))

        # Check if `node` joined the cluster
        node_in_cluster = False
        n_cluster_name = ""
        for v in node_cluster_status["data"]:
            if v["type"] == "cluster":
                node_in_cluster = True
                n_cluster_name = v["name"]

        # If `node` is in an cluster, check, if it's the one it's supposed to be in
        if node_in_cluster == True and n_cluster_name == cluster_name:
            module.exit_json(**result, ansible_facts={
                'proxmox_pve_auth': module.params['cluster_auth']
            })
        else:
            module.fail_json(msg='Node did not join cluster')


def main():
    run_module()


if __name__ == '__main__':
    main()
