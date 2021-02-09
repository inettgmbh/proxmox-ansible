#!/usr/bin/python

# Copyright: (c) 2020, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        access=dict(
            choices=['pvesh', 'http'],
            required=False,
            default='pvesh'),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    ansible_facts = dict()
    cluster = dict()
    nodes = dict()

    rc, out, err, obj = mod.query_json("get", "/cluster/status")
    if rc != 0:
        mod.fail_json("API query failed", rc=rc, stdout=out, stderr=err)

    for e in obj:
        if e["type"] == "cluster":
            if e["name"] != "":
                cluster = e
        elif e["type"] == "node":
            nodes[e["name"]] = e

    ansible_facts["cluster"] = cluster
    ansible_facts["nodes"] = nodes

    mod.exit_json(changed=False, ansible_facts=ansible_facts)


def main():
    run_module()


if __name__ == '__main__':
    main()
