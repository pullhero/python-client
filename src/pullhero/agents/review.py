from pullhero.vcs.base import VCSOperations

def action_review(vcs_provider: str,
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
                llm_api_model: str) -> None:
#    vcs_provider: str,
#    vcs_token: str,
#    agent_action: str,
#    repo: str,
#    vcs_change_id: Optional[str] = None,
#    **kwargs
#):
    # Validate inputs
    if not vcs_token:
        raise ValueError(f"{vcs_provider} token required")
    
    # Initialize provider
    provider = VCSOperations.from_provider(vcs_provider, vcs_token)
    
    # # Dispatch actions
    # if agent_action == "comment":
    #     if not vcs_change_id:
    #         raise ValueError("PR ID required for comments")
    #     return provider.post_comment(vcs_repository, vcs_change_id, "asdf") #kwargs['comment_body'])
    
    if agent_action == "review":
        if not vcs_change_id:
            raise ValueError("PR ID required for reviews")
        return provider.submit_review(
            vcs_repository,
            vcs_change_id,
            "asdf", # kwargs['review_comment'],
            False # kwargs.get('approve', False)
        )
    
    # elif agent_action == "create-pr":
    #     return provider.create_pr(
    #         vcs_repository,
    #         "title", #kwargs['pr_title'],
    #         "body", #kwargs['pr_body'],
    #         vcs_base_branch, #kwargs['base_branch'],
    #         vcs_head_branch, ##kwargs['head_branch']
    #     )
    
    else:
        raise ValueError(f"Unknown review action: {agent_action}")







def build_prompt():
    

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

    local_repo_path = "/tmp/clone"
    repo_url = f"https://github.com/{owner}/{repo}.git"
    clone_repo_with_token(repo_url, local_repo_path, args.github_token)

    # Use the ingest method to get repository context (e.g., summary of code)
    summary, tree, content = ingest(f"{local_repo_path}")
    # TODO: When gitingest supports pulling private repos use the native method
    # summary, tree, content = ingest(f"https://github.com/{owner}/{repo}.git")
    
    prompt = f"""Code Review Task:
Begin Repository Content Section
{content}
End Repository Content Section

Begin PR Changes Diff Section
{diff}
End PR Changes Diff Section

Instructions:
1. Analyze exclusively the changes in the PR diff for quality, bugs, and best practices.
2. Provide concise feedback only for the diff using the Repository Content Section if needed.
3. End with "Vote: +1" (approve) or "Vote: -1" (request changes)."""
    
    try:
        review_text = call_ai_api(args.api_host, args.api_key, args.api_model, prompt)
    except Exception as e:
        logging.error(f"AI API call failed: {e}")
        sys.exit(1)
    
    vote = "+1" if "+1" in review_text else "-1" if "-1" in review_text else "0"
    
    provider_data = f"Provider: {args.api_host} Model: {args.api_model}"
    sourcerepo = "**[PullHero](https://github.com/ccamacho/pullhero)**"
    comment_text = (
        f"### [PullHero](https://github.com/ccamacho/pullhero) Review\n\n"
        f"**{provider_data}**\n\n{review_text}\n\n"
        f"**Vote**: {vote}\n\n{sourcerepo}"
    )
    
    g = Github(args.github_token)
    repo_obj = g.get_repo(f"{owner}/{repo}")
    pr_obj = repo_obj.get_pull(pr_number)

    if args.vote_action.lower() == "vote":
        if vote == "+1":
            pr_obj.create_review(body=comment_text, event="APPROVE")
            logging.info("Review created with event APPROVE")
        elif vote == "-1":
            pr_obj.create_review(body=comment_text, event="REQUEST_CHANGES")
            logging.info("Review created with event REQUEST_CHANGES")
        else:
            pr_obj.create_review(body=comment_text, event="COMMENT")
            logging.info("Review created with event COMMENT (neutral vote)")
    else:
        pr_obj.create_issue_comment(comment_text)
        logging.info("Review comment added using create_issue_comment")
    
    logging.info(f"Review completed with vote: {vote}")
