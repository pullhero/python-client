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

setup_logging()


def action_review(
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
    """
    Perform a code review action on a VCS pull/merge request using an LLM-powered agent.

    This function:
    1. Validates input parameters
    2. Initializes the VCS provider
    3. Gets an AI-generated review payload
    4. Posts comments or submits formal reviews based on the agent's decision

    Parameters:
    -----------
    vcs_provider : str
        Version control system provider ('github' or 'gitlab')
    vcs_token : str
        Authentication token for the VCS provider
    vcs_repository : str
        Repository identifier (format depends on provider)
    vcs_change_id : str
        Pull/Merge request ID (numeric string)
    vcs_change_type : str
        Type of change ('pr' or 'mr')
    vcs_base_branch : str
        Target branch name (e.g., 'main')
    vcs_head_branch : str
        Source branch name (e.g., 'feature/new-login')
    agent : str
        Review agent type ('default', 'security', 'docs', etc.)
    agent_action : str
        Action to perform ('comment' or 'review')
    llm_api_key : str
        API key for the LLM service
    llm_api_host : str
        Base URL for the LLM API
    llm_api_model : str
        Model name for the LLM service

    Returns:
    --------
    None

    Raises:
    -------
    ValueError
        If required parameters are missing or invalid
    Exception
        For VCS operations failures

    Example:
    --------
    >>> action_review(
    ...     vcs_provider="github",
    ...     vcs_token="ghp_...",
    ...     vcs_repository="owner/repo",
    ...     vcs_change_id="123",
    ...     vcs_change_type="pr",
    ...     vcs_base_branch="main",
    ...     vcs_head_branch="feature/new-login",
    ...     agent="default",
    ...     agent_action="review",
    ...     llm_api_key="sk-...",
    ...     llm_api_host="https://api.openai.com/v1",
    ...     llm_api_model="gpt-4"
    ... )
    """

    logging.info(f"Starting review action for {vcs_repository} PR/MR {vcs_change_id}")

    # Validate inputs
    if not vcs_token:
        error_msg = f"{vcs_provider} token required"
        logging.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Initialize provider
        logging.info(f"Initializing {vcs_provider} provider")
        provider = VCSOperations.from_provider(vcs_provider, vcs_token)

        # Get AI review payload
        logging.info("Getting AI review payload")
        review_payload = get_review(
            vcs_provider=vcs_provider,
            vcs_token=vcs_token,
            vcs_repository=vcs_repository,
            vcs_change_id=vcs_change_id,
            llm_api_key=llm_api_key,
            llm_api_host=llm_api_host,
            llm_api_model=llm_api_model,
            llm_api_endpoint=llm_api_endpoint,
        )

        # Determine review vote
        vote = (
            "+1" if "+1" in review_payload else "-1" if "-1" in review_payload else "0"
        )
        logging.info(f"Determined review vote: {vote}")

        # Construct review comment
        provider_data = f"Provider: {llm_api_host} Model: {llm_api_model}"
        sourcerepo = "**[PullHero](https://github.com/pullhero/)**"
        comment_text = (
            f"### [PullHero](https://github.com/pullhero) Review\n\n"
            f"**{provider_data}**\n\n{review_payload}\n\n"
            f"**Vote**: {vote}\n\n{sourcerepo}"
        )

        # Execute the requested action
        if agent_action == "comment":
            logging.info("Posting comment on PR/MR")
            if not vcs_change_id:
                error_msg = "PR ID required for comments"
                logging.error(error_msg)
                raise ValueError(error_msg)
            provider.post_comment(
                vcs_repository, int(vcs_change_id), comment_text, "pr"
            )
            logging.info("Comment posted successfully")

        elif agent_action == "review":
            logging.info("Submitting formal review")
            if not vcs_change_id:
                error_msg = "PR ID required for reviews"
                logging.error(error_msg)
                raise ValueError(error_msg)

            if vote == "+1":
                provider.submit_review(
                    vcs_repository, int(vcs_change_id), comment_text, approve=True
                )
                logging.info("Approved review submitted")
            elif vote == "-1":
                provider.submit_review(
                    vcs_repository, int(vcs_change_id), comment_text, approve=False
                )
                logging.info("Review submitted requesting changes")
            else:
                provider.submit_review(vcs_repository, int(vcs_change_id), comment_text)
                logging.info("Neutral review comment submitted")

        else:
            error_msg = f"Unknown review action: {agent_action}"
            logging.error(error_msg)
            raise ValueError(error_msg)

        logging.info("Review action completed successfully")

    except Exception as e:
        logging.error(f"Failed to complete review action: {str(e)}")
        raise


def get_review(
    vcs_provider: str,
    vcs_token: str,
    vcs_repository: str,
    vcs_change_id: str,
    llm_api_key: str,
    llm_api_host: str,
    llm_api_model: str,
    llm_api_endpoint: str,
) -> str:
    """
    Retrieves an AI-generated code review for a given pull/merge request.

    This function:
    1. Initializes the VCS provider
    2. Fetches the PR/MR diff
    3. Clones the repository
    4. Ingests repository content
    5. Generates a review prompt
    6. Calls the AI API for review generation

    Parameters:
    -----------
    vcs_provider : str
        Version control system ('github' or 'gitlab')
    vcs_token : str
        Authentication token for the VCS provider
    vcs_repository : str
        Repository identifier (format depends on provider)
    vcs_change_id : str
        Pull/Merge request ID (numeric string)
    llm_api_key : str
        API key for the LLM service
    llm_api_host : str
        Base URL for the LLM API
    llm_api_model : str
        Model name for the LLM service

    Returns:
    --------
    str
        The AI-generated review text containing analysis and vote

    Raises:
    -------
    ValueError
        If required parameters are missing
    Exception
        For VCS operations or API call failures

    Example:
    --------
    >>> review = get_review(
    ...     vcs_provider="github",
    ...     vcs_token="ghp_...",
    ...     vcs_repository="owner/repo",
    ...     vcs_change_id="123",
    ...     llm_api_key="sk-...",
    ...     llm_api_host="https://api.openai.com/v1",
    ...     llm_api_model="gpt-4"
    ... )
    """
    logging.info(
        f"Starting review generation for {vcs_repository} PR/MR {vcs_change_id}"
    )

    # Validate inputs
    if not all([vcs_provider, vcs_token, vcs_repository, vcs_change_id]):
        error_msg = "Missing required parameters for review generation"
        logging.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Initialize provider and get diff
        logging.info(f"Initializing {vcs_provider} provider")
        provider = VCSOperations.from_provider(vcs_provider, vcs_token)

        logging.info(f"Fetching diff for PR/MR {vcs_change_id}")
        diff = provider.get_pr_diff(vcs_repository, vcs_change_id)
        logging.debug(f"Retrieved diff with {len(diff.splitlines())} lines")

        # Clone and analyze repository
        repo_url = (
            f"https://github.com/{vcs_repository}"
            if vcs_provider == "github"
            else f"https://gitlab.com/{vcs_repository}"
        )

        logging.info(f"Cloning repository from {repo_url}")
        clone_repo_with_token(repo_url, vcs_token)

        logging.info("Analyzing repository content")
        summary, tree, content = ingest_repository("/tmp/clone")
        logging.debug(
            f"Repository analysis complete - {len(content.splitlines())} lines of content"
        )

        # Generate and submit prompt
        logging.info("Generating review prompt")
        prompt = get_prompt(content, diff)
        logging.debug(f"Prompt generated with {len(prompt.splitlines())} lines")

        logging.info(f"Calling AI API ({llm_api_model}) for review generation")
        review_text = call_ai_api(llm_api_host, llm_api_key, llm_api_model, llm_api_endpoint, prompt)
        logging.info("AI review generation completed successfully")

        return review_text

    except Exception as e:
        logging.error(f"Review generation failed: {str(e)}")
        raise


def get_prompt(content: str, diff: str) -> str:
    """
    Generates a standardized prompt for AI code review analysis.

    Constructs a structured prompt containing:
    - Repository content overview
    - PR/MR diff changes
    - Clear instructions for the AI reviewer

    Parameters:
    -----------
    content : str
        The analyzed repository content (from ingest_repository)
    diff : str
        The git diff output for the PR/MR changes

    Returns:
    --------
    str
        The formatted prompt ready for AI processing

    Example:
    --------
    >>> prompt = get_prompt(
    ...     content="...repository analysis...",
    ...     diff="...git diff output..."
    ... )
    """
    logging.info("Constructing AI review prompt")

    prompt = f"""Code Review Task:

Repository Context:
------------------
The following shows the relevant repository structure and content that provides
context for the changes being reviewed.

Begin Repository Content Section
{content}
End Repository Content Section

Changes to Review:
-----------------
Below are the specific changes being proposed in this pull/merge request.
Focus your analysis exclusively on these modifications.

Begin PR Changes Diff Section
{diff}
End PR Changes Diff Section

Review Instructions:
-------------------
1. Analyze the changes for:
   - Code quality and maintainability
   - Potential bugs or security issues
   - Adherence to project conventions
   - Documentation completeness

2. Consider the repository context only when necessary to understand the changes.

3. Provide specific, actionable feedback:
   - Praise good practices with examples
   - Flag concerns with clear explanations
   - Suggest improvements where applicable

4. Format your response in clear Markdown sections.

5. Conclude with exactly one of these voting directives:
   - "Vote: +1" (approve if changes are excellent)
   - "Vote: -1" (request changes if significant issues exist)

6. Keep the review professional and constructive."""

    logging.debug(f"Generated prompt with {len(prompt.splitlines())} lines")
    return prompt
