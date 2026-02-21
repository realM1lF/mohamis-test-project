"""Infrastructure module for customer workspace and repository management.

This module provides:
- WorkspaceManager: Manages customer workspaces with DDEV integration
- RepositoryManager: Handles Git operations (clone, pull, push)
- DDEVManager: Advanced DDEV orchestration capabilities
"""

from .workspace_manager import WorkspaceManager, CustomerWorkspace, WorkspaceStatus
from .repository_manager import RepositoryManager, RepositoryInfo, GitProvider
from .ddev_manager import DDEVManager

__all__ = [
    "WorkspaceManager", 
    "CustomerWorkspace", 
    "WorkspaceStatus",
    "RepositoryManager",
    "RepositoryInfo",
    "GitProvider",
    "DDEVManager",
]
