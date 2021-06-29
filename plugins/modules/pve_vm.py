#!/usr/bin/python

# Copyright: (c) 2021, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        state=dict(
            choices=['absent', 'running', 'stopped'],
            required=False, default='stopped'
        ),

        # VM identification
        vmid=dict(type='int', required=False, default=None),
        name=dict(type='str', required=False),
        pool=dict(type='int', required=False, default=None),

        # Clone
        source_vmid=dict(type='int', required=False, default=None),

        # Hardware
        agent=dict(
            type='dict',
            options=dict(
                enable=dict(type='bool', default=True),
                fstrim_cloned_disk=dict(type='bool', default=False),
                type=dict(choices=['virtio', 'isa'], default='virtio'),
            ),
        ),
        bios=dict(choices=['ovmf', 'seabios'], required=False, default='ovmf'),
        boot_order=dict(
            type='list', elements='str', default=['scsi0', 'ide2']
        ),
        cpu=dict(
            type='dict',
            options=dict(
                cputype=dict(type='str', default='kvm64'),
                hidden=dict(type='bool', default=False),
                limit=dict(type='int', default=4),
                vcpus=dict(type='int', default=0),
            ),
        ),
        efivars_storage=dict(type='str', required=False, default='rbd:1'),
        hotplug=dict(type='list', default=['network', 'disk', 'usb', 'cpu']),
        machine=dict(choices=['q35'], required=False, default=None),
        net=dict(
            type='list', elements='dict', required=False,
            options=dict(
                id=dict(type='int'),
                model=dict(choices=['virtio'], default='virtio'),
                bridge=dict(type='str', required=True),
                tag=dict(type='int', default=None),
                trunks=dict(type='list', elements='int', default=list()),
                mac=dict(type='str', required=False, default=None),
                firewall=dict(type='bool', default=True),
            )
        ),
        numa=dict(type='bool', default=True),
        ostype=dict(
            choices=[
                'other', 'wxp', 'w2k', 'w2k3', 'w2k8', 'wvista', 'win7',
                'win8', 'win10', 'l24', 'l26', 'solaris'],
            default='l26'
        ),
        replace=dict(type='bool', required=False, default=False),
        scsihw=dict(
            choices=[
                'lsi', 'lsi53c810', 'virtio-scsi-pci', 'virtio-scsi-single',
                'megasas', 'pvscsi'
            ],
            required=False, default='virtio-scsi-pci',
        ),
        setup_iso=dict(
            type='dict', required=False, default=None,
            options=dict(
                storage=dict(type='str', default='cephfs'),
                image_name=dict(type='str', required=True),
                media=dict(type='str', default='cdrom'),
            )
        ),
        scsi=dict(
            type='list', elements='dict',
            options=dict(
                id=dict(type='int', default=0),
                storage=dict(type='str', default='rbd'),
                size=dict(type='int', default=32),
                cache=dict(
                    choices=['writeback'],
                    default='writeback', required=False
                ),
                discard=dict(type='bool', required=False, default=True),
            ),
            default=[
                dict(id=0,
                     storage='rbd', size=32, cache='writeback', discard=True,
                     ),
            ],
        ),
        vga=dict(
            choices=['std', 'cirrus', 'qxl'],
            required=False, default='qxl'
        ),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    node = str(mod.get_local_node())
    vmid = None
    if ('vmid' in mod.params) and (mod.params['vmid'] is not None):
        vmid = mod.params['vmid']

    existing, vmid = mod.vmid_magic(vmid)
    rc, out, err = (None, None, None)

    if (
            (not existing) and (mod.params['state'] == 'absent')
    ):
        mod.exit_json(changed=False)
        return

    if existing and (
            (mod.params['state'] == 'absent')
            or (mod.params.get('replace', False))
    ):
        vm_info = mod.vm_info(mod.params.get('vmid'))
        vm_node = vm_info.get('node')
        if vm_info['status'] != 'stopped':
            _rc, _out, _err = mod.query_api(
                'create', "/nodes/%s/qemu/%d/status/stop" % (node, vmid),
                fail='failed to stop VM'
            )
        rc, out, err = mod.query_api(
            'delete', "/nodes/%s/qemu/%d" % (vm_node, vmid),
            params=dict(purge=True),
        )
        if mod.params['state'] == 'absent':
            mod.exit_json(
                changed=(rc == 0), failed=(rc != 0), stdout=out, stderr=err
            )
            return
        existing = False

    if (not existing) and (mod.params['state'] in ['stopped', 'running']):
        if 'source_vmid' in mod.params:
            source_vmid = mod.params.get('source_vmid')
            source_vm = mod.vm_info(source_vmid)
            source_node = source_vm.get('node')
            name = mod.params.get('name', source_vm.get('name', None))
            pool = mod.params.get('pool', None)
            clone_params = dict(newid=int(vmid), full=True, target=node)
            if name is not None:
                clone_params['name'] = name
            if pool is not None:
                clone_params['pool'] = pool
            rc, out, err = mod.query_api(
                'create',
                "/nodes/%s/qemu/%s/clone" % (source_node, source_vmid),
                params=clone_params, fail='failed to clone VM'
            )
        else:
            mod.fail_json(msg="creation not supported yet")
            return

            mp_agent = mod['params'].get('agent', {})
            mp_cpu = mod['params'].get('cpu', {})
            mp_setup_iso = mod['params'].get('setup_iso', {})
            name = mod.params.get('name', None)
            pool = mod.params.get('pool', None)

            create_params = dict(
                agent=dict(
                    enable=bool(mp_agent.get('enable', True)),
                    fstrim_cloned_disk=bool(mp_agent.get('fstrim_cloned_disk', False)),
                    type=str(mp_agent.get('type', 'virtio')),
                ),
                bios=str(mod['params'].get('bios', 'ovmf')),
                boot_order=mod.params.get('boot_order', ['scsi0', 'ide2']),
                cpu=dict(
                    cputype=mp_cpu.get('cputype', 'kvm64'),
                    hidden=mp_cpu.get('cputype', 'kvm64'),
                ),
                cpulimit=int(mp_cpu.get('limit', 1)),
                efivars_storage="{%s}:1" % mod['params'].get('efivars_storage', 'rbd'),
                hotplug=mod.params.get('hotplug', ['network', 'disk', 'usb', 'cpu']),
                ide2=dict(
                    file="%s:iso/%s" % (mp_setup_iso.get('storage', 'cephfs'), mp_setup_iso.get('image_name')),
                    media=mp_setup_iso.get('media', 'cdrom'),
                ),
                machine=str(mod['params'].get('machine', 'q35')),
                numa=mod.params.get('numa', True),
                ostype=str(mod['params'].get('ostype', 'l26')),
                scsihw=str(mod['params'].get('scsihw', 'qxl')),
                vcpus=int(mp_cpu.get('vcpus', mp_cpu.get('limit', 1))),
                vmid=str(mod['params']['vmid']),
                vga=str(mod['params'].get('vga', 'qxl')),
            )

            if name is not None:
                create_params['name'] = name
            if pool is not None:
                create_params['pool'] = pool

            for s in mod['params'].get('scsi', list()):
                create_params["scsi%s" % s.get('id')] = dict(
                    file="%s:%d}" % (s.get('storage', 'rbd'), s.get('size', 32)),
                    cache=s.get('cache', 'writeback'),
                    discard=s.get('discard', True),
                )

            for n in mod['params'].get('net', list()):
                create_params["net%s" % n.get('id')] = dict(
                    model=n.get('model', 'virtio'),
                    bridge=n.get('bridge', 'writeback'),
                    discard=n.get('discard', True),
                )
                if n.get('tag', None) is not None:
                    create_params["net%s" % n.get('id')]['tag'] = int(n.get('tag'))
                if len(n.get('trunks', [])) is not 0:
                    create_params["net%s" % n.get('id')]['trunks'] = n.get('trunks')

            rc, out, err = mod.query_api(
                'create', "/nodes/%s/qemu" % node,
                params=create_params, fail='failed to create VM'
            )

    vm_info = mod.vm_info(mod.params.get('vmid'))
    
    if mod.params['state'] == vm_info['status']:
        mod.exit_json(changed=False)
        return

    if (mod.params['state'] == 'running') and (vm_info['status'] != 'running'):
        rc, out, err = mod.query_api(
            'create', "/nodes/%s/qemu/%d/status/start" % (node, vmid),
            fail='failed to start VM'
        )
    if (mod.params['state'] == 'stopped') and (vm_info['status'] != 'stopped'):
        rc, out, err = mod.query_api(
            'create', "/nodes/%s/qemu/%d/status/stop" % (node, vmid),
            fail='failed to stop VM'
        )

    if rc == 0:
        mod.exit_json(changed=True, stdout=out, stderr=err)
        return

    mod.fail_json(
        msg='uncovered malfunction', existing=existing, vmid=vmid,
        rc=rc, stdout=out, stderr=err,
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
