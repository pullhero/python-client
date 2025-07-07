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

from pullhero.vcs.base import VCSOperations
from pullhero.utils.misc import (
    call_ai_api,
    setup_logging,
    clone_repo_with_token,
    ingest_repository,
)
import logging
import sys


setup_logging()


def action_consult(
    vcs_provider: str,
    vcs_token: str,
    vcs_repository: str,
    vcs_change_id: str,
    vcs_change_type: str,
    vcs_base_branch: str,
    vcs_head_branch: str,
    agent: str,
    agent_action: str,
    llm_api_key: str,
    llm_api_host: str,
    llm_api_model: str,
    llm_api_endpoint: str,
) -> None:

    label_to_parse = "consult"
    logging.info(f"Starting document action for {vcs_repository} PR/MR {vcs_change_id}")

    # Validate inputs
    if not vcs_token:
        error_msg = f"{vcs_provider} token required"
        logging.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Initialize provider
        logging.info(f"Initializing {vcs_provider} provider")
        provider = VCSOperations.from_provider(vcs_provider, vcs_token)

        # Clone and analyze repository
        repo_url = (
            f"https://github.com/{vcs_repository}"
            if vcs_provider == "github"
            else f"https://gitlab.com/{vcs_repository}"
        )

        logging.info(f"Cloning repository from {repo_url}")
        clone_repo_with_token(repo_url, vcs_token)

        logging.info("Analyzing repository content")
        summary, tree, repo_content = ingest_repository("/tmp/clone")
        logging.debug(
            f"Repository analysis complete - {len(repo_content.splitlines())} lines of content"
        )

        # Generate and submit prompt
        logging.info("Generating consult prompts")

        issues = provider.get_issues_with_label(vcs_repository, label_to_parse)
        for issue in issues:
            issue_details = provider.get_issue_details(
                repo_identifier=vcs_repository,  # GitHub: "owner/repo", GitLab: "namespace/project"
                issue_id=issue["number"],  # GitHub: issue number, GitLab: issue IID
            )
            comments = provider.get_issue_comments(vcs_repository, str(issue["number"]))

            prompt = get_prompt(
                repo_content, issue_details["title"], issue_details["body"], comments
            )

            logging.debug(f"Prompt generated with {len(prompt.splitlines())} lines")

            logging.info(f"Calling AI API ({llm_api_model}) for review generation")
            try:
                consult_result = call_ai_api(
                    llm_api_host, llm_api_key, llm_api_model, llm_api_endpoint, prompt
                )
                provider.post_comment(
                    vcs_repository, str(issue["number"]), consult_result, "issue"
                )
                logging.info("Comment posted successfully")
                provider.remove_label_from_issue(
                    vcs_repository, str(issue["number"]), label_to_parse
                )
            except Exception as e:
                logging.error("AI API call failed: %s", e)
                sys.exit(1)

        logging.info("Consult updates completed successfully.")

    except Exception as e:
        logging.error(f"Failed to complete consult action: {str(e)}")
        raise


def get_prompt(
    repo_content: str, issue_title: str, issue_body: str, issue_comments: str
) -> str:

    logging.info("Constructing AI review prompt")

    prompt = f"""Consultation Task:
Content:
{repo_content}

Issue title:
{issue_title}

Description:
{issue_body}

Comments:
{issue_comments}

Instructions:
1. Answer the questions or concerns in the issue.
2. Include in the analysis the comments if needed.
3. Provide a detailed and helpful response.
4. Use the repository Summary, Tree, and Content as context.
5. Format the output in Markdown format.
"""
    logging.debug(f"Generated prompt with {len(prompt.splitlines())} lines")
    return prompt
