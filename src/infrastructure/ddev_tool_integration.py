"""Integration between DDEV tools and the agent system.

This module provides seamless integration of DDEV tools with the agent framework,
including automatic tool registration and customer context resolution.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from .workspace_manager import WorkspaceManager, CustomerWorkspace, get_workspace_manager
from ..tools.base import ToolResult

logger = logging.getLogger(__name__)


class DDEVToolIntegration:
    """Integrates DDEV tools with the agent system.
    
    This class provides:
    - Automatic customer context resolution
    - Tool result formatting for LLM consumption
    - Error handling and recovery
    - Logging and monitoring
    """
    
    def __init__(self, workspace_manager: Optional[WorkspaceManager] = None):
        """Initialize the DDEV tool integration.
        
        Args:
            workspace_manager: Optional workspace manager instance
        """
        self.workspace_manager = workspace_manager or get_workspace_manager()
        self._execution_history: Dict[str, list] = {}
    
    def resolve_customer(self, context: Any) -> Optional[str]:
        """Resolve customer ID from agent context.
        
        Args:
            context: Agent context object
            
        Returns:
            Customer ID or None if not found
        """
        # Try to get customer from context
        if hasattr(context, 'customer_id'):
            return context.customer_id
        
        if isinstance(context, dict):
            return context.get('customer_id')
        
        # Try from thread-local or session
        # This would be implemented based on the agent framework's context management
        
        return None
    
    def get_customer_info(self, customer_id: str) -> Dict[str, Any]:
        """Get formatted customer information for LLM prompts.
        
        Args:
            customer_id: The customer identifier
            
        Returns:
            Dictionary with customer information
        """
        workspace = self.workspace_manager.get_workspace(customer_id)
        
        if not workspace:
            return {"error": f"Customer '{customer_id}' not found"}
        
        return {
            "customer_id": workspace.customer_id,
            "display_name": workspace.display_name,
            "description": workspace.description,
            "shopware_version": workspace.shopware_config.get('version'),
            "php_version": workspace.ddev_config.get('php_version'),
            "database": {
                "type": workspace.ddev_config.get('database', {}).get('type'),
                "version": workspace.ddev_config.get('database', {}).get('version')
            },
            "plugins": [
                {"name": p.get('name'), "path": p.get('path')}
                for p in workspace.shopware_config.get('custom_plugins', [])
            ],
            "workspace_path": str(workspace.workspace_path),
            "status": workspace.status.value
        }
    
    def format_result_for_llm(self, result: ToolResult, 
                              command: str,
                              customer_id: str) -> str:
        """Format a tool result for LLM consumption.
        
        Args:
            result: The tool execution result
            command: The command that was executed
            customer_id: The customer ID
            
        Returns:
            Formatted result string
        """
        if result.success:
            data = result.data or {}
            output = data.get('stdout', '')
            
            # Truncate long outputs
            max_output_length = 4000
            if len(output) > max_output_length:
                output = output[:max_output_length] + f"\n... ({len(output) - max_output_length} more characters)"
            
            return f"""Command executed successfully in {customer_id} DDEV environment:

$ {command}

Output:
{output}

Execution time: {result.execution_time_ms:.0f}ms
"""
        else:
            error = result.error or "Unknown error"
            return f"""Command failed in {customer_id} DDEV environment:

$ {command}

Error: {error}

Please check:
1. Is the DDEV environment running? Use ddev_status to check.
2. Is the command valid for this Shopware version?
3. Are there any permission issues?
"""
    
    def log_execution(self, customer_id: str, command: str, 
                      result: ToolResult):
        """Log a command execution for history tracking.
        
        Args:
            customer_id: The customer ID
            command: The command executed
            result: The execution result
        """
        if customer_id not in self._execution_history:
            self._execution_history[customer_id] = []
        
        from datetime import datetime
        self._execution_history[customer_id].append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'success': result.success,
            'execution_time_ms': result.execution_time_ms
        })
        
        # Keep only last 100 entries per customer
        self._execution_history[customer_id] = \
            self._execution_history[customer_id][-100:]
    
    def get_execution_history(self, customer_id: str, 
                              limit: int = 10) -> list:
        """Get command execution history for a customer.
        
        Args:
            customer_id: The customer ID
            limit: Maximum number of entries to return
            
        Returns:
            List of execution history entries
        """
        history = self._execution_history.get(customer_id, [])
        return history[-limit:]
    
    def suggest_fix(self, error_output: str, 
                    customer_id: str) -> Optional[str]:
        """Suggest a fix for a common error.
        
        Args:
            error_output: The error output from a command
            customer_id: The customer ID
            
        Returns:
            Suggested fix or None
        """
        # Common error patterns and fixes
        error_patterns = {
            'Could not open input file: bin/console': 
                "Shopware is not installed. Try running 'composer install' first.",
            
            'Connection refused': 
                "The DDEV environment may not be running. Try starting it with 'ddev start'.",
            
            'Permission denied': 
                "There may be permission issues. Try 'ddev exec sudo chown -R www-data:www-data /var/www/html'.",
            
            'Unknown command': 
                "The command may not exist in this Shopware version. Check the Shopware documentation.",
            
            'Table.*doesn\'t exist': 
                "Database tables may be missing. Try running 'bin/console database:migrate'.",
            
            'Out of memory': 
                "The PHP memory limit may be exceeded. Try increasing memory_limit in php.ini.",
        }
        
        for pattern, suggestion in error_patterns.items():
            import re
            if re.search(pattern, error_output, re.IGNORECASE):
                return suggestion
        
        return None
    
    def get_working_directory(self, customer_id: str) -> str:
        """Get the working directory for a customer workspace.
        
        Args:
            customer_id: The customer ID
            
        Returns:
            Working directory path
        """
        workspace = self.workspace_manager.get_workspace(customer_id)
        if workspace:
            return str(workspace.source_path)
        return ""
    
    def validate_shopware_version(self, customer_id: str, 
                                  required_version: str) -> bool:
        """Check if customer's Shopware version meets requirements.
        
        Args:
            customer_id: The customer ID
            required_version: Minimum required version
            
        Returns:
            True if version is compatible
        """
        workspace = self.workspace_manager.get_workspace(customer_id)
        if not workspace:
            return False
        
        current_version = workspace.shopware_config.get('version', '')
        
        # Simple version comparison (could be enhanced with semver)
        return current_version >= required_version


# Convenience functions for direct use
def get_customer_working_directory(customer_id: str) -> str:
    """Get working directory for a customer.
    
    Args:
        customer_id: The customer ID
        
    Returns:
        Working directory path
    """
    manager = get_workspace_manager()
    workspace = manager.get_workspace(customer_id)
    return str(workspace.source_path) if workspace else ""


def get_customer_php_version(customer_id: str) -> str:
    """Get PHP version for a customer.
    
    Args:
        customer_id: The customer ID
        
    Returns:
        PHP version string
    """
    manager = get_workspace_manager()
    workspace = manager.get_workspace(customer_id)
    return workspace.ddev_config.get('php_version', '8.2') if workspace else '8.2'


def get_customer_shopware_version(customer_id: str) -> str:
    """Get Shopware version for a customer.
    
    Args:
        customer_id: The customer ID
        
    Returns:
        Shopware version string
    """
    manager = get_workspace_manager()
    workspace = manager.get_workspace(customer_id)
    return workspace.shopware_config.get('version', '') if workspace else ""


def is_ddev_running(customer_id: str) -> bool:
    """Check if DDEV is running for a customer.
    
    Args:
        customer_id: The customer ID
        
    Returns:
        True if DDEV is running
    """
    manager = get_workspace_manager()
    status = manager.get_status(customer_id)
    return status.get('ddev_status') == 'running'
