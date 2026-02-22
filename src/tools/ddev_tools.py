"""DDEV Tools for Agent integration.

This module provides tools that agents can use to interact with customer workspaces.
DDEV runs INSIDE the cloned repository, not as separate containers.
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass

from .base import BaseTool, ToolResult, ToolParameter, ToolParameterType
from ..infrastructure.workspace_manager import get_workspace_manager, WorkspaceStatus

logger = logging.getLogger(__name__)


class DDEVExecuteTool(BaseTool):
    """Tool to execute commands inside a customer's workspace.
    
    If DDEV is configured and running, commands execute inside DDEV.
    Otherwise, commands execute locally in the workspace.
    """
    
    name = "ddev_execute"
    description = """Execute a command inside a customer's workspace.

This tool runs commands in the customer's cloned repository.
If DDEV is configured in the repo and running, commands run inside DDEV.
Otherwise, commands run locally in the workspace.

Use this tool to:
- Run CLI commands (e.g., bin/console for Shopware)
- Run package manager commands (composer, npm, pip)
- Execute shell commands in the customer environment
- Run tests

Examples:
- "bin/console cache:clear" → Clears Shopware cache (in DDEV)
- "composer install" → Installs PHP dependencies
- "python -m pytest" → Runs Python tests
- "ls -la" → Lists files in project root
- "npm run build" → Builds frontend assets
"""
    
    parameters = [
        ToolParameter(
            name="customer_id",
            description="Customer ID (e.g., 'test-customer')",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="repository",
            description="Optional repository slug (e.g., 'owner/repo') for customers with multiple repositories",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
        ToolParameter(
            name="command",
            description="Command to execute in the workspace",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="working_dir",
            description="Working directory relative to workspace root (default: project root)",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
        ToolParameter(
            name="use_ddev",
            description="Use DDEV if available (default: true)",
            type=ToolParameterType.BOOLEAN,
            required=False,
            default=True
        ),
        ToolParameter(
            name="timeout",
            description="Timeout in seconds (default: 300)",
            type=ToolParameterType.INTEGER,
            required=False,
            default=300
        )
    ]
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = get_workspace_manager()
    
    async def run(self, customer_id: str, repository: str = "", command: str = "", 
                  working_dir: str = "", use_ddev: bool = True,
                  timeout: int = 300) -> ToolResult:
        """Execute a command in the customer's workspace.
        
        Args:
            customer_id: The customer identifier
            command: Command to execute
            working_dir: Optional working directory
            use_ddev: Whether to use DDEV if available
            timeout: Timeout in seconds
            
        Returns:
            ToolResult with execution output
        """
        import time
        start_time = time.time()
        
        try:
            # Check if workspace exists
            workspace = self.workspace_manager.get_workspace(customer_id, repository or None)
            if not workspace:
                return ToolResult.error_result(
                    error=f"Customer '{customer_id}' not found. "
                          f"Available: {', '.join(self.workspace_manager.workspaces.keys())}",
                    tool_name=self.name
                )
            
            # Check if workspace is initialized
            if workspace.status == WorkspaceStatus.NOT_INITIALIZED:
                return ToolResult.error_result(
                    error=f"Workspace for '{customer_id}' not initialized. "
                          f"Run setup_workspace first.",
                    tool_name=self.name
                )
            
            # Execute command
            success, stdout, stderr = self.workspace_manager.execute_command(
                customer_id=customer_id,
                repository=repository or None,
                command=command,
                timeout=timeout,
                cwd=working_dir if working_dir else None,
                use_ddev=use_ddev
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Build result
            result_data = {
                "customer_id": customer_id,
                "command": command,
                "workspace_path": str(workspace.workspace_path),
                "used_ddev": use_ddev and workspace.has_ddev_config and workspace.ddev_started,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": 0 if success else 1
            }
            
            if success:
                return ToolResult.success_result(
                    data=result_data,
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
            else:
                return ToolResult.error_result(
                    error=f"Command failed: {stderr or stdout}",
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult.error_result(
                error=f"Error executing command: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=self.name
            )


class WorkspaceSetupTool(BaseTool):
    """Tool to setup a workspace for a customer."""
    
    name = "workspace_setup"
    description = """Setup a workspace for a customer by cloning their repository.

This tool:
1. Clones the repository from config/customers.yaml
2. If DDEV config exists: starts DDEV
3. Otherwise: workspace is ready for direct usage

Use this BEFORE working on a customer project.
"""
    
    parameters = [
        ToolParameter(
            name="customer_id",
            description="Customer ID (e.g., 'test-customer')",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="repository",
            description="Optional repository slug (e.g., 'owner/repo') for customers with multiple repositories",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
        ToolParameter(
            name="branch",
            description="Optional branch to clone (uses default from config if not specified)",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
        ToolParameter(
            name="start_ddev",
            description="Start DDEV if config exists (default: true)",
            type=ToolParameterType.BOOLEAN,
            required=False,
            default=True
        )
    ]
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = get_workspace_manager()
    
    async def run(self, customer_id: str, repository: str = "", branch: str = "", 
                  start_ddev: bool = True) -> ToolResult:
        """Setup workspace for a customer.
        
        Args:
            customer_id: The customer identifier
            branch: Optional branch to clone
            start_ddev: Whether to start DDEV
            
        Returns:
            ToolResult with setup result
        """
        import time
        start_time = time.time()
        
        try:
            success, message = self.workspace_manager.setup_workspace(
                customer_id=customer_id,
                repository=repository or None,
                branch=branch if branch else None,
                start_ddev=start_ddev
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if success:
                workspace = self.workspace_manager.get_workspace(customer_id, repository or None)
                return ToolResult.success_result(
                    data={
                        "customer_id": customer_id,
                        "workspace_path": str(workspace.workspace_path) if workspace else None,
                        "status": workspace.status.value if workspace else None,
                        "has_ddev": workspace.has_ddev_config if workspace else False,
                        "message": message
                    },
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
            else:
                return ToolResult.error_result(
                    error=message,
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult.error_result(
                error=f"Error setting up workspace: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=self.name
            )


class WorkspaceStatusTool(BaseTool):
    """Tool to check workspace status."""
    
    name = "workspace_status"
    description = """Check the status of a customer's workspace.

Shows:
- Workspace path
- Repository status
- DDEV status (if configured)
- Current branch and commit
"""
    
    parameters = [
        ToolParameter(
            name="customer_id",
            description="Customer ID (e.g., 'test-customer')",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="repository",
            description="Optional repository slug (e.g., 'owner/repo') for customers with multiple repositories",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = get_workspace_manager()
    
    async def run(self, customer_id: str, repository: str = "") -> ToolResult:
        """Get workspace status.
        
        Args:
            customer_id: The customer identifier
            
        Returns:
            ToolResult with status information
        """
        import time
        start_time = time.time()
        
        try:
            status = self.workspace_manager.get_status(customer_id, repository or None)
            
            execution_time = (time.time() - start_time) * 1000
            
            if "error" in status:
                return ToolResult.error_result(
                    error=status["error"],
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
            
            return ToolResult.success_result(
                data=status,
                execution_time_ms=execution_time,
                tool_name=self.name
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult.error_result(
                error=f"Error getting status: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=self.name
            )


class DDEVStartTool(BaseTool):
    """Tool to start DDEV for a customer."""
    
    name = "ddev_start"
    description = """Start DDEV for a customer workspace.

Only works if the cloned repository has a .ddev/config.yaml file.
DDEV runs inside the workspace directory, not as a separate container.
"""
    
    parameters = [
        ToolParameter(
            name="customer_id",
            description="Customer ID (e.g., 'test-customer')",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="repository",
            description="Optional repository slug (e.g., 'owner/repo') for customers with multiple repositories",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = get_workspace_manager()
    
    async def run(self, customer_id: str, repository: str = "") -> ToolResult:
        """Start DDEV for a customer.
        
        Args:
            customer_id: The customer identifier
            
        Returns:
            ToolResult with start result
        """
        import time
        start_time = time.time()
        
        try:
            success, message = self.workspace_manager.start_ddev(customer_id, repository or None)
            
            execution_time = (time.time() - start_time) * 1000
            
            if success:
                return ToolResult.success_result(
                    data={
                        "customer_id": customer_id,
                        "message": message
                    },
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
            else:
                return ToolResult.error_result(
                    error=message,
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult.error_result(
                error=f"Error starting DDEV: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=self.name
            )


class DDEVStopTool(BaseTool):
    """Tool to stop DDEV for a customer."""
    
    name = "ddev_stop"
    description = """Stop DDEV for a customer workspace."""
    
    parameters = [
        ToolParameter(
            name="customer_id",
            description="Customer ID (e.g., 'test-customer')",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="repository",
            description="Optional repository slug (e.g., 'owner/repo') for customers with multiple repositories",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
        ToolParameter(
            name="delete",
            description="Delete DDEV containers and volumes (default: false)",
            type=ToolParameterType.BOOLEAN,
            required=False,
            default=False
        )
    ]
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = get_workspace_manager()
    
    async def run(self, customer_id: str, repository: str = "", delete: bool = False) -> ToolResult:
        """Stop DDEV for a customer.
        
        Args:
            customer_id: The customer identifier
            delete: Whether to delete containers and volumes
            
        Returns:
            ToolResult with stop result
        """
        import time
        start_time = time.time()
        
        try:
            success, message = self.workspace_manager.stop_ddev(
                customer_id, repository=repository or None, remove_data=delete
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if success:
                return ToolResult.success_result(
                    data={
                        "customer_id": customer_id,
                        "deleted": delete,
                        "message": message
                    },
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
            else:
                return ToolResult.error_result(
                    error=message,
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult.error_result(
                error=f"Error stopping DDEV: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=self.name
            )


class TestRunnerTool(BaseTool):
    """Tool to run tests in a customer's workspace."""
    
    name = "run_tests"
    description = """Run tests in a customer's workspace.

Auto-detects test command based on tech_stack configuration.
- Python projects: python -m pytest
- PHP/Shopware: vendor/bin/phpunit
- Can override with custom command

Use this tool to verify code changes.
"""
    
    parameters = [
        ToolParameter(
            name="customer_id",
            description="Customer ID (e.g., 'test-customer')",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="repository",
            description="Optional repository slug (e.g., 'owner/repo') for customers with multiple repositories",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
        ToolParameter(
            name="test_command",
            description="Custom test command (auto-detected if not provided)",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
        ToolParameter(
            name="use_ddev",
            description="Use DDEV if available (default: true)",
            type=ToolParameterType.BOOLEAN,
            required=False,
            default=True
        ),
        ToolParameter(
            name="timeout",
            description="Timeout in seconds (default: 600)",
            type=ToolParameterType.INTEGER,
            required=False,
            default=600
        )
    ]
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = get_workspace_manager()
    
    async def run(self, customer_id: str, repository: str = "", test_command: str = "",
                  use_ddev: bool = True, timeout: int = 600) -> ToolResult:
        """Run tests in the customer's workspace.
        
        Args:
            customer_id: The customer identifier
            test_command: Custom test command
            use_ddev: Whether to use DDEV
            timeout: Timeout in seconds
            
        Returns:
            ToolResult with test results
        """
        import time
        start_time = time.time()
        
        try:
            success, stdout, stderr = self.workspace_manager.run_tests(
                customer_id=customer_id,
                repository=repository or None,
                test_command=test_command if test_command else None,
                use_ddev=use_ddev,
                timeout=timeout
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Parse test results
            result_data = {
                "customer_id": customer_id,
                "command": test_command or "auto-detected",
                "stdout": stdout,
                "stderr": stderr,
                "return_code": 0 if success else 1,
                "passed": success
            }
            
            # Try to extract test counts for PHPUnit
            import re
            tests_match = re.search(r'Tests:\s+(\d+)', stdout)
            failures_match = re.search(r'Failures:\s+(\d+)', stdout)
            
            if tests_match:
                result_data["tests_total"] = int(tests_match.group(1))
            if failures_match:
                result_data["tests_failed"] = int(failures_match.group(1))
            
            # Try to extract for pytest
            passed_match = re.search(r'(\d+) passed', stdout)
            failed_match = re.search(r'(\d+) failed', stdout)
            
            if passed_match:
                result_data["tests_total"] = int(passed_match.group(1)) + int(failed_match.group(1) if failed_match else 0)
            if failed_match:
                result_data["tests_failed"] = int(failed_match.group(1))
            
            if success:
                return ToolResult.success_result(
                    data=result_data,
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
            else:
                return ToolResult.error_result(
                    error=f"Tests failed:\n{stderr or stdout}",
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult.error_result(
                error=f"Error running tests: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=self.name
            )


class GitSyncTool(BaseTool):
    """Tool to sync workspace changes to Git repository."""
    
    name = "git_sync"
    description = """Sync workspace changes to the Git repository.

Commits and pushes all changes to the remote repository.
IMPORTANT: Review your changes before syncing!
"""
    
    parameters = [
        ToolParameter(
            name="customer_id",
            description="Customer ID (e.g., 'test-customer')",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="repository",
            description="Optional repository slug (e.g., 'owner/repo') for customers with multiple repositories",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
        ToolParameter(
            name="commit_message",
            description="Commit message describing the changes",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="branch",
            description="Branch to push to (uses default if not specified)",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        )
    ]
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = get_workspace_manager()
    
    async def run(self, customer_id: str, repository: str = "", commit_message: str = "",
                  branch: str = "") -> ToolResult:
        """Sync workspace changes to repository.
        
        Args:
            customer_id: The customer identifier
            commit_message: Commit message
            branch: Target branch
            
        Returns:
            ToolResult with sync result
        """
        import time
        start_time = time.time()
        
        try:
            success, message = self.workspace_manager.sync_to_repo(
                customer_id=customer_id,
                repository=repository or None,
                branch=branch if branch else None,
                commit_message=commit_message
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if success:
                return ToolResult.success_result(
                    data={
                        "customer_id": customer_id,
                        "branch": branch or "default",
                        "message": message
                    },
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
            else:
                return ToolResult.error_result(
                    error=message,
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult.error_result(
                error=f"Error syncing to repo: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=self.name
            )


class GitPullTool(BaseTool):
    """Tool to pull latest changes from remote repository."""
    
    name = "git_pull"
    description = """Pull latest changes from the remote repository.

Updates the local workspace with changes from the remote.
"""
    
    parameters = [
        ToolParameter(
            name="customer_id",
            description="Customer ID (e.g., 'test-customer')",
            type=ToolParameterType.STRING,
            required=True
        ),
        ToolParameter(
            name="repository",
            description="Optional repository slug (e.g., 'owner/repo') for customers with multiple repositories",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        ),
        ToolParameter(
            name="branch",
            description="Branch to pull (uses current if not specified)",
            type=ToolParameterType.STRING,
            required=False,
            default=""
        )
    ]
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = get_workspace_manager()
    
    async def run(self, customer_id: str, repository: str = "", branch: str = "") -> ToolResult:
        """Pull changes from remote.
        
        Args:
            customer_id: The customer identifier
            branch: Optional branch to pull
            
        Returns:
            ToolResult with pull result
        """
        import time
        start_time = time.time()
        
        try:
            success, message = self.workspace_manager.pull_changes(
                customer_id=customer_id,
                repository=repository or None,
                branch=branch if branch else None
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if success:
                return ToolResult.success_result(
                    data={
                        "customer_id": customer_id,
                        "branch": branch or "current",
                        "message": message
                    },
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
            else:
                return ToolResult.error_result(
                    error=message,
                    execution_time_ms=execution_time,
                    tool_name=self.name
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult.error_result(
                error=f"Error pulling changes: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=self.name
            )


class ListWorkspacesTool(BaseTool):
    """Tool to list all available workspaces."""
    
    name = "list_workspaces"
    description = """List all configured customer workspaces and their status.

Shows available customers, their workspace paths, and current status.
"""
    
    parameters = []
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = get_workspace_manager()
    
    async def run(self) -> ToolResult:
        """List all workspaces.
        
        Returns:
            ToolResult with workspace list
        """
        import time
        start_time = time.time()
        
        try:
            workspaces = self.workspace_manager.list_available_workspaces()
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResult.success_result(
                data={
                    "workspaces": workspaces,
                    "count": len(workspaces)
                },
                execution_time_ms=execution_time,
                tool_name=self.name
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult.error_result(
                error=f"Error listing workspaces: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=self.name
            )


# Tool registry helper
def register_ddev_tools(registry):
    """Register all DDEV and workspace tools with the tool registry.
    
    Args:
        registry: Tool registry instance
    """
    tools = [
        WorkspaceSetupTool(),
        WorkspaceStatusTool(),
        DDEVExecuteTool(),
        DDEVStartTool(),
        DDEVStopTool(),
        TestRunnerTool(),
        GitSyncTool(),
        GitPullTool(),
        ListWorkspacesTool(),
    ]
    
    for tool in tools:
        registry.register_tool(tool)
        logger.info(f"Registered workspace tool: {tool.name}")
