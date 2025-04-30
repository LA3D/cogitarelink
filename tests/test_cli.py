"""
Tests for the CLI functionality in CogitareLink.
"""
import json
import pytest
from pathlib import Path
import sys
import os

from cogitarelink.cli.cli import Agent, AgentContext, ToolRegistry
from cogitarelink.core.cache import InMemoryCache

class TestBasicAgent:
    """Tests for the basic Agent class."""
    
    def test_agent_creation(self):
        """Test that an agent can be created."""
        agent = Agent(name="test-agent")
        assert agent.name == "test-agent"
        assert isinstance(agent.tools, ToolRegistry)
        assert isinstance(agent.context, AgentContext)
    
    def test_core_tools_registration(self):
        """Test that core tools are registered."""
        agent = Agent()
        tools = agent.run_tool('list_tools')
        tool_names = [t['name'] for t in tools]
        
        # Check core tools
        assert 'get_version' in tool_names
        assert 'list_tools' in tool_names
        assert 'get_agent_memory' in tool_names
    
    def test_run_tool(self):
        """Test running a tool."""
        agent = Agent()
        version = agent.run_tool('get_version')
        assert isinstance(version, str)
        
        # Test list_tools
        tools = agent.run_tool('list_tools')
        assert isinstance(tools, list)
        assert len(tools) >= 3  # At least the core tools
        
        # Test memory
        memory = agent.run_tool('get_agent_memory')
        assert isinstance(memory, dict)
        
    def test_agent_context(self):
        """Test agent context functionality."""
        agent = Agent()
        
        # Test remember/recall
        agent.context.remember('test_key', 'test_value')
        value = agent.context.recall('test_key')
        assert value == 'test_value'
        
        # Test non-existent key
        value = agent.context.recall('non_existent', default='default')
        assert value == 'default'
        
    def test_tool_registration(self):
        """Test registering a custom tool."""
        agent = Agent()
        
        # Define a custom tool function
        def test_tool(param1, param2=None):
            """A test tool."""
            return {"param1": param1, "param2": param2}
        
        # Register the tool using the method directly
        agent.register_tool(func=test_tool, name="test_tool", description="A test tool")
        
        # Check if tool is registered
        tools = agent.run_tool('list_tools')
        tool_names = [t['name'] for t in tools]
        assert 'test_tool' in tool_names
        
        # Run the tool
        result = agent.run_tool('test_tool', param1="value1", param2="value2")
        assert result["param1"] == "value1"
        assert result["param2"] == "value2"
        
    def test_cached_tool_execution(self):
        """Test cached tool execution."""
        agent = Agent()
        
        # Create a counter to track calls
        call_count = {"count": 0}
        
        def counting_tool():
            """A tool that counts calls."""
            call_count["count"] += 1
            return call_count["count"]
        
        # Register the tool
        agent.register_tool(func=counting_tool, name="counting_tool")
        
        # First call
        result1 = agent.run_cached_tool('counting_tool')
        assert result1 == 1
        
        # Second call (should use cache)
        result2 = agent.run_cached_tool('counting_tool')
        assert result2 == 1  # Same result from cache
        assert call_count["count"] == 1  # Function only called once
        
        # Direct call (bypassing cache)
        result3 = agent.run_tool('counting_tool')
        assert result3 == 2  # New call
        assert call_count["count"] == 2

class TestToolRegistry:
    """Tests for the ToolRegistry class."""
    
    def test_tool_registry_creation(self):
        """Test creating a tool registry."""
        registry = ToolRegistry()
        assert isinstance(registry.tools, dict)
        assert len(registry.tools) == 0
    
    def test_tool_registration(self):
        """Test registering tools in the registry."""
        registry = ToolRegistry()
        
        def test_tool(param1, param2=None):
            """A test tool docstring."""
            return param1, param2
            
        # Use the register method as a decorator with a return value
        decorated_func = registry.register(name="test_tool", description="A test tool")(test_tool)
        
        # The decorator should return the original function
        assert decorated_func == test_tool
        
        # Check if the tool was registered correctly
        assert "test_tool" in registry.tools
        tool = registry.get("test_tool")
        assert tool["name"] == "test_tool"
        assert tool["description"] == "A test tool"
        assert callable(tool["function"])
        
    def test_tool_execution(self):
        """Test executing a tool from the registry."""
        registry = ToolRegistry()
        
        @registry.register()
        def add(a, b):
            """Add two numbers."""
            return a + b
        
        result = registry.execute("add", a=2, b=3)
        assert result == 5
        
    def test_list_tools(self):
        """Test listing tools."""
        registry = ToolRegistry()
        
        @registry.register(name="tool1")
        def tool1():
            """Tool 1."""
            pass
            
        @registry.register(name="tool2")
        def tool2(a: int, b: str):
            """Tool 2."""
            pass
        
        tools = registry.list_tools()
        assert len(tools) == 2
        
        # Check tool signatures
        tool2_info = next(t for t in tools if t["name"] == "tool2")
        assert "a" in tool2_info["signature"]
        assert tool2_info["signature"]["a"] == "<class 'int'>"
        
    def test_tool_not_found(self):
        """Test getting a non-existent tool."""
        registry = ToolRegistry()
        
        with pytest.raises(ValueError):
            registry.get("non_existent")
            
        with pytest.raises(ValueError):
            registry.execute("non_existent")

class TestCLIFunctions:
    """Tests for CLI entry point functions."""
    
    def test_cli_main_notebook(self, monkeypatch):
        """Test cli_main in notebook environment."""
        from cogitarelink.cli.cli import cli_main
        
        # Mock the 'ipykernel' module to simulate notebook environment
        monkeypatch.setitem(sys.modules, 'ipykernel', object())
        
        # Call cli_main, which should return an Agent in notebook context
        result = cli_main()
        assert isinstance(result, Agent)
        
    def test_cli_main_args(self, monkeypatch, capsys):
        """Test cli_main with command line arguments."""
        from cogitarelink.cli.cli import cli_main
        
        # Remove ipykernel from sys.modules if present
        if 'ipykernel' in sys.modules:
            monkeypatch.delitem(sys.modules, 'ipykernel')
        
        # Test --version flag
        monkeypatch.setattr('sys.argv', ['cogitarelink', '--version'])
        exit_code = cli_main()
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "CogitareLink version:" in captured.out
        
        # Test --list-tools flag
        monkeypatch.setattr('sys.argv', ['cogitarelink', '--list-tools'])
        exit_code = cli_main()
        assert exit_code == 0
        captured = capsys.readouterr()
        tools_list = json.loads(captured.out)
        assert isinstance(tools_list, list)
        assert len(tools_list) >= 3
        
        # Test --run-tool with invalid tool
        monkeypatch.setattr('sys.argv', ['cogitarelink', '--run-tool', 'non_existent'])
        exit_code = cli_main()
        assert exit_code == 1
        
        # Test --run-tool with valid tool
        monkeypatch.setattr('sys.argv', ['cogitarelink', '--run-tool', 'get_version'])
        exit_code = cli_main()
        assert exit_code == 0
        
        # Test --help (implicit when no args)
        monkeypatch.setattr('sys.argv', ['cogitarelink'])
        exit_code = cli_main()
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out