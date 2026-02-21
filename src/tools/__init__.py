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

# Git tools
try:
    from .git_tools import (
        GitBranchTool,
        GitCommitTool,
        GitStatusTool,
        GitLogTool,
    )
except ImportError:
    GitBranchTool = None
    GitCommitTool = None
    GitStatusTool = None
    GitLogTool = None

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
    # Git Tools (may be None if import failed)
    "GitBranchTool",
    "GitCommitTool",
    "GitStatusTool",
    "GitLogTool",
    # Code Tools (may be None if import failed)
    "CodeGenerateTool",
    "CodeAnalyzeTool",
    "CodeRefactorTool",
    "CodeTestTool",
    "CodeReviewTool",
]
