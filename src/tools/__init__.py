"""Tool-Use Framework for Mohami AI Agents.

This module provides the infrastructure for tool-based AI interactions,
following the OpenAI Function Calling pattern.
"""

from .base import BaseTool, ToolResult, ToolParameter, ToolParameterType
from .registry import ToolRegistry
from .executor import ToolExecutor

# Local file system tools
from .file_tools import (
    FileReadTool,
    FileWriteTool,
    FileListTool,
    FileSearchTool,
)

# Git tools (local and remote)
try:
    from .git_tools import (
        # Local Git tools
        GitBranchTool,
        GitCommitTool,
        GitStatusTool,
        GitLogTool,
        # Remote GitHub tools
        GitHubReadFileTool,
        GitHubWriteFileTool,
        GitHubListFilesTool,
        GitHubCreateBranchTool,
        GitHubGetRepoInfoTool,
        # Backward compatibility aliases
        ReadFileTool,
        WriteFileTool,
        ListFilesTool,
        CreateBranchTool,
        GetRepoInfoTool,
    )
except ImportError:
    GitBranchTool = None
    GitCommitTool = None
    GitStatusTool = None
    GitLogTool = None
    GitHubReadFileTool = None
    GitHubWriteFileTool = None
    GitHubListFilesTool = None
    GitHubCreateBranchTool = None
    GitHubGetRepoInfoTool = None
    ReadFileTool = None
    WriteFileTool = None
    ListFilesTool = None
    CreateBranchTool = None
    GetRepoInfoTool = None

# Code tools
try:
    from .code_tools import (
        CodeGenerateTool,
        CodeAnalyzeTool,
        CodeRefactorTool,
        CodeTestTool,
        CodeReviewTool,
    )
except ImportError:
    CodeGenerateTool = None
    CodeAnalyzeTool = None
    CodeRefactorTool = None
    CodeTestTool = None
    CodeReviewTool = None

# DDEV tools
try:
    from .ddev_tools import (
        DDEVExecuteTool,
        DDEVShopwareCommandTool,
        DDEVTestTool,
        DDEVComposerTool,
        DDEVStatusTool,
        DDEVGitSyncTool,
    )
except ImportError:
    DDEVExecuteTool = None
    DDEVShopwareCommandTool = None
    DDEVTestTool = None
    DDEVComposerTool = None
    DDEVStatusTool = None
    DDEVGitSyncTool = None

__all__ = [
    # Base classes
    "BaseTool",
    "ToolResult",
    "ToolParameter",
    "ToolParameterType",
    # Infrastructure
    "ToolRegistry",
    "ToolExecutor",
    # File Tools
    "FileReadTool",
    "FileWriteTool",
    "FileListTool",
    "FileSearchTool",
    # Local Git Tools (may be None if import failed)
    "GitBranchTool",
    "GitCommitTool",
    "GitStatusTool",
    "GitLogTool",
    # Remote GitHub Tools (may be None if import failed)
    "GitHubReadFileTool",
    "GitHubWriteFileTool",
    "GitHubListFilesTool",
    "GitHubCreateBranchTool",
    "GitHubGetRepoInfoTool",
    # Backward compatibility aliases
    "ReadFileTool",
    "WriteFileTool",
    "ListFilesTool",
    "CreateBranchTool",
    "GetRepoInfoTool",
    # Code Tools (may be None if import failed)
    "CodeGenerateTool",
    "CodeAnalyzeTool",
    "CodeRefactorTool",
    "CodeTestTool",
    "CodeReviewTool",
    # DDEV Tools (may be None if import failed)
    "DDEVExecuteTool",
    "DDEVShopwareCommandTool",
    "DDEVTestTool",
    "DDEVComposerTool",
    "DDEVStatusTool",
    "DDEVGitSyncTool",
]
