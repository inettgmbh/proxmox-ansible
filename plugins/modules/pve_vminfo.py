#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, inett Gmbh <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

from ansible_collections.inett.pve.plugins.module_utils.tools import replaced
from vm_get_config import run_module as vm_get_config_module

RETURN = r'''

'''


@replaced("Ansible module inett.pve.vm_get_config")
def run_module():
    return vm_get_config_module()


def main():
    run_module()


if __name__ == '__main__':
    main()
