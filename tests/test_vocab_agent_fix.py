"""
Test the fixed VocabToolAgent implementation.

This test specifically validates that the create_croissant_dataset tool
works correctly with the updated run_tool method to avoid the
'got multiple values for argument name' error.
"""

import pytest
import json
from cogitarelink.cli.vocab_tools import VocabToolAgent

def test_create_croissant_dataset():
    """Test that the create_croissant_dataset tool works correctly."""
    # Create a VocabToolAgent
    agent = VocabToolAgent(name="test-fix-agent")
    
    # Create a simple dataset
    result = agent.run_tool("create_croissant_dataset", 
                          name="Test Dataset", 
                          description="A test dataset for verifying the fix")
    
    # Verify the result
    assert result["success"] is True
    assert result["dataset"]["@type"] == "Dataset"
    assert result["dataset"]["name"] == "Test Dataset"
    assert result["dataset"]["description"] == "A test dataset for verifying the fix"
    print("✓ create_croissant_dataset tool works correctly!")
    
    # Try the alignment tool as well
    align_result = agent.run_tool("align_dataset_to_wikidata",
                                dataset=result["dataset"],
                                confidence_threshold=0.6)
    
    # Should succeed (even if no alignments are found)
    assert align_result["success"] is True
    print("✓ align_dataset_to_wikidata tool works correctly!")
    
    return result

if __name__ == "__main__":
    dataset = test_create_croissant_dataset()
    print(f"\nCreated dataset: {json.dumps(dataset['dataset'], indent=2)}")