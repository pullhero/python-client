#!/usr/bin/env python3

# GNU GENERAL PUBLIC LICENSE
# Version 3, 29 June 2007
#
# Copyright (C) 2025 authors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Action

from pullhero.utils.misc import get_banner, setup_logging
from pullhero.agents.code import action_code
from pullhero.agents.review import action_review
from pullhero.agents.consult import action_consult
from pullhero.agents.document import action_document
from pullhero.__about__ import __name__, __description__, __version__

import json
import logging
import os
import sys

from pkg_resources import get_distribution


class JsonVersionAction(Action):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        dist = get_distribution("pullhero")
        version_info = {
            "name": __name__,
            "description": __description__,
            "version": __version__,
        }
        print(json.dumps(version_info, indent=2))
        sys.exit(0)


def main():
    """
    Application's entry point.

    Here, application's settings are read from the command line,
    environment variables and CRD. Then, retrieving and processing
    of Kubernetes events are initiated.
    """
    setup_logging()

    # First stage: Only parse banner/version
    base_parser = ArgumentParser(add_help=False)
    base_parser.add_argument(
        "-b", "--banner", action="store_true", help="Print PullHero's banner"
    )
    base_parser.add_argument(
        "-v",
        "--version",
        action=JsonVersionAction,
        help="Show PullHero's version in a JSON object",
    )

    # Parse known args first to check for early-exit options
    args, _ = base_parser.parse_known_args()

    if args.banner:
        print(get_banner())
        return  # Exit after handling banner

    parser = ArgumentParser(
        description="PullHero your agentic asistant",
        formatter_class=ArgumentDefaultsHelpFormatter,
        epilog="Note: All API requests (for any provider) will use the endpoint '/v1/chat/completions'.",
    )

    # Specific to the VCS (GitHub OR Gitlab)
    parser.add_argument(
        "--vcs-provider",
        required=not os.environ.get("VCS_PROVIDER"),
        default=os.environ.get("VCS_PROVIDER"),
        help="VCS Provider",
    )
    parser.add_argument(
        "--vcs-token",
        required=not os.environ.get("VCS_TOKEN"),
        default=os.environ.get("VCS_TOKEN"),
        help="VCS Token",
    )
    parser.add_argument(
        "--vcs-repository",
        required=not os.environ.get("VCS_REPOSITORY"),
        default=os.environ.get("VCS_REPOSITORY"),
        help="VCS Repository",
    )
    parser.add_argument(
        "--vcs-change-id",
        required=not os.environ.get("VCS_CHANGE_ID"),
        default=os.environ.get("VCS_CHANGE_ID"),
        help="VCS change, this can be the ID of a PR or an issue",
    )
    parser.add_argument(
        "--vcs-change-type",
        required=not os.environ.get("VCS_CHANGE_TYPE"),
        default=os.environ.get("VCS_CHANGE_TYPE"),
        help="VCS change type, this can be the an issue, pr, mr...",
    )
    parser.add_argument(
        "--vcs-base-branch",
        required=not os.environ.get("VCS_BASE_BRANCH"),
        default=os.environ.get("VCS_BASE_BRANCH"),
        help="VCS base branch",
    )
    parser.add_argument(
        "--vcs-head-branch",
        required=not os.environ.get("VCS_HEAD_BRANCH"),
        default=os.environ.get("VCS_HEAD_BRANCH"),
        help="VCS head branch",
    )

    # Specific to PullHero (How to interact with the agents)
    parser.add_argument(
        "--agent",
        required=not os.environ.get("ACTION"),
        default=os.environ.get("ACTION"),
        choices=["code", "review", "consult", "document"],
        help="PullHero agent (required, options: %(choices)s)",
    )
    parser.add_argument(
        "--agent-action",
        required=not os.environ.get("REVIEW_ACTION"),
        default=os.environ.get("REVIEW_ACTION"),
        choices=["comment", "review"],
        help="PullHero agent action (required, options: %(choices)s)",
    )

    # Specific to the endpoint parameters (How to interact with the LLM providers)
    parser.add_argument(
        "--llm-api-key",
        required=not os.environ.get("LLM_API_KEY"),
        default=os.environ.get("LLM_API_KEY"),
        help="AI API Key",
    )
    parser.add_argument(
        "--llm-api-host",
        required=not os.environ.get("LLM_API_HOST"),
        default=os.environ.get("LLM_API_HOST", "api.openai.com"),
        help="LLM API HOST, e.g., api.openai.com",
    )
    parser.add_argument(
        "--llm-api-model",
        required=not os.environ.get("LLM_API_MODEL"),
        default=os.environ.get("LLM_API_MODEL", "gpt-4o-mini"),
        help="LLM Model, e.g., gpt-4o-mini",
    )
    parser.add_argument(
        "--llm-api-endpoint",
        default=os.environ.get("LLM_API_ENDPOINT", "/v1/chat/completions"),
        help="LLM API Endpoint, default: /v1/chat/completions",
    )

    args = parser.parse_args()

    common_params = {
        "vcs_provider": args.vcs_provider,
        "vcs_token": args.vcs_token,
        "vcs_repository": args.vcs_repository,
        "vcs_change_id": args.vcs_change_id,
        "vcs_change_type": args.vcs_change_type,
        "vcs_base_branch": args.vcs_base_branch,
        "vcs_head_branch": args.vcs_head_branch,
        "agent": args.agent,
        "agent_action": args.agent_action,
        "llm_api_key": args.llm_api_key,
        "llm_api_host": args.llm_api_host,
        "llm_api_model": args.llm_api_model,
        "llm_api_endpoint": args.llm_api_endpoint,
    }

    logging.info(f"PullHero v{__version__}")

    if args.agent == "code":
        action_code(**common_params)
    elif args.agent == "review":
        action_review(**common_params)
    elif args.agent == "consult":
        action_consult(**common_params)
    elif args.agent == "document":
        action_document(**common_params)
    else:
        print("Unsupported action provided.")
        exit(1)
