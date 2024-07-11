#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import time

from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule

RETURN = r'''

'''


def run_module():
    arg_spec = dict(
        enabled=dict(type='bool', required=False, default=False),
        node_name=dict(type='str', required=False, default=None),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)

    node_name = mod.params["node_name"]
    if node_name is None:
        node_name = mod.get_local_node()
    active = mod.get_node_lrm_maintenance(node_name)
    enabled = mod.params["enabled"]

    changed = (active != enabled)

    if changed and not mod.check_mode:
        mod.set_node_lrm_maintenance(node_name, enabled)

        time.sleep(20)
        while mod.get_node_lrm_maintenance(node_name) != enabled and not mod.get_node_lrm_idle(node_name):
            time.sleep(5)

    mod.exit_json(
        changed=changed,
        message=enabled,
        original_message=active
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
