# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import pprint

from ansible.module_utils.basic import AnsibleModule


class PveApiModule(AnsibleModule):
    af = None
    pp = None

    def __init__(self, argument_spec=dict(), **kwargs):
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
        self.af = open('/tmp/ansible.audit.log', 'w')
        self.pp = pprint.PrettyPrinter(stream=self.af)

    def __del__(self):
        self.af.close()

    @staticmethod
    def _get_cmd(method, url, https_proxy=None, params=dict()):
        ret = list()
        if https_proxy is not None:
            ret.append('https_proxy="' + https_proxy + '"')
        ret += ["pvesh", method, url]
        for (k, v) in params.items():
            if isinstance(v, str):
                ret += ["--%s" % k, v]
            if type(v) is int:
                ret += ["--%s" % k, str(v)]
            if type(v) is bool:
                ret += ["--%s" % k, str(int(v))]
            if v is None:
                ret += ["--%s" % k]
            if type(v) is dict:
                ret += ["--%s" % k, PveApiModule._params_dict_to_string(v)]
        ret += ["--output-format", "json"]
        return ret

    @staticmethod
    def _params_dict_to_string(in_dict):
        ret_a = list()

        for (k, v) in in_dict.items():
            if isinstance(v, str):
                ret_a += ["%s=%s" % (k, v)]
            if type(v) is int:
                ret_a += ["%s=%d" % (k, v)]
            if type(v) is bool:
                ret_a += ["%s=%d" % (k, int(v))]
            if type(v) is list:
                ret_a += ["%s=%s" % (k, ';'.join(v))]
            if v is None:
                ret_a += [k]

        return ','.join(ret_a)

    def query_api(
            self, method, url,
            access=None, https_proxy=None, fail=None, params=dict()
    ):
        if access is None:
            access = self.params['access'].lower()
        if (access != "pvesh") and (https_proxy is not None):
            self.fail_json("https_proxy can only be used with pvesh")
        if access == "pvesh":
            f = open('/tmp/ansible.audit.log')
            self.pp.pprint(params)
            c_params = self._get_cmd(method, url, params=params)
            self.pp.pprint(c_params)
            f.close()
            rc, out, err = self.run_command(c_params)
        else:
            rc, out, err = 1, "", "Access method %s not supported yet" % access
        if (rc != 0) and (fail is not None):
            self.fail_json(fail, rc=rc, stdout=out, stderr=err)
        return rc, out, err

    def query_json(
            self, method, url,
            access=None, https_proxy=None, fail=None, params=dict()
    ):
        rc, out, err = self.query_api(
            method, url,
            access=access, https_proxy=https_proxy, fail=None, params=params
        )
        try:
            obj = json.loads(out)
            if (rc != 0) and (fail is not None):
                self.fail_json(fail, rc=rc, stdout=out, stderr=err, obj=obj)
                return rc, out, err, obj
        except:
            obj = None
        return rc, out, err, obj

    def get_local_node(self):
        rc, out, err, obj = self.query_json("get", "/cluster/status")
        if rc != 0:
            self.fail_json(
                "failed to query nodes",
                rc=rc, stdout=out, obj=obj,
            )
        for node in obj:
            if (node['type'] == 'node') and bool(int(node['local'])):
                return node['name']

        self.fail_json(
            "Cannot find local node",
            stdout=out, stderr=err, json=obj,
        )

    def get_nodes(self):
        rc, out, err, obj = self.query_json("get", "/nodes")
        if rc != 0:
            self.fail_json(
                "failed to query nodes",
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
            rc, out, err, qemu = self.query_json("get", "/nodes/" + node + "/qemu")
            if rc != 0:
                self.fail_json(
                    "failed to query qemu vms for node %s" % node,
                    rc=rc, stdout=out, stderr=err, obj=qemu,
                )
            rc, out, err, lxc = self.query_json("get", "/nodes/" + node + "/lxc")
            if rc != 0:
                self.fail_json(
                    "failed to query lxc containers for node %s" % node,
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
            rc, out, err, qemu = self.query_json("get", "/nodes/%s/qemu" % node)
            if rc != 0:
                self.fail_json(
                    "failed to query qemu vms for node %s" % node,
                    rc=rc, stdout=out, stderr=err, obj=qemu,
                )
            rc, out, err, lxc = self.query_json("get", "/nodes/%s/lxc" % node)
            if rc != 0:
                self.fail_json(
                    "failed to query lxc containers for node %s" % node,
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

    def vmid_magic(self, vmid=None):
        r_params = dict(
            vmid=vmid
        )
        rc, out, err = self.query_api(
            "get", "/cluster/nextid",
            params=r_params
        )
        exists = (rc != 0)
        if (vmid is None) and (not exists):
            vmid = out.strip()
        return exists, vmid

    def vm_info(self, f_vmid, node=None):
        vms = self.get_vms(node)
        for vmid in vms:
            if int(vmid) == f_vmid:
                return vms[vmid]
        self.fail_json("Unable to locate VM")
