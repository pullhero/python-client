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

import os
import json
import logging
import argparse
import requests
import sys
from github import Github, GithubException
from gitingest import ingest
import pygit2
from pathlib import Path


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def clone_repo_with_token(repo_url, local_path, github_token):
    """
    Clone the repository using the GITHUB_TOKEN for authentication with pygit2.
    """

    # Define the callback function for credentials (used by pygit2 for authentication)
    def credentials_callback(url, username_from_url, allowed_types):
        """
        Provide authentication credentials (username and password/token) for Git.
        """
        if github_token:
            return pygit2.UserPass(
                "x-access-token", github_token
            )  # Use GitHub token for authentication
        else:
            raise ValueError("GITHUB_TOKEN is not set")

    try:
        # Perform the clone using pygit2 and pass the credentials callback for authentication
        logging.info(f"Cloning repository from {repo_url} to {local_path}")

        # Create a RemoteCallbacks object and pass it to pygit2
        remote_callbacks = pygit2.RemoteCallbacks(credentials=credentials_callback)

        # Set the callbacks to handle authentication
        pygit2.clone_repository(repo_url, local_path, callbacks=remote_callbacks)

        logging.info(f"Repository cloned to {local_path}")
    except Exception as e:
        logging.error(f"Error cloning the repository: {e}")
        raise


def get_pr_info_from_comment(github_token):
    if not github_token:
        logging.error("GITHUB_TOKEN not found in environment variables")

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        logging.error("GITHUB_EVENT_PATH not found")

    with open(event_path, "r") as f:
        event_data = json.load(f)

    if "issue" not in event_data or "pull_request" not in event_data["issue"]:
        print("This comment is not on a pull request")
        return None, None, None

    # Get the PR number from the issue object
    pr_number = event_data["issue"]["number"]

    # Get PR details from GitHub API
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Call the GitHub API to get PR details
    url = f"https://api.github.com/repos/{github_repository}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"API call failed: {response.status_code} - {response.text}")
        return pr_number, None, None

    pr_data = response.json()
    pr_branch = pr_data["head"]["ref"]  # Source branch of the PR
    base_branch = pr_data["base"]["ref"]  # Target branch of the PR

    return pr_number, pr_branch, base_branch


def create_or_update_pr(repo, branch, base_branch, pr_title="", pr_body=""):
    """Create a new pull request or update an existing one from the branch."""
    pulls = repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch}")
    if pulls.totalCount == 0:
        pr = repo.create_pull(
            title=pr_title, body=pr_body, head=branch, base=base_branch
        )
        logging.info("Created PR #%s for code improvements.", pr.number)
    else:
        pr = pulls[0]
        logging.info("Existing PR #%s found for code improvements.", pr.number)
    return pr


def get_current_file(repo, branch, filename):
    """Fetch the current file content from the given branch, if it exists."""
    try:
        file_content = repo.get_contents(filename, ref=branch)
        return file_content.decoded_content.decode("utf-8"), file_content.sha
    except GithubException:
        logging.info(f"No existing {filename} found.")
        return "", None


def call_ai_api(api_host, api_key, api_model, prompt):
    """Handles API calls with error handling."""
    url = f"https://{api_host}/v1/chat/completions"
    payload = {
        "model": api_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def update_file(repo, branch, filename, new_content):
    """Update or create the file on the given branch."""
    commit_message = f"Update {filename} via PullHero"
    try:
        file_content, sha = get_current_file(repo, branch, filename)
        if sha:
            repo.update_file(
                path=filename,
                message=commit_message,
                content=new_content,
                sha=sha,
                branch=branch,
            )
            logging.info(f"{filename} updated on branch '{branch}'.")
    except GithubException as e:
        # if file not exists
        logging.error("Failed to update file: %s", e)
        sys.exit(1)


def update_pr(repo, branch):
    """Update the existing PR from the branch."""
    pulls = repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch}")
    if pulls.totalCount == 0:
        logging.info("PR not found, something went wrong.")
    else:
        pr = pulls[0]
        logging.info("Existing PR #%s found for file update.", pr.number)
    return pr


def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="PullHero automatic code updates",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Note: All API requests (for any provider) will use the endpoint '/v1/chat/completions'.",
    )
    # GitHub specific parameters
    parser.add_argument(
        "--github-token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub Token"
    )
    # LLM endpoint specific parameters
    parser.add_argument(
        "--api-key", default=os.environ.get("LLM_API_KEY"), help="AI API Key"
    )
    parser.add_argument(
        "--api-host",
        default=os.environ.get("LLM_API_HOST", "api.openai.com"),
        help="LLM API HOST, e.g., api.openai.com",
    )
    parser.add_argument(
        "--api-model",
        default=os.environ.get("LLM_API_MODEL", "gpt-4-turbo"),
        help="LLM Model, e.g., gpt-4-turbo",
    )

    args = parser.parse_args()

    # Get repository info from the environment
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_name:
        logging.error("GITHUB_REPOSITORY environment variable is not set.")
        sys.exit(1)
    owner, repo_str = repo_name.split("/")

    # Initialize GitHub API
    g = Github(args.github_token)
    try:
        repo = g.get_repo(f"{owner}/{repo_str}")
    except GithubException as e:
        logging.error("Error accessing repository: %s", e)
        sys.exit(1)

    for key, value in os.environ.items():
        print(f"{key}: {value}")

    pr_number, pr_branch, base_branch = get_pr_info_from_comment(args.github_token)
    improvements_branch = f"{pr_branch}-pullhero-improvements"  # XXX check

    if not pr_branch:
        logging.error(
            f"GHA environment variables not set, are you running a GHA Workflow?"
        )
        # sys.exit(1)

    local_repo_path = "/tmp/clone"
    repo_url = f"https://github.com/{owner}/{repo_str}.git"
    clone_repo_with_token(repo_url, local_repo_path, args.github_token)

    # Use the ingest method to get repository context (e.g., summary of code)
    summary, tree, content = ingest(f"{local_repo_path}")
    context = content  # You might also combine tree/summary if needed.

    pr_title = "PullHero Code Improvements for PR whatever"
    pr_body = "Some description of PR body..."

    # Create the improvements PR targeting the original PR branch
    create_or_update_pr(repo, improvements_branch, pr_branch, pr_title, pr_body)

    local_prompt = Path(f"{local_repo_path}/.pullhero.prompt")

    pull_request = repo.get_pull(pr_number)
    for file in pull_request.get_files():
        filename = file.name
        # TODO evaluate extensions and skip if match
        # for now, only edit one test file
        if filename not in ["test_file.py"]:
            continue

        current_file_content, _ = get_current_file(repo, pr_branch, filename)

        if local_prompt.is_file():
            logging.info("Found local prompt file")
            with open(local_prompt, "r") as f:
                prompt_template = f.read()

            prompt = prompt_template.format(
                code_context=context,
                current_code=current_file_content,
            )

        else:
            # Default prompt
            prompt = f"""Code Improvement Task:
Context of the repository:
{context}

Current code to improve:
{current_file_content}

Instructions:
Based on the above repository context and current code, generate an improved version of this code.
Focus on enhancing readability, optimizing performance, and applying best practices.
Follow these principles:
- Maintain the original functionality while improving implementation
- Add appropriate comments to explain complex logic
- Apply consistent formatting and naming conventions
- Reduce code duplication and complexity
- Ensure proper error handling where appropriate
- Consider modularity and reusability

Output only the complete improved code without explanations.
"""
        logging.info("Sending prompt to AI API to generate improved code...")
        try:
            new_content = call_ai_api(
                args.api_host, args.api_key, args.api_model, prompt
            )
        except Exception as e:
            logging.error("AI API call failed: %s", e)
            sys.exit(1)

        # Update the file on the branch with the LLM response
        update_file(repo, pr_branch, filename, new_content)

        # Update the current pull request
        create_or_update_pr(repo, improvements_branch, pr_branch)

        logging.info(f"{filename} update process completed successfully.")


if __name__ == "__main__":
    main()
