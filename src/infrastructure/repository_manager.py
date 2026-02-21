"""Repository Manager for Git operations (GitHub and Bitbucket).

This module manages local git repositories for customer workspaces,
providing clone, pull, push, and status operations.
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class GitProvider(Enum):
    """Supported Git providers."""
    GITHUB = "github"
    BITBUCKET = "bitbucket"
    GITLAB = "gitlab"
    GENERIC = "generic"


class RepositoryStatus(Enum):
    """Status of a local repository."""
    NOT_CLONED = "not_cloned"
    CLONING = "cloning"
    READY = "ready"
    HAS_CHANGES = "has_changes"
    ERROR = "error"


@dataclass
class RepositoryInfo:
    """Information about a repository."""
    customer_id: str
    repo_url: str
    provider: GitProvider
    default_branch: str
    workspace_path: Path
    current_branch: Optional[str] = None
    last_commit: Optional[str] = None
    has_changes: bool = False
    status: RepositoryStatus = RepositoryStatus.NOT_CLONED
    cloned_at: Optional[datetime] = None
    last_fetch: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert repository info to dictionary."""
        return {
            "customer_id": self.customer_id,
            "repo_url": self.repo_url,
            "provider": self.provider.value,
            "default_branch": self.default_branch,
            "workspace_path": str(self.workspace_path),
            "current_branch": self.current_branch,
            "last_commit": self.last_commit,
            "has_changes": self.has_changes,
            "status": self.status.value,
            "cloned_at": self.cloned_at.isoformat() if self.cloned_at else None,
            "last_fetch": self.last_fetch.isoformat() if self.last_fetch else None,
        }


class RepositoryManager:
    """Manages Git repositories for customer workspaces.
    
    This class provides methods to:
    - Clone repositories from GitHub and Bitbucket
    - Pull changes from remote
    - Push changes to remote
    - Get repository status and info
    """
    
    def __init__(self, base_workspaces_path: str = "~/ki-data/workspaces"):
        """Initialize the repository manager.
        
        Args:
            base_workspaces_path: Base path for all customer workspaces
        """
        self.base_path = Path(base_workspaces_path).expanduser().resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.repositories: Dict[str, RepositoryInfo] = {}
        
    def _detect_provider(self, repo_url: str) -> GitProvider:
        """Detect the Git provider from the repository URL.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Detected Git provider
        """
        url_lower = repo_url.lower()
        if "github.com" in url_lower:
            return GitProvider.GITHUB
        elif "bitbucket.org" in url_lower:
            return GitProvider.BITBUCKET
        elif "gitlab.com" in url_lower:
            return GitProvider.GITLAB
        else:
            return GitProvider.GENERIC
    
    def _normalize_url(self, repo_url: str, provider: GitProvider) -> str:
        """Normalize repository URL for cloning.
        
        Args:
            repo_url: Repository URL (can be HTTPS or SSH)
            provider: Git provider type
            
        Returns:
            Normalized HTTPS URL
        """
        # If already HTTPS, return as-is
        if repo_url.startswith("https://"):
            return repo_url
        
        # Convert SSH to HTTPS
        if repo_url.startswith("git@"):
            # Parse SSH URL: git@github.com:owner/repo.git
            match = re.match(r"git@([^:]+):(.+)\.git?", repo_url)
            if match:
                host, path = match.groups()
                return f"https://{host}/{path}"
        
        # Handle owner/repo shorthand for GitHub
        if "/" in repo_url and not repo_url.startswith(("http", "git@")):
            if provider == GitProvider.GITHUB:
                return f"https://github.com/{repo_url}"
            elif provider == GitProvider.BITBUCKET:
                return f"https://bitbucket.org/{repo_url}"
        
        return repo_url
    
    def _get_repo_name_from_url(self, repo_url: str) -> str:
        """Extract repository name from URL.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Repository name
        """
        # Remove .git suffix
        repo_url = repo_url.replace(".git", "")
        
        # Parse URL
        parsed = urlparse(repo_url)
        if parsed.path:
            # Get last part of path
            return parsed.path.strip("/").split("/")[-1]
        
        return "repository"
    
    def get_workspace_path(self, customer_id: str) -> Path:
        """Get the workspace path for a customer.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Path to customer workspace
        """
        return self.base_path / customer_id
    
    def clone_repo(
        self, 
        customer_id: str, 
        repo_url: str, 
        branch: Optional[str] = None,
        auth_token: Optional[str] = None,
        depth: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Clone a repository for a customer.
        
        Args:
            customer_id: Customer identifier
            repo_url: Repository URL (HTTPS or SSH)
            branch: Optional branch to clone (default: default branch)
            auth_token: Optional authentication token for private repos
            depth: Optional clone depth for shallow clones
            
        Returns:
            Tuple of (success, message)
        """
        workspace_path = self.get_workspace_path(customer_id)
        
        try:
            # Detect provider and normalize URL
            provider = self._detect_provider(repo_url)
            clone_url = self._normalize_url(repo_url, provider)
            
            # Add auth token to URL if provided
            if auth_token and provider == GitProvider.GITHUB:
                clone_url = clone_url.replace("https://", f"https://{auth_token}@")
            elif auth_token and provider == GitProvider.BITBUCKET:
                clone_url = clone_url.replace("https://", f"https://x-token-auth:{auth_token}@")
            
            # Create workspace directory
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Check if already cloned
            git_dir = workspace_path / ".git"
            if git_dir.exists():
                logger.info(f"Repository already exists for {customer_id}, pulling changes")
                return self.pull_changes(customer_id)
            
            logger.info(f"Cloning {repo_url} for customer {customer_id}")
            
            # Build clone command
            cmd = ["git", "clone"]
            
            if branch:
                cmd.extend(["-b", branch])
            
            if depth:
                cmd.extend(["--depth", str(depth)])
            
            cmd.extend([clone_url, str(workspace_path)])
            
            # Execute clone
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                # Clean up on failure
                if workspace_path.exists():
                    import shutil
                    shutil.rmtree(workspace_path, ignore_errors=True)
                
                error_msg = result.stderr or "Unknown error"
                # Mask token in error message
                if auth_token:
                    error_msg = error_msg.replace(auth_token, "***")
                return False, f"Failed to clone repository: {error_msg}"
            
            # Get repository info
            default_branch = self._get_default_branch(workspace_path)
            current_branch = self._get_current_branch(workspace_path)
            last_commit = self._get_last_commit(workspace_path)
            
            # Store repository info
            repo_info = RepositoryInfo(
                customer_id=customer_id,
                repo_url=repo_url,
                provider=provider,
                default_branch=default_branch or branch or "main",
                workspace_path=workspace_path,
                current_branch=current_branch,
                last_commit=last_commit,
                status=RepositoryStatus.READY,
                cloned_at=datetime.now()
            )
            self.repositories[customer_id] = repo_info
            
            logger.info(f"Successfully cloned repository for {customer_id}")
            return True, f"Repository cloned successfully to {workspace_path}"
            
        except subprocess.TimeoutExpired:
            # Clean up on timeout
            if workspace_path.exists():
                import shutil
                shutil.rmtree(workspace_path, ignore_errors=True)
            return False, "Clone operation timed out after 10 minutes"
            
        except Exception as e:
            # Clean up on error
            if workspace_path.exists():
                import shutil
                shutil.rmtree(workspace_path, ignore_errors=True)
            logger.error(f"Error cloning repository for {customer_id}: {e}")
            return False, f"Error cloning repository: {str(e)}"
    
    def pull_changes(self, customer_id: str, branch: Optional[str] = None) -> Tuple[bool, str]:
        """Pull latest changes from remote repository.
        
        Args:
            customer_id: Customer identifier
            branch: Optional specific branch to pull
            
        Returns:
            Tuple of (success, message)
        """
        workspace_path = self.get_workspace_path(customer_id)
        
        if not workspace_path.exists() or not (workspace_path / ".git").exists():
            return False, f"Repository not found for customer '{customer_id}'. Run clone_repo first."
        
        try:
            logger.info(f"Pulling changes for {customer_id}")
            
            # Stash any local changes
            subprocess.run(
                ["git", "stash", "push", "-m", "auto-stash-before-pull"],
                cwd=str(workspace_path),
                capture_output=True,
                timeout=60
            )
            
            # Fetch all branches
            result = subprocess.run(
                ["git", "fetch", "--all"],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return False, f"Failed to fetch: {result.stderr}"
            
            # Determine target branch
            if branch:
                target_branch = branch
            else:
                target_branch = self._get_current_branch(workspace_path) or "main"
            
            # Pull changes
            result = subprocess.run(
                ["git", "pull", "origin", target_branch],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return False, f"Failed to pull: {result.stderr}"
            
            # Update stored info
            if customer_id in self.repositories:
                self.repositories[customer_id].last_fetch = datetime.now()
                self.repositories[customer_id].current_branch = self._get_current_branch(workspace_path)
                self.repositories[customer_id].last_commit = self._get_last_commit(workspace_path)
                self.repositories[customer_id].has_changes = self._has_uncommitted_changes(workspace_path)
            
            return True, f"Successfully pulled changes from {target_branch}"
            
        except subprocess.TimeoutExpired:
            return False, "Pull operation timed out"
        except Exception as e:
            logger.error(f"Error pulling changes for {customer_id}: {e}")
            return False, f"Error pulling changes: {str(e)}"
    
    def push_changes(
        self, 
        customer_id: str, 
        branch: Optional[str] = None,
        message: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Push local changes to remote repository.
        
        Args:
            customer_id: Customer identifier
            branch: Optional target branch (uses current if not specified)
            message: Optional commit message
            
        Returns:
            Tuple of (success, message)
        """
        workspace_path = self.get_workspace_path(customer_id)
        
        if not workspace_path.exists() or not (workspace_path / ".git").exists():
            return False, f"Repository not found for customer '{customer_id}'"
        
        try:
            # Check if there are changes to commit
            if not self._has_uncommitted_changes(workspace_path):
                return True, "No changes to commit"
            
            logger.info(f"Pushing changes for {customer_id}")
            
            # Stage all changes
            result = subprocess.run(
                ["git", "add", "-A"],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return False, f"Failed to stage changes: {result.stderr}"
            
            # Commit changes
            commit_msg = message or f"KI-Mitarbeiter changes - {datetime.now().isoformat()}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return False, f"Failed to commit: {result.stderr}"
            
            # Determine target branch
            if branch:
                target_branch = branch
            else:
                target_branch = self._get_current_branch(workspace_path) or "main"
            
            # Push changes
            result = subprocess.run(
                ["git", "push", "origin", target_branch],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return False, f"Failed to push: {result.stderr}"
            
            # Update stored info
            if customer_id in self.repositories:
                self.repositories[customer_id].has_changes = False
                self.repositories[customer_id].last_commit = self._get_last_commit(workspace_path)
            
            return True, f"Changes pushed to {target_branch}"
            
        except subprocess.TimeoutExpired:
            return False, "Push operation timed out"
        except Exception as e:
            logger.error(f"Error pushing changes for {customer_id}: {e}")
            return False, f"Error pushing changes: {str(e)}"
    
    def get_repo_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get repository information for a customer.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Repository info dictionary or None if not found
        """
        workspace_path = self.get_workspace_path(customer_id)
        
        if not workspace_path.exists() or not (workspace_path / ".git").exists():
            return None
        
        try:
            # Get current status
            current_branch = self._get_current_branch(workspace_path)
            default_branch = self._get_default_branch(workspace_path)
            last_commit = self._get_last_commit(workspace_path)
            has_changes = self._has_uncommitted_changes(workspace_path)
            remote_url = self._get_remote_url(workspace_path)
            
            # Get recent commits
            recent_commits = self._get_recent_commits(workspace_path, 5)
            
            return {
                "customer_id": customer_id,
                "workspace_path": str(workspace_path),
                "remote_url": remote_url,
                "current_branch": current_branch,
                "default_branch": default_branch,
                "last_commit": last_commit,
                "has_uncommitted_changes": has_changes,
                "recent_commits": recent_commits,
                "status": RepositoryStatus.HAS_CHANGES.value if has_changes else RepositoryStatus.READY.value
            }
            
        except Exception as e:
            logger.error(f"Error getting repo info for {customer_id}: {e}")
            return None
    
    def checkout_branch(self, customer_id: str, branch: str, create: bool = False) -> Tuple[bool, str]:
        """Checkout a branch in the repository.
        
        Args:
            customer_id: Customer identifier
            branch: Branch name to checkout
            create: If True, create the branch if it doesn't exist
            
        Returns:
            Tuple of (success, message)
        """
        workspace_path = self.get_workspace_path(customer_id)
        
        if not workspace_path.exists() or not (workspace_path / ".git").exists():
            return False, f"Repository not found for customer '{customer_id}'"
        
        try:
            cmd = ["git", "checkout"]
            if create:
                cmd.append("-b")
            cmd.append(branch)
            
            result = subprocess.run(
                cmd,
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return False, f"Failed to checkout branch: {result.stderr}"
            
            # Update stored info
            if customer_id in self.repositories:
                self.repositories[customer_id].current_branch = branch
            
            return True, f"Switched to branch '{branch}'"
            
        except Exception as e:
            logger.error(f"Error checking out branch for {customer_id}: {e}")
            return False, f"Error checking out branch: {str(e)}"
    
    def create_branch(self, customer_id: str, branch: str, base_branch: Optional[str] = None) -> Tuple[bool, str]:
        """Create and checkout a new branch.
        
        Args:
            customer_id: Customer identifier
            branch: New branch name
            base_branch: Branch to create from (default: current)
            
        Returns:
            Tuple of (success, message)
        """
        workspace_path = self.get_workspace_path(customer_id)
        
        if not workspace_path.exists() or not (workspace_path / ".git").exists():
            return False, f"Repository not found for customer '{customer_id}'"
        
        try:
            # If base branch specified, checkout it first
            if base_branch:
                success, msg = self.checkout_branch(customer_id, base_branch)
                if not success:
                    return False, f"Failed to checkout base branch: {msg}"
            
            # Create and checkout new branch
            return self.checkout_branch(customer_id, branch, create=True)
            
        except Exception as e:
            logger.error(f"Error creating branch for {customer_id}: {e}")
            return False, f"Error creating branch: {str(e)}"
    
    def list_branches(self, customer_id: str, remote: bool = False) -> Tuple[bool, List[str]]:
        """List branches in the repository.
        
        Args:
            customer_id: Customer identifier
            remote: If True, list remote branches
            
        Returns:
            Tuple of (success, branches list)
        """
        workspace_path = self.get_workspace_path(customer_id)
        
        if not workspace_path.exists() or not (workspace_path / ".git").exists():
            return False, []
        
        try:
            cmd = ["git", "branch", "-r"] if remote else ["git", "branch"]
            
            result = subprocess.run(
                cmd,
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False, []
            
            # Parse branch list
            branches = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line.startswith("* "):
                    line = line[2:]  # Remove current branch indicator
                elif line.startswith("remotes/origin/"):
                    line = line.replace("remotes/origin/", "")
                if line and line != "HEAD -> origin":
                    branches.append(line)
            
            return True, list(set(branches))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error listing branches for {customer_id}: {e}")
            return False, []
    
    def _run_git_command(self, workspace_path: Path, args: List[str]) -> Tuple[bool, str]:
        """Run a git command in the workspace.
        
        Args:
            workspace_path: Path to git repository
            args: Git command arguments
            
        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)
    
    def _get_current_branch(self, workspace_path: Path) -> Optional[str]:
        """Get the current branch name."""
        success, output = self._run_git_command(workspace_path, ["branch", "--show-current"])
        return output if success else None
    
    def _get_default_branch(self, workspace_path: Path) -> Optional[str]:
        """Get the default branch name."""
        success, output = self._run_git_command(
            workspace_path, 
            ["rev-parse", "--abbrev-ref", "origin/HEAD"]
        )
        if success and output.startswith("origin/"):
            return output.replace("origin/", "")
        return "main"  # Fallback
    
    def _get_last_commit(self, workspace_path: Path) -> Optional[str]:
        """Get the last commit hash."""
        success, output = self._run_git_command(
            workspace_path,
            ["rev-parse", "--short", "HEAD"]
        )
        return output if success else None
    
    def _get_remote_url(self, workspace_path: Path) -> Optional[str]:
        """Get the remote origin URL."""
        success, output = self._run_git_command(
            workspace_path,
            ["remote", "get-url", "origin"]
        )
        return output if success else None
    
    def _has_uncommitted_changes(self, workspace_path: Path) -> bool:
        """Check if there are uncommitted changes."""
        success, output = self._run_git_command(
            workspace_path,
            ["status", "--porcelain"]
        )
        return success and len(output.strip()) > 0
    
    def _get_recent_commits(self, workspace_path: Path, count: int = 5) -> List[Dict[str, str]]:
        """Get recent commits."""
        success, output = self._run_git_command(
            workspace_path,
            ["log", f"-{count}", "--pretty=format:%h|%s|%an|%ai"]
        )
        
        commits = []
        if success:
            for line in output.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 3)
                    if len(parts) >= 3:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3] if len(parts) > 3 else ""
                        })
        return commits
    
    def cleanup_repo(self, customer_id: str) -> Tuple[bool, str]:
        """Remove a cloned repository.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Tuple of (success, message)
        """
        workspace_path = self.get_workspace_path(customer_id)
        
        if not workspace_path.exists():
            return True, "Repository does not exist"
        
        try:
            import shutil
            shutil.rmtree(workspace_path, ignore_errors=True)
            
            if customer_id in self.repositories:
                del self.repositories[customer_id]
            
            return True, f"Repository for {customer_id} removed"
            
        except Exception as e:
            logger.error(f"Error cleaning up repository for {customer_id}: {e}")
            return False, f"Error removing repository: {str(e)}"


# Singleton instance for application-wide use
_repository_manager_instance: Optional[RepositoryManager] = None


def get_repository_manager(base_path: str = "~/ki-data/workspaces") -> RepositoryManager:
    """Get or create the singleton RepositoryManager instance."""
    global _repository_manager_instance
    if _repository_manager_instance is None:
        _repository_manager_instance = RepositoryManager(base_path)
    return _repository_manager_instance
