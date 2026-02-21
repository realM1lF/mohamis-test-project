"""Tool Executor - Handles tool execution with error handling and logging."""

import time
import json
import logging
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .base import BaseTool, ToolResult
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRecord:
    """Record of a tool execution for logging/auditing."""
    tool_name: str
    parameters: Dict[str, Any]
    result: ToolResult
    started_at: datetime
    completed_at: datetime
    execution_time_ms: float
    agent_id: Optional[str] = None
    ticket_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": {
                "success": self.result.success,
                "data": self.result.data,
                "error": self.result.error,
            },
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "agent_id": self.agent_id,
            "ticket_id": self.ticket_id,
        }


class ToolExecutor:
    """Executes tools with error handling, logging, and callbacks.
    
    The executor provides:
    - Parameter validation before execution
    - Execution time tracking
    - Comprehensive error handling
    - Execution logging/history
    - Pre/post execution callbacks
    - Result formatting for LLM consumption
    
    Example:
        registry = ToolRegistry()
        # ... register tools ...
        
        executor = ToolExecutor(registry)
        result = await executor.execute("file_read", {"path": "/tmp/test.txt"})
        
        if result.success:
            print(f"Content: {result.data}")
        else:
            print(f"Error: {result.error}")
    """
    
    def __init__(
        self,
        registry: ToolRegistry,
        log_executions: bool = True,
        max_history: int = 100
    ):
        """Initialize the executor.
        
        Args:
            registry: The ToolRegistry containing available tools
            log_executions: Whether to keep execution history
            max_history: Maximum number of execution records to keep
        """
        self.registry = registry
        self.log_executions = log_executions
        self.max_history = max_history
        self._history: list[ExecutionRecord] = []
        self._pre_execution_hooks: list[Callable[[str, Dict[str, Any]], None]] = []
        self._post_execution_hooks: list[Callable[[str, Dict[str, Any], ToolResult], None]] = []
    
    def add_pre_execution_hook(self, hook: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add a hook that runs before tool execution.
        
        Args:
            hook: Function(tool_name, parameters) called before execution
        """
        self._pre_execution_hooks.append(hook)
    
    def add_post_execution_hook(self, hook: Callable[[str, Dict[str, Any], ToolResult], None]) -> None:
        """Add a hook that runs after tool execution.
        
        Args:
            hook: Function(tool_name, parameters, result) called after execution
        """
        self._post_execution_hooks.append(hook)
    
    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        validate: bool = True
    ) -> ToolResult:
        """Execute a tool by name with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Dictionary of parameter names to values
            agent_id: Optional ID of the calling agent (for logging)
            ticket_id: Optional ticket ID (for logging)
            validate: Whether to validate parameters before execution
            
        Returns:
            ToolResult: The result of the execution
        """
        started_at = datetime.utcnow()
        start_time = time.time()
        
        # Get tool from registry
        tool = self.registry.get(tool_name)
        if tool is None:
            execution_time = (time.time() - start_time) * 1000
            result = ToolResult.error_result(
                error=f"Tool '{tool_name}' not found in registry",
                execution_time_ms=execution_time,
                tool_name=tool_name
            )
            if self.log_executions:
                self._log_execution(tool_name, parameters, result, started_at, agent_id, ticket_id)
            return result
        
        # Run pre-execution hooks
        for hook in self._pre_execution_hooks:
            try:
                hook(tool_name, parameters)
            except Exception as e:
                logger.warning(f"Pre-execution hook failed: {e}")
        
        # Validate parameters if requested
        if validate:
            is_valid, error = tool.validate_parameters(parameters)
            if not is_valid:
                execution_time = (time.time() - start_time) * 1000
                result = ToolResult.error_result(
                    error=f"Parameter validation failed: {error}",
                    execution_time_ms=execution_time,
                    tool_name=tool_name
                )
                if self.log_executions:
                    self._log_execution(tool_name, parameters, result, started_at, agent_id, ticket_id)
                return result
        
        # Execute the tool
        try:
            logger.debug(f"Executing tool '{tool_name}' with params: {parameters}")
            result = await tool.run(**parameters)
            result.tool_name = tool_name  # Ensure tool name is set
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time
            
            if result.success:
                logger.debug(f"Tool '{tool_name}' executed successfully in {execution_time:.2f}ms")
            else:
                logger.warning(f"Tool '{tool_name}' failed: {result.error}")
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.exception(f"Tool '{tool_name}' execution threw exception")
            result = ToolResult.error_result(
                error=f"Execution failed: {str(e)}",
                execution_time_ms=execution_time,
                tool_name=tool_name
            )
        
        # Run post-execution hooks
        for hook in self._post_execution_hooks:
            try:
                hook(tool_name, parameters, result)
            except Exception as e:
                logger.warning(f"Post-execution hook failed: {e}")
        
        # Log execution
        if self.log_executions:
            self._log_execution(tool_name, parameters, result, started_at, agent_id, ticket_id)
        
        return result
    
    async def execute_from_llm_response(
        self,
        response: Dict[str, Any],
        agent_id: Optional[str] = None,
        ticket_id: Optional[str] = None
    ) -> ToolResult:
        """Execute a tool from an LLM function calling response.
        
        Handles OpenAI function calling format:
        {
            "name": "tool_name",
            "arguments": '{"param1": "value1"}'
        }
        
        Args:
            response: LLM function calling response
            agent_id: Optional agent ID
            ticket_id: Optional ticket ID
            
        Returns:
            ToolResult: The execution result
        """
        # Handle OpenAI format
        if "name" in response:
            tool_name = response["name"]
            arguments = response.get("arguments", "{}")
            if isinstance(arguments, str):
                parameters = json.loads(arguments)
            else:
                parameters = arguments
        # Handle our internal format
        elif "tool" in response:
            tool_name = response["tool"]
            parameters = response.get("parameters", {})
        else:
            return ToolResult.error_result(
                error=f"Invalid LLM response format: {response}",
                tool_name="unknown"
            )
        
        return await self.execute(
            tool_name=tool_name,
            parameters=parameters,
            agent_id=agent_id,
            ticket_id=ticket_id
        )
    
    def _log_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: ToolResult,
        started_at: datetime,
        agent_id: Optional[str],
        ticket_id: Optional[str]
    ) -> None:
        """Log an execution to history."""
        completed_at = datetime.utcnow()
        
        record = ExecutionRecord(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            started_at=started_at,
            completed_at=completed_at,
            execution_time_ms=result.execution_time_ms or 0,
            agent_id=agent_id,
            ticket_id=ticket_id
        )
        
        self._history.append(record)
        
        # Trim history if needed
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
    
    def get_history(
        self,
        tool_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        limit: int = 10
    ) -> list[ExecutionRecord]:
        """Get execution history with optional filtering.
        
        Args:
            tool_name: Filter by tool name
            agent_id: Filter by agent ID
            ticket_id: Filter by ticket ID
            limit: Maximum records to return
            
        Returns:
            List of execution records
        """
        records = self._history
        
        if tool_name:
            records = [r for r in records if r.tool_name == tool_name]
        if agent_id:
            records = [r for r in records if r.agent_id == agent_id]
        if ticket_id:
            records = [r for r in records if r.ticket_id == ticket_id]
        
        return records[-limit:]
    
    def get_last_execution(self) -> Optional[ExecutionRecord]:
        """Get the most recent execution record."""
        return self._history[-1] if self._history else None
    
    def clear_history(self) -> None:
        """Clear execution history."""
        self._history.clear()
    
    def format_result_for_llm(self, result: ToolResult) -> str:
        """Format a tool result for LLM consumption.
        
        Args:
            result: The tool result to format
            
        Returns:
            Formatted string for LLM
        """
        lines = [
            f"Tool: {result.tool_name or 'unknown'}",
            f"Success: {result.success}",
        ]
        
        if result.success:
            lines.append(f"Result: {json.dumps(result.data, indent=2, default=str)}")
        else:
            lines.append(f"Error: {result.error}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"<ToolExecutor: registry={self.registry}, history={len(self._history)}>"
