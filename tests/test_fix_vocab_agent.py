"""
Test script for verifying the fix to the VocabToolAgent's tool registration.
This specifically tests the create_croissant_dataset tool that was causing issues.
"""
import pytest
from cogitarelink.cli.vocab_tools import VocabToolAgent

def test_create_croissant_dataset():
    """Test that the create_croissant_dataset tool works without errors."""
    # Create a VocabToolAgent
    agent = VocabToolAgent(name="test-fix-agent")
    
    # List available tools
    tools = agent.run_tool('list_tools')
    tool_names = [t['name'] for t in tools]
    
    # Check that the croissant tool is registered
    assert 'create_croissant_dataset' in tool_names
    
    # Create a dataset
    try:
        result = agent.run_tool('create_croissant_dataset', 
                              name="Test Dataset", 
                              description="A test dataset for verifying the fix")
        
        # Verify the result
        assert result["success"] is True
        assert result["dataset"]["@type"] == "Dataset"
        assert result["dataset"]["name"] == "Test Dataset"
        assert result["dataset"]["description"] == "A test dataset for verifying the fix"
        
        print("✅ create_croissant_dataset tool works correctly!")
    except TypeError as e:
        if "got multiple values for argument 'name'" in str(e):
            pytest.fail("The TypeError 'got multiple values for argument name' still exists!")
        else:
            pytest.fail(f"Unexpected TypeError: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")
    
if __name__ == "__main__":
    test_create_croissant_dataset()