# GNU GENERAL PUBLIC LICENSE
# Version 3, 29 June 2007
#
# Copyright (C) 2025 Carlos Camacho and authors
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
import requests
import sys
from github import Github

def get_pr_diff(github_token, owner, repo, pr_number):
    """Fetches the diff of a pull request."""
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def call_ai_api(provider, api_key, model, prompt):
    """Handles API calls to OpenAI, DeepSeek, or a custom endpoint with proper error handling."""
    try:
        if provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
        elif provider == "deepseek":
            url = "https://api.deepseek.com/v1/chat/completions"
        else:  # Custom endpoint
            url = provider.rstrip("/") + "/v1/chat/completions"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)

        # Attempt to parse JSON response
        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid response format from {provider}: {response.text}") from e

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network/API error while calling {provider}: {str(e)}") from e

    except Exception as e:
        raise RuntimeError(f"Unexpected error in call_ai_api: {str(e)}") from e

def main():
    # Get inputs
    api_key = os.environ['INPUT_API_KEY']
    provider = os.environ.get('INPUT_PROVIDER', 'openai')
    model = os.environ.get('INPUT_MODEL', 'gpt-4-turbo')
    github_token = os.environ['INPUT_GITHUB_TOKEN']

    if not api_key:
        print("Error: API key is missing or empty.")
        sys.exit(1)

    # Get repository context
    with open(os.environ['GITHUB_EVENT_PATH'], 'r') as f:
        event = json.load(f)

    repo_name = os.environ['GITHUB_REPOSITORY']
    owner, repo = repo_name.split('/')

    # Determine PR number based on event type
    if "pull_request" in event:
        pr_number = event["pull_request"]["number"]
    elif "issue" in event and "pull_request" in event["issue"]:
        pr_url = event["issue"]["pull_request"]["url"]
        pr_number = int(pr_url.split("/")[-1])  # Extract PR number from URL
    else:
        print("Error: No valid pull request found in event payload.")
        sys.exit(1)

    print(f"Processing PR #{pr_number}")

    # Get PR diff
    diff = get_pr_diff(github_token, owner, repo, pr_number)

    # Prepare prompt
    prompt = f"""Code Review Task:
PR Changes:
{diff}

Instructions:
1. Analyze changes for quality, bugs, and best practices.
2. Provide concise feedback.
3. End with "Vote: +1" (approve) or "Vote: -1" (request changes)."""

    # Call LLM API
    try:
        review_text = call_ai_api(provider, api_key, model, prompt)
    except Exception as e:
        print(f"PullHero API call failed: {str(e)}")
        sys.exit(1)

    # Determine vote
    vote = "+1" if "+1" in review_text else "-1" if "-1" in review_text else "0"

    # Post comment to GitHub
    g = Github(github_token)
    repo = g.get_repo(f"{owner}/{repo}")
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(
        f"### PullHero Review\n\n{review_text}\n\n**Vote**: {vote}"
    )

    print(f"Review completed with vote: {vote}")

if __name__ == "__main__":
    try:
        print(f"INPUT_API_KEY: {os.environ.get('INPUT_API_KEY', 'MISSING')}")
        print(f"INPUT_PROVIDER: {os.environ.get('INPUT_PROVIDER', 'MISSING')}")
        print(f"INPUT_MODEL: {os.environ.get('INPUT_MODEL', 'MISSING')}")
        print(f"INPUT_GITHUB_TOKEN: {'SET' if os.environ.get('INPUT_GITHUB_TOKEN') else 'MISSING'}")
        main()
    except Exception as e:
        print(f"Action failed: {str(e)}")
        sys.exit(1)
