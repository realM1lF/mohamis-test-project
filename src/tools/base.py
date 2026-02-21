"""Base classes for the Tool-Use Framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type, get_type_hints
import json


class ToolParameterType(Enum):
    """Supported parameter types for tools."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Schema definition for a tool parameter."""
    name: str
    description: str
    type: ToolParameterType
    required: bool = True
    enum: Optional[List[Any]] = None
    default: Any = None
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = {
            "type": self.type.value,
            "description": self.description,
        }
        if self.enum is not None:
            schema["enum"] = self.enum
        if self.default is not None and not self.required:
            schema["default"] = self.default
        return schema


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    tool_name: Optional[str] = None
    
    @classmethod
    def success_result(cls, data: Any, execution_time_ms: float = 0.0, tool_name: str = None) -> "ToolResult":
        """Create a successful result."""
        return cls(
            success=True,
            data=data,
            execution_time_ms=execution_time_ms,
            tool_name=tool_name
        )
    
    @classmethod
    def error_result(cls, error: str, execution_time_ms: float = 0.0, tool_name: str = None) -> "ToolResult":
        """Create an error result."""
        return cls(
            success=False,
            error=error,
            execution_time_ms=execution_time_ms,
            tool_name=tool_name
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM consumption."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class BaseTool(ABC):
    """Abstract base class for all tools.
    
    Tools represent capabilities that an AI agent can use.
    Each tool has:
    - A unique name
    - A description (used in LLM prompts)
    - A parameter schema (JSON Schema compatible)
    - An async run() method
    """
    
    # Tool metadata - must be defined by subclasses
    name: str = ""
    description: str = ""
    
    # Parameter definitions
    parameters: List[ToolParameter] = field(default_factory=list)
    
    def __init__(self):
        """Initialize the tool."""
        self._validate_tool()
    
    def _validate_tool(self):
        """Validate that the tool is properly configured."""
        if not self.name:
            raise ValueError(f"Tool {self.__class__.__name__} must have a name")
        if not self.description:
            raise ValueError(f"Tool {self.name} must have a description")
    
    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """Execute the tool with the given parameters.
        
        Args:
            **kwargs: Parameters as defined in self.parameters
            
        Returns:
            ToolResult: The result of the execution
        """
        pass
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the JSON Schema for this tool's parameters.
        
        Returns:
            Dict conforming to JSON Schema for OpenAI Function Calling
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_schema()
            if param.required:
                required.append(param.name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }
    
    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI Function Calling format.
        
        Returns:
            Dict in OpenAI function schema format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            }
        }
    
    def to_anthropic_schema(self) -> Dict[str, Any]:
        """Convert to Anthropic Tool Use format.
        
        Returns:
            Dict in Anthropic tool schema format
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_parameters_schema(),
        }
    
    def to_generic_schema(self) -> Dict[str, Any]:
        """Get generic schema for any LLM provider.
        
        Returns:
            Generic tool schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters_schema(),
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate parameters against the schema.
        
        Args:
            params: Dictionary of parameter names to values
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in params:
                return False, f"Missing required parameter: {param.name}"
            
            # Skip further validation if param not provided
            if param.name not in params:
                continue
                
            value = params[param.name]
            
            # Type validation
            if param.type == ToolParameterType.STRING and not isinstance(value, str):
                return False, f"Parameter {param.name} must be a string"
            elif param.type == ToolParameterType.INTEGER and not isinstance(value, int):
                return False, f"Parameter {param.name} must be an integer"
            elif param.type == ToolParameterType.NUMBER and not isinstance(value, (int, float)):
                return False, f"Parameter {param.name} must be a number"
            elif param.type == ToolParameterType.BOOLEAN and not isinstance(value, bool):
                return False, f"Parameter {param.name} must be a boolean"
            elif param.type == ToolParameterType.ARRAY and not isinstance(value, list):
                return False, f"Parameter {param.name} must be an array"
            elif param.type == ToolParameterType.OBJECT and not isinstance(value, dict):
                return False, f"Parameter {param.name} must be an object"
            
            # Enum validation
            if param.enum is not None and value not in param.enum:
                return False, f"Parameter {param.name} must be one of: {param.enum}"
        
        return True, None
    
    async def run_with_validation(self, **kwargs) -> ToolResult:
        """Run the tool with parameter validation.
        
        Args:
            **kwargs: Parameters to pass to run()
            
        Returns:
            ToolResult: Result of execution or validation error
        """
        # Validate parameters
        is_valid, error = self.validate_parameters(kwargs)
        if not is_valid:
            return ToolResult.error_result(
                error=f"Parameter validation failed: {error}",
                tool_name=self.name
            )
        
        # Execute the tool
        try:
            return await self.run(**kwargs)
        except Exception as e:
            return ToolResult.error_result(
                error=f"Tool execution failed: {str(e)}",
                tool_name=self.name
            )
    
    def __repr__(self) -> str:
        return f"<Tool {self.name}: {self.description[:50]}...>"
