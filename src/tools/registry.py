"""Tool Registry - Central registration and discovery of tools."""

from typing import Dict, List, Optional, Type, Any
import logging

from .base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available tools.
    
    The registry maintains a mapping of tool names to tool instances.
    It provides discovery capabilities for LLM function calling.
    
    Example:
        registry = ToolRegistry()
        registry.register(FileReadTool(), "file")
        registry.register(FileWriteTool(), "file")
        
        # Get schemas for LLM
        schemas = registry.get_schemas_for_llm()
        
        # Get a specific tool
        tool = registry.get("file_read")
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        logger.debug("ToolRegistry initialized")
    
    def register(self, tool: BaseTool, category: Optional[str] = None) -> "ToolRegistry":
        """Register a tool in the registry.
        
        Args:
            tool: The tool instance to register
            category: Optional category for organizing tools (e.g., "file", "git", "code")
            
        Returns:
            Self for chaining
            
        Raises:
            ValueError: If a tool with the same name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        
        self._tools[tool.name] = tool
        
        # Add to category
        if category:
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(tool.name)
        
        logger.debug(f"Registered tool: {tool.name}")
        return self
    
    def register_all(self, tools: List[BaseTool], category: Optional[str] = None) -> "ToolRegistry":
        """Register multiple tools at once.
        
        Args:
            tools: List of tool instances to register
            category: Optional category for all tools
            
        Returns:
            Self for chaining
        """
        for tool in tools:
            self.register(tool, category)
        return self
    
    def unregister(self, name: str) -> bool:
        """Remove a tool from the registry.
        
        Args:
            name: Name of the tool to remove
            
        Returns:
            True if tool was removed, False if not found
        """
        if name not in self._tools:
            return False
        
        del self._tools[name]
        
        # Remove from categories
        for cat_tools in self._categories.values():
            if name in cat_tools:
                cat_tools.remove(name)
        
        logger.debug(f"Unregistered tool: {name}")
        return True
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            name: The tool name
            
        Returns:
            The tool instance or None if not found
        """
        return self._tools.get(name)
    
    def get_required(self, name: str) -> BaseTool:
        """Get a tool by name, raising an error if not found.
        
        Args:
            name: The tool name
            
        Returns:
            The tool instance
            
        Raises:
            KeyError: If tool is not found
        """
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found in registry")
        return tool
    
    def list_available(self) -> List[BaseTool]:
        """List all registered tools.
        
        Returns:
            List of all registered tool instances
        """
        return list(self._tools.values())
    
    def list_names(self) -> List[str]:
        """List names of all registered tools.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def list_by_category(self, category: str) -> List[BaseTool]:
        """Get all tools in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of tools in that category
        """
        names = self._categories.get(category, [])
        return [self._tools[name] for name in names if name in self._tools]
    
    def get_categories(self) -> List[str]:
        """Get all registered category names.
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())
    
    def is_registered(self, name: str) -> bool:
        """Check if a tool is registered.
        
        Args:
            name: Tool name to check
            
        Returns:
            True if registered, False otherwise
        """
        return name in self._tools
    
    def clear(self) -> None:
        """Remove all tools from the registry."""
        self._tools.clear()
        self._categories.clear()
        logger.debug("ToolRegistry cleared")
    
    def get_schemas_for_llm(self, format: str = "openai") -> List[Dict[str, Any]]:
        """Get tool schemas formatted for LLM consumption.
        
        Args:
            format: The LLM provider format ("openai", "anthropic", "generic")
            
        Returns:
            List of tool schemas in the requested format
            
        Raises:
            ValueError: If format is not supported
        """
        schemas = []
        
        for tool in self._tools.values():
            if format == "openai":
                schemas.append(tool.to_openai_schema())
            elif format == "anthropic":
                schemas.append(tool.to_anthropic_schema())
            elif format == "generic":
                schemas.append(tool.to_generic_schema())
            else:
                raise ValueError(f"Unknown LLM format: {format}")
        
        return schemas
    
    def get_formatted_tools_prompt(self) -> str:
        """Get a formatted prompt describing all available tools.
        
        This is useful for LLMs that don't support native function calling.
        
        Returns:
            Formatted string describing all tools
        """
        lines = [
            "# Available Tools",
            "",
            "You have access to the following tools:",
            "",
        ]
        
        for tool in self._tools.values():
            lines.append(f"## {tool.name}")
            lines.append(f"{tool.description}")
            lines.append("")
            
            schema = tool.get_parameters_schema()
            if schema.get("properties"):
                lines.append("Parameters:")
                for param_name, param_schema in schema["properties"].items():
                    req = " (required)" if param_name in schema.get("required", []) else ""
                    param_desc = param_schema.get("description", "No description")
                    param_type = param_schema.get("type", "any")
                    lines.append(f'  - {param_name}: {param_desc}{req} (type: {param_type})')
            lines.append("")
        
        lines.extend([
            "## Tool Usage Format",
            "",
            "To use a tool, respond with JSON in this format:",
            "```json",
            '{"tool": "tool_name", "parameters": {"param1": "value1"}}',
            "```",
            "",
        ])
        
        return "\n".join(lines)
    
    def __len__(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """Check if a tool name is registered."""
        return name in self._tools
    
    def __repr__(self) -> str:
        categories = ", ".join([f"{cat}({len(tools)})" for cat, tools in self._categories.items()])
        return f"<ToolRegistry: {len(self._tools)} tools [{categories}]>"
