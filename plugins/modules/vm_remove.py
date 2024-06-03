#!/usr/bin/python

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        vmid=dict(type='int', required=True),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=False)

    vmid = None
    if ('vmid' in mod.params) and (mod.params['vmid'] is not None):
        vmid = mod.params['vmid']

    existing, vmid = mod.vmid_magic(vmid)

    if not existing:
        mod.exit_json(changed=False)
        return

    vm_info = mod.vm_info(mod.params.get("vmid"))
    vm_node = mod.vm_locate(mod.params.get("vmid"))

    if vm_info['status'] != 'stopped':
        _rc, _out, _err = mod.query_api(
            'create', "/nodes/%s/qemu/%d/status/stop" % (vm_node, mod.params.get('vmid')),
            fail='failed to stop VM'
        )
    rc, out, err = mod.query_api(
        'delete', "/nodes/%s/qemu/%d" % (vm_node, mod.params.get('vmid')),
        params=dict(purge=True),
    )
    mod.exit_json(
        changed=(rc == 0), failed=(rc != 0), stdout=out, stderr=err
    )


def main():
    run_module()


if __name__ == '__main__':
    main()