#!/usr/bin/python

import random
import time

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: proxmox_migrate
short_description: Migrates VMs and LXC container inside cluster
version_added: "2.9.9"

description:
    - "Migrates QEMU VMs and LXC container inside cluster"

options:
    check_ha:
        description:
            - Check HA groups for migration
            - Migrate ony inside HA groups
            - Default: true
        required: fase
    migrate_ha:
        description:
            - wather or not to migrate vms in HA setup
            - If set to false, check_ha is set to true
            - Default true
        required: true
    maxworkers:
        description:
            - Maximum Number of parallel Workers for the migration process
            - Default: 1
    src_node_name:
        description:
            - node to migrate away from
    target_nodes:
        description:
            - List of nodes to migrate to
            - Will automatically detect other nodes in the cluster if not set or list includes 'all'
            - Be careful in HA setups as Proxmox will move VMs back inside HA group if the target node is not part of it
    vmids:
        description:
             - List of VMIDs to migrate
             - Will auto detect and migrate all running vms on the source node if not set or list includes '_auto'
    with_local_disks:
        description:
            - weather to allow migration with local disks
            - Default: False

author:
    - Maximilian Hill (mhill@inett.de)
'''

EXAMPELS = '''
- name: Migrate all running vms to other nodes in the cluster
  delegate_to: localhost
  proxmox_migrate:
    src_node_name: "{{ inventory_hostname }}"
    validate_certs: false
'''


def _pick_target(targets, target_nodes, fallback):
    if len(target_nodes) == 0:
        _ret = fallback
    elif len(target_nodes) == 1:
        _ret = target_nodes[0]
    else:
        min_l = min([len(targets[x]) for x in target_nodes])
        min_l_lists = [k for k in target_nodes if len(targets[k]) == min_l]
        l_i = random.randint(0, len(min_l_lists) - 1)
        _ret = min_l_lists[l_i]
    return _ret


def run_module():
    module_args = dict(
        check_ha=dict(type='bool', required=False, default=True),
        migrate_ha=dict(type='bool', required=False, default=True),
        maxworkers=dict(type='int', required=False, default=1),
        src_node_name=dict(type='str', required=True),
        target_nodes=dict(type='list', required=False, default=['_all']),
        vmids=dict(type='list', required=False, default=['_auto']),
        with_local_disks=dict(type='bool', required=False, default=False)
    )
    result = dict(
        changed=False,
        original_message={},
        message={}
    )

    module = PveApiModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    module.params['validate_certs'] = (module.params['validate_certs'] == "True")

    if not module.params['migrate_ha']:
        module.params['check_ha'] = True

    if module.params['check_ha']:
        rc, _out, _err, ha_groups = module.query_json("get", "/cluster/ha/groups")

        if rc != 0:
            module.fail_json(msg="failed to get HA groups")

        ha_group_node_map = {}
        for v in ha_groups:
            ha_group_node_map[v['group']] = v['nodes'].split(',')


        rc, _out, _err, ha_resources = module.query_json("get", "/cluster/ha/resources")

        if rc != 0:
            module.fail_json(msg="failed to get HA resources")

        ha_vm_group_map = {}
        for v in ha_resources:
            if 'group' in v.keys():
                ha_vm_group_map[v['sid'].split(':', 1)[1]] = v['group']

        def _get_target_nodes(vmid, default):
            if vmid in ha_vm_group_map:
                if ha_vm_group_map[vmid] in ha_group_node_map:
                    _ret = ha_group_node_map[ha_vm_group_map[vmid]]
                    if module.params['src_node_name'] in _ret:
                        _ret.remove(module.params['src_node_name'])
                    return _ret
            return default
    else:
        def _get_target_nodes(_vmid, default):
            return default

    facts = dict()
    targets = dict()

    # Get possible targets
    target_nodes = []

    if '_all' in module.params['target_nodes']:
        rc, out, err, qs_data = module.query_json("get", "/cluster/status")
        if rc == 0:
            for v in qs_data:
                if v["type"] == "node":
                    if v["name"] != module.params["src_node_name"]:
                        target_nodes.append(v["name"])
        else:
            module.fail_json(msg="failed to get target nodes")
    else:
        target_nodes = module.params['target_nodes']

    for v in target_nodes:
        result['message'][v] = []
        targets[v] = []
        targets[module.params['src_node_name']] = []

    if '_auto' in module.params['vmids']:
        # Get qemu vms to move
        qemu_migrate = []
        rc, _out, _err, sq_data = module.query_json("get",
                                                    "/nodes/"+module.params['src_node_name']+"/qemu"
                                                    )
        if rc == 0:
            for v in sq_data:
                if v["status"] == "running":
                    qemu_migrate.append(v["vmid"])

        # Determine qemu targets
        for vmid in qemu_migrate:
            _target_nodes = _get_target_nodes(vmid, target_nodes)
            _target_node = _pick_target(targets, _target_nodes, module.params['src_node_name'])
            targets[_target_node].append(vmid)

        # Get lxc container to move
        lxc_migrate = []
        rc, _out, _err, lxc_data = module.query_json("get",
                                                     "/nodes/"+module.params['src_node_name']+"/lxc"
                                                     )
        if rc == 0:
            for v in lxc_data:
                if v["status"] == "running":
                    lxc_migrate.append(v["vmid"])

        # Determine LXC targets
        for vmid in lxc_migrate:
            _target_nodes = _get_target_nodes(vmid, target_nodes)
            _target_node = _pick_target(targets, _target_nodes, module.params['src_node_name'])
            targets[_target_node].append(vmid)

        result['message'] = targets

        result['original_message'][module.params['src_node_name']] = (
                qemu_migrate + lxc_migrate
        )
    else:
        for vmid in module.params['vmids']:
            _target_nodes = _get_target_nodes(vmid, target_nodes)
            _target_node = _pick_target(targets, _target_nodes, module.params['src_node_name'])
            targets[_target_node].append(vmid)

        result['message'] = targets

        result['original_message'] = {
            module.params['src_node_name']: module.params['vmids']
        }

    for k in targets:
        if (len(targets[k]) > 0) and (k != module.params['src_node_name']):
            result['changed'] = True

    facts['parked_vms'] = result['message']

    if module.check_mode:
        module.exit_json(**result, ansible_facts=facts)

    # Migrate 'em all
    for k in targets:
        if (len(targets[k]) < 1) or (k == module.params['src_node_name']):
            continue

        qemu_data = {
            "target": k,
            "vms": targets[k],
            "maxworkers": module.params['maxworkers'],
            "with-local-disks": int(module.params['with_local_disks'])
        }
        rc_qemu, _out, _err = module.query_api("create",
                                               "/nodes/"+module.params["src_node_name"]+"/migrateall",
                                               params=qemu_data
                                               )
        lxc_data = {
            "target": k,
            "vms": targets[k],
            "maxworkers": module.params['maxworkers']
        }
        rc_lxc, _out, _err = module.query_api("create",
                                              "/nodes/"+module.params["src_node_name"]+"/migrateall",
                                              params=lxc_data
                                              )
        if (rc_lxc != 0) or (rc_qemu != 0):
            module.fail_json(msg="failed to migrate")

    if result['changed']:
        time.sleep(5)

    module.exit_json(**result, ansible_facts=facts)


def main():
    run_module()


if __name__ == '__main__':
    main()
