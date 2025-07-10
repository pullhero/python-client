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

import sys
import os
import shutil
import logging
import requests
from gitingest import ingest
import pygit2
from typing import Tuple, Optional
from pathlib import Path
from pullhero.__about__ import __version__


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_banner():
    """
    Get banner method.

    This method prints
    pullhero's banner.
    """
    # Big Money-nw
    # JS Stick Letters
    banner = f"""
$$$$$$$\  $$\   $$\ $$\       $$\       $$\   $$\ $$$$$$$$\ $$$$$$$\   $$$$$$\
$$  __$$\ $$ |  $$ |$$ |      $$ |      $$ |  $$ |$$  _____|$$  __$$\ $$  __$$\
$$ |  $$ |$$ |  $$ |$$ |      $$ |      $$ |  $$ |$$ |      $$ |  $$ |$$ /  $$ |
$$$$$$$  |$$ |  $$ |$$ |      $$ |      $$$$$$$$ |$$$$$\    $$$$$$$  |$$ |  $$ |
$$  ____/ $$ |  $$ |$$ |      $$ |      $$  __$$ |$$  __|   $$  __$$< $$ |  $$ |
$$ |      $$ |  $$ |$$ |      $$ |      $$ |  $$ |$$ |      $$ |  $$ |$$ |  $$ |
$$ |      \$$$$$$  |$$$$$$$$\ $$$$$$$$\ $$ |  $$ |$$$$$$$$\ $$ |  $$ | $$$$$$  |
\__|       \______/ \________|\________|\__|  \__|\________|\__|  \__| \______/
        __      __         __  ___   ___ __         __  __   _____      ___
    \ //  \|  ||__)    /\ / _`|__ |\ |||/  `    /\ /__`/__`|/__`| /\ |\ ||
     | \__/\__/|  \   /~~\\\\__>|___| \|||\__,   /~~\.__/.__/|.__/|/~~\| \||

v{__version__}
"""
    return banner


#
# THis is external because is not specific to a VCS we will just clone a Git repo (private or public)
#


def clone_repo_with_token(repo_url: str, vcs_token: str) -> None:
    """
    Clone a repository using authentication token with pygit2.

    This function:
    1. Ensures the target directory (/tmp/clone) is clean
    2. Sets up authentication callbacks
    3. Performs the git clone operation
    4. Handles errors and provides detailed logging

    Parameters:
    -----------
    repo_url : str
        The URL of the repository to clone (e.g., 'https://github.com/owner/repo.git')
    vcs_token : str
        The authentication token for the VCS provider

    Returns:
    --------
    None

    Raises:
    -------
    ValueError
        If the VCS token is missing or invalid
    pygit2.GitError
        If the clone operation fails
    Exception
        For general filesystem or permission errors

    Example:
    --------
    >>> clone_repo_with_token(
    ...     repo_url="https://github.com/owner/repo.git",
    ...     vcs_token="ghp_abc123..."
    ... )
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting repository clone from {repo_url}")

    def credentials_callback(
        url: str, username_from_url: Optional[str], allowed_types: int
    ) -> pygit2.UserPass:
        """
        Authentication callback for pygit2 clone operation.

        Args:
            url: Repository URL being accessed
            username_from_url: Username extracted from URL (if any)
            allowed_types: Bitmask of allowed credential types

        Returns:
            Configured UserPass credentials object

        Raises:
            ValueError: If no token is provided
        """
        if not vcs_token:
            error_msg = "VCS token is required for authentication"
            logger.error(error_msg)
            raise ValueError(error_msg)
        return pygit2.UserPass("x-access-token", vcs_token)

    try:
        clone_dir = "/tmp/clone"

        # Clean up existing directory if present
        if os.path.exists(clone_dir):
            logger.info(f"Removing existing directory: {clone_dir}")
            shutil.rmtree(clone_dir)

        # Create fresh directory
        logger.info(f"Creating clean directory: {clone_dir}")
        os.makedirs(clone_dir, exist_ok=True)

        # Configure clone options
        logger.debug("Configuring clone options with authentication")
        callbacks = pygit2.RemoteCallbacks(credentials=credentials_callback)

        # Perform clone
        logger.info(f"Cloning repository to {clone_dir}")
        pygit2.clone_repository(url=repo_url, path=clone_dir, callbacks=callbacks)

        logger.info(f"Successfully cloned repository to {clone_dir}")

    except pygit2.GitError as ge:
        logger.error(f"Git operation failed: {str(ge)}")
        raise
    except OSError as oe:
        logger.error(f"Filesystem error: {str(oe)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during clone: {str(e)}")
        raise


def ingest_repository(local_repo_path: str) -> Tuple[str, str, str]:
    """
    Analyze and ingest repository content for review processing.

    Processes a local repository to generate:
    - Summary metadata
    - File tree structure
    - File content dictionary

    Parameters:
    -----------
    local_repo_path : str
        Path to the local repository directory

    Returns:
    --------
    Tuple containing:
        - summary (str): Repository metadata summary
        - tree (dict): Hierarchical file structure
        - content (dict): Key-value pairs of file paths and content

    Raises:
    -------
    ValueError
        If the path is invalid or repository is inaccessible
    Exception
        For any processing failures

    Example:
    --------
    >>> summary, tree, content = ingest_repository(
    ...     local_repo_path="/tmp/clone"
    ... )
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting repository ingestion from {local_repo_path}")

    try:
        # Validate input path
        abs_path = Path(local_repo_path).absolute()
        if not abs_path.exists():
            error_msg = f"Repository path does not exist: {abs_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not abs_path.is_dir():
            error_msg = f"Path is not a directory: {abs_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Processing repository at {abs_path}")

        # Perform ingestion (assuming ingest() is defined elsewhere)
        summary, tree, content = ingest(str(abs_path))

        logger.info(f"Ingestion complete - {len(content)} files processed")
        logger.debug(f"Summary: {summary[:100]}...")
        logger.debug(f"Tree structure: {str(tree)[:200]}...")

        return summary, tree, content

    except Exception as e:
        logger.error(f"Repository ingestion failed: {str(e)}")
        raise


def call_ai_api(
    api_host: str, api_key: str, api_model: str, api_endpoint: str, prompt: str, timeout: int = 360
) -> str:
    """
    Make an API call to an AI service for code review analysis.

    Parameters:
    -----------
    api_host : str
        Base hostname for the API (e.g., 'api.openai.com')
    api_key : str
        Authentication API key
    api_model : str
        Model identifier to use (e.g., 'gpt-4')
    prompt : str
        The review prompt to send to the AI
    timeout : int, optional
        Request timeout in seconds (default: 360)

    Returns:
    --------
    str
        The AI-generated response content

    Raises:
    -------
    requests.HTTPError
        For API request failures
    ValueError
        For invalid inputs or missing parameters
    Exception
        For general request failures

    Example:
    --------
    >>> response = call_ai_api(
    ...     api_host="api.openai.com",
    ...     api_key="sk-abc123...",
    ...     api_model="gpt-4",
    ...     prompt="Review this code..."
    ... )
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Initiating AI API call to {api_host} with model {api_model}")

    try:
        # Validate inputs
        if not all([api_host, api_key, api_model, prompt]):
            error_msg = "Missing required API parameters"
            logger.error(error_msg)
            raise ValueError(error_msg)

        url = f"https://{api_host}{api_endpoint}"
        payload = {
            "model": api_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7,
        }
        
        # Convert timeout to milliseconds for APIcast
        timeout_ms = timeout * 1000
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-APIcast-Timeout": str(timeout_ms),
            "X-APIcast-Upstream-Timeout": str(timeout_ms),
            "X-APIcast-Request-Timeout": str(timeout_ms),
            "X-Request-Timeout": str(timeout_ms),
            "Connection": "keep-alive",
            "Keep-Alive": f"timeout={timeout}"
        }

        logger.debug(f"Sending request to {url}")
        logger.debug(f"Payload size: {len(prompt)} characters")
        prompt_preview = "\n".join(prompt.split("\n")[:20])
        logger.debug(f"Prompt preview (first 20 lines):\n{prompt_preview}")
        logger.debug(f"Using timeout settings: {timeout} seconds ({timeout_ms} ms)")

        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"Response: {data}")
        result = data["choices"][0]["message"]["content"]

        logger.info("AI API call successful")
        logger.debug(f"Response length: {len(result)} characters")

        return result

    except requests.HTTPError as he:
        logger.error(
            f"API request failed: {he.response.status_code} - {he.response.text}"
        )
        raise he
    except requests.Timeout:
        logger.error("API request timed out")
        raise
    except Exception as e:
        logger.error(f"Unexpected API error: {str(e)}")
        raise
