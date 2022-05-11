#!/usr/bin/python

# Copyright: (c) 2021, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        # VM identification
        vmid=dict(type='int', required=False, default=None),

        # Storage configuration
        scsi=dict(
            type='dict', required=False, default={},  # elements='dict'
        ),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)
    vm, vm_config = mod.vm_config_get(mod.params['vmid'])
    update_params = dict()
    update_args = dict()

    for k, s in mod.params.get('scsi', dict()).items():
        update_args["scsi%s" % k] = s
        update_params["scsi%s" % k] = dict(
            file="%s:%d" % (
                s.get('storage', mod.params.get('storage')),
                s.get('size', 32)
            ),
            cache=s.get('cache', 'writeback'),
            discard=('on' if s.get('discard', True) else 'ignore'),
            iothread=('on' if s.get('iothread', True) else 'ignore'),
            ssd=('on' if s.get('ssd', True) else 'ignore'),
            mbps_rd=600, mbps_wr=300,
        )

    message = update_params

    old_message = dict({k: vm_config.get(k, None) for (k, v) in update_params.items()})
    changed = (old_message != message)

    if changed and not mod.check_mode:
        mod.vm_config_set(
            mod.params.get('vmid'),
            node=vm['node'],
            config=update_params,
            vm=vm
        )

    mod.exit_json(
        changed=changed,
        message=message,
        original_message=old_message
    )


def main():
    run_module()


if __name__ == '__main__':
    main()

