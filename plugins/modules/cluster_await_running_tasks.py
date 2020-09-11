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
module: proxmox_cluster_wait_for_running_tasks
short_description: Waits until there is no running task in the cluster
version_added: "2.9.9"

description:
    - "Waits until there is no running task in the cluster"

options:

author:
    - Maximilian Hill (mhill@inett.de)
'''

EXAMPELS = '''
- name: Wait until there is no running task in the cluster
  delegate_to: localhost
  throttle: 1
  proxmox_cluster_wait_for_running_tasks:
    cluster_node: "10.1.99.21"
    cluster_auth: "{{ hostvars['pve-b-1']['proxmox_pve_auth'] }}"
    validate_certs: false
'''


def wait_for_no_running_tasks(module):
    exclude_types = [
        'vncshell', 'vncproxy'
    ]

    while True:
        time.sleep(5)

        # Get cluster status
        rc, _out, _err, cluster_tasks = module.query_json("get", "/cluster/tasks")
        if rc != 0:
            continue
        try:
            running = 0
            for v in cluster_tasks:
                if ('status' not in v) and (v['type'] not in exclude_types):
                    running += 1
            if running == 0:
                break
        except:
            continue


def run_module():
    module_args = dict(
    )

    result = dict(
        changed=False,
    )

    module = PveApiModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    wait_for_no_running_tasks(module)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
