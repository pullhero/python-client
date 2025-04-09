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
from typing import Dict, Literal, Tuple, Optional, List
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
        self, repo_name: str, title: str, body: str, base: str, head: str
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

            return {"url": pr.html_url, "id": pr.number}
        except Exception as e:
            self.logger.error(f"Failed to create PR: {str(e)}")
            raise

    def post_comment(
        self,
        repo_identifier: str,
        target_id: str,
        body: str,
        target_type: Literal["pr", "issue"] = "pr",
    ) -> Dict[str, str]:
        """
        GitHub implementation to post comments on PRs or Issues.
        """
        self.logger.info(
            f"Posting comment on {target_type.upper()} #{target_id} in {repo_identifier}"
        )
        self.logger.debug(f"Comment preview: {body[:50]}...")

        try:
            repo = self.client.get_repo(repo_identifier)

            if target_type == "pr":
                # For PRs, use create_issue_comment() instead of create_comment()
                target = repo.get_issue(
                    int(target_id)
                )  # Note: Using get_issue for PR comments
                comment = target.create_comment(body)
            elif target_type == "issue":
                target = repo.get_issue(int(target_id))
                comment = target.create_comment(body)
            else:
                raise ValueError(f"Invalid target_type: {target_type}")

            self.logger.info(f"Successfully posted comment with ID {comment.id}")
            return {"id": comment.id, "url": comment.html_url}
        except Exception as e:
            self.logger.error(f"Failed to post comment: {str(e)}")
            raise

    def submit_review(
        self, repo_name: str, pr_id: int, comment: str, approve: bool = False
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
        review_type: Literal["APPROVE", "COMMENT", "REQUEST_CHANGES"] = (
            "APPROVE" if approve else "COMMENT"
        )

        self.logger.info(
            f"Submitting {review_type} review for PR #{pr_id} in {repo_name}"
        )

        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_id)
            review = pr.create_review(body=comment, event=review_type)

            self.logger.info(
                f"Successfully submitted {review_type} review with ID {review.id}"
            )
            return {"id": review.id}
        except Exception as e:
            self.logger.error(f"Failed to submit review: {str(e)}")
            raise

    def get_pr_diff(self, repo_name: str, pr_id: int) -> str:
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
            if "/" not in repo_name:
                error_msg = "repo_name should be in format 'owner/repo'"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            owner, repo = repo_name.split("/", 1)
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_id}"

            self.logger.debug(f"Making API request to: {url}")

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3.diff",
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

    def get_current_readme(
        self, repo_name: str, branch: str
    ) -> Tuple[str, Optional[str]]:
        """
        Fetch the current README.md content from the given branch, if it exists.
        """
        self.logger.info(f"Fetching README.md from {repo_name} on branch {branch}")
        try:
            repo = self.client.get_repo(repo_name)
            readme_file = repo.get_contents("README.md", ref=branch)
            return readme_file.decoded_content.decode("utf-8"), readme_file.sha
        except Exception:
            self.logger.info("No existing README.md found.: {str(e)}")
            return "", None

    def create_or_update_branch(
        self, repo_name: str, branch_name: str, base_branch: str
    ) -> Dict[str, str]:
        """
        Create the branch if it doesn't exist, otherwise return the branch reference.
        """
        self.logger.info(f"Checking/Creating branch {branch_name} from {base_branch}")
        repo = self.client.get_repo(repo_name)

        try:
            branch_ref = repo.get_git_ref(f"heads/{branch_name}")
            self.logger.info(f"Branch '{branch_name}' already exists.")
            return {"ref": branch_name, "status": "exists"}
        except Exception as e:
            main_ref = repo.get_git_ref(f"heads/{base_branch}")
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha
            )
            self.logger.info(f"Branch '{branch_name}' created from '{base_branch}'.")
            self.logger.info(f"Exception '{e}'")
            return {"ref": branch_name, "status": "created"}

    def update_readme_file(
        self, repo_name: str, branch: str, new_content: str
    ) -> Dict[str, str]:
        """
        Update or create the README.md file on the given branch.
        """
        self.logger.info(f"Updating README.md on branch {branch}")
        commit_message = "Update README documentation via PullHero"
        repo = self.client.get_repo(repo_name)

        try:
            readme_content, sha = self.get_current_readme(repo_name, branch)
            if sha:
                result = repo.update_file(
                    path="README.md",
                    message=commit_message,
                    content=new_content,
                    sha=sha,
                    branch=branch,
                )
                self.logger.info("README.md updated on branch '%s'.", branch)
                return {"status": "updated", "sha": result["commit"].sha}
            else:
                result = repo.create_file(
                    path="README.md",
                    message="Create README documentation via PullHero",
                    content=new_content,
                    branch=branch,
                )
                self.logger.info("README.md created on branch '%s'.", branch)
                return {"status": "created", "sha": result["commit"].sha}
        except GithubException as e:
            self.logger.error("Failed to update README.md: %s", e)
            raise

    def create_or_update_pr(
        self, repo_name: str, branch: str, base_branch: str, pr_title: str, pr_body: str
    ) -> Dict[str, str]:
        """
        Create a new pull request or update an existing one from the branch.
        """
        self.logger.info(f"Creating/Updating PR from {branch} to {base_branch}")
        repo = self.client.get_repo(repo_name)

        pulls = repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch}")
        if pulls.totalCount == 0:
            pr = repo.create_pull(
                title=pr_title, body=pr_body, head=branch, base=base_branch
            )
            self.logger.info("Created PR #%s for README update.", pr.number)
            return {"url": pr.html_url, "id": pr.number, "status": "created"}
        else:
            pr = pulls[0]
            self.logger.info("Existing PR #%s found for README update.", pr.number)
            return {"url": pr.html_url, "id": pr.number, "status": "exists"}

    def get_issues_with_label(self, repo_identifier: str, label: str) -> List[Dict]:
        """
        GitHub implementation for getting issues with a specific label.
        """
        self.logger.info(f"Getting issues with label '{label}' from {repo_identifier}")
        try:
            url = (
                f"https://api.github.com/repos/{repo_identifier}/issues?labels={label}"
            )
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get issues with label: {str(e)}")
            raise

    def get_issue_comments(self, repo_identifier: str, issue_id: str) -> List[Dict]:
        """
        GitHub implementation for getting issue comments.
        """
        self.logger.info(f"Getting comments for issue #{issue_id} in {repo_identifier}")
        try:
            # Validate issue_id is numeric
            if not issue_id.isdigit():
                raise ValueError(f"Invalid issue ID: {issue_id}")

            # Get repository and issue
            repo = self.client.get_repo(repo_identifier)
            issue = repo.get_issue(int(issue_id))

            # Get and return comments
            comments = issue.get_comments()
            return [
                {
                    "id": comment.id,
                    "body": comment.body,
                    "created_at": comment.created_at,
                    "user": comment.user.login,
                    "html_url": comment.html_url,
                }
                for comment in comments
            ]

        except ValueError as ve:
            self.logger.error(f"Validation error: {str(ve)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to get issue comments: {str(e)}")
            raise

    def remove_label_from_issue(
        self, repo_identifier: str, issue_number: str, label: str
    ) -> bool:
        """
        GitHub implementation for removing a label from an issue.
        """
        self.logger.info(f"Removing label '{label}' from issue #{issue_number}")
        try:
            url = f"https://api.github.com/repos/{repo_identifier}/issues/{issue_number}/labels/{label}"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.delete(url, headers=headers)

            if response.status_code in (200, 204):
                self.logger.info(f"Successfully removed label '{label}'")
                return True
            else:
                self.logger.error(f"Failed to remove label: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to remove label: {str(e)}")
            raise

    def get_issue_details(self, repo_identifier: str, issue_id: str) -> Dict[str, str]:
        """
        GitHub implementation to fetch issue title and body.
        """
        self.logger.info(f"Fetching details for issue #{issue_id} in {repo_identifier}")
        try:
            repo = self.client.get_repo(repo_identifier)
            issue = repo.get_issue(int(issue_id))

            return {
                "title": issue.title,
                "body": issue.body,
                "url": issue.html_url,
                "state": issue.state,  # e.g., "open" or "closed"
            }
        except Exception as e:
            self.logger.error(f"Failed to fetch issue details: {str(e)}")
            raise

    def get_pr_info_from_comment(
        self, repo_identifier: str, pr_number: str
    ) -> Optional[Dict[str, str]]:
        """
        GitHub implementation to get PR info from repository and PR number.
        """
        self.logger.info(f"Getting PR info for #{pr_number} in {repo_identifier}")
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            url = f"https://api.github.com/repos/{repo_identifier}/pulls/{pr_number}"
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                self.logger.error(f"API call failed: {response.status_code}")
                return None

            pr_data = response.json()
            return {
                "pr_number": str(pr_number),
                "pr_branch": pr_data["head"]["ref"],
                "base_branch": pr_data["base"]["ref"],
                "repo_identifier": repo_identifier,
                "pr_url": pr_data["html_url"],
                "title": pr_data["title"],
                "state": pr_data["state"],
            }
        except Exception as e:
            self.logger.error(f"Failed to get PR info: {str(e)}")
            raise

    def get_pr_files(
        self, repo_identifier: str, pr_number: str
    ) -> List[Dict[str, str]]:
        """
        GitHub implementation to get list of files in a PR.
        """
        self.logger.info(f"Getting files for PR #{pr_number} in {repo_identifier}")
        try:
            repo = self.client.get_repo(repo_identifier)
            pr = repo.get_pull(int(pr_number))

            files = []
            for file in pr.get_files():
                files.append(
                    {
                        "filename": file.filename,
                        "status": file.status,
                        "changes": file.changes,
                        "additions": file.additions,
                        "deletions": file.deletions,
                        "raw_url": file.raw_url,
                    }
                )
            return files
        except Exception as e:
            self.logger.error(f"Failed to get PR files: {str(e)}")
            raise

    def get_current_file(
        self, repo_identifier: str, branch: str, filename: str
    ) -> Tuple[str, Optional[str]]:
        """
        GitHub implementation to get file content.
        """
        self.logger.info(f"Fetching {filename} from {repo_identifier}@{branch}")
        try:
            repo = self.client.get_repo(repo_identifier)
            file_content = repo.get_contents(filename, ref=branch)
            return file_content.decoded_content.decode("utf-8"), file_content.sha
        except GithubException:
            self.logger.info(f"File {filename} not found")
            return "", None
        except Exception as e:
            self.logger.error(f"Failed to get file: {str(e)}")
            raise

    def update_file(
        self, repo_identifier: str, branch: str, filename: str, new_content: str
    ) -> Dict[str, str]:
        """
        GitHub implementation to update/create file.
        """
        self.logger.info(f"Updating {filename} on {repo_identifier}@{branch}")
        try:
            repo = self.client.get_repo(repo_identifier)
            commit_message = f"Update {filename} via PullHero"

            current_content, sha = self.get_current_file(
                repo_identifier, branch, filename
            )
            if sha:
                result = repo.update_file(
                    path=filename,
                    message=commit_message,
                    content=new_content,
                    sha=sha,
                    branch=branch,
                )
                self.logger.info(f"File {filename} updated")
                return {"status": "updated", "sha": result["commit"].sha}
            else:
                result = repo.create_file(
                    path=filename,
                    message=f"Create {filename} via PullHero",
                    content=new_content,
                    branch=branch,
                )
                self.logger.info(f"File {filename} created")
                return {"status": "created", "sha": result["commit"].sha}
        except Exception as e:
            self.logger.error(f"Failed to update file: {str(e)}")
            raise

    def update_pr(self, repo_identifier: str, branch: str) -> Optional[Dict[str, str]]:
        """
        GitHub implementation to get PR info from branch.
        """
        self.logger.info(f"Checking for PR from {branch} in {repo_identifier}")
        try:
            repo = self.client.get_repo(repo_identifier)
            pulls = repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch}")

            if pulls.totalCount == 0:
                self.logger.info("No open PR found")
                return None

            pr = pulls[0]
            return {
                "pr_number": str(pr.number),
                "pr_url": pr.html_url,
                "title": pr.title,
                "state": pr.state,
            }
        except Exception as e:
            self.logger.error(f"Failed to get PR info: {str(e)}")
            raise
