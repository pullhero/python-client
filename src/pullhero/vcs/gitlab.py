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
from typing import Optional, List, Dict, Literal, Tuple
from pullhero.vcs.base import VCSOperations


class GitLabProvider(VCSOperations):
    def __init__(self, token: str):
        super().__init__(token)
        self.client = gitlab.Gitlab(private_token=self.token)

    def create_pr(
        self, repo_identifier: str, title: str, body: str, base: str, head: str
    ) -> Dict[str, str]:
        """
        Create a new GitLab Merge Request.
        """
        project = self.client.projects.get(repo_identifier)
        mr = project.mergerequests.create(
            {
                "title": title,
                "description": body,
                "source_branch": head,
                "target_branch": base,
            }
        )
        return {"url": mr.web_url, "id": str(mr.iid)}

    def post_comment(
        self,
        project_id: str,
        target_id: str,
        body: str,
        target_type: Literal["pr", "issue"] = "pr",
    ) -> Dict[str, str]:
        """
        GitLab implementation to post comments on MRs or Issues.
        """
        self.logger.info(
            f"Posting comment on {target_type.upper()} #{target_id} in {project_id}"
        )
        self.logger.debug(f"Comment preview: {body[:50]}...")

        try:
            project = self.client.projects.get(project_id)

            if target_type == "pr":
                target = project.mergerequests.get(target_id)
            elif target_type == "issue":
                target = project.issues.get(target_id)
            else:
                raise ValueError(f"Invalid target_type: {target_type}")

            note = target.notes.create({"body": body})

            self.logger.info(f"Successfully posted comment with ID {note.id}")
            return {"id": note.id, "url": f"{target.web_url}#note_{note.id}"}
        except gitlab.exceptions.GitlabError as e:
            self.logger.error(f"Failed to post comment: {str(e)}")
            raise

    def submit_review(
        self, pr_id: str, comment: str, approve: bool = False
    ) -> Dict[str, str]:
        """
        Submit a review for a GitLab Merge Request, with optional approval.
        """
        # In GitLab, we need both project ID and MR IID
        if ":" not in pr_id:
            raise ValueError("pr_id must be in format 'project_id:mr_iid'")

        project_id, mr_iid = pr_id.split(":", 1)

        project = self.client.projects.get(project_id)
        mr = project.mergerequests.get(int(mr_iid))

        if approve:
            mr.approve()

        note = mr.notes.create({"body": comment})
        return {"id": str(note.id), "approved": approve}

    def get_pr_diff(self, repo_identifier: str, pr_id: str) -> str:
        """
        Get the diff for a merge request using GitLab API.
        """
        project = self.client.projects.get(repo_identifier)
        mr = project.mergerequests.get(int(pr_id))
        # GitLab returns diff directly in the MR object
        changes = mr.changes()
        return "".join([change.get("diff", "") for change in changes["changes"]])

    def get_current_readme(
        self, project_id: str, branch: str
    ) -> Tuple[str, Optional[str]]:
        """
        Fetch the current README.md content from the given branch, if it exists.
        """
        self.logger.info(f"Fetching README.md from {project_id} on branch {branch}")
        project = self.client.projects.get(project_id)
        try:
            readme_file = project.files.get(file_path="README.md", ref=branch)
            # Return readme content and the file path as ID (gitlab doesn't use file_id for updates)
            return readme_file.decode().decode("utf-8"), "README.md"
        except gitlab.exceptions.GitlabGetError:
            self.logger.info("No existing README.md found.")
            return "", None

    def create_or_update_branch(
        self, project_id: str, branch_name: str, base_branch: str
    ) -> Dict[str, str]:
        """
        Create the branch if it doesn't exist, otherwise return the branch reference.
        """
        self.logger.info(f"Checking/Creating branch {branch_name} from {base_branch}")
        project = self.client.projects.get(project_id)

        try:
            branch = project.branches.get(branch_name)
            self.logger.info(f"Branch '{branch_name}' already exists.")
            return {"ref": branch_name, "status": "exists"}
        except gitlab.exceptions.GitlabGetError:
            branch = project.branches.create(
                {"branch": branch_name, "ref": base_branch}
            )
            self.logger.info(f"Branch '{branch_name}' created from '{base_branch}'.")
            return {"ref": branch_name, "status": "created"}

    def update_readme_file(
        self, project_id: str, branch: str, new_content: str
    ) -> Dict[str, str]:
        """
        Update or create the README.md file on the given branch.
        """
        self.logger.info(f"Updating README.md on branch {branch}")
        project = self.client.projects.get(project_id)

        try:
            readme_content, file_id = self.get_current_readme(project_id, branch)

            if file_id:
                commit_message = "Update README documentation via PullHero"
                self.logger.debug(
                    f"Updating README.md with branch: '{branch}', content length: {len(new_content)} chars"
                )

                result = project.files.update(
                    file_path="README.md",
                    new_data={
                        "branch": branch,
                        "content": new_content,
                        "commit_message": commit_message,
                    },
                )

                commits = project.commits.list(ref_name=branch, per_page=1)
                latest_commit_id = commits[0].id if commits else None

                self.logger.info("README.md updated on branch '%s'.", branch)
                return {"status": "updated", "sha": latest_commit_id}
            else:
                commit_message = ("Create README documentation via PullHero",)

                result = project.files.create(
                    file_path="README.md",
                    new_data={
                        "branch": branch,
                        "content": new_content,
                        "commit_message": commit_message,
                    },
                )

                commits = project.commits.list(ref_name=branch, per_page=1)
                latest_commit_id = commits[0].id if commits else None

                self.logger.info("README.md created on branch '%s'.", branch)
                return {"status": "updated", "sha": latest_commit_id}
        except Exception as e:
            self.logger.error("Failed to update README.md: %s", e)
            raise

    def create_or_update_pr(
        self,
        project_id: str,
        branch: str,
        base_branch: str,
        pr_title: str,
        pr_body: str,
    ) -> Dict[str, str]:
        """
        Create a new merge request or update an existing one from the branch.
        """
        self.logger.info(f"Creating/Updating MR from {branch} to {base_branch}")
        project = self.client.projects.get(project_id)

        mrs = project.mergerequests.list(
            state="opened", source_branch=branch, target_branch=base_branch
        )

        if not mrs:
            mr = project.mergerequests.create(
                {
                    "title": pr_title,
                    "description": pr_body,
                    "source_branch": branch,
                    "target_branch": base_branch,
                }
            )
            self.logger.info("Created MR !%s for README update.", mr.iid)
            return {"url": mr.web_url, "id": mr.iid, "status": "created"}
        else:
            mr = mrs[0]
            self.logger.info("Existing MR !%s found for README update.", mr.iid)
            return {"url": mr.web_url, "id": mr.iid, "status": "exists"}

    def get_issues_with_label(self, project_id: str, label: str) -> List[Dict]:
        """
        GitLab implementation for getting issues with a specific label.
        """
        self.logger.info(f"Getting issues with label '{label}' from {project_id}")
        try:
            project = self.client.projects.get(project_id)
            issues = project.issues.list(labels=[label])
            return [issue.attributes for issue in issues]
        except gitlab.exceptions.GitlabError as e:
            self.logger.error(f"Failed to get issues with label: {str(e)}")
            raise

    def get_issue_comments(self, project_id: str, issue_iid: str) -> List[Dict]:
        """
        GitLab implementation for getting issue comments (notes).
        """
        self.logger.info(f"Getting comments for issue !{issue_iid} in {project_id}")
        try:
            # Get project and issue
            project = self.client.projects.get(project_id)
            issue = project.issues.get(issue_iid)

            # Get and return notes (comments)
            notes = issue.notes.list()
            return [
                {
                    "id": note.id,
                    "body": note.body,
                    "created_at": note.created_at,
                    "author": note.author["username"],
                    "system": note.system,
                }
                for note in notes
            ]

        except gitlab.exceptions.GitlabGetError as ge:
            self.logger.error(f"GitLab error getting comments: {str(ge)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to get issue comments: {str(e)}")
            raise

    def remove_label_from_issue(
        self, project_id: str, issue_number: str, label: str
    ) -> bool:
        """
        GitLab implementation for removing a label from an issue.
        """
        self.logger.info(f"Removing label '{label}' from issue #{issue_number}")
        try:
            project = self.client.projects.get(project_id)
            issue = project.issues.get(issue_number)

            current_labels = issue.labels

            if label in current_labels:
                current_labels.remove(label)

                # Update issue with new labels
                issue.labels = current_labels
                issue.save()

                self.logger.info(f"Successfully removed label '{label}'")
                return True
            else:
                self.logger.info(f"Label '{label}' not found on issue")
                return False
        except gitlab.exceptions.GitlabError as e:
            self.logger.error(f"Failed to remove label: {str(e)}")
            return False

    def get_issue_details(self, project_id: str, issue_iid: str) -> Dict[str, str]:
        """
        GitLab implementation to fetch issue (merge request) title and body.
        """
        self.logger.info(f"Fetching details for issue !{issue_iid} in {project_id}")
        try:
            project = self.client.projects.get(project_id)
            issue = project.issues.get(issue_iid)

            return {
                "title": issue.title,
                "body": issue.description,
                "url": issue.web_url,
                "state": issue.state,  # e.g., "opened" or "closed"
            }
        except gitlab.exceptions.GitlabError as e:
            self.logger.error(f"Failed to fetch issue details: {str(e)}")
            raise

    def get_pr_info_from_comment(
        self, project_id: str, mr_iid: str
    ) -> Optional[Dict[str, str]]:
        """
        GitLab implementation to get MR info from project and MR IID.
        """
        self.logger.info(f"Getting MR info for !{mr_iid} in {project_id}")
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            return {
                "pr_number": str(mr.iid),
                "pr_branch": mr.source_branch,
                "base_branch": mr.target_branch,
                "repo_identifier": project_id,
                "pr_url": mr.web_url,
                "title": mr.title,
                "state": mr.state,
            }
        except gitlab.exceptions.GitlabGetError:
            self.logger.error(f"MR !{mr_iid} not found")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get MR info: {str(e)}")
            raise

    def get_pr_files(self, project_id: str, mr_iid: str) -> List[Dict[str, str]]:
        """
        GitLab implementation to get list of files in an MR.
        """
        self.logger.info(f"Getting files for MR !{mr_iid} in {project_id}")
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            files = []
            for change in mr.changes()["changes"]:
                files.append(
                    {
                        "filename": change["new_path"],
                        "status": change["new_file"]
                        and "added"
                        or change["deleted_file"]
                        and "deleted"
                        or "modified",
                        "changes": change["diff"].count("\n"),
                        "additions": change["diff"].count("+ ")
                        - 1,  # Subtract header line
                        "deletions": change["diff"].count("- ")
                        - 1,  # Subtract header line
                        "raw_url": f"{project.web_url}/-/raw/{mr.source_branch}/{change['new_path']}",
                    }
                )
            return files
        except gitlab.exceptions.GitlabError as e:
            self.logger.error(f"Failed to get MR files: {str(e)}")
            raise

    def get_current_file(
        self, project_id: str, branch: str, filename: str
    ) -> Tuple[str, Optional[str]]:
        """
        GitLab implementation to get file content.
        """
        self.logger.info(f"Fetching {filename} from {project_id}@{branch}")
        try:
            project = self.client.projects.get(project_id)
            file_content = project.files.get(file_path=filename, ref=branch)
            return file_content.decode().decode("utf-8"), file_content.id
        except gitlab.exceptions.GitlabGetError:
            self.logger.info(f"File {filename} not found")
            return "", None
        except Exception as e:
            self.logger.error(f"Failed to get file: {str(e)}")
            raise

    def update_file(
        self, project_id: str, branch: str, filename: str, new_content: str
    ) -> Dict[str, str]:
        """
        GitLab implementation to update/create file.
        """
        self.logger.info(f"Updating {filename} on {project_id}@{branch}")
        try:
            project = self.client.projects.get(project_id)
            commit_message = f"Update {filename} via PullHero"

            current_content, file_id = self.get_current_file(
                project_id, branch, filename
            )
            if file_id:
                result = project.files.update(
                    file_path=filename,
                    branch=branch,
                    content=new_content,
                    commit_message=commit_message,
                )
                self.logger.info(f"File {filename} updated")
                return {"status": "updated", "sha": result["commit_id"]}
            else:
                result = project.files.create(
                    {
                        "file_path": filename,
                        "branch": branch,
                        "content": new_content,
                        "commit_message": f"Create {filename} via PullHero",
                    }
                )
                self.logger.info(f"File {filename} created")
                return {"status": "created", "sha": result["commit_id"]}
        except Exception as e:
            self.logger.error(f"Failed to update file: {str(e)}")
            raise

    def update_pr(self, project_id: str, branch: str) -> Optional[Dict[str, str]]:
        """
        GitLab implementation to get MR info from branch.
        """
        self.logger.info(f"Checking for MR from {branch} in {project_id}")
        try:
            project = self.client.projects.get(project_id)
            mrs = project.mergerequests.list(state="opened", source_branch=branch)

            if not mrs:
                self.logger.info("No open MR found")
                return None

            mr = mrs[0]
            return {
                "pr_number": str(mr.iid),
                "pr_url": mr.web_url,
                "title": mr.title,
                "state": mr.state,
            }
        except Exception as e:
            self.logger.error(f"Failed to get MR info: {str(e)}")
            raise
