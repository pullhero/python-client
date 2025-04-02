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

from github import Github
from pullhero.vcs.base import VCSOperations
import requests
import logging
from typing import Dict, Literal
from typing_extensions import TypedDict

# Type definitions for better type hints
class PRCreationResult(TypedDict):
    url: str
    id: int

class CommentResult(TypedDict):
    id: int

class ReviewResult(TypedDict):
    id: int

class GitHubProvider(VCSOperations):
    """
    GitHub implementation of VCSOperations interface.

    This class provides concrete GitHub-specific implementations for:
    - Pull Request creation
    - PR commenting
    - Code reviews
    - Diff retrieval

    Uses both PyGithub library and direct GitHub API calls where needed.
    """

    def __init__(self, token: str) -> None:
        """
        Initialize GitHub provider with authentication token.

        Args:
            token: GitHub personal access token with appropriate permissions

        Raises:
            ValueError: If token is empty or invalid
        """
        super().__init__(token)
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        if not token:
            self.logger.error("Empty GitHub token provided")
            raise ValueError("GitHub token cannot be empty")
        
        try:
            self.client = Github(self.token)
            self.logger.info("Successfully initialized GitHub client")
        except Exception as e:
            self.logger.error(f"Failed to initialize GitHub client: {str(e)}")
            raise

    def create_pr(
        self,
        repo_name: str,
        title: str,
        body: str,
        base: str,
        head: str
    ) -> PRCreationResult:
        """
        Create a new GitHub Pull Request.

        Args:
            repo_name: Repository name in 'owner/repo' format
            title: Title of the pull request
            body: Description/content of the pull request
            base: Target branch name
            head: Source branch name

        Returns:
            Dictionary containing:
            - 'url': URL of the created PR
            - 'id': PR number

        Raises:
            ValueError: For invalid repository name or missing parameters
            Exception: For GitHub API failures
        """
        self.logger.info(f"Creating PR in {repo_name} from {head} to {base}")
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=body, base=base, head=head)
            
            self.logger.info(f"Successfully created PR #{pr.number}")
            self.logger.debug(f"PR URL: {pr.html_url}")
            
            return {
                "url": pr.html_url,
                "id": pr.number
            }
        except Exception as e:
            self.logger.error(f"Failed to create PR: {str(e)}")
            raise

    def post_comment(
        self,
        repo_name: str,
        pr_id: int,
        body: str
    ) -> CommentResult:
        """
        Post a comment on a GitHub Pull Request.

        Args:
            repo_name: Repository name in 'owner/repo' format
            pr_id: Pull Request number
            body: Comment content

        Returns:
            Dictionary containing:
            - 'id': ID of the created comment

        Raises:
            ValueError: For invalid repository name or PR ID
            Exception: For GitHub API failures
        """
        self.logger.info(f"Posting comment on PR #{pr_id} in {repo_name}")
        self.logger.debug(f"Comment preview: {body[:50]}...")
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_id)
            comment = pr.create_issue_comment(body)
            
            self.logger.info(f"Successfully posted comment with ID {comment.id}")
            return {"id": comment.id}
        except Exception as e:
            self.logger.error(f"Failed to post comment: {str(e)}")
            raise

    def submit_review(
        self,
        repo_name: str,
        pr_id: int,
        comment: str,
        approve: bool = False
    ) -> ReviewResult:
        """
        Submit a formal review for a GitHub Pull Request.

        Args:
            repo_name: Repository name in 'owner/repo' format
            pr_id: Pull Request number
            comment: Review comment content
            approve: Whether to approve the PR (default: False)

        Returns:
            Dictionary containing:
            - 'id': ID of the created review

        Raises:
            ValueError: For invalid repository name or PR ID
            Exception: For GitHub API failures
        """
        review_type: Literal["APPROVE", "COMMENT", "REQUEST_CHANGES"] = \
            "APPROVE" if approve else "COMMENT"
            
        self.logger.info(
            f"Submitting {review_type} review for PR #{pr_id} in {repo_name}"
        )
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_id)
            review = pr.create_review(
                body=comment,
                event=review_type
            )
            
            self.logger.info(
                f"Successfully submitted {review_type} review with ID {review.id}"
            )
            return {"id": review.id}
        except Exception as e:
            self.logger.error(f"Failed to submit review: {str(e)}")
            raise

    def get_pr_diff(
        self,
        repo_name: str,
        pr_id: int
    ) -> str:
        """
        Retrieve the unified diff for a GitHub Pull Request.

        Uses direct GitHub API call to get raw diff format.

        Args:
            repo_name: Repository name in 'owner/repo' format
            pr_id: Pull Request number

        Returns:
            String containing the unified diff text

        Raises:
            ValueError: For invalid repository format
            requests.HTTPError: For API request failures
        """
        self.logger.info(f"Fetching diff for PR #{pr_id} in {repo_name}")
        
        try:
            if '/' not in repo_name:
                error_msg = "repo_name should be in format 'owner/repo'"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            owner, repo = repo_name.split('/', 1)
            url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_id}'
            
            self.logger.debug(f"Making API request to: {url}")
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/vnd.github.v3.diff'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            diff = response.text
            self.logger.info(f"Successfully retrieved diff ({len(diff)} chars)")
            self.logger.debug(f"Diff preview:\n{diff[:200]}...")
            
            return diff
        except requests.HTTPError as he:
            self.logger.error(
                f"API request failed: {he.response.status_code} - {he.response.text}"
            )
            raise
        except Exception as e:
            self.logger.error(f"Failed to get PR diff: {str(e)}")
            raise
