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

        # Clone
        source_vmid=dict(type='int', required=False, default=0),

        # Creation
        agent=dict(
            type='dict',
            options=dict(
                enabled=dict(type='bool', default=True),
                fstrim_cloned_disks=dict(type='bool', default=False),
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
                cores=dict(type='int', default=4),
                cputype=dict(type='str', default='kvm64'),
                hidden=dict(type='bool', default=False),
                limit=dict(type='int', default=None),
                vcpus=dict(type='int', default=0),
            ),
        ),
        efivars_storage=dict(type='str', required=False),
        hotplug=dict(type='list', default=['network', 'disk', 'usb']),
        memory=dict(type='int', required=False, default=2048),
        machine=dict(choices=['q35'], required=False, default='q35'),
        net=dict(
            type='dict', required=False, default={},  # elements='dict'
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
            type='dict', required=False,
            options=dict(
                storage=dict(type='str', default='cephfs'),
                image_name=dict(type='str', default='none'),
                media=dict(type='str', default='cdrom'),
            )
        ),
        scsi=dict(
            type='dict',  # elements='dict',
        ),
        vga=dict(
            choices=['std', 'cirrus', 'qxl'],
            required=False, default='qxl'
        ),
        storage=dict(type='str', required=False),
    )

    changed = False

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
                'create', "/nodes/%s/qemu/%d/status/stop" % (vm_node, mod.params.get('vmid')),
                fail='failed to stop VM'
            )
        rc, out, err = mod.query_api(
            'delete', "/nodes/%s/qemu/%d" % (vm_node, mod.params.get('vmid')),
            params=dict(purge=True),
        )
        if mod.params['state'] == 'absent':
            mod.exit_json(
                changed=(rc == 0), failed=(rc != 0), stdout=out, stderr=err
            )
            return
        vmid = None
        if ('vmid' in mod.params) and (mod.params['vmid'] is not None):
            vmid = mod.params['vmid']
        existing, vmid = mod.vmid_magic(vmid)
        # existing = False

    if (not existing) and (mod.params['state'] in ['stopped', 'running']):
        if ('source_vmid' in mod.params) and (mod.params.get('source_vmid', 0) >= 100):
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
            changed = True
        else:
            mp_agent = mod.params.get('agent', {})
            mp_cpu = mod.params.get('cpu', {})
            mp_setup_iso = mod.params.get('setup_iso', {})
            name = mod.params.get('name', None)
            pool = mod.params.get('pool', None)

            create_params = dict(
                agent=dict(
                    enabled=bool(mp_agent.get('enabled', True)),
                    fstrim_cloned_disks=bool(mp_agent.get('fstrim_cloned_disks', False)),
                    type=str(mp_agent.get('type', 'virtio')),
                ),
                bios=str(mod.params.get('bios', 'ovmf')),
                boot=dict(order=mod.params.get('boot_order', ['scsi0', 'ide2'])),
                cores=int(mp_cpu.get('cores', 4)),
                cpu=dict(
                    cputype=mp_cpu.get('cputype', 'kvm64'),
                    hidden=mp_cpu.get('hidden', False),
                ),
                hotplug=mod.params.get('hotplug', ['network', 'disk', 'usb']),
                memory=str(mod.params.get('memory', 2048)),
                machine=str(mod.params.get('machine', 'q35')),
                numa=mod.params.get('numa', True),
                ostype=str(mod.params.get('ostype', 'l26')),
                scsihw=str(mod.params.get('scsihw', 'qxl')),
                vcpus=int(mp_cpu.get('vcpus', mp_cpu.get('limit', 1))),
                vmid=str(mod.params['vmid']),
                vga=str(mod.params.get('vga', 'qxl')),
            )

            if mp_setup_iso.get('image_name', 'none') == 'none':
                create_params.update(ide2={
                    'file': "none", 'media': mp_setup_iso.get('media', 'cdrom'),
                }),
            else:
                create_params.update(ide2={
                    'file': "%s:iso/%s" % (mp_setup_iso.get('storage', 'cephfs'), mp_setup_iso.get('image_name')),
                    'media': mp_setup_iso.get('media', 'cdrom'),
                }),

            if name is not None:
                create_params['name'] = name

            for k, n in mod.params.get('net', dict()).items():
                create_params["net%s" % k] = n
                if n.get('model', None) is None:
                    create_params["net%s" % k]['model'] = 'virtio'
                if n.get('tag', None) is not None:
                    create_params["net%s" % k]['tag'] = int(n.get('tag'))
                if len(n.get('trunks', [])) > 0:
                    create_params["net%s" % k]['trunks'] = n.get('trunks')

                create_params["ipconfig%s" % k] = dict()

                ip4 = n.get('ip', None)
                net4 = n.get('s_net', None)
                ip4 = ip4 if net4 is None else "%s/%s" % (ip4, net4)
                if net4 is not None:
                    create_params["net%s" % k].pop('s_net', None)
                if ip4 is not None:
                    create_params["net%s" % k].pop('ip', None)
                    create_params["ipconfig%s" % k].update(dict(ip=ip4))
                gw4 = n.get('gw', None)
                if gw4 is not None:
                    create_params["net%s" % k].pop('gw', None)
                    create_params["ipconfig%s" % k].update(dict(gw=gw4))
                ip6 = n.get('ip6', None)
                net6 = n.get('s_net6', None)
                ip6 = ip6 if net6 is None else "%s/%s" % (ip6, net6)
                if net6 is not None:
                    create_params["net%s" % k].pop('s_net6', None)
                if ip6 is not None:
                    create_params["net%s" % k].pop('ip6', None)
                    create_params["ipconfig%s" % k].update(dict(ip6=ip6))
                gw6 = n.get('gw6', None)
                if gw6 is not None:
                    create_params["net%s" % k].pop('gw6', None)
                    create_params["ipconfig%s" % k].update(dict(gw6=gw6))

                if len(create_params["ipconfig%s" % k]) == 0:
                    create_params.pop("ipconfig%s" % k, None)

            if pool is not None:
                create_params['pool'] = pool

            for k, s in mod.params.get('scsi', dict()).items():
                create_params["scsi%s" % k] = dict(
                    file="%s:%d" % (s.get('storage', mod.params.get('storage')), s.get('size', 32)),
                    cache=s.get('cache', 'writeback'),
                    discard=('on' if s.get('discard', True) else 'ignore'),
                )

            if 'limit' in mp_cpu and mp_cpu.get('limit', None) is not None:
                create_params['cpulimit'] = int(mp_cpu.get('limit'))

            if create_params['bios'] == 'ovmf' and 'efivars_storage' in mod.params:
                create_params['efidisk0'] = "%s:0" % mod.params.get('efivars_storage', mod.params.get('storage', 'rbd'))
                if create_params['efidisk0'].startswith('None'):
                    create_params['efidisk0'] = "%s:0" % mod.params.get('storage', 'rbd')

            if 'storage' in mod.params and mod.params.get('storage') is not None:
                create_params['storage'] = mod.params['storage']

            rc, out, err = mod.query_api(
                'create', "/nodes/%s/qemu" % node,
                params=create_params, fail='failed to create VM'
            )
            changed = True

    vm_info = mod.vm_info(mod.params.get('vmid'))

    if (mod.params['state'] == 'running') and (vm_info['status'] != 'running'):
        rc, out, err = mod.query_api(
            'create', "/nodes/%s/qemu/%d/status/start" % (node, vmid),
            fail='failed to start VM'
        )
        changed = True
    if (mod.params['state'] == 'stopped') and (vm_info['status'] != 'stopped'):
        rc, out, err = mod.query_api(
            'create', "/nodes/%s/qemu/%d/status/stop" % (node, vmid),
            fail='failed to stop VM'
        )
        changed = True

    if rc == 0:
        mod.exit_json(changed=changed, stdout=out, stderr=err)
        return

    mod.exit_json(
        existing=existing, vmid=vmid,
        rc=(rc if rc is not None else 0), stdout=out, stderr=err,
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
