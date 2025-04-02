import gitlab
from .base import VCSOperations

class GitLabProvider(VCSOperations):
    def __init__(self, token: str):
        super().__init__(token)
        self.client = gitlab.Gitlab(private_token=self.token)
    
    def create_pr(self, project_id: str, title: str, body: str, base: str, head: str) -> dict:
        project = self.client.projects.get(project_id)
        mr = project.mergerequests.create({
            'title': title,
            'description': body,
            'source_branch': head,
            'target_branch': base
        })
        return {"url": mr.web_url, "id": mr.iid}
    
    def post_comment(self, project_id: str, mr_iid: int, body: str) -> dict:
        project = self.client.projects.get(project_id)
        mr = project.mergerequests.get(mr_iid)
        note = mr.notes.create({'body': body})
        return {"id": note.id}
    
    def submit_review(self, project_id: str, mr_iid: int, comment: str, approve: bool = False) -> dict:
        project = self.client.projects.get(project_id)
        mr = project.mergerequests.get(mr_iid)
        
        if approve:
            mr.approve()
        
        note = mr.notes.create({'body': comment})
        return {"id": note.id, "approved": approve}
