# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

from ansible.module_utils.basic import AnsibleModule


class PveApiModule(AnsibleModule):
    def __init__(self,
                 argument_spec=dict(),
                 **kwargs
                 ):
        arc_spec = dict(
            access=dict(
                choices=['pvesh', 'http'],
                required=False,
                default='pvesh'),
        )
        arc_spec.update(argument_spec)
        kwargs['supports_check_mode'] = True
        super(PveApiModule, self).__init__(
            argument_spec=arc_spec, **kwargs
        )

    def _get_cmd(self, method, url):
        return [
            "pvesh",
            method, url,
            "--output-format", "json"
        ]

    def query_api(self, method, url, access=None):
        if access is None:
            access = self.params['access'].lower()
        if access == "pvesh":
            return self.run_command(self._get_cmd(method, url))
        else:
            return 1, "", "Access method "+access+" not supported yet"

    def query_json(self, method, url, access=None):
        rc, out, err = self.query_api(method, url, access=access)
        try:
            obj = json.loads(out)
        except:
            obj = None
        return rc, out, err, obj

    def get_nodes(self):
        rc, out, err, obj = self.query_json("get", "/nodes")
        if rc != 0:
            self.fail_json("failed to query nodes",
                rc=rc, stdout=out, obj=obj,
            )
        ret = list()
        for node in obj:
            ret.append(node["node"])
        return ret

    def get_vmids(self, node=None):
        ret = list()
        if node is None:
            for node in self.get_nodes():
                ret.update(self.get_vmids(node=node))
            return ret
        else:
            rc, out, err, qemu = self.query_json("get", "/nodes/"+node+"/qemu")
            if rc != 0:
                self.fail_json("failed to query qemu vms for node "+node,
                    rc=rc, stdout=out, stderr=err, obj=qemu,
                )
            rc, out, err, lxc = self.query_json("get", "/nodes/"+node+"/lxc")
            if rc != 0:
                self.fail_json("failed to query lxc containers for node "+node,
                    rc=rc, stdout=out, stderr=err, obj=lxc,
                )
            for vm in qemu:
                ret.append(vm["vmid"])
            for vm in lxc:
                ret.append(vm["vmid"])
        return ret

    def get_vms(self, node=None):
        ret = dict()
        if node is None:
            for node in self.get_nodes():
                ret.update(self.get_vms(node=node))
            return ret
        else:
            rc, out, err, qemu = self.query_json("get", "/nodes/"+node+"/qemu")
            if rc != 0:
                self.fail_json("failed to query qemu vms for node "+node,
                    rc=rc, stdout=out, stderr=err, obj=qemu,
                )
            rc, out, err, lxc = self.query_json("get", "/nodes/"+node+"/lxc")
            if rc != 0:
                self.fail_json("failed to query lxc containers for node "+node,
                    rc=rc, stdout=out, stderr=err, obj=lxc,
                )
            for vm in qemu:
                ret[vm['vmid']] = vm
                ret[vm['vmid']]['type'] = "qemu"
                ret[vm['vmid']]['node'] = node
            for vm in lxc:
                ret[vm['vmid']] = vm
                ret[vm['vmid']]['type'] = "lxc"
                ret[vm['vmid']]['node'] = node
        return ret

    def vm_info(self, f_vmid, node=None):
        vms = self.get_vms(node)
        for vmid in vms:
            if int(vmid) == int(f_vmid):
                return vms[vmid]
        self.fail_json("Unable to locate VM")
