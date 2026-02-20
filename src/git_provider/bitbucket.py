"""Bitbucket provider implementation."""

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


class BitbucketProvider(GitProvider):
    """Bitbucket Cloud API provider implementation.
    
    Uses Bitbucket REST API 2.0.
    """
    
    BASE_URL = "https://api.bitbucket.org/2.0"
    
    def __init__(self, token: str, workspace: Optional[str] = None):
        super().__init__(token)
        self.workspace = workspace
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make an authenticated request to Bitbucket API."""
        url = f"{self.BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=json_data,
                params=params,
                timeout=30.0
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid Bitbucket token")
            elif response.status_code == 404:
                raise RepositoryNotFoundError(f"Resource not found: {endpoint}")
            elif response.status_code >= 400:
                raise Exception(f"Bitbucket API error: {response.status_code} - {response.text}")
            
            return response.json() if response.content else {}
    
    def _parse_repo(self, repo: str) -> tuple:
        """Parse workspace/repo_slug from repo string."""
        if "/" in repo:
            return repo.split("/", 1)
        if self.workspace:
            return self.workspace, repo
        raise ValueError(f"Repository must be in format 'workspace/repo' or workspace must be set: {repo}")
    
    async def list_repositories(self) -> List[RepositoryInfo]:
        """List all accessible repositories."""
        if not self.workspace:
            raise ValueError("Workspace must be set to list repositories")
        
        data = await self._request("GET", f"/repositories/{self.workspace}")
        
        repos = []
        for repo in data.get("values", []):
            repos.append(RepositoryInfo(
                id=repo["uuid"],
                name=repo["name"],
                full_name=repo["full_name"],
                default_branch=repo.get("mainbranch", {}).get("name", "master"),
                url=repo["links"]["html"]["href"],
                description=repo.get("description"),
                private=repo.get("is_private", True)
            ))
        
        return repos
    
    async def get_repository_info(self, repo: str) -> RepositoryInfo:
        """Get repository information."""
        workspace, repo_slug = self._parse_repo(repo)
        data = await self._request("GET", f"/repositories/{workspace}/{repo_slug}")
        
        return RepositoryInfo(
            id=data["uuid"],
            name=data["name"],
            full_name=data["full_name"],
            default_branch=data.get("mainbranch", {}).get("name", "master"),
            url=data["links"]["html"]["href"],
            description=data.get("description"),
            private=data.get("is_private", True)
        )
    
    async def get_file_content(self, repo: str, path: str, branch: str = "master") -> str:
        """Get file content from repository."""
        workspace, repo_slug = self._parse_repo(repo)
        
        try:
            data = await self._request(
                "GET",
                f"/repositories/{workspace}/{repo_slug}/src/{branch}/{path}"
            )
            
            # Bitbucket returns raw content directly for file endpoints
            # But for API, we need to handle it differently
            # This is a simplified version - actual implementation may vary
            raise NotImplementedError("Bitbucket file content retrieval needs raw API access")
            
        except RepositoryNotFoundError:
            raise FileNotFoundError(f"File not found: {path} in {repo}@{branch}")
    
    async def create_branch(self, repo: str, branch_name: str, from_branch: str = "master") -> str:
        """Create a new branch."""
        workspace, repo_slug = self._parse_repo(repo)
        
        # Get the commit SHA of the source branch
        ref_data = await self._request(
            "GET",
            f"/repositories/{workspace}/{repo_slug}/refs/branches/{from_branch}"
        )
        
        target_sha = ref_data["target"]["hash"]
        
        # Create new branch reference
        await self._request(
            "POST",
            f"/repositories/{workspace}/{repo_slug}/refs/branches",
            json_data={
                "name": branch_name,
                "target": {
                    "hash": target_sha
                }
            }
        )
        
        return f"https://bitbucket.org/{workspace}/{repo_slug}/branch/{branch_name}"
    
    async def delete_branch(self, repo: str, branch_name: str) -> None:
        """Delete a branch."""
        workspace, repo_slug = self._parse_repo(repo)
        
        await self._request(
            "DELETE",
            f"/repositories/{workspace}/{repo_slug}/refs/branches/{branch_name}"
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
        """Create a commit with file changes."""
        workspace, repo_slug = self._parse_repo(repo)
        
        # Bitbucket API doesn't support creating commits directly via REST API easily
        # Usually requires using git commands or source API
        # This is a placeholder - actual implementation would use git-over-HTTPS or similar
        raise NotImplementedError(
            "Bitbucket commit creation via API is limited. "
            "Consider using local git commands with HTTPS auth."
        )
    
    async def create_pr(
        self,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "master"
    ) -> PullRequestInfo:
        """Create a pull request."""
        workspace, repo_slug = self._parse_repo(repo)
        
        data = await self._request(
            "POST",
            f"/repositories/{workspace}/{repo_slug}/pullrequests",
            json_data={
                "title": title,
                "description": body,
                "source": {
                    "branch": {
                        "name": head_branch
                    }
                },
                "destination": {
                    "branch": {
                        "name": base_branch
                    }
                }
            }
        )
        
        return PullRequestInfo(
            id=data["id"],
            number=data["id"],
            title=data["title"],
            body=data.get("description", ""),
            head_branch=head_branch,
            base_branch=base_branch,
            url=data["links"]["html"]["href"],
            state=data["state"]
        )
    
    async def get_pr(self, repo: str, pr_number: int) -> PullRequestInfo:
        """Get pull request information."""
        workspace, repo_slug = self._parse_repo(repo)
        data = await self._request(
            "GET",
            f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_number}"
        )
        
        return PullRequestInfo(
            id=data["id"],
            number=data["id"],
            title=data["title"],
            body=data.get("description", ""),
            head_branch=data["source"]["branch"]["name"],
            base_branch=data["destination"]["branch"]["name"],
            url=data["links"]["html"]["href"],
            state=data["state"]
        )
    
    async def list_branches(self, repo: str) -> List[str]:
        """List all branches."""
        workspace, repo_slug = self._parse_repo(repo)
        
        data = await self._request(
            "GET",
            f"/repositories/{workspace}/{repo_slug}/refs/branches"
        )
        
        return [branch["name"] for branch in data.get("values", [])]
