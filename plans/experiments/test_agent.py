#!/usr/bin/env python
"""
Test script for CogitareLink's CLI agent functionality.
This script tests both the basic Agent and the VocabToolAgent.
"""

from cogitarelink.cli.cli import Agent
from cogitarelink.cli.vocab_tools import VocabToolAgent

def fix_register_croissant_tools(agent):
    """Fix the croissant tools registration method"""
    def create_croissant_dataset(name, description=None, recordsets=None):
        """
        Create a Croissant dataset with the specified properties.
        
        Parameters:
            name: Dataset name
            description: Optional dataset description
            recordsets: Optional list of recordset definitions
            
        Returns:
            Complete Croissant dataset object
        """
        return {
            "success": True,
            "dataset": {
                "@type": "Dataset",
                "name": name,
                "description": description or "",
                "recordSet": recordsets or []
            }
        }
    
    agent.register_tool(func=create_croissant_dataset, name="create_croissant_dataset")
    return agent

def test_basic_agent():
    """Test the basic Agent functionality"""
    print("\n=== Testing Basic Agent ===")
    agent = Agent(name="test-agent")
    
    # List available tools
    print("\nListing available tools:")
    tools = agent.run_tool('list_tools')
    for tool in tools:
        print(f"- {tool['name']}: {tool['description']}")
    
    # Get version
    print("\nGetting version:")
    version = agent.run_tool('get_version')
    print(f"CogitareLink version: {version}")
    

def test_vocab_tool_agent():
    """Test the VocabToolAgent functionality"""
    print("\n=== Testing VocabToolAgent ===")
    
    try:
        # Create a VocabToolAgent instance
        agent = VocabToolAgent(name="test-vocab-agent")
        
        # Fix the registration method for Croissant tools
        agent = fix_register_croissant_tools(agent)
        
        # List available tools
        print("\nListing available tools:")
        tools = agent.run_tool('list_tools')
        vocab_tools = [t for t in tools if t['name'] not in ['get_version', 'list_tools', 'get_agent_memory']]
        print(f"Found {len(vocab_tools)} vocabulary-specific tools:")
        
        # Group tools by category
        registry_tools = [t for t in vocab_tools if t['name'].startswith('explore_') or t['name'].startswith('get_vocabulary_')]
        context_tools = [t for t in vocab_tools if t['name'].startswith('compose_') or t['name'].startswith('analyze_')]
        retrieval_tools = [t for t in vocab_tools if t['name'].startswith('retrieve_') or t['name'].startswith('wikidata_')]
        croissant_tools = [t for t in vocab_tools if t['name'].startswith('create_croissant_')]
        
        print(f"- Registry tools: {len(registry_tools)}")
        for t in registry_tools:
            print(f"  - {t['name']}")
            
        print(f"- Context tools: {len(context_tools)}")
        for t in context_tools:
            print(f"  - {t['name']}")
            
        print(f"- Retrieval tools: {len(retrieval_tools)}")
        for t in retrieval_tools:
            print(f"  - {t['name']}")
            
        print(f"- Croissant tools: {len(croissant_tools)}")
        for t in croissant_tools:
            print(f"  - {t['name']}")
        
        # Test registry exploration
        print("\nExploring vocabulary registry:")
        try:
            registries = agent.run_tool('explore_registry')
            print(f"Found {len(registries)} vocabularies")
            for prefix, entry in list(registries.items())[:3]:  # Show first 3
                print(f"- {prefix}: {entry['uri']}")
        except Exception as e:
            print(f"Error exploring registry: {e}")
        
        
    # Removed return to avoid PytestReturnNotNoneWarning
    
    except Exception as e:
        print(f"Error creating VocabToolAgent: {e}")

if __name__ == "__main__":
    # Test the basic agent
    basic_agent = test_basic_agent()
    
    # Test the vocab tool agent
    vocab_agent = test_vocab_tool_agent()