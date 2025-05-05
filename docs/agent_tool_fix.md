# Agent Tool Registry Fix Documentation

## Issue

The VocabToolAgent class had a bug where tools were registered correctly but couldn't be called due to a parameter conflict:

```
TypeError: Agent.run_tool() got multiple values for argument 'name'
```

This error occurred because of how the `run_tool` method in the `Agent` class is implemented. The method has a signature:

```python
def run_tool(self, name: str, **kwargs) -> Any:
```

When calling `run_tool("tool_name", param="value")`, the first argument "tool_name" gets assigned to `name`. But when a parameter is called `name`, it conflicts with the positional argument.

## Solution

The fix involves:

1. Override the `run_tool` method in the `VocabToolAgent` class to avoid the parameter conflict:

```python
def run_tool(self, tool_name: str, **kwargs) -> Any:
    """Override run_tool to fix name parameter issue."""
    try:
        # Get the tool directly from the registry
        tool = self.tools.get(tool_name)
        func = tool["function"]
        # Execute the function directly
        result = func(**kwargs)
        self.context.log_action(tool_name, kwargs, result)
        return result
    except Exception as e:
        self.context.log_action(tool_name, kwargs, e)
        raise
```

2. Update the implementation of `_register_croissant_tools` to use direct function calls instead of `run_tool`:

```python
# Use tool function directly to avoid run_tool parameter issue
tool = self.tools.get("load_context_for_vocabulary")
ctx_result = tool["function"](prefix="croissant")
```

## Affected Areas

- `VocabToolAgent` class in `cogitarelink/cli/vocab_tools.py`

## Verification

Created a test file (`tests/test_vocab_agent_fix.py`) to verify the fix works properly:

```python
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
```

## Next Steps

For better robustness, the `run_tool` method in the `Agent` class could be updated to use a parameter name other than `name` for the tool name, such as `tool_name`. This would prevent similar conflicts in the future.

Additionally, the AgentCLI class inherits this issue as well. A similar override could be added there, or a more general solution could be implemented in the base Agent class.