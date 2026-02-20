"""Abstract base class for Git providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


class GitError(Exception):
    """Base exception for Git provider errors."""
    pass


class AuthenticationError(GitError):
    """Raised when authentication fails."""
    pass


class RepositoryNotFoundError(GitError):
    """Raised when repository is not found."""
    pass


class BranchNotFoundError(GitError):
    """Raised when branch is not found."""
    pass


class FileNotFoundError(GitError):
    """Raised when file is not found."""
    pass


@dataclass
class RepositoryInfo:
    """Information about a repository."""
    id: str
    name: str
    full_name: str
    default_branch: str
    url: str
    description: Optional[str] = None
    private: bool = True


@dataclass
class PullRequestInfo:
    """Information about a pull request."""
    id: str
    number: int
    title: str
    body: str
    head_branch: str
    base_branch: str
    url: str
    state: str


class GitProvider(ABC):
    """Abstract base class for Git providers (GitHub, Bitbucket, etc.).
    
    This interface abstracts all Git operations so that the AI agent
    doesn't need to know which provider is being used.
    """
    
    def __init__(self, token: str):
        self.token = token
    
    @abstractmethod
    async def list_repositories(self) -> List[RepositoryInfo]:
        """List all accessible repositories.
        
        Returns:
            List of RepositoryInfo objects
        """
        pass
    
    @abstractmethod
    async def get_repository_info(self, repo: str) -> RepositoryInfo:
        """Get information about a specific repository.
        
        Args:
            repo: Repository name (e.g., "owner/repo")
            
        Returns:
            RepositoryInfo object
            
        Raises:
            RepositoryNotFoundError: If repository doesn't exist
            AuthenticationError: If not authorized
        """
        pass
    
    @abstractmethod
    async def get_file_content(self, repo: str, path: str, branch: str = "main") -> str:
        """Get content of a file from repository.
        
        Args:
            repo: Repository name
            path: File path within repository
            branch: Branch name (default: main)
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            BranchNotFoundError: If branch doesn't exist
        """
        pass
    
    @abstractmethod
    async def create_branch(self, repo: str, branch_name: str, from_branch: str = "main") -> str:
        """Create a new branch.
        
        Args:
            repo: Repository name
            branch_name: Name for new branch
            from_branch: Branch to create from (default: main)
            
        Returns:
            URL or ref of created branch
        """
        pass
    
    @abstractmethod
    async def delete_branch(self, repo: str, branch_name: str) -> None:
        """Delete a branch.
        
        Args:
            repo: Repository name
            branch_name: Branch to delete
        """
        pass
    
    @abstractmethod
    async def create_commit(
        self, 
        repo: str, 
        branch: str, 
        message: str, 
        files: Dict[str, str],
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> str:
        """Create a commit with file changes.
        
        Args:
            repo: Repository name
            branch: Branch to commit to
            message: Commit message
            files: Dict of {file_path: file_content}
            author_name: Optional commit author name
            author_email: Optional commit author email
            
        Returns:
            Commit SHA or URL
        """
        pass
    
    @abstractmethod
    async def create_pr(
        self,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> PullRequestInfo:
        """Create a pull request.
        
        Args:
            repo: Repository name
            title: PR title
            body: PR description
            head_branch: Branch with changes
            base_branch: Target branch (default: main)
            
        Returns:
            PullRequestInfo object
        """
        pass
    
    @abstractmethod
    async def get_pr(self, repo: str, pr_number: int) -> PullRequestInfo:
        """Get pull request information.
        
        Args:
            repo: Repository name
            pr_number: PR number
            
        Returns:
            PullRequestInfo object
        """
        pass
    
    @abstractmethod
    async def list_branches(self, repo: str) -> List[str]:
        """List all branches in repository.
        
        Args:
            repo: Repository name
            
        Returns:
            List of branch names
        """
        pass
