from github import Github
from .base import VCSOperations

class GitHubProvider(VCSOperations):
    def __init__(self, token: str):
        super().__init__(token)
        self.client = Github(self.token)
    
    def create_pr(self, repo_name: str, title: str, body: str, base: str, head: str) -> dict:
        repo = self.client.get_repo(repo_name)
        pr = repo.create_pull(title=title, body=body, base=base, head=head)
        return {"url": pr.html_url, "id": pr.number}
    
    def post_comment(self, repo_name: str, pr_id: int, body: str) -> dict:
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_id)
        comment = pr.create_issue_comment(body)
        return {"id": comment.id}
    
    def submit_review(self, repo_name: str, pr_id: int, comment: str, approve: bool = False) -> dict:
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_id)
        event = "APPROVE" if approve else "COMMENT"
        review = pr.create_review(body=comment, event=event)
        return {"id": review.id}


    def get_pr_diff(self, github_token, owner, repo, pr_number):
        """Fetches the diff of a pull request."""
        url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github.v3.diff'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
