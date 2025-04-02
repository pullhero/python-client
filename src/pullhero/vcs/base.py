from abc import ABC, abstractmethod
from typing import Optional

class VCSOperations(ABC):
    @abstractmethod
    def __init__(self, token: str):
        self.token = token
    
    @abstractmethod
    def create_pr(self, title: str, body: str, base: str, head: str) -> dict:
        """Create a pull/merge request"""
    
    @abstractmethod
    def post_comment(self, pr_id: str, body: str) -> dict:
        """Post comment on a PR/MR"""
    
    @abstractmethod
    def submit_review(self, pr_id: str, comment: str, approve: bool = False) -> dict:
        """Submit formal review with optional approval"""
    
    @classmethod
    def from_provider(cls, provider: str, token: Optional[str] = None):
        providers = {
            "github": GitHubProvider,
            "gitlab": GitLabProvider
        }
        if provider not in providers:
            raise ValueError(f"Unsupported provider: {provider}")
        return providers[provider](token)
