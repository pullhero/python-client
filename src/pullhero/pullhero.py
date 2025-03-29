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

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from pullhero.utils.misc import get_banner, setup_logging
from pullhero.agents.code import action_code
from pullhero.agents.review import action_review
from pullhero.agents.consult import action_consult
from pullhero.agents.document import action_document

from pkg_resources import get_distribution
import os

pullhero_version = get_distribution('pullhero').version


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
        '-b', '--banner',
        action='store_true',
        help="Print PullHero's banner"
    )
    base_parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'pullhero {pullhero_version}'
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

    # Specific to PullHero
    parser.add_argument(
        "--pullhero-github-api-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub API Token"
    )
    parser.add_argument(
        "--pullhero-action",
        required=not os.environ.get("PULLHERO_ACTION"),
        default=os.environ.get("PULLHERO_ACTION"),
        choices=["code", "review", "consult", "document"],
        help="PullHero action (required, options: %(choices)s)",
    )
    parser.add_argument(
        "--pullhero-review-action",
        required=not os.environ.get("PULLHERO_REVIEW_ACTION"),
        default=os.environ.get("PULLHERO_REVIEW_ACTION"),
        choices=["comment", "review"],
        help="PullHero review action (required, options: %(choices)s)",
    )

    # LLM endpoint specific parameters
    parser.add_argument(
        "--llm-api-key",
        required=not os.environ.get("LLM_API_KEY"),
        default=os.environ.get("LLM_API_KEY"),
        help="AI API Key"
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

    args = parser.parse_args()

    common_params = {
        "github_token": args.pullhero_github_api_token,
        "review_action": args.pullhero_review_action,
        "llm_api_key": args.llm_api_key,
        "llm_api_host": args.llm_api_host,
        "llm_api_model": args.llm_api_model
    }

    if args.pullhero_action == "code":
        action_code(**common_params)
    elif args.pullhero_action == "review":
        action_review(**common_params)
    elif args.pullhero_action == "consult":
        action_consult(**common_params)
    elif args.pullhero_action == "document":
        action_document(**common_params)
    else:
        print("Unsupported action provided.")
        exit(1)
