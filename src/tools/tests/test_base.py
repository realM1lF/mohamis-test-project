"""Tests for BaseTool and related classes."""

import pytest
from src.tools.base import (
    BaseTool,
    ToolResult,
    ToolParameter,
    ToolParameterType,
)


class TestToolResult:
    """Tests for ToolResult dataclass."""
    
    def test_success_result(self):
        """Test creating a success result."""
        result = ToolResult.success_result(
            data={"key": "value"},
            execution_time_ms=100.5,
            tool_name="test_tool"
        )
        
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.execution_time_ms == 100.5
        assert result.tool_name == "test_tool"
    
    def test_error_result(self):
        """Test creating an error result."""
        result = ToolResult.error_result(
            error="Something went wrong",
            execution_time_ms=50.0,
            tool_name="test_tool"
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"
        assert result.execution_time_ms == 50.0
        assert result.tool_name == "test_tool"
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ToolResult.success_result(data="test")
        d = result.to_dict()
        
        assert d["success"] is True
        assert d["data"] == "test"
        assert "error" in d
    
    def test_to_json(self):
        """Test converting to JSON."""
        result = ToolResult.success_result(data={"nested": "value"})
        json_str = result.to_json()
        
        assert '"success": true' in json_str
        assert '"nested": "value"' in json_str


class TestToolParameter:
    """Tests for ToolParameter class."""
    
    def test_basic_parameter(self):
        """Test basic parameter creation."""
        param = ToolParameter(
            name="test_param",
            description="A test parameter",
            type=ToolParameterType.STRING,
            required=True
        )
        
        schema = param.to_schema()
        assert schema["type"] == "string"
        assert schema["description"] == "A test parameter"
        assert "enum" not in schema
    
    def test_enum_parameter(self):
        """Test parameter with enum."""
        param = ToolParameter(
            name="choice",
            description="A choice parameter",
            type=ToolParameterType.STRING,
            required=True,
            enum=["option1", "option2", "option3"]
        )
        
        schema = param.to_schema()
        assert schema["enum"] == ["option1", "option2", "option3"]


class TestBaseTool:
    """Tests for BaseTool abstract class."""
    
    def test_tool_validation(self):
        """Test that tools must have name and description."""
        class InvalidTool(BaseTool):
            pass
        
        with pytest.raises(ValueError, match="must have a name"):
            InvalidTool()
    
    def test_valid_tool(self):
        """Test creating a valid tool."""
        class ValidTool(BaseTool):
            name = "valid_tool"
            description = "A valid test tool"
            parameters = [
                ToolParameter(
                    name="input",
                    description="Input value",
                    type=ToolParameterType.STRING,
                    required=True
                )
            ]
            
            async def run(self, input: str) -> ToolResult:
                return ToolResult.success_result(data={"result": input.upper()})
        
        tool = ValidTool()
        assert tool.name == "valid_tool"
        assert tool.description == "A valid test tool"
    
    def test_get_parameters_schema(self):
        """Test getting parameter schema."""
        class TestTool(BaseTool):
            name = "test_tool"
            description = "Test tool"
            parameters = [
                ToolParameter(
                    name="required_param",
                    description="Required parameter",
                    type=ToolParameterType.STRING,
                    required=True
                ),
                ToolParameter(
                    name="optional_param",
                    description="Optional parameter",
                    type=ToolParameterType.INTEGER,
                    required=False,
                    default=42
                )
            ]
            
            async def run(self, **kwargs) -> ToolResult:
                return ToolResult.success_result(data=kwargs)
        
        tool = TestTool()
        schema = tool.get_parameters_schema()
        
        assert schema["type"] == "object"
        assert "required_param" in schema["properties"]
        assert "optional_param" in schema["properties"]
        assert schema["required"] == ["required_param"]
    
    def test_to_openai_schema(self):
        """Test OpenAI schema format."""
        class TestTool(BaseTool):
            name = "test_tool"
            description = "Test tool"
            parameters = []
            
            async def run(self, **kwargs) -> ToolResult:
                return ToolResult.success_result(data={})
        
        tool = TestTool()
        schema = tool.to_openai_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "test_tool"
        assert schema["function"]["description"] == "Test tool"
    
    def test_validate_parameters(self):
        """Test parameter validation."""
        class TestTool(BaseTool):
            name = "test_tool"
            description = "Test tool"
            parameters = [
                ToolParameter(
                    name="name",
                    description="Name",
                    type=ToolParameterType.STRING,
                    required=True
                ),
                ToolParameter(
                    name="count",
                    description="Count",
                    type=ToolParameterType.INTEGER,
                    required=True
                ),
            ]
            
            async def run(self, **kwargs) -> ToolResult:
                return ToolResult.success_result(data=kwargs)
        
        tool = TestTool()
        
        # Valid parameters
        is_valid, error = tool.validate_parameters({"name": "test", "count": 5})
        assert is_valid is True
        assert error is None
        
        # Missing required parameter
        is_valid, error = tool.validate_parameters({"name": "test"})
        assert is_valid is False
        assert "Missing required parameter" in error
        
        # Wrong type
        is_valid, error = tool.validate_parameters({"name": "test", "count": "five"})
        assert is_valid is False
        assert "must be an integer" in error
    
    @pytest.mark.asyncio
    async def test_run_with_validation_success(self):
        """Test run with validation - success case."""
        class TestTool(BaseTool):
            name = "test_tool"
            description = "Test tool"
            parameters = [
                ToolParameter(
                    name="value",
                    description="Value",
                    type=ToolParameterType.STRING,
                    required=True
                )
            ]
            
            async def run(self, value: str) -> ToolResult:
                return ToolResult.success_result(data={"processed": value})
        
        tool = TestTool()
        result = await tool.run_with_validation(value="hello")
        
        assert result.success is True
        assert result.data == {"processed": "hello"}
    
    @pytest.mark.asyncio
    async def test_run_with_validation_error(self):
        """Test run with validation - validation error."""
        class TestTool(BaseTool):
            name = "test_tool"
            description = "Test tool"
            parameters = [
                ToolParameter(
                    name="value",
                    description="Value",
                    type=ToolParameterType.STRING,
                    required=True
                )
            ]
            
            async def run(self, value: str) -> ToolResult:
                return ToolResult.success_result(data={"processed": value})
        
        tool = TestTool()
        result = await tool.run_with_validation()  # Missing required param
        
        assert result.success is False
        assert "Parameter validation failed" in result.error
