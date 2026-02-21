"""Tests for ToolRegistry."""

import pytest
from src.tools.registry import ToolRegistry
from src.tools.base import BaseTool, ToolParameter, ToolParameterType, ToolResult


class MockTool(BaseTool):
    """Mock tool for testing."""
    name = "mock_tool"
    description = "A mock tool for testing"
    parameters = [
        ToolParameter(
            name="input",
            description="Input value",
            type=ToolParameterType.STRING,
            required=True
        )
    ]
    
    async def run(self, input: str) -> ToolResult:
        return ToolResult.success_result(data={"result": input})


class AnotherMockTool(BaseTool):
    """Another mock tool for testing."""
    name = "another_tool"
    description = "Another mock tool"
    parameters = []
    
    async def run(self, **kwargs) -> ToolResult:
        return ToolResult.success_result(data={})


class TestToolRegistry:
    """Tests for ToolRegistry."""
    
    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockTool()
        
        registry.register(tool)
        
        assert "mock_tool" in registry
        assert registry.get("mock_tool") == tool
    
    def test_register_duplicate(self):
        """Test registering duplicate tool raises error."""
        registry = ToolRegistry()
        tool = MockTool()
        
        registry.register(tool)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(MockTool())
    
    def test_register_with_category(self):
        """Test registering with category."""
        registry = ToolRegistry()
        
        registry.register(MockTool(), category="test")
        registry.register(AnotherMockTool(), category="test")
        
        tools = registry.list_by_category("test")
        assert len(tools) == 2
        
        cats = registry.get_categories()
        assert "test" in cats
    
    def test_unregister(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        success = registry.unregister("mock_tool")
        assert success is True
        assert "mock_tool" not in registry
        
        # Unregister non-existent
        success = registry.unregister("nonexistent")
        assert success is False
    
    def test_get_not_found(self):
        """Test getting non-existent tool returns None."""
        registry = ToolRegistry()
        
        result = registry.get("nonexistent")
        assert result is None
    
    def test_get_required_not_found(self):
        """Test get_required raises on not found."""
        registry = ToolRegistry()
        
        with pytest.raises(KeyError, match="not found"):
            registry.get_required("nonexistent")
    
    def test_list_available(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(AnotherMockTool())
        
        tools = registry.list_available()
        assert len(tools) == 2
    
    def test_list_names(self):
        """Test listing tool names."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        names = registry.list_names()
        assert "mock_tool" in names
    
    def test_is_registered(self):
        """Test checking if tool is registered."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        assert registry.is_registered("mock_tool") is True
        assert registry.is_registered("nonexistent") is False
    
    def test_clear(self):
        """Test clearing registry."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        registry.clear()
        
        assert len(registry) == 0
        assert "mock_tool" not in registry
    
    def test_get_schemas_openai(self):
        """Test getting OpenAI format schemas."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        schemas = registry.get_schemas_for_llm("openai")
        
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "mock_tool"
    
    def test_get_schemas_anthropic(self):
        """Test getting Anthropic format schemas."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        schemas = registry.get_schemas_for_llm("anthropic")
        
        assert len(schemas) == 1
        assert schemas[0]["name"] == "mock_tool"
    
    def test_get_schemas_unknown_format(self):
        """Test unknown format raises error."""
        registry = ToolRegistry()
        
        with pytest.raises(ValueError, match="Unknown LLM format"):
            registry.get_schemas_for_llm("unknown")
    
    def test_formatted_tools_prompt(self):
        """Test formatted tools prompt."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        prompt = registry.get_formatted_tools_prompt()
        
        assert "mock_tool" in prompt
        assert "A mock tool for testing" in prompt
        assert "Parameters:" in prompt
    
    def test_len(self):
        """Test __len__."""
        registry = ToolRegistry()
        
        assert len(registry) == 0
        
        registry.register(MockTool())
        assert len(registry) == 1
    
    def test_contains(self):
        """Test __contains__."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        assert "mock_tool" in registry
        assert "nonexistent" not in registry
    
    def test_register_all(self):
        """Test registering multiple tools."""
        registry = ToolRegistry()
        
        registry.register_all([MockTool(), AnotherMockTool()], category="test")
        
        assert len(registry) == 2
        assert len(registry.list_by_category("test")) == 2
    
    def test_repr(self):
        """Test __repr__."""
        registry = ToolRegistry()
        registry.register(MockTool(), category="test")
        
        repr_str = repr(registry)
        assert "ToolRegistry" in repr_str
        assert "1 tools" in repr_str
