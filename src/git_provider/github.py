"""GitHub provider implementation."""

import base64
import json
from typing import Dict, List, Optional

import httpx

from .base import (
    GitProvider, 
    RepositoryInfo, 
    PullRequestInfo,
    AuthenticationError,
    RepositoryNotFoundError,
    BranchNotFoundError,
    FileNotFoundError
)


class GitHubProvider(GitProvider):
    """GitHub API provider implementation.
    
    Uses GitHub REST API v3.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str):
        super().__init__(token)
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict] = None
    ) -> Dict:
        """Make an authenticated request to GitHub API."""
        url = f"{self.BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=json_data,
                timeout=30.0
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid GitHub token")
            elif response.status_code == 404:
                raise RepositoryNotFoundError(f"Resource not found: {endpoint}")
            elif response.status_code >= 400:
                raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
            
            return response.json() if response.content else {}
    
    async def list_repositories(self) -> List[RepositoryInfo]:
        """List all accessible repositories."""
        data = await self._request("GET", "/user/repos?per_page=100")
        
        return [
            RepositoryInfo(
                id=str(repo["id"]),
                name=repo["name"],
                full_name=repo["full_name"],
                default_branch=repo.get("default_branch", "main"),
                url=repo["html_url"],
                description=repo.get("description"),
                private=repo.get("private", True)
            )
            for repo in data
        ]
    
    async def get_repository_info(self, repo: str) -> RepositoryInfo:
        """Get repository information."""
        data = await self._request("GET", f"/repos/{repo}")
        
        return RepositoryInfo(
            id=str(data["id"]),
            name=data["name"],
            full_name=data["full_name"],
            default_branch=data.get("default_branch", "main"),
            url=data["html_url"],
            description=data.get("description"),
            private=data.get("private", True)
        )
    
    async def get_file_content(self, repo: str, path: str, branch: str = "main") -> str:
        """Get file content from repository."""
        try:
            data = await self._request(
                "GET", 
                f"/repos/{repo}/contents/{path}?ref={branch}"
            )
            
            if "content" not in data:
                raise FileNotFoundError(f"Path is not a file: {path}")
            
            # GitHub returns base64 encoded content
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
            
        except RepositoryNotFoundError:
            raise FileNotFoundError(f"File not found: {path} in {repo}@{branch}")
    
    async def create_branch(self, repo: str, branch_name: str, from_branch: str = "main") -> str:
        """Create a new branch from an existing branch."""
        # First, get the SHA of the source branch
        ref_data = await self._request(
            "GET", 
            f"/repos/{repo}/git/refs/heads/{from_branch}"
        )
        
        sha = ref_data["object"]["sha"]
        
        # Create new branch
        await self._request(
            "POST",
            f"/repos/{repo}/git/refs",
            json_data={
                "ref": f"refs/heads/{branch_name}",
                "sha": sha
            }
        )
        
        return f"https://github.com/{repo}/tree/{branch_name}"
    
    async def delete_branch(self, repo: str, branch_name: str) -> None:
        """Delete a branch."""
        await self._request(
            "DELETE",
            f"/repos/{repo}/git/refs/heads/{branch_name}"
        )
    
    async def create_commit(
        self,
        repo: str,
        branch: str,
        message: str,
        files: Dict[str, str],
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> str:
        """Create a commit with multiple file changes using Contents API.
        
        This creates/updates each file individually, which is simpler and more reliable.
        """
        import base64
        
        # Get current commit SHA for parent
        try:
            ref_data = await self._request(
                "GET",
                f"/repos/{repo}/git/refs/heads/{branch}"
            )
            current_sha = ref_data["object"]["sha"]
        except:
            current_sha = None
        
        # Create/update each file
        for file_path, content in files.items():
            # Check if file exists
            file_exists = False
            current_file_sha = None
            try:
                file_data = await self._request(
                    "GET",
                    f"/repos/{repo}/contents/{file_path}?ref={branch}"
                )
                file_exists = True
                current_file_sha = file_data.get("sha")
            except:
                pass
            
            # Prepare payload
            content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            payload = {
                "message": f"{message}\n\nAdd/Update {file_path}",
                "content": content_b64,
                "branch": branch
            }
            
            # If file exists, need to provide SHA
            if file_exists and current_file_sha:
                payload["sha"] = current_file_sha
            
            # Create/update file
            await self._request(
                "PUT",
                f"/repos/{repo}/contents/{file_path}",
                json_data=payload
            )
        
        # Get the new commit SHA
        ref_data = await self._request(
            "GET",
            f"/repos/{repo}/git/refs/heads/{branch}"
        )
        return ref_data["object"]["sha"]
    
    async def create_pr(
        self,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> PullRequestInfo:
        """Create a pull request."""
        data = await self._request(
            "POST",
            f"/repos/{repo}/pulls",
            json_data={
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch
            }
        )
        
        return PullRequestInfo(
            id=str(data["id"]),
            number=data["number"],
            title=data["title"],
            body=data.get("body", ""),
            head_branch=head_branch,
            base_branch=base_branch,
            url=data["html_url"],
            state=data["state"]
        )
    
    async def get_pr(self, repo: str, pr_number: int) -> PullRequestInfo:
        """Get pull request information."""
        data = await self._request("GET", f"/repos/{repo}/pulls/{pr_number}")
        
        return PullRequestInfo(
            id=str(data["id"]),
            number=data["number"],
            title=data["title"],
            body=data.get("body", ""),
            head_branch=data["head"]["ref"],
            base_branch=data["base"]["ref"],
            url=data["html_url"],
            state=data["state"]
        )
    
    async def list_branches(self, repo: str) -> List[str]:
        """List all branches."""
        data = await self._request("GET", f"/repos/{repo}/branches?per_page=100")
        return [branch["name"] for branch in data]
