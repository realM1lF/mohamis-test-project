"""DDEV Manager for orchestrating multiple DDEV projects.

This module provides advanced DDEV management capabilities including:
- Multi-project orchestration
- Health monitoring
- Resource management
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class DDEVProjectStatus:
    """Status of a DDEV project."""
    name: str
    status: str  # running, stopped, paused, not_created
    health: str  # healthy, unhealthy, unknown
    urls: List[str]
    php_version: str
    database_type: str
    last_checked: datetime


class DDEVManager:
    """Manages multiple DDEV projects for the KI-Mitarbeiter system."""
    
    def __init__(self):
        """Initialize the DDEV manager."""
        self.project_status: Dict[str, DDEVProjectStatus] = {}
        self._last_global_check: Optional[datetime] = None
    
    def list_all_projects(self) -> List[Dict[str, Any]]:
        """List all DDEV projects on the system.
        
        Returns:
            List of project information dictionaries
        """
        try:
            result = subprocess.run(
                ["ddev", "list", "--json-output"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('raw', [])
            else:
                logger.error(f"Failed to list DDEV projects: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing DDEV projects: {e}")
            return []
    
    def get_project_status(self, project_name: str) -> Optional[DDEVProjectStatus]:
        """Get detailed status of a specific DDEV project.
        
        Args:
            project_name: The DDEV project name
            
        Returns:
            Project status or None if not found
        """
        projects = self.list_all_projects()
        
        for project in projects:
            if project.get('name') == project_name:
                status = DDEVProjectStatus(
                    name=project_name,
                    status=project.get('status', 'unknown'),
                    health=project.get('health', 'unknown'),
                    urls=project.get('urls', []),
                    php_version=project.get('php_version', 'unknown'),
                    database_type=project.get('database_type', 'unknown'),
                    last_checked=datetime.now()
                )
                self.project_status[project_name] = status
                return status
        
        return None
    
    def start_project(self, project_path: Path) -> Tuple[bool, str]:
        """Start a DDEV project.
        
        Args:
            project_path: Path to the DDEV project directory
            
        Returns:
            Tuple of (success, message)
        """
        try:
            result = subprocess.run(
                ["ddev", "start"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, "Project started successfully"
            else:
                return False, f"Failed to start project: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout while starting project"
        except Exception as e:
            return False, f"Error starting project: {str(e)}"
    
    def stop_project(self, project_path: Path, stop_all: bool = False) -> Tuple[bool, str]:
        """Stop a DDEV project.
        
        Args:
            project_path: Path to the DDEV project directory
            stop_all: Stop all DDEV projects
            
        Returns:
            Tuple of (success, message)
        """
        try:
            cmd = ["ddev", "stop"]
            if stop_all:
                cmd.append("--all")
            
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return True, "Project stopped successfully"
            else:
                return False, f"Failed to stop project: {result.stderr}"
                
        except Exception as e:
            return False, f"Error stopping project: {str(e)}"
    
    def restart_project(self, project_path: Path) -> Tuple[bool, str]:
        """Restart a DDEV project.
        
        Args:
            project_path: Path to the DDEV project directory
            
        Returns:
            Tuple of (success, message)
        """
        try:
            result = subprocess.run(
                ["ddev", "restart"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, "Project restarted successfully"
            else:
                return False, f"Failed to restart project: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout while restarting project"
        except Exception as e:
            return False, f"Error restarting project: {str(e)}"
    
    def delete_project(self, project_path: Path, omit_snapshot: bool = True) -> Tuple[bool, str]:
        """Delete a DDEV project (containers and volumes).
        
        Args:
            project_path: Path to the DDEV project directory
            omit_snapshot: Skip creating a snapshot
            
        Returns:
            Tuple of (success, message)
        """
        try:
            cmd = ["ddev", "delete", "-y"]
            if omit_snapshot:
                cmd.append("--omit-snapshot")
            
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return True, "Project deleted successfully"
            else:
                return False, f"Failed to delete project: {result.stderr}"
                
        except Exception as e:
            return False, f"Error deleting project: {str(e)}"
    
    def exec_command(self, project_path: Path, command: str, 
                     service: str = "web",
                     timeout: int = 300) -> Tuple[bool, str, str]:
        """Execute a command inside a DDEV container.
        
        Args:
            project_path: Path to the DDEV project directory
            command: Command to execute
            service: Service to execute in (web, db, etc.)
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            cmd = ["ddev", "exec"]
            if service != "web":
                cmd.extend(["-s", service])
            cmd.append(command)
            
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", f"Error executing command: {str(e)}"
    
    def snapshot_create(self, project_path: Path, 
                        name: Optional[str] = None) -> Tuple[bool, str]:
        """Create a snapshot of the DDEV project.
        
        Args:
            project_path: Path to the DDEV project directory
            name: Optional snapshot name
            
        Returns:
            Tuple of (success, message)
        """
        try:
            cmd = ["ddev", "snapshot"]
            if name:
                cmd.extend(["--name", name])
            
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, f"Snapshot created: {result.stdout}"
            else:
                return False, f"Failed to create snapshot: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout while creating snapshot"
        except Exception as e:
            return False, f"Error creating snapshot: {str(e)}"
    
    def snapshot_restore(self, project_path: Path, 
                         name: str) -> Tuple[bool, str]:
        """Restore a DDEV snapshot.
        
        Args:
            project_path: Path to the DDEV project directory
            name: Snapshot name to restore
            
        Returns:
            Tuple of (success, message)
        """
        try:
            result = subprocess.run(
                ["ddev", "snapshot", "restore", name],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, f"Snapshot restored: {result.stdout}"
            else:
                return False, f"Failed to restore snapshot: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout while restoring snapshot"
        except Exception as e:
            return False, f"Error restoring snapshot: {str(e)}"
    
    def get_logs(self, project_path: Path, service: str = "web",
                 follow: bool = False, tail: Optional[int] = None) -> Tuple[bool, str]:
        """Get logs from a DDEV service.
        
        Args:
            project_path: Path to the DDEV project directory
            service: Service to get logs from (web, db, etc.)
            follow: Follow logs (not supported in this implementation)
            tail: Number of lines to show
            
        Returns:
            Tuple of (success, logs)
        """
        try:
            cmd = ["ddev", "logs"]
            if service != "web":
                cmd.extend(["-s", service])
            if tail:
                cmd.extend(["--tail", str(tail)])
            
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, f"Failed to get logs: {result.stderr}"
                
        except Exception as e:
            return False, f"Error getting logs: {str(e)}"
    
    def import_db(self, project_path: Path, 
                  dump_file: Path) -> Tuple[bool, str]:
        """Import a database dump into the DDEV project.
        
        Args:
            project_path: Path to the DDEV project directory
            dump_file: Path to the database dump file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not dump_file.exists():
                return False, f"Dump file not found: {dump_file}"
            
            result = subprocess.run(
                ["ddev", "import-db", "--file", str(dump_file)],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                return True, "Database imported successfully"
            else:
                return False, f"Failed to import database: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout while importing database"
        except Exception as e:
            return False, f"Error importing database: {str(e)}"
    
    def export_db(self, project_path: Path, 
                  output_file: Path) -> Tuple[bool, str]:
        """Export the database from the DDEV project.
        
        Args:
            project_path: Path to the DDEV project directory
            output_file: Path where the dump will be saved
            
        Returns:
            Tuple of (success, message)
        """
        try:
            result = subprocess.run(
                ["ddev", "export-db", "--file", str(output_file)],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, f"Database exported to {output_file}"
            else:
                return False, f"Failed to export database: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout while exporting database"
        except Exception as e:
            return False, f"Error exporting database: {str(e)}"
    
    def share_start(self, project_path: Path) -> Tuple[bool, str]:
        """Start DDEV share (ngrok tunnel).
        
        Args:
            project_path: Path to the DDEV project directory
            
        Returns:
            Tuple of (success, message with URL)
        """
        try:
            result = subprocess.run(
                ["ddev", "share"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, f"Failed to start share: {result.stderr}"
                
        except Exception as e:
            return False, f"Error starting share: {str(e)}"
    
    def health_check(self, project_path: Path) -> Tuple[bool, Dict[str, Any]]:
        """Perform a health check on a DDEV project.
        
        Args:
            project_path: Path to the DDEV project directory
            
        Returns:
            Tuple of (healthy, details)
        """
        details = {
            "project_path": str(project_path),
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check if .ddev directory exists
            ddev_config = project_path / ".ddev" / "config.yaml"
            details["checks"]["config_exists"] = ddev_config.exists()
            
            if not ddev_config.exists():
                return False, details
            
            # Get DDEV status
            result = subprocess.run(
                ["ddev", "status", "--json-output"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                details["checks"]["status"] = status_data
                
                # Check if running
                is_running = status_data.get('raw', {}).get('status') == 'running'
                details["checks"]["is_running"] = is_running
                
                if is_running:
                    # Test web access
                    urls = status_data.get('raw', {}).get('urls', [])
                    details["checks"]["urls"] = urls
                    
                    # Test database connection
                    db_result = self.exec_command(
                        project_path,
                        "mysql -e 'SELECT 1'",
                        service="db",
                        timeout=10
                    )
                    details["checks"]["database"] = {
                        "success": db_result[0],
                        "error": db_result[2] if not db_result[0] else None
                    }
                    
                    healthy = all([
                        details["checks"]["config_exists"],
                        details["checks"]["is_running"],
                        details["checks"]["database"]["success"]
                    ])
                    
                    return healthy, details
                else:
                    return False, details
            else:
                details["checks"]["status_error"] = result.stderr
                return False, details
                
        except Exception as e:
            details["checks"]["error"] = str(e)
            return False, details
    
    def check_ddev_installed(self) -> Tuple[bool, str]:
        """Check if DDEV is installed and available.
        
        Returns:
            Tuple of (installed, version_info)
        """
        try:
            result = subprocess.run(
                ["ddev", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, "DDEV command failed"
                
        except FileNotFoundError:
            return False, "DDEV not found in PATH"
        except Exception as e:
            return False, f"Error checking DDEV: {str(e)}"
