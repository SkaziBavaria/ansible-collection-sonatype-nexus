#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the haxorof.sonatype_nexus project
# MIT License (see COPYING or https://opensource.org/license/mit/)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: nexus_routing_rule
short_description: Manage routing rules
"""

EXAMPLES = r"""
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.haxorof.sonatype_nexus.plugins.module_utils.nexus import (
    NexusHelper,
)


def routing_rule_exists(helper):
    endpoint = "routing-rules"
    info, content = helper.request(
        api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
            url=helper.module.params["url"],
            name=helper.module.params["name"],
        ),
        method="GET",
    )
    rule_exists = (info["status"] in [200])
    if rule_exists:
        content.pop("fetch_url_retries", None)

    return rule_exists, content


def update_routing_rule(helper):
    state = helper.module.params["state"]
    endpoint = "routing-rules"
    info = None
    content = None
    changed = True
    successful = False

    if state == "present":
        no_update_needed = False
        data = {
            "name": helper.module.params["name"],
            "description": helper.module.params["description"],
            "mode": helper.module.params["mode"].upper(),
            "matchers": helper.module.params["matchers"],
        }
        rule_exists, existing_data = routing_rule_exists(helper)
        if rule_exists:
            no_update_needed = all(
                existing_data[k] == v for k, v in data.items() if k in existing_data
            )
            if no_update_needed == False:
                info, content = helper.request(
                    api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
                        url=helper.module.params["url"],
                        name=helper.module.params["name"],
                    ),
                    method="PUT",
                    data=data,
                )
        else:
            info, content = helper.request(
                api_url=(helper.NEXUS_API_ENDPOINTS[endpoint]).format(
                    url=helper.module.params["url"],
                ),
                method="POST",
                data=data,
            )
        if no_update_needed:
            changed = False
            content = existing_data
            successful = True
        elif info["status"] in [204]:
            successful = True

    elif state == "absent":
        info, content = helper.request(
            api_url=(helper.NEXUS_API_ENDPOINTS[endpoint] + "/{name}").format(
                url=helper.module.params["url"],
                name=helper.module.params["name"],
            ),
            method="DELETE",
        )
        if info["status"] in [204]:
            successful = True
        elif info["status"] in [404]:
            # Routing rule not found = OK
            changed = False
            successful = True

    if successful:
        # Routing rule was successfully created/updated/deleted
        content.pop("fetch_url_retries", None)
    else:
        if info["status"] == 400:
            helper.module.fail_json(
                msg="A routing rule with the same name '{routing_rule_name}' already exists or required parameters missing.".format(
                    routing_rule_name=helper.module.params["name"],
                )
            )
        elif info["status"] == 403:
            helper.module.fail_json(
                msg="Insufficient permissions to create/update routing rule '{routing_rule_name}'.".format(
                    routing_rule_name=helper.module.params["name"],
                )
            )
        elif info["status"] != 204:
            helper.module.fail_json(
                msg="Failed to create/update/delete routing rule '{routing_rule_name}', http_status={status}.".format(
                    routing_rule_name=helper.module.params["name"],
                    status=info["status"],
                )
            )

    return content, changed


def main():
    argument_spec = NexusHelper.nexus_argument_spec()
    argument_spec.update(
        name=dict(type="str", required=True, no_log=False),
        description=dict(type="str", required=False, no_log=False),
        mode=dict(
            type="str",
            required=False,
            no_log=False,
            default="block",
            choices=["allow", "ALLOW", "block", "BLOCK"],
        ),
        matchers=dict(
            type="list", elements="str", required=False, no_log=False, default=list()
        ),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[("username", "password")],
    )

    helper = NexusHelper(module)

    # Seed the result dict in the object
    result = dict(
        changed=False,
        name=module.params["name"],
        state=module.params["state"],
        messages=[],
        json={},
    )

    content = {}
    changed = True
    if not module.check_mode:
        content, changed = update_routing_rule(helper)
    result["json"] = content
    result["changed"] = changed

    module.exit_json(**result)


if __name__ == "__main__":
    main()
