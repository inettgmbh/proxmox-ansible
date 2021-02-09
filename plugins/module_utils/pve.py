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
