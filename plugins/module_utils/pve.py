# -*- coding: utf-8 -*-

# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import sys

from ansible.module_utils.basic import AnsibleModule


class PveApiModule(AnsibleModule):

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

    @staticmethod
    def _get_cmd(method, url, https_proxy=None, params=dict()):
        """Builds cli command

        :param method: 'get', 'create' or 'delete'
        :type method: str
        :param url: path according to Proxmox VE API
        :type url: str
        :param https_proxy: https_proxy environment variable. None by default
        :type https_proxy: str
        :param params: Command line arguments (key: name of argument; value: bool, dict, int, list, str)
        :type params: dict
        :rtype: list
        :returns: list of strings to pass to self.run_command()
        """

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
            if type(v) is list:
                ret += ["--%s" % k, ','.join(v)]
            if type(v) is dict:
                ret += ["--%s" % k, PveApiModule.params_dict_to_string(v)]
        ret += ["--output-format", "json"]
        return ret

    @staticmethod
    def params_dict_to_string(in_dict):
        """Converts dictionary to string

        :param in_dict: dict
        :rtype: str
        """

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

    @staticmethod
    def valid_nets():
        """Returns valid config keys for network interfaces

        :rtype: list
        :returns: valid nic names
        """

        ret = []
        for x in range(32):
            ret.append("net%d" % x)
        return ret

    @staticmethod
    def valid_nic_models():
        """Returns valid nic models

        :rtype: list
        :returns: valid nic models
        """

        return [
            "e1000", "e1000-82540em", "e1000-82544gc", "e1000-82545em",
            "e1000e", "i82551", "i82557b", "i82559er", "ne2k_isa", "ne2k_pci",
            "pcnet", "rtl8139", "virtio", "vmxnet3",
        ]

    @staticmethod
    def valid_storages():
        """Returns valid config keys for storage devices

        :rtype: list
        :returns: valid config keys for storage devices
        """

        ret = []
        for x in range(4):
            ret.append("ide%d" % x)
        for x in range(6):
            ret.append("sata%d" % x)
        for x in range(31):
            ret.append("scsi%d" % x)
        for x in range(16):
            ret.append("virtio%d" % x)
        ret.append("efidisk0")
        ret.append("tpmstate0")
        return ret

    def query_api(
            self, method, url,
            access=None, https_proxy=None, fail=None, params=dict()
    ):
        """Query API and return raw stdout and stderr only

       :param method: Proxmox VE CLI method ('get', 'create' or 'delete')
       :type method: str
       :param url: Proxmox VE CLI path
       :type url: str
       :param fail: Fail message
       :type fail: str
       :param params: Parameters to pass
       :type params: dict

       :returns: tuple: (int: rc, str: stdout, str: stderr)
       :rtype: tuple
       """

        if access is None:
            access = self.params['access'].lower()
        if (access != "pvesh") and (https_proxy is not None):
            self.fail_json(msg="https_proxy can only be used with pvesh")
        if access == "pvesh":
            c_params = self._get_cmd(method, url, params=params)
            rc, out, err = self.run_command(c_params)
        else:
            rc, out, err = 1, "", "Access method %s not supported yet" % access
        if (rc != 0) and (fail is not None):
            self.fail_json(msg=fail, rc=rc, stdout=out, stderr=err)
        return rc, out, err

    def query_json(
            self, method, url,
            access=None, https_proxy=None, fail=None, params=dict()
    ):
        """Query API and return raw stdout, raw stderr and parsed json stdout

        :param method: Proxmox VE CLI method ('get', 'create' or 'delete')
        :type method: str
        :param url: Proxmox VE CLI path
        :type url: str
        :param fail: Fail message
        :type fail: str
        :param params: Parameters to pass
        :type params: dict

        :returns: tuple: (int: rc, str: stdout, str: stderr, Any: object)
        :rtype: tuple
        """

        rc, out, err = self.query_api(
            method, url,
            access=access, https_proxy=https_proxy, fail=None, params=params
        )
        try:
            obj = json.loads(out)
            if (rc != 0) and (fail is not None):
                self.fail_json(msg=fail, rc=rc, stdout=out, stderr=err, obj=obj)
                return rc, out, err, obj
        except:
            obj = None
        return rc, out, err, obj

    def get_local_node(self):
        """Return node this module is run on

        :returns: name of the node this module is run on
        :rtype: str
        """

        rc, out, err, obj = self.query_json("get", "/cluster/status")
        if rc != 0:
            self.fail_json(
                msg="failed to query nodes",
                rc=rc, stdout=out, obj=obj,
            )
        for node in obj:
            if (node['type'] == 'node') and bool(int(node['local'])):
                return node['name']

        self.fail_json(
            msg="Cannot find local node",
            stdout=out, stderr=err, json=obj,
        )

    def get_nodes(self):
        """Return list of nodes in Proxmox VE cluster

        :returns: list of nodes n Proxmox VE cluster
        :rtype: list
        """

        rc, out, err, obj = self.query_json("get", "/nodes")
        if rc != 0:
            self.fail_json(
                msg="failed to query nodes",
                rc=rc, stdout=out, obj=obj,
            )
        ret = list()
        for node in obj:
            ret.append(node["node"])
        return ret

    def get_node_lrm_idle(self, node):
        """Return true if node lrm is idle

        :param node: Name of node
        :type node: str
        :returns: true if node lrm is idle
        :rtype: bool
        """

        rc, _out, _err, obj = self.query_json("get", "/cluster/ha/status/current")
        if rc != 0:
            self.fail_json("Unable to get cluster HA status")
        for e in obj:
            if e["type"] == "lrm" and e["node"] == node:
                return "idle" in e["status"]

    def get_node_lrm_maintenance(self, node):
        """Return true if node lrm is in maintenance mode

        :param node: Name of node
        :type node: str
        :returns: true if node lrm is in maintenance mode
        :rtype: bool
        """
        rc, _out, _err, obj = self.query_json("get", "/cluster/ha/status/current")
        if rc != 0:
            self.fail_json("Unable to get cluster HA status")
        for e in obj:
            if e["type"] == "lrm" and e["node"] == node:
                return "maintenance mode" in e["status"]

    def get_vmids(self, node=None):
        """Return list of guest VMIDs on given node.

        If no node is given guest VMIDs on all nodes will be returned

        :param node: Name of node
        :type node: str
        :return: VMIDs
        :rtype: set
        """

        ret = list()
        if node is None:
            for node in self.get_nodes():
                ret.extend(self.get_vmids(node=node))
            return ret
        else:
            rc, out, err, qemu = self.query_json("get", "/nodes/" + node + "/qemu")
            if rc != 0:
                self.fail_json(
                    msg="failed to query qemu vms for node %s" % node,
                    rc=rc, stdout=out, stderr=err, obj=qemu,
                )
            rc, out, err, lxc = self.query_json("get", "/nodes/" + node + "/lxc")
            if rc != 0:
                self.fail_json(
                    msg="failed to query lxc containers for node %s" % node,
                    rc=rc, stdout=out, stderr=err, obj=lxc,
                )
            for vm in qemu:
                ret.append(vm["vmid"])
            for vm in lxc:
                ret.append(vm["vmid"])
        return set(ret)

    def get_vms(self, node=None):
        """Return list of guest VMIDs on given node.

        If no node is given guest VMIDs on all nodes will be returned

        :param node: Name of node
        :type node: str
        :return: list of guests
        :rtype: list
        """

        if node is None:
            for node in self.get_nodes():
                for vm in self.get_vms(node=node):
                    yield vm
        else:
            _rc, _out, _err, qemu = self.query_json(
                "get", "/nodes/%s/qemu" % node,
                fail="failed to query qemu vms for node %s" % node
            )
            _rc, _out, _err, lxc = self.query_json(
                "get", "/nodes/%s/lxc" % node,
                fail="failed to query lxc containers for node %s" % node
            )
            if qemu is not None:
                for vm in qemu:
                    vm['node'] = node
                    vm['type'] = "qemu"
                    yield vm
            if lxc is not None:
                for vm in lxc:
                    vm['node'] = node
                    vm['type'] = "lxc"
                    yield vm

    def set_node_lrm_maintenance(self, node, enabled):
        """Set maintenance mode on node

        :param node: Name of node
        :type node: str
        :param enabled: target state of node lrm
        :type enabled: bool
        """

        if enabled:
            action = "enable"
        else:
            action = "disable"
        cmd = ["ha-manager", "crm-command", "node-maintenance", action, node]
        s_cmd = ' '.join(cmd)
        rc, out, err = self.run_command(cmd)
        if rc != 0:
            self.fail_json("failed to set maintenance mode", rc=rc, out=out, err=err, cmd=cmd, s_cmd=s_cmd)

    def vmid_magic(self, vmid=None):
        r_params = dict(
            vmid=vmid
        )
        """Returns same as the magic /cluster/nextid

        If a VMID is given and the VMID is already taken, this function will
        return (true, ${vmid}); if it isn't taken it'll return
        (false, ${vmid}).

        If no VMID is given, this funtion will return (false, next_free_vmid)

        :param vmid:
        :return: (if VM already exists, affected VMID)
        :rtype: tuple
        """

        rc, out, err = self.query_api(
            "get", "/cluster/nextid",
            params=r_params
        )
        exists = (rc != 0)
        if (vmid is None) and (not exists):
            vmid = out.strip()
        return exists, vmid

    def vm_info(self, f_vmid, node=None):
        """Get basic info about a guest

        :param f_vmid: ID of guest information is requested about
        :type f_vmid: int
        :param node: node to search. Defaults to all nodes.
        :type node: str
        :returns: basic information about guest
        :rtype: dict
        """

        for vm in self.get_vms(node):
            if int(vm['vmid']) == int(f_vmid):
                return vm
        self.fail_json(msg="Unable to locate VM")

    def vm_locate(self, f_vmid):
        """Locate VM in cluster

        :param f_vmid: id of guest to locate
        :type f_vmid: int
        :returns: Node name the guest is on
        :rtype: str
        """

        vm = self.vm_info(f_vmid)
        if vm.get('node', None) is not None:
            return vm.get('node')
        self.fail_json(msg="VM %s found but seems to have no node" % f_vmid)

    def vm_config_get(self, f_vmid, node=None, vm=None):
        """Returns fully parsed config

        resolves lists seperated by commas and semicolon as well as
        dictionaries in which key and value are seperated by '='

        :param f_vmid: id of guest to fetch config of
        :param node: node on which to look up VMID
        :param vm:
        :returna:
        """

        if (node is None) or (vm is None):
            vm = self.vm_info(f_vmid, node=node)
            # node = vm['node']
        _rc, _out, _err, vm_config = self.query_json(
            'get', "/nodes/%s/%s/%s/config" % (vm['node'], vm['type'], vm['vmid']),
            fail="error fetching config for VM %s" % vm['vmid']
        )
        ret_config = dict()
        for k in vm_config:
            v = vm_config[k]
            if isinstance(v, str):
                if k == "tags":
                    ret_config.update({k: v.split(";")})
                elif '=' in v:
                    n_v = dict()
                    for l in v.split(','):
                        l_s = l.split('=')
                        try:
                            if len(l_s) == 1 and k == "agent":
                                n_v.update({"enabled": bool(int(l_s[0]))})
                            elif len(l_s) == 1 and k in self.valid_storages():
                                n_v.update({"volume": l_s[0]})
                            elif len(l_s) == 2 and k in self.valid_nets():
                                if l_s[0] == "firewall":
                                    n_v.update({"firewall": bool(int(l_s[1]))})
                                elif l_s[0] == "trunks":
                                    n_v.update({
                                        "trunks": [int(t) for t in l_s[1].split(";")]
                                    })
                                elif l_s[0] in self.valid_nic_models():
                                    n_v.update({"model": l_s[0], "macaddr": l_s[1]})
                                else:
                                    n_v.update({l_s[0]: l_s[1]})
                            elif k == "agent" and l_s[0] in ["fstrim_cloned_disks"]:
                                n_v.update({l_s[0]: bool(int(l_s[1]))})
                            else:
                                n_v.update({l_s[0]: l_s[1]})
                        except:
                            self.fail_json(msg="failed to parse config",
                                    vm_config=vm_config, key=k, value=v,
                                    lst=l, lst_el_split=l_s, lst_sp_len=len(l_s),
                                    exception=sys.exc_info(),
                            )
                    ret_config.update({k: n_v})
                elif ',' in v:
                    ret_config.update({k: v.split(',')})
        return vm, ret_config

    def vm_config_set(self, f_vmid, node=None, digest=None, config=dict(), vm=None):
        """Configure Proxmox VE guest

        :param f_vmid: ID of guest to configure
        :type f_vmid: int
        :param node: node to look up guest in. Defaults to all nodes
        :type node: str
        :param digest: optional digest of current config
        :type digest: str
        :param config: options to set.
        :type config: dict
        :param vm: basic vm info
        :type vm: dict
        :returns: new configuration
        :rtype: tuple
        """
        if (node is None) or (digest is None) or (vm is None):
            vm, vm_config = self.vm_config_get(f_vmid, node)
            digest = vm_config.get('digest', None)
            node = vm['node']
        if digest is not None:
            config.update(dict(digest=digest))
        self.query_api(
            'create', "/nodes/%s/%s/%s/config" % (vm['node'], vm['type'], vm['vmid']),
            params=config,
            fail="error updating config for VM %s" % vm['vmid']
        )
        return self.vm_config_get(f_vmid, node=node, vm=vm)
