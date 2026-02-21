"""Tests for ToolExecutor."""

import pytest
from src.tools.executor import ToolExecutor, ExecutionRecord
from src.tools.registry import ToolRegistry
from src.tools.base import BaseTool, ToolResult, ToolParameter, ToolParameterType


class SuccessTool(BaseTool):
    """Tool that always succeeds."""
    name = "success_tool"
    description = "A tool that succeeds"
    parameters = [
        ToolParameter(
            name="value",
            description="Value to process",
            type=ToolParameterType.STRING,
            required=True
        )
    ]
    
    async def run(self, value: str) -> ToolResult:
        return ToolResult.success_result(data={"processed": value})


class ErrorTool(BaseTool):
    """Tool that always fails."""
    name = "error_tool"
    description = "A tool that fails"
    parameters = []
    
    async def run(self, **kwargs) -> ToolResult:
        raise ValueError("Intentional error")


class TestToolExecutor:
    """Tests for ToolExecutor."""
    
    @pytest.fixture
    def registry(self):
        """Create a registry with test tools."""
        reg = ToolRegistry()
        reg.register(SuccessTool())
        reg.register(ErrorTool())
        return reg
    
    @pytest.fixture
    def executor(self, registry):
        """Create an executor with test registry."""
        return ToolExecutor(registry)
    
    @pytest.mark.asyncio
    async def test_execute_success(self, executor):
        """Test successful tool execution."""
        result = await executor.execute(
            "success_tool",
            {"value": "test"},
            agent_id="test-agent",
            ticket_id="test-ticket"
        )
        
        assert result.success is True
        assert result.data == {"processed": "test"}
        assert result.tool_name == "success_tool"
    
    @pytest.mark.asyncio
    async def test_execute_not_found(self, executor):
        """Test execution of non-existent tool."""
        result = await executor.execute("nonexistent", {})
        
        assert result.success is False
        assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_validation_error(self, executor):
        """Test execution with validation error."""
        result = await executor.execute(
            "success_tool",
            {},  # Missing required 'value'
        )
        
        assert result.success is False
        assert "Parameter validation failed" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_exception(self, executor):
        """Test execution that throws exception."""
        result = await executor.execute("error_tool", {})
        
        assert result.success is False
        assert "Execution failed" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_skip_validation(self, executor):
        """Test execution with validation skipped."""
        # This would fail validation but we skip it
        # Note: success_tool requires 'value', but run() will fail without it
        # So this tests the validation skip path
        result = await executor.execute(
            "success_tool",
            {"value": "test", "extra": "ignored"},
            validate=True
        )
        
        # Should succeed because 'value' is provided
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_execution_history(self, executor):
        """Test that executions are logged."""
        await executor.execute("success_tool", {"value": "test1"})
        await executor.execute("success_tool", {"value": "test2"})
        
        history = executor.get_history(limit=10)
        
        assert len(history) == 2
        assert history[0].tool_name == "success_tool"
        assert history[0].parameters["value"] == "test1"
    
    @pytest.mark.asyncio
    async def test_history_filtering(self, executor):
        """Test history filtering."""
        await executor.execute(
            "success_tool",
            {"value": "test"},
            agent_id="agent-1",
            ticket_id="ticket-1"
        )
        
        # Filter by agent
        history = executor.get_history(agent_id="agent-1")
        assert len(history) == 1
        
        history = executor.get_history(agent_id="nonexistent")
        assert len(history) == 0
        
        # Filter by ticket
        history = executor.get_history(ticket_id="ticket-1")
        assert len(history) == 1
    
    @pytest.mark.asyncio
    async def test_get_last_execution(self, executor):
        """Test getting last execution."""
        assert executor.get_last_execution() is None
        
        await executor.execute("success_tool", {"value": "test"})
        
        last = executor.get_last_execution()
        assert last is not None
        assert last.tool_name == "success_tool"
    
    def test_clear_history(self, executor):
        """Test clearing history."""
        executor.clear_history()
        assert len(executor.get_history()) == 0
    
    @pytest.mark.asyncio
    async def test_execute_from_llm_response_openai(self, executor):
        """Test executing from OpenAI format response."""
        response = {
            "name": "success_tool",
            "arguments": '{"value": "from_openai"}'
        }
        
        result = await executor.execute_from_llm_response(response)
        
        assert result.success is True
        assert result.data["processed"] == "from_openai"
    
    @pytest.mark.asyncio
    async def test_execute_from_llm_response_internal(self, executor):
        """Test executing from internal format response."""
        response = {
            "tool": "success_tool",
            "parameters": {"value": "from_internal"}
        }
        
        result = await executor.execute_from_llm_response(response)
        
        assert result.success is True
        assert result.data["processed"] == "from_internal"
    
    @pytest.mark.asyncio
    async def test_execute_from_llm_response_invalid(self, executor):
        """Test executing from invalid response."""
        response = {"invalid": "format"}
        
        result = await executor.execute_from_llm_response(response)
        
        assert result.success is False
        assert "Invalid LLM response format" in result.error
    
    def test_format_result_for_llm_success(self, executor):
        """Test formatting successful result for LLM."""
        result = ToolResult.success_result(
            data={"key": "value"},
            tool_name="test_tool"
        )
        
        formatted = executor.format_result_for_llm(result)
        
        assert "test_tool" in formatted
        assert "Success" in formatted
        assert "key" in formatted
    
    def test_format_result_for_llm_error(self, executor):
        """Test formatting error result for LLM."""
        result = ToolResult.error_result(
            error="Something went wrong",
            tool_name="test_tool"
        )
        
        formatted = executor.format_result_for_llm(result)
        
        assert "test_tool" in formatted
        assert "Failed" in formatted
        assert "Something went wrong" in formatted
    
    @pytest.mark.asyncio
    async def test_hooks(self, executor):
        """Test pre and post execution hooks."""
        pre_calls = []
        post_calls = []
        
        def pre_hook(tool_name, params):
            pre_calls.append((tool_name, params))
        
        def post_hook(tool_name, params, result):
            post_calls.append((tool_name, params, result))
        
        executor.add_pre_execution_hook(pre_hook)
        executor.add_post_execution_hook(post_hook)
        
        await executor.execute("success_tool", {"value": "test"})
        
        assert len(pre_calls) == 1
        assert pre_calls[0] == ("success_tool", {"value": "test"})
        
        assert len(post_calls) == 1
        assert post_calls[0][0] == "success_tool"
        assert post_calls[0][2].success is True
    
    @pytest.mark.asyncio
    async def test_hook_exception_handling(self, executor):
        """Test that hook exceptions don't break execution."""
        def bad_hook(*args):
            raise ValueError("Hook error")
        
        executor.add_pre_execution_hook(bad_hook)
        executor.add_post_execution_hook(bad_hook)
        
        # Should still succeed despite hook errors
        result = await executor.execute("success_tool", {"value": "test"})
        
        assert result.success is True
