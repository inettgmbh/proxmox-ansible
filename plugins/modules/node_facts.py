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

DOCUMENTATION = '''
---
module: node_facts
short_description: Retrieves and sets facts about the Proxmox VE node
version_added: "2.9"

description:
    - "Retrieves and sets facts about the Proxmox VE node"

options:

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: gather fact of Proxmox VE node
  inett.pve.node_facts:
    
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
ansible_facts:
    description: Return code of API command execution
    type: dict
    returned: success
    contains:
        pve_node_name:
            type: str
            returned: success
        pve_ceph_installed:
            type: boolean
            returned: success
        pve_ceph_health:
            type: str
            returned: when supported
        pve_release:
            type: str
            returned: success
        pve_major_release:
            type: int
            returned: success
        pve_version:
            type: str
            returned: success
        pve_repoid:
            type: str
            returned: siccess
        pve_cluster:
            type: dict
            returned: when supported
        pve_cluster_name:
            type: str
            returned: when supported
        pve_cluster_nodes:
            type: list
            returned: when supported
            elements: str
        pve_local_node:
            type: str
            returned: success
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        access=dict(
            choices=['pvesh', 'http'],
            required=False,
            default='pvesh'),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    ansible_facts = dict()
    cluster = None
    nodes = dict()
    last_node = None
    has_ceph = False
    ceph_health = None

    rc, out, err, obj = mod.query_json("get", "/cluster/status")
    if rc != 0:
        mod.fail_json(msg="API query failed", rc=rc, stdout=out, stderr=err)

    for e in obj:
        if e["type"] == "cluster":
            if e["name"] != "":
                cluster = e
        elif e["type"] == "node":
            nodes[e["name"]] = e
        last_node = e

    node_name = mod.get_local_node()

    rc, out, err, obj = mod.query_json("get", "/cluster/ceph/status")
    if rc == 0:
        has_ceph = True
        for e in obj:
            if e == "health":
                ceph_health = obj[e]['status']
                break

    if node_name is not None:
        ansible_facts["pve_node_name"] = node_name

    ansible_facts["pve_ceph_installed"] = has_ceph
    if has_ceph and ceph_health is not None:
        ansible_facts["pve_ceph_health"] = ceph_health
    rc, out, err, obj = mod.query_json("get", "/version")
    if rc == 0:
        ansible_facts["ansible_distribution"] = "Proxmox_VE"
        ansible_facts["ansible_distribution_major_release"] = obj["release"]
        ansible_facts["pve_release"] = obj["release"]
        major_release = obj["release"].split(".")
        major_release = major_release[0]
        ansible_facts["pve_major_release"] = int(major_release)
        ansible_facts["pve_version"] = obj["version"]
        ansible_facts["pve_repoid"] = obj["repoid"]

    if cluster is not None:
        ansible_facts["pve_cluster"] = cluster
        ansible_facts["pve_cluster_name"] = cluster.get('name', None)
        ansible_facts["pve_cluster_nodes"] = nodes
    else:
        ansible_facts["pve_cluster_nodes"] = last_node
    ansible_facts["pve_local_node"] = node_name

    mod.exit_json(changed=False, ansible_facts=ansible_facts)


def main():
    run_module()


if __name__ == '__main__':
    main()
