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

    rc, out, err, obj = mod.query_json(
        method="get",
        url="/version",
    )
    if rc == 0:
        ret = dict(
            pve_release=obj["release"],
            pve_version=obj["version"],
            pve_repoid=obj["repoid"],
        )
        mod.exit_json(ansible_facts=ret)
    else:
        mod.fail_json("API query failed", rc=rc, stdout=out, stderr=err)


def main():
    run_module()


if __name__ == '__main__':
    main()
