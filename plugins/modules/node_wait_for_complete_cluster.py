#!/usr/bin/python

import time

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: proxmox_cluster_wait_for_nodes
short_description: Waits for proxmox nodes to be online
version_added: "2.9.9"

description:
    - "Let a node join a proxmox cluster"

options:
    proxmox_cluster_wait_for_nodes:
        description:
            - API node
        required: true
    nodes:
        description:
             - nodes to wait for online state
             - Array of node names
             - If value isn't passed, module will wait for all nodes to be online

author:
    - Maximilian Hill (mhill@inett.de)
'''

EXAMPELS = '''
- name: Wait for proxmox nodes
  delegate_to: localhost
  throttle: 1
  proxmox_cluster_wait_for_nodes:
    nodes: ['node0', 'node1']
'''


def wait_for_nodes(module, nodes=None):
    if nodes is None:
        nodes = ['_all']

    while True:
        time.sleep(1)

        # Get cluster status

        rc, _out, _err, obj = module.query_json("get", "/cluster/status")

        if rc != 0:
            continue
        try:
            online_nodes = 0
            in_cluster = False
            n_nodes = 100
            if '_all' in nodes:
                for e in obj:
                    if e["type"] == "cluster":
                        n_nodes = int(e["nodes"])
                        in_cluster = True
                    if e["type"] == "node" and int(e["online"]) == 1:
                        online_nodes += 1
            else:
                for e in obj:
                    if e["type"] == "node" and e["name"] in nodes:
                        n_nodes += 1
                        if int(e["online"]) == 1:
                            online_nodes += 1

            if (online_nodes == n_nodes) or not in_cluster:
                return
        except:
            continue


def run_module():
    module_args = dict(
        nodes=dict(type='list', required=False, default=['_all']),
        validate_certs=dict(type='bool', required=False, default=True)
    )

    result = dict(
        changed=False,
    )

    module = PveApiModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    nodes = module.params["nodes"]

    wait_for_nodes(module, nodes)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
