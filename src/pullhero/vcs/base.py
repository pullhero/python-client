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

from abc import ABC, abstractmethod
from typing import Optional, Dict, Tuple, Literal, List
import logging


class VCSOperations(ABC):
    """
    Abstract Base Class defining Version Control System operations interface.

    This class provides an abstract interface for common VCS operations
    that must be implemented by concrete providers (GitHub, GitLab, etc.).

    Key Features:
    - Standardized interface for PR/MR operations
    - Factory method for provider instantiation
    - Type-hinted method signatures
    - Comprehensive documentation

    Implementations must support:
    - Pull/Merge Request creation
    - PR/MR commenting
    - Formal code reviews
    - Diff retrieval
    """

    def __init__(self, token: str) -> None:
        """
        Initialize VCS provider with authentication token.

        Args:
            token: Authentication token for the VCS provider
        """
        self.token = token
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.info("Initializing VCS provider")

    @abstractmethod
    def create_pr(self, title: str, body: str, base: str, head: str) -> Dict[str, str]:
        """
        Create a new pull/merge request.

        Args:
            title: Title of the PR/MR
            body: Description/content of the PR/MR
            base: Target branch name
            head: Source branch name

        Returns:
            Dictionary containing:
            - 'url': Web URL of the created PR/MR
            - 'id': Identifier of the created PR/MR

        Raises:
            ValueError: If required parameters are missing
            Exception: For VCS-specific operation failures
        """
        pass

    def post_comment(
        self,
        repo_identifier: str,
        target_id: str,
        body: str,
        target_type: Literal["pr", "issue"] = "pr",
    ) -> Dict[str, str]:
        """
        Post a comment on a Pull Request or Issue.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            target_id: PR/MR number or Issue ID
            body: Comment content
            target_type: Type of target ("pr" or "issue")

        Returns:
            Dictionary containing:
            - 'id': ID of the created comment
            - 'url': URL to the comment (if available)

        Raises:
            ValueError: For invalid repository or target ID
            Exception: For VCS-specific operation failures
        """
        pass

    @abstractmethod
    def submit_review(
        self, pr_id: str, comment: str, approve: bool = False
    ) -> Dict[str, str]:
        """
        Submit a formal review for a pull/merge request.

        Args:
            pr_id: Identifier of the PR/MR
            comment: Review comment content
            approve: Whether to approve the changes (default: False)

        Returns:
            Dictionary containing:
            - 'id': Identifier of the created review
            - 'approved': Whether approval was given (GitLab only)

        Raises:
            ValueError: If PR/MR not found
            Exception: For VCS-specific operation failures
        """
        pass

    @abstractmethod
    def get_pr_diff(self, repo_identifier: str, pr_id: str) -> str:
        """
        Retrieve the unified diff for a pull/merge request.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            pr_id: PR/MR identifier

        Returns:
            String containing the unified diff text

        Raises:
            ValueError: If PR/MR not found
            Exception: For VCS-specific operation failures
        """
        pass

    @abstractmethod
    def get_current_readme(
        self, repo_identifier: str, branch: str
    ) -> Tuple[str, Optional[str]]:
        """
        Fetch the current README.md content from the given branch, if it exists.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            branch: Branch name to check for README.md

        Returns:
            Tuple containing:
            - README content as string (empty if not found)
            - SHA/ID of the file (None if not found)
        """
        pass

    @abstractmethod
    def create_or_update_branch(
        self, repo_identifier: str, branch_name: str, base_branch: str
    ) -> Dict[str, str]:
        """
        Create the branch if it doesn't exist, otherwise return the branch reference.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            branch_name: Name of the branch to create/check
            base_branch: Name of the base branch to create from

        Returns:
            Dictionary containing:
            - 'ref': Reference to the branch
            - 'status': 'created' or 'exists'
        """
        pass

    @abstractmethod
    def update_readme_file(
        self, repo_identifier: str, branch: str, new_content: str
    ) -> Dict[str, str]:
        """
        Update or create the README.md file on the given branch.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            branch: Branch name to update README.md on
            new_content: New content for README.md

        Returns:
            Dictionary containing:
            - 'status': 'created' or 'updated'
            - 'sha': New SHA/ID of the file
        """
        pass

    @abstractmethod
    def create_or_update_pr(
        self,
        repo_identifier: str,
        branch: str,
        base_branch: str,
        pr_title: str,
        pr_body: str,
    ) -> Dict[str, str]:
        """
        Create a new pull request or update an existing one from the branch.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            branch: Source branch name
            base_branch: Target branch name
            pr_title: Title of the pull request
            pr_body: Body/description of the pull request

        Returns:
            Dictionary containing:
            - 'url': URL of the PR/MR
            - 'id': ID of the PR/MR
            - 'status': 'created' or 'exists'
        """
        pass

    @abstractmethod
    def get_issues_with_label(self, repo_identifier: str, label: str) -> List[Dict]:
        """
        Retrieve all issues with a specific label.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            label: Label to filter issues by

        Returns:
            List of issue dictionaries with their details

        Raises:
            ValueError: If repository is invalid or label is empty
            Exception: For VCS-specific operation failures
        """
        pass

    @abstractmethod
    def get_issue_comments(self, repo_identifier: str, issue_id: str) -> List[Dict]:
        """
        Retrieve all comments for a specific issue.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            issue_id: Number/ID of the issue

        Returns:
            List of comment dictionaries with their details

        Raises:
            ValueError: If repository or issue identifier is invalid
            Exception: For VCS-specific operation failures
        """
        pass

    @abstractmethod
    def remove_label_from_issue(
        self, repo_identifier: str, issue_number: str, label: str
    ) -> bool:
        """
        Remove a label from a specific issue.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            issue_number: Number/ID of the issue
            label: Label to remove

        Returns:
            True if removal was successful, False otherwise

        Raises:
            ValueError: If any parameter is invalid
            Exception: For VCS-specific operation failures
        """
        pass

    @abstractmethod
    def get_issue_details(self, repo_identifier: str, issue_id: str) -> Dict[str, str]:
        """
        Retrieve the title and body of a specific issue.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            issue_id: Number/ID of the issue (GitHub: number, GitLab: IID)

        Returns:
            Dictionary containing:
            - 'title': Issue title
            - 'body': Issue description/body
            - 'url': URL to the issue (optional)

        Raises:
            ValueError: If repository or issue ID is invalid
            Exception: For VCS-specific operation failures
        """
        pass

    @abstractmethod
    def get_pr_info_from_comment(
        self, repo_identifier: str, pr_number: str
    ) -> Optional[Dict[str, str]]:
        """
        Get PR/MR information from repository and PR number.

        Args:
            repo_identifier: Repository identifier (format varies by provider)
            pr_number: PR/MR number

        Returns:
            Dictionary containing:
            - 'pr_number': PR/MR number
            - 'pr_branch': Source branch
            - 'base_branch': Target branch
            - 'repo_identifier': Repository identifier
            None if PR not found

        Raises:
            Exception: For VCS-specific operation failures
        """
        pass

    @abstractmethod
    def get_pr_files(
        self, repo_identifier: str, pr_number: str
    ) -> List[Dict[str, str]]:
        """
        Get list of files modified in a PR/MR.

        Args:
            repo_identifier: Repository identifier
            pr_number: PR/MR number

        Returns:
            List of dictionaries with file information:
            - 'filename': Path to file
            - 'status': Modification status (added, modified, removed)
            - 'changes': Number of changes
            - 'additions': Lines added
            - 'deletions': Lines removed
        """
        pass

    @abstractmethod
    def get_current_file(
        self, repo_identifier: str, branch: str, filename: str
    ) -> Tuple[str, Optional[str]]:
        """
        Fetch the current file content from the given branch.

        Args:
            repo_identifier: Repository identifier
            branch: Branch name
            filename: Path to the file

        Returns:
            Tuple of (file_content, file_sha) or ("", None) if file doesn't exist
        """
        pass

    @abstractmethod
    def update_file(
        self, repo_identifier: str, branch: str, filename: str, new_content: str
    ) -> Dict[str, str]:
        """
        Update or create a file on the given branch.

        Args:
            repo_identifier: Repository identifier
            branch: Branch name
            filename: Path to the file
            new_content: New file content

        Returns:
            Dictionary with operation status and commit SHA
        """
        pass

    @abstractmethod
    def update_pr(self, repo_identifier: str, branch: str) -> Dict[str, str]:
        """
        Get information about an existing PR from a branch.

        Args:
            repo_identifier: Repository identifier
            branch: Source branch name

        Returns:
            Dictionary with PR information or None if not found
        """
        pass

    @classmethod
    def from_provider(
        cls, provider: Literal["github", "gitlab"], token: Optional[str] = None
    ) -> "VCSOperations":
        """
        Factory method to instantiate the appropriate VCS provider.

        Args:
            provider: VCS provider name ('github' or 'gitlab')
            token: Optional authentication token

        Returns:
            Concrete VCSOperations instance for the specified provider

        Raises:
            ValueError: If provider is unsupported or token is missing
            ImportError: If required provider module cannot be imported

        Example:
            >>> vcs = VCSOperations.from_provider("github", "ghp_abc123")
        """
        logger = logging.getLogger("VCSFactory")
        logger.info(f"Initializing {provider} provider")

        providers = {"github": "GitHubProvider", "gitlab": "GitLabProvider"}

        if provider not in providers:
            error_msg = f"Unsupported provider: {provider}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            if provider == "github":
                from pullhero.vcs.github import GitHubProvider

                logger.debug("Successfully imported GitHub provider")
                return GitHubProvider(token)
            elif provider == "gitlab":
                from pullhero.vcs.gitlab import GitLabProvider

                logger.debug("Successfully imported GitLab provider")
                return GitLabProvider(token)
        except ImportError as ie:
            logger.error(f"Failed to import {provider} provider: {str(ie)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing {provider}: {str(e)}")
            raise
