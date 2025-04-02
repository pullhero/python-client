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

import gitlab
from pullhero.vcs.base import VCSOperations

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

    def get_pr_diff(self, project_id: str, mr_iid: int) -> str:
        """Get the diff for a merge request using GitLab API"""
        project = self.client.projects.get(project_id)
        mr = project.mergerequests.get(mr_iid)
        # GitLab returns diff directly in the MR object
        return mr.diffs().diff
