"""Customer Workspace Manager for DDEV-based development environments.

This module manages isolated development workspaces for multiple customers,
with automatic repository cloning and DDEV integration.

RICHTIGER WORKFLOW:
1. Kunde konfiguriert in config/customers.yaml
2. Agent ruft WorkspaceManager.setup_workspace():
   - Cloned repo nach ~/ki-data/workspaces/{customer}/
   - Wenn has_ddev: startet DDEV im geklonten Repo
   - Sonst: nutzt Container direkt
3. Agent arbeitet lokal im Workspace
4. Commit & Push zurück
"""

import os
import re
import yaml
import shutil
import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime

from .repository_manager import RepositoryManager, GitProvider, get_repository_manager

logger = logging.getLogger(__name__)


class WorkspaceStatus(Enum):
    """Status of a customer workspace."""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    CLONING = "cloning"
    READY = "ready"
    DDEV_RUNNING = "ddev_running"
    DDEV_STOPPED = "ddev_stopped"
    ERROR = "error"


@dataclass
class CustomerWorkspace:
    """Represents a customer workspace configuration."""
    customer_id: str
    repository: Optional[str]
    name: str
    git_provider: str  # github, bitbucket, gitlab
    repo_url: str
    has_ddev: bool
    default_branch: str
    workspace_path: Path
    tech_stack: Dict[str, Any] = field(default_factory=dict)
    auth_token: Optional[str] = None
    status: WorkspaceStatus = WorkspaceStatus.NOT_INITIALIZED
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    ddev_started: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def ddev_config_path(self) -> Path:
        """Get the DDEV config directory path."""
        return self.workspace_path / ".ddev"
    
    @property
    def has_ddev_config(self) -> bool:
        """Check if the cloned repo has DDEV configuration."""
        return (self.workspace_path / ".ddev" / "config.yaml").exists()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workspace to dictionary."""
        return {
            "customer_id": self.customer_id,
            "repository": self.repository,
            "name": self.name,
            "git_provider": self.git_provider,
            "repo_url": self.repo_url,
            "has_ddev": self.has_ddev,
            "default_branch": self.default_branch,
            "workspace_path": str(self.workspace_path),
            "tech_stack": self.tech_stack,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "ddev_started": self.ddev_started,
            "has_ddev_config": self.has_ddev_config,
        }


class WorkspaceManager:
    """Manages customer workspaces with repository cloning and DDEV integration.
    
    This class provides methods to:
    - Setup new customer workspaces by cloning repositories
    - Start/stop DDEV environments (if present in cloned repo)
    - Execute commands in DDEV containers or locally
    - Sync changes to repositories
    """
    
    def __init__(self, config_path: str = "config/customers.yaml"):
        """Initialize the workspace manager.
        
        Args:
            config_path: Path to the customers configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.workspaces: Dict[str, CustomerWorkspace] = {}
        self.default_workspace_for_customer: Dict[str, str] = {}
        self.repo_manager = get_repository_manager()
        self._load_workspaces()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load the customer configuration from YAML."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return {"customers": {}}
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f) or {}

    def _normalize_repo_ref(self, repo_value: str, provider: str) -> str:
        """Normalize repo references like owner/repo to cloneable URLs."""
        if not repo_value:
            return ""
        if repo_value.startswith(("https://", "git@")):
            return repo_value
        if "/" in repo_value:
            if provider == "bitbucket":
                return f"https://bitbucket.org/{repo_value}"
            if provider == "gitlab":
                return f"https://gitlab.com/{repo_value}"
            return f"https://github.com/{repo_value}"
        return repo_value

    def _workspace_key(self, customer_id: str, repository: Optional[str]) -> str:
        if not repository:
            return customer_id
        safe = repository.replace("/", "__")
        return f"{customer_id}__{safe}"

    def _resolve_auth_token(self, token_value: Optional[str]) -> Optional[str]:
        """Support plain tokens and ${ENV_VAR} references."""
        if not token_value:
            return None
        token_value = token_value.strip()
        if token_value.startswith("${") and token_value.endswith("}"):
            env_name = token_value[2:-1].strip()
            return os.getenv(env_name) or None
        return token_value

    def _resolve_workspace(self, customer_id: str, repository: Optional[str] = None) -> Optional[CustomerWorkspace]:
        """Resolve workspace by customer+repository, with fallback to customer default."""
        if repository:
            ws = self.workspaces.get(self._workspace_key(customer_id, repository))
            if ws:
                return ws
        default_key = self.default_workspace_for_customer.get(customer_id)
        if default_key:
            return self.workspaces.get(default_key)
        return self.workspaces.get(customer_id)
    
    def _load_workspaces(self):
        """Load existing workspaces from configuration."""
        customers = self.config.get('customers', {})
        base_workspace_path = Path("~/ki-data/workspaces").expanduser().resolve()
        self.workspaces = {}
        self.default_workspace_for_customer = {}

        for customer_id, customer_config in customers.items():
            provider = customer_config.get('git_provider', 'github')
            customer_name = customer_config.get('name', customer_config.get('display_name', customer_id))
            repositories = customer_config.get('repositories', [])
            resolved_auth_token = self._resolve_auth_token(customer_config.get('auth_token'))
            if not resolved_auth_token and provider == "github":
                resolved_auth_token = os.getenv("GITHUB_TOKEN")

            # Legacy single-repo fallback
            if not repositories:
                repo_url = customer_config.get('repo_url', '')
                if repo_url:
                    repositories = [{
                        "repo": repo_url,
                        "default_branch": customer_config.get('default_branch', 'main'),
                        "tech_stack": customer_config.get('tech_stack', {}),
                    }]

            for idx, repo_cfg in enumerate(repositories):
                if isinstance(repo_cfg, str):
                    repo_cfg = {"repo": repo_cfg}

                repo_ref = str(repo_cfg.get("repo", "")).strip()
                repo_url = self._normalize_repo_ref(repo_ref, provider)
                repo_branch = repo_cfg.get('default_branch', customer_config.get('default_branch', 'main'))
                repo_tech = repo_cfg.get('tech_stack', customer_config.get('tech_stack', {}))
                if not repo_tech:
                    repo_tech = {
                        "type": customer_config.get('shopware', {}).get('version', 'unknown'),
                        "php_version": customer_config.get('ddev', {}).get('php_version', '8.2'),
                    }

                workspace_path = customer_config.get('workspace_path')
                if workspace_path:
                    workspace_path = Path(workspace_path).expanduser().resolve()
                else:
                    # Separate workspace per repository to avoid collisions.
                    repo_slug = repo_ref.split("/")[-1] if repo_ref else f"repo-{idx+1}"
                    workspace_path = base_workspace_path / customer_id / repo_slug

                workspace = CustomerWorkspace(
                    customer_id=customer_id,
                    repository=repo_ref or None,
                    name=customer_name,
                    git_provider=provider,
                    repo_url=repo_url,
                    has_ddev=customer_config.get('has_ddev', customer_config.get('ddev', {}).get('enabled', True)),
                    default_branch=repo_branch,
                    workspace_path=workspace_path,
                    tech_stack=repo_tech,
                    auth_token=resolved_auth_token,
                )

                # Check if workspace already exists
                if workspace.workspace_path.exists() and (workspace.workspace_path / ".git").exists():
                    workspace.status = WorkspaceStatus.READY
                    if workspace.has_ddev_config:
                        ddev_status = self._check_ddev_status(workspace.workspace_path)
                        if ddev_status == "running":
                            workspace.status = WorkspaceStatus.DDEV_RUNNING
                            workspace.ddev_started = True
                        elif ddev_status == "stopped":
                            workspace.status = WorkspaceStatus.DDEV_STOPPED

                key = self._workspace_key(customer_id, workspace.repository)
                self.workspaces[key] = workspace
                if customer_id not in self.default_workspace_for_customer:
                    self.default_workspace_for_customer[customer_id] = key
    
    def _check_ddev_status(self, workspace_path: Path) -> str:
        """Check if DDEV is running in the workspace.
        
        Args:
            workspace_path: Path to the workspace
            
        Returns:
            Status string: 'running', 'stopped', 'not_configured', or 'unknown'
        """
        # First check if .ddev/config.yaml exists
        if not (workspace_path / ".ddev" / "config.yaml").exists():
            return "not_configured"
        
        try:
            result = subprocess.run(
                ["ddev", "status", "--json-output"],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                import json
                status_data = json.loads(result.stdout)
                return status_data.get('raw', {}).get('status', 'unknown')
        except FileNotFoundError:
            logger.debug("DDEV not found in PATH")
            return "not_installed"
        except Exception as e:
            logger.debug(f"Could not check DDEV status: {e}")
        return "unknown"
    
    def get_workspace(self, customer_id: str, repository: Optional[str] = None) -> Optional[CustomerWorkspace]:
        """Get a workspace by customer and optional repository."""
        return self._resolve_workspace(customer_id, repository)
    
    def list_workspaces(self) -> List[CustomerWorkspace]:
        """List all configured workspaces."""
        return list(self.workspaces.values())
    
    def setup_workspace(
        self, 
        customer_id: str, 
        repository: Optional[str] = None,
        repo_url: Optional[str] = None,
        branch: Optional[str] = None,
        start_ddev: bool = True
    ) -> Tuple[bool, str]:
        """Setup a new workspace for a customer by cloning the repository.
        
        This is the main entry point for setting up a workspace:
        1. Clones the repository from config or provided URL
        2. If DDEV config exists in repo: starts DDEV
        3. Otherwise: workspace is ready for direct container usage
        
        Args:
            customer_id: The customer identifier (e.g., 'test-customer')
            repo_url: Optional repository URL to clone (overrides config)
            branch: Optional branch to clone
            start_ddev: Whether to start DDEV if config exists
            
        Returns:
            Tuple of (success, message)
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            # Try to create from URL directly
            if repo_url:
                workspace = CustomerWorkspace(
                    customer_id=customer_id,
                    repository=repository,
                    name=customer_id,
                    git_provider="github",
                    repo_url=repo_url,
                    has_ddev=False,
                    default_branch=branch or "main",
                    workspace_path=self.repo_manager.get_workspace_path(
                        self._workspace_key(customer_id, repository)
                    ),
                )
                key = self._workspace_key(customer_id, repository)
                self.workspaces[key] = workspace
                self.default_workspace_for_customer.setdefault(customer_id, key)
            else:
                return False, (
                    f"Customer '{customer_id}' not found in configuration"
                    + (f" for repository '{repository}'" if repository else "")
                )
        
        if workspace.status == WorkspaceStatus.INITIALIZING:
            return False, f"Workspace for '{customer_id}' is already being initialized"
        
        try:
            workspace.status = WorkspaceStatus.INITIALIZING
            
            # Determine repository URL
            clone_url = repo_url or workspace.repo_url
            
            if not clone_url:
                workspace.status = WorkspaceStatus.ERROR
                return False, f"No repository URL configured for '{customer_id}'"
            
            # Clone repository using RepositoryManager
            logger.info(f"Cloning repository {clone_url} for customer {customer_id}")
            workspace.status = WorkspaceStatus.CLONING
            
            success, message = self.repo_manager.clone_repo(
                customer_id=self._workspace_key(workspace.customer_id, workspace.repository),
                repo_url=clone_url,
                branch=branch or workspace.default_branch,
                auth_token=workspace.auth_token
            )
            
            if not success:
                workspace.status = WorkspaceStatus.ERROR
                return False, message
            
            # Check if the cloned repo has DDEV config
            has_ddev = workspace.has_ddev_config
            workspace.has_ddev = has_ddev
            
            if has_ddev and start_ddev:
                # Start DDEV in the cloned repository
                logger.info(f"Starting DDEV for {customer_id}")
                ddev_success, ddev_message = self.start_ddev(customer_id, workspace.repository)
                if ddev_success:
                    workspace.status = WorkspaceStatus.DDEV_RUNNING
                    workspace.ddev_started = True
                    message += f". DDEV started: {ddev_message}"
                else:
                    workspace.status = WorkspaceStatus.READY
                    message += f". DDEV failed to start: {ddev_message}"
            else:
                workspace.status = WorkspaceStatus.READY
                if has_ddev:
                    message += ". DDEV config found but not started (start_ddev=False)"
                else:
                    message += ". No DDEV config found - using container directly"
            
            workspace.last_accessed = datetime.now()
            
            return True, message
            
        except Exception as e:
            workspace.status = WorkspaceStatus.ERROR
            logger.error(f"Error setting up workspace for {customer_id}: {e}")
            return False, f"Error setting up workspace: {str(e)}"
    
    def start_ddev(self, customer_id: str, repository: Optional[str] = None) -> Tuple[bool, str]:
        """Start the DDEV environment for a customer.
        
        DDEV runs IN the cloned repository, not as a separate container.
        
        Args:
            customer_id: The customer identifier
            
        Returns:
            Tuple of (success, message)
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return False, f"Customer '{customer_id}' not found"
        
        if not workspace.workspace_path.exists():
            return False, f"Workspace for '{customer_id}' not initialized. Run setup_workspace first."
        
        # Check if DDEV config exists
        if not workspace.has_ddev_config:
            return False, f"No DDEV configuration found in {workspace.workspace_path}"
        
        try:
            logger.info(f"Starting DDEV for {customer_id}")
            
            result = subprocess.run(
                ["ddev", "start"],
                cwd=str(workspace.workspace_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                workspace.status = WorkspaceStatus.DDEV_RUNNING
                workspace.ddev_started = True
                workspace.last_accessed = datetime.now()
                return True, f"DDEV started successfully for '{customer_id}'"
            else:
                workspace.status = WorkspaceStatus.ERROR
                return False, f"Failed to start DDEV: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout while starting DDEV"
        except FileNotFoundError:
            return False, "DDEV not found in PATH. Please install DDEV."
        except Exception as e:
            workspace.status = WorkspaceStatus.ERROR
            return False, f"Error starting DDEV: {str(e)}"
    
    def stop_ddev(self, customer_id: str, repository: Optional[str] = None, remove_data: bool = False) -> Tuple[bool, str]:
        """Stop the DDEV environment for a customer.
        
        Args:
            customer_id: The customer identifier
            remove_data: If True, remove containers and volumes (ddev delete)
            
        Returns:
            Tuple of (success, message)
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return False, f"Customer '{customer_id}' not found"
        
        try:
            if remove_data:
                result = subprocess.run(
                    ["ddev", "delete", "-y"],
                    cwd=str(workspace.workspace_path),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            else:
                result = subprocess.run(
                    ["ddev", "stop"],
                    cwd=str(workspace.workspace_path),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            
            if result.returncode == 0:
                workspace.status = WorkspaceStatus.DDEV_STOPPED if not remove_data else WorkspaceStatus.READY
                workspace.ddev_started = False
                return True, f"DDEV {'deleted' if remove_data else 'stopped'} successfully for '{customer_id}'"
            else:
                return False, f"Failed to stop DDEV: {result.stderr}"
                
        except Exception as e:
            return False, f"Error stopping DDEV: {str(e)}"
    
    def execute_command(
        self, 
        customer_id: str, 
        repository: Optional[str],
        command: str, 
        timeout: int = 300,
        cwd: Optional[str] = None,
        use_ddev: bool = True
    ) -> Tuple[bool, str, str]:
        """Execute a command in the customer's workspace.
        
        If DDEV is running and use_ddev=True, executes inside DDEV.
        Otherwise, executes locally in the workspace.
        
        Args:
            customer_id: The customer identifier
            command: The command to execute
            timeout: Timeout in seconds
            cwd: Working directory relative to workspace root
            use_ddev: Whether to use DDEV if available
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return False, "", f"Customer '{customer_id}' not found"
        
        # Determine working directory
        work_dir = workspace.workspace_path
        if cwd:
            work_dir = work_dir / cwd
        
        # Use DDEV if available and running
        if use_ddev and workspace.has_ddev_config and workspace.ddev_started:
            return self.execute_in_ddev(customer_id, repository, command, timeout, cwd)
        
        # Execute locally
        try:
            logger.debug(f"Executing locally [{customer_id}]: {command}")
            
            result = subprocess.run(
                command,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", f"Error executing command: {str(e)}"
    
    def execute_in_ddev(
        self, 
        customer_id: str, 
        repository: Optional[str],
        command: str, 
        timeout: int = 300,
        cwd: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """Execute a command inside the DDEV container.
        
        Args:
            customer_id: The customer identifier
            command: The command to execute
            timeout: Timeout in seconds
            cwd: Working directory inside the container (relative to project root)
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return False, "", f"Customer '{customer_id}' not found"
        
        # Ensure DDEV is running
        if not workspace.ddev_started:
            success, msg = self.start_ddev(customer_id, repository)
            if not success:
                return False, "", f"DDEV not running and could not start: {msg}"
        
        try:
            cmd_parts = ["ddev", "exec"]
            
            if cwd:
                cmd_parts.extend(["-d", cwd])
            
            cmd_parts.append(command)
            
            logger.debug(f"Executing in DDEV [{customer_id}]: {command}")
            
            result = subprocess.run(
                cmd_parts,
                cwd=str(workspace.workspace_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", f"Error executing command: {str(e)}"
    
    def sync_to_repo(
        self, 
        customer_id: str, 
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Sync workspace changes to the Git repository.
        
        Args:
            customer_id: The customer identifier
            branch: Branch to push to (uses default if not specified)
            commit_message: Commit message (auto-generated if not specified)
            
        Returns:
            Tuple of (success, message)
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return False, f"Customer '{customer_id}' not found"
        
        # Use RepositoryManager to push changes
        return self.repo_manager.push_changes(
            customer_id=self._workspace_key(workspace.customer_id, workspace.repository),
            branch=branch or workspace.default_branch,
            message=commit_message
        )
    
    def pull_changes(self, customer_id: str, repository: Optional[str] = None, branch: Optional[str] = None) -> Tuple[bool, str]:
        """Pull latest changes from remote repository.
        
        Args:
            customer_id: The customer identifier
            branch: Optional branch to pull
            
        Returns:
            Tuple of (success, message)
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return False, f"Customer '{customer_id}' not found"
        return self.repo_manager.pull_changes(
            self._workspace_key(workspace.customer_id, workspace.repository), branch
        )
    
    def get_repo_info(self, customer_id: str, repository: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get repository information for a customer.
        
        Args:
            customer_id: The customer identifier
            
        Returns:
            Repository info dictionary or None
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return None
        return self.repo_manager.get_repo_info(
            self._workspace_key(workspace.customer_id, workspace.repository)
        )
    
    def get_status(self, customer_id: str, repository: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed status of a workspace.
        
        Args:
            customer_id: The customer identifier
            
        Returns:
            Dictionary with status information
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return {"error": f"Customer '{customer_id}' not found"}
        
        status = {
            "customer_id": customer_id,
            "name": workspace.name,
            "repository": workspace.repository,
            "workspace_path": str(workspace.workspace_path),
            "status": workspace.status.value,
            "exists": workspace.workspace_path.exists(),
            "repo_url": workspace.repo_url,
            "has_ddev_config": workspace.has_ddev_config,
            "ddev_started": workspace.ddev_started,
            "tech_stack": workspace.tech_stack,
        }
        
        # Get DDEV status if configured
        if workspace.has_ddev_config:
            ddev_status = self._check_ddev_status(workspace.workspace_path)
            status["ddev_status"] = ddev_status
        
        # Get repository info
        repo_info = self.repo_manager.get_repo_info(
            self._workspace_key(workspace.customer_id, workspace.repository)
        )
        if repo_info:
            status["repository"] = repo_info
        
        return status
    
    def run_tests(
        self, 
        customer_id: str, 
        repository: Optional[str] = None,
        test_command: Optional[str] = None,
        use_ddev: bool = True,
        timeout: int = 600
    ) -> Tuple[bool, str, str]:
        """Run tests in the customer's workspace.
        
        Args:
            customer_id: The customer identifier
            test_command: Test command (auto-detected if not provided)
            use_ddev: Whether to use DDEV if available
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return False, "", f"Customer '{customer_id}' not found"
        
        # Auto-detect test command based on tech stack
        if not test_command:
            tech_type = workspace.tech_stack.get('type', 'unknown')
            if tech_type == 'python':
                test_command = 'python -m pytest'
            elif tech_type == 'php' or 'shopware' in tech_type.lower():
                test_command = 'vendor/bin/phpunit'
            else:
                test_command = 'echo "No test command configured"'
        
        return self.execute_command(
            customer_id=customer_id,
            repository=repository,
            command=test_command,
            timeout=timeout,
            use_ddev=use_ddev
        )
    
    def cleanup_workspace(self, customer_id: str, repository: Optional[str] = None, remove_all: bool = False) -> Tuple[bool, str]:
        """Clean up a workspace.
        
        Args:
            customer_id: The customer identifier
            remove_all: If True, remove the entire workspace directory
            
        Returns:
            Tuple of (success, message)
        """
        workspace = self._resolve_workspace(customer_id, repository)
        if not workspace:
            return False, f"Customer '{customer_id}' not found"
        
        try:
            # Stop DDEV first if running
            if workspace.ddev_started:
                self.stop_ddev(customer_id, repository=repository, remove_data=True)
            
            if remove_all:
                # Remove entire workspace using RepositoryManager
                return self.repo_manager.cleanup_repo(
                    self._workspace_key(workspace.customer_id, workspace.repository)
                )
            else:
                # Just clean temporary files
                for cleanup_path in ['var/cache', 'var/log', '__pycache__', '.pytest_cache']:
                    path = workspace.workspace_path / cleanup_path
                    if path.exists():
                        shutil.rmtree(path, ignore_errors=True)
                return True, f"Temporary files cleaned for '{customer_id}'"
                
        except Exception as e:
            return False, f"Error cleaning up workspace: {str(e)}"
    
    def list_available_workspaces(self) -> List[Dict[str, Any]]:
        """List all available workspaces with their status.
        
        Returns:
            List of workspace info dictionaries
        """
        return [ws.to_dict() for ws in self.workspaces.values()]
    
    def reload_config(self):
        """Reload the configuration from file."""
        self.config = self._load_config()
        self._load_workspaces()


# Singleton instance for application-wide use
_workspace_manager_instance: Optional[WorkspaceManager] = None


def get_workspace_manager(config_path: str = "config/customers.yaml") -> WorkspaceManager:
    """Get or create the singleton WorkspaceManager instance."""
    global _workspace_manager_instance
    if _workspace_manager_instance is None:
        _workspace_manager_instance = WorkspaceManager(config_path)
    return _workspace_manager_instance
