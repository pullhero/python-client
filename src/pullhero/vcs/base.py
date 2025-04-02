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
from typing import Optional, Dict, Literal
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
    def create_pr(
        self,
        title: str,
        body: str,
        base: str,
        head: str
    ) -> Dict[str, str]:
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

    @abstractmethod
    def post_comment(
        self,
        pr_id: str,
        body: str
    ) -> Dict[str, str]:
        """
        Post a comment on an existing pull/merge request.

        Args:
            pr_id: Identifier of the PR/MR
            body: Content of the comment

        Returns:
            Dictionary containing:
            - 'id': Identifier of the created comment

        Raises:
            ValueError: If PR/MR not found
            Exception: For VCS-specific operation failures
        """
        pass

    @abstractmethod
    def submit_review(
        self,
        pr_id: str,
        comment: str,
        approve: bool = False
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
    def get_pr_diff(
        self,
        repo_identifier: str,
        pr_id: str
    ) -> str:
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

    @classmethod
    def from_provider(
        cls,
        provider: Literal["github", "gitlab"],
        token: Optional[str] = None
    ) -> 'VCSOperations':
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

        providers = {
            "github": "GitHubProvider",
            "gitlab": "GitLabProvider"
        }

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
