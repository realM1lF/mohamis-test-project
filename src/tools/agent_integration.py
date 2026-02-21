"""Integration layer for connecting tools with the DeveloperAgent.

This module provides the bridge between the tool framework and the agent,
handling LLM tool calling, response parsing, and result formatting.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

from .base import BaseTool, ToolResult
from .registry import ToolRegistry
from .executor import ToolExecutor

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a tool call from an LLM."""
    tool_name: str
    parameters: Dict[str, Any]
    raw_response: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_openai_format(cls, function_call: Dict[str, Any]) -> "ToolCall":
        """Parse from OpenAI function calling format.
        
        Args:
            function_call: OpenAI function_call object
            
        Returns:
            Parsed ToolCall
        """
        name = function_call.get("name", "")
        arguments = function_call.get("arguments", "{}")
        
        # Parse arguments (OpenAI sends them as JSON string)
        if isinstance(arguments, str):
            try:
                parameters = json.loads(arguments)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse arguments: {arguments}")
                parameters = {}
        else:
            parameters = arguments
        
        return cls(
            tool_name=name,
            parameters=parameters,
            raw_response=function_call
        )
    
    @classmethod
    def from_anthropic_format(cls, tool_use: Dict[str, Any]) -> "ToolCall":
        """Parse from Anthropic tool_use format.
        
        Args:
            tool_use: Anthropic tool_use block
            
        Returns:
            Parsed ToolCall
        """
        return cls(
            tool_name=tool_use.get("name", ""),
            parameters=tool_use.get("input", {}),
            raw_response=tool_use
        )
    
    @classmethod
    def from_text_format(cls, text: str) -> Optional["ToolCall"]:
        """Parse tool call from text (for LLMs without native function calling).
        
        Looks for JSON blocks like:
        ```json
        {"tool": "file_read", "parameters": {"path": "/tmp/test.txt"}}
        ```
        
        Args:
            text: Text potentially containing tool call
            
        Returns:
            Parsed ToolCall or None if not found
        """
        # Look for JSON code blocks
        import re
        
        # Pattern for ```json ... ``` blocks
        json_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match.strip())
                if "tool" in data:
                    return cls(
                        tool_name=data["tool"],
                        parameters=data.get("parameters", {}),
                        raw_response=data
                    )
            except json.JSONDecodeError:
                continue
        
        return None


class AgentToolManager:
    """Manages tools for an agent, handling LLM interactions.
    
    This class provides:
    - Tool registry management
    - LLM prompt generation with tool descriptions
    - Tool call parsing from LLM responses
    - Tool execution and result formatting
    
    Example:
        manager = AgentToolManager()
        manager.register_default_tools()
        
        # Get system prompt with tool descriptions
        system_prompt = manager.get_system_prompt_with_tools()
        
        # After LLM call, handle any tool calls
        tool_calls = manager.parse_tool_calls(llm_response)
        for call in tool_calls:
            result = await manager.execute_tool_call(call, agent_id="dev-1")
            # Add result back to conversation
    """
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        """Initialize the tool manager.
        
        Args:
            registry: Optional existing registry. If None, creates new one.
        """
        self.registry = registry or ToolRegistry()
        self.executor = ToolExecutor(self.registry)
        self.tool_results: List[Dict[str, Any]] = []
    
    def register_tool(self, tool: BaseTool, category: Optional[str] = None) -> None:
        """Register a tool.
        
        Args:
            tool: Tool to register
            category: Optional category
        """
        self.registry.register(tool, category)
    
    def register_default_tools(self) -> None:
        """Register the default set of tools for a developer agent."""
        from .file_tools import FileReadTool, FileWriteTool, FileListTool, FileSearchTool
        from .git_tools import GitBranchTool, GitCommitTool, GitStatusTool, GitLogTool
        from .code_tools import CodeAnalyzeTool, CodeReviewTool
        
        # File tools
        self.registry.register(FileReadTool(), "file")
        self.registry.register(FileWriteTool(), "file")
        self.registry.register(FileListTool(), "file")
        self.registry.register(FileSearchTool(), "file")
        
        # Git tools
        self.registry.register(GitBranchTool(), "git")
        self.registry.register(GitCommitTool(), "git")
        self.registry.register(GitStatusTool(), "git")
        self.registry.register(GitLogTool(), "git")
        
        # Code tools
        self.registry.register(CodeAnalyzeTool(), "code")
        self.registry.register(CodeReviewTool(), "code")
        
        logger.info(f"Registered {len(self.registry)} default tools")
    
    def get_tools_for_llm(self, format: str = "openai") -> List[Dict[str, Any]]:
        """Get tool schemas formatted for LLM.
        
        Args:
            format: LLM format ("openai", "anthropic", "generic")
            
        Returns:
            List of tool schemas
        """
        return self.registry.get_schemas_for_llm(format)
    
    def get_system_prompt_with_tools(self) -> str:
        """Generate a system prompt describing available tools.
        
        This is useful for LLMs that don't support native function calling
        but can understand tool descriptions in the prompt.
        
        Returns:
            System prompt with tool descriptions
        """
        lines = [
            "You are Mohami, an AI developer agent.",
            "",
            "You have access to the following tools to complete your tasks:",
            "",
        ]
        
        # Group tools by category
        for category in self.registry.get_categories():
            tools = self.registry.list_by_category(category)
            lines.append(f"## {category.upper()} Tools")
            lines.append("")
            
            for tool in tools:
                lines.append(f"### {tool.name}")
                lines.append(tool.description)
                lines.append("")
                
                # Parameters
                schema = tool.get_parameters_schema()
                if schema.get("properties"):
                    lines.append("Parameters:")
                    for param_name, param_schema in schema["properties"].items():
                        req = " (required)" if param_name in schema.get("required", []) else ""
                        param_type = param_schema.get("type", "any")
                        param_desc = param_schema.get("description", "")
                        lines.append(f'  - {param_name} ({param_type}){req}: {param_desc}')
                lines.append("")
        
        lines.extend([
            "## How to Use Tools",
            "",
            "When you need to use a tool, respond with a JSON code block in this format:",
            "```json",
            '{"tool": "tool_name", "parameters": {"param1": "value1"}}',
            "```",
            "",
            "The user will execute the tool and return the result. Only use one tool at a time.",
            "",
            "Think step by step:",
            "1. Analyze what needs to be done",
            "2. Choose the appropriate tool",
            "3. Execute the tool",
            "4. Use the result to continue",
            "",
        ])
        
        return "\n".join(lines)
    
    def parse_tool_calls(
        self,
        response: Any,
        format: str = "auto"
    ) -> List[ToolCall]:
        """Parse tool calls from an LLM response.
        
        Args:
            response: LLM response object
            format: Format type ("openai", "anthropic", "text", "auto")
            
        Returns:
            List of parsed tool calls
        """
        tool_calls = []
        
        # Auto-detect format
        if format == "auto":
            if isinstance(response, dict):
                if "function_call" in response:
                    format = "openai"
                elif "tool_calls" in response:
                    format = "openai"
                elif "tool_use" in response or "content" in response and isinstance(response.get("content"), list):
                    format = "anthropic"
                else:
                    format = "text"
            else:
                format = "text"
        
        # Parse based on format
        if format == "openai":
            # OpenAI format
            if isinstance(response, dict):
                # Single function_call
                if "function_call" in response and response["function_call"]:
                    tool_calls.append(ToolCall.from_openai_format(response["function_call"]))
                
                # Multiple tool_calls
                if "tool_calls" in response:
                    for tc in response["tool_calls"]:
                        if "function" in tc:
                            tool_calls.append(ToolCall.from_openai_format(tc["function"]))
                        elif "name" in tc:
                            tool_calls.append(ToolCall.from_openai_format(tc))
        
        elif format == "anthropic":
            # Anthropic format
            if isinstance(response, dict) and "content" in response:
                for block in response.get("content", []):
                    if block.get("type") == "tool_use":
                        tool_calls.append(ToolCall.from_anthropic_format(block))
        
        elif format == "text":
            # Text format - parse JSON blocks
            text = response if isinstance(response, str) else str(response)
            
            # Keep parsing until no more found
            remaining_text = text
            while True:
                call = ToolCall.from_text_format(remaining_text)
                if call:
                    tool_calls.append(call)
                    # Remove this call from text and continue
                    # (simplified - in real implementation, we'd track positions)
                    break
                else:
                    break
        
        return tool_calls
    
    async def execute_tool_call(
        self,
        tool_call: ToolCall,
        agent_id: Optional[str] = None,
        ticket_id: Optional[str] = None
    ) -> ToolResult:
        """Execute a parsed tool call.
        
        Args:
            tool_call: Parsed tool call
            agent_id: Optional agent ID
            ticket_id: Optional ticket ID
            
        Returns:
            Tool execution result
        """
        result = await self.executor.execute(
            tool_name=tool_call.tool_name,
            parameters=tool_call.parameters,
            agent_id=agent_id,
            ticket_id=ticket_id
        )
        
        # Store result
        self.tool_results.append({
            "tool": tool_call.tool_name,
            "parameters": tool_call.parameters,
            "result": result.to_dict(),
        })
        
        return result
    
    def format_tool_result_for_llm(self, result: ToolResult) -> str:
        """Format a tool result for inclusion in LLM context.
        
        Args:
            result: Tool result
            
        Returns:
            Formatted string
        """
        lines = [
            f"## Tool Result: {result.tool_name}",
            "",
        ]
        
        if result.success:
            lines.append("Status: ✅ Success")
            lines.append("")
            
            if isinstance(result.data, dict):
                for key, value in result.data.items():
                    if isinstance(value, list) and len(value) > 10:
                        # Truncate long lists
                        lines.append(f"{key}: ({len(value)} items, showing first 10)")
                        for item in value[:10]:
                            lines.append(f"  - {item}")
                    elif isinstance(value, str) and len(value) > 500:
                        # Truncate long strings
                        lines.append(f"{key}: {value[:500]}...")
                    else:
                        lines.append(f"{key}: {value}")
            else:
                lines.append(f"Result: {result.data}")
        else:
            lines.append("Status: ❌ Failed")
            lines.append(f"Error: {result.error}")
        
        return "\n".join(lines)
    
    def get_tool_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get history of tool calls and results.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of tool call records
        """
        return self.tool_results[-limit:]
    
    def clear_history(self) -> None:
        """Clear tool call history."""
        self.tool_results.clear()
        self.executor.clear_history()


class ToolUsingDeveloperAgent:
    """Mixin/Helper for adding tool use to DeveloperAgent.
    
    This class provides the tool use capabilities that can be integrated
    into the existing DeveloperAgent class.
    """
    
    def __init__(self, tool_manager: Optional[AgentToolManager] = None):
        """Initialize tool capabilities.
        
        Args:
            tool_manager: Optional existing manager
        """
        self.tool_manager = tool_manager or AgentToolManager()
        self._current_tool_results: List[ToolResult] = []
    
    def setup_tools(self) -> None:
        """Set up default tools."""
        self.tool_manager.register_default_tools()
    
    async def run_tool_loop(
        self,
        llm_client,
        initial_prompt: str,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
        agent_id: Optional[str] = None,
        ticket_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a loop of LLM -> Tool Call -> LLM until task complete.
        
        This implements the ReAct pattern with tools.
        
        Args:
            llm_client: LLM client with chat method
            initial_prompt: Initial user prompt
            system_prompt: Optional system prompt
            max_iterations: Maximum tool iterations
            agent_id: Agent ID
            ticket_id: Ticket ID
            
        Returns:
            Final result with conversation history
        """
        from ..llm.kimi_client import Message
        
        # Prepare system prompt with tools
        if system_prompt is None:
            system_prompt = self.tool_manager.get_system_prompt_with_tools()
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=initial_prompt),
        ]
        
        conversation_history = []
        tool_calls_made = []
        
        for iteration in range(max_iterations):
            # Get LLM response
            response = await llm_client.chat(messages, temperature=0.3)
            
            assistant_message = response.content
            conversation_history.append({"role": "assistant", "content": assistant_message})
            
            # Check for tool calls
            tool_calls = self.tool_manager.parse_tool_calls(assistant_message)
            
            if not tool_calls:
                # No tool calls, task is complete
                return {
                    "complete": True,
                    "final_response": assistant_message,
                    "conversation_history": conversation_history,
                    "tool_calls_made": tool_calls_made,
                    "iterations": iteration + 1,
                }
            
            # Execute tool calls
            for tool_call in tool_calls:
                result = await self.tool_manager.execute_tool_call(
                    tool_call,
                    agent_id=agent_id,
                    ticket_id=ticket_id
                )
                
                tool_calls_made.append({
                    "tool": tool_call.tool_name,
                    "parameters": tool_call.parameters,
                    "result": result.to_dict(),
                })
                
                # Format result and add to messages
                result_message = self.tool_manager.format_tool_result_for_llm(result)
                messages.append(Message(role="assistant", content=assistant_message))
                messages.append(Message(role="user", content=result_message))
                conversation_history.append({"role": "tool", "content": result_message})
        
        # Max iterations reached
        return {
            "complete": False,
            "final_response": "Maximum iterations reached",
            "conversation_history": conversation_history,
            "tool_calls_made": tool_calls_made,
            "iterations": max_iterations,
        }
