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
import logging
import argparse
import requests
import sys
from github import Github
from gitingest import ingest

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

def get_pr_diff(github_token, owner, repo, pr_number):
    """Fetches the diff of a pull request."""
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def call_ai_api(provider, api_key, model, prompt):
    """Handles API calls with error handling."""
    url_map = {
        "openai": "https://api.openai.com/v1/chat/completions",
        "deepseek": "https://api.deepseek.com/v1/chat/completions"
    }
    url = url_map.get(provider, provider.rstrip("/") + "/v1/chat/completions")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    return data["choices"][0]["message"]["content"]

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description='Automated PR Review Bot')
    parser.add_argument('--api-key', default=os.environ.get('INPUT_API_KEY'), required=not os.environ.get('INPUT_API_KEY'), help='AI API Key')
    parser.add_argument('--provider', default=os.environ.get('INPUT_PROVIDER', 'openai'), help='LLM Provider')
    parser.add_argument('--model', default=os.environ.get('INPUT_MODEL', 'gpt-4-turbo'), help='LLM Model')
    parser.add_argument('--github-token', default=os.environ.get('INPUT_GITHUB_TOKEN'), required=not os.environ.get('INPUT_GITHUB_TOKEN'), help='GitHub Token')
    parser.add_argument('--event-path', default=os.environ.get('GITHUB_EVENT_PATH'), required=not os.environ.get('GITHUB_EVENT_PATH'), help='GitHub Event JSON Path')
    
    args = parser.parse_args()
    
    with open(args.event_path, 'r') as f:
        event = json.load(f)

    repo_name = os.environ['GITHUB_REPOSITORY']
    owner, repo = repo_name.split('/')

    if "pull_request" in event:
        pr_number = event["pull_request"]["number"]
    elif "issue" in event and "pull_request" in event["issue"]:
        pr_number = int(event["issue"]["pull_request"]["url"].split("/")[-1])
    else:
        logging.error("No valid pull request found in event payload.")
        sys.exit(1)
    
    logging.info(f"Processing PR #{pr_number}")
    
    diff = get_pr_diff(args.github_token, owner, repo, pr_number)
    
    summary, tree, content = ingest(f"https://github.com/{owner}/{repo}.git")
    context = summary
    
    prompt = f"""Code Review Task:
Context:
{context}

PR Changes:
{diff}

Instructions:
1. Analyze changes for quality, bugs, and best practices.
2. Provide concise feedback.
3. End with \"Vote: +1\" (approve) or \"Vote: -1\" (request changes)."""
    
    try:
        review_text = call_ai_api(args.provider, args.api_key, args.model, prompt)
    except Exception as e:
        logging.error(f"AI API call failed: {e}")
        sys.exit(1)
    
    vote = "+1" if "+1" in review_text else "-1" if "-1" in review_text else "0"
    
    g = Github(args.github_token)
    repo = g.get_repo(f"{owner}/{repo}")
    pr = repo.get_pull(pr_number)

    sourcerepo = "**[PullHero](https://github.com/ccamacho/pullhero)**"
    pr.create_issue_comment(f"### PullHero Review\n\n{review_text}\n\n**Vote**: {vote}\n\n{sourcerepo}") 

    logging.info(f"Review completed with vote: {vote}")

if __name__ == "__main__":
    main()
