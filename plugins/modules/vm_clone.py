#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        source_vmid=dict(type="int", required=True),
        vmid=dict(type="int", required=False, default=None),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=False)

    param_source_vmid = int(mod.params["source_vmid"])
    (source_vm_exists, source_vmid) = mod.vmid_magic(param_source_vmid)
    if not source_vm_exists:
        mod.fail_json("Source VM does not exist", changed=False)
        return

    param_target_vmid = mod.params["vmid"]
    if param_target_vmid is None:
        (target_vm_exists, target_vmid) = mod.vmid_magic()
    else:
        (target_vm_exists, target_vmid) = mod.vmid_magic(int(param_target_vmid))

    if target_vm_exists:
        mod.fail_json("Target VM does already exist", changed=False)
        return

    node_source_vm = mod.vm_locate(source_vmid)
    node_target_vm = mod.get_local_node()

    rc, out, err = mod.query_api(
        "create", "/nodes/%s/qemu/%s/clone" % (node_source_vm, source_vmid),
        params=dict(newid=target_vmid, target=node_target_vm, full=True),
        fail="Failed to clone VM"
    )
    if rc == 0:
        mod.exit_json(
            changed=True, stdout=out, stderr=err,
            stdout_lines=out.split("\n"), stderr_lines=err.split("\n"),
            source_vmid=source_vmid, target_vmid=target_vmid,
        )
        return
    else:
        mod.fail_json("Failed to clone VM")


def main():
    run_module()


if __name__ == "__main__":
    main()