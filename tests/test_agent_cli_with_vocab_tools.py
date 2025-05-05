"""
Test the integration between AgentCLI and VocabToolAgent.

This test verifies that the tools from VocabToolAgent work correctly
when registered and used through the AgentCLI class.
"""

import pytest
pytest.skip("Skipping CLI/Croissant integration until Croissant logic is refactored", allow_module_level=True)
import json
from cogitarelink.cli.agent_cli import AgentCLI
from cogitarelink.core.debug import get_logger

# Create the logger manually to work around import issue
log = get_logger("agent_cli")

def test_agent_cli_with_vocab_tools():
    """Test that AgentCLI can successfully use VocabToolAgent tools."""
    # Create an AgentCLI instance (which should register VocabToolAgent tools)
    # First fix the log reference (which is imported but not available)
    import cogitarelink.cli.agent_cli
    cogitarelink.cli.agent_cli.log = log
    
    agent = AgentCLI(name="test-agent-cli")
    
    # List all available tools
    tools = agent.run_tool("list_tools")
    tool_names = [t["name"] for t in tools]
    
    # Check that vocab tools are registered
    assert "explore_registry" in tool_names
    assert "get_vocabulary_info" in tool_names
    assert "create_croissant_dataset" in tool_names
    print("✓ VocabToolAgent tools successfully registered in AgentCLI")
    
    # Try to create a Croissant dataset through AgentCLI
    try:
        # Use regular run_tool instead of run_tool_with_guidance to avoid parameter conflict
        result = agent.run_tool("create_croissant_dataset", 
                              name="Test Dataset via AgentCLI", 
                              description="Testing VocabToolAgent integration")
        
        # Verify the result
        assert result["success"] is True
        assert result["dataset"]["@type"] == "Dataset"
        assert result["dataset"]["name"] == "Test Dataset via AgentCLI"
        print("✓ Successfully used create_croissant_dataset through AgentCLI")
        
        return result
    except Exception as e:
        pytest.fail(f"Failed to use create_croissant_dataset through AgentCLI: {e}")

if __name__ == "__main__":
    result = test_agent_cli_with_vocab_tools()
    print(f"\nCreated dataset via AgentCLI: {json.dumps(result['dataset'], indent=2)}")