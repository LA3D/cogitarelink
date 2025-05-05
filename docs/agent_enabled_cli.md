# Agent-Enabled CLI for Cogitarelink

## Overview

This document outlines a proposed refactoring of the Cogitarelink CLI to better support agent-based interactions, using the earth616_ontology as a test case. The goal is to expose Cogitarelink's powerful vocabulary and JSON-LD capabilities directly to agents like Claude through well-defined tools, eliminating the need for agents to write Python code to interact with the system.

## Current State Assessment

As an agent attempting to work with the earth616_ontology through Cogitarelink, I encountered several limitations:

1. **Limited CLI Tool Exposure**: Only basic tools (`get_version`, `list_tools`, `get_agent_memory`) are exposed through the CLI, despite rich functionality being available in the codebase.

2. **Agent-Unfriendly Architecture**: To access vocabulary tools, an agent must write Python code that directly instantiates the `VocabToolAgent` class.

3. **Inconsistent Tool Registration**: The `VocabToolAgent` class exists but isn't registered with the default CLI agent.

4. **Missing Direct Access**: Common operations like registering contexts, validating against shapes, or generating examples require custom Python code rather than simple tool invocations.

## User Story: Agent Working with earth616_ontology

As an agent, I want to:

1. Retrieve and register the earth616_ontology context
2. Examine its structure and vocabulary terms
3. Compose contexts using the earth616 vocabulary
4. Validate data against the earth616 SHACL shapes
5. Convert between different formats (JSON-LD, Turtle)
6. Generate valid example instances based on shapes

Currently, accomplishing these tasks requires writing custom Python code that directly uses the Cogitarelink classes, which is inefficient and error-prone for an agent.

## Proposed Refactoring

### 1. Tool Registration System

Modify the `cli_main()` function to automatically register specialized tool agents:

```python
def cli_main():
    """Main entry point for the CLI."""
    # Skip argument parsing when run inside a notebook
    in_notebook = 'ipykernel' in sys.modules
    
    if in_notebook:
        # Default behavior for notebook - create an agent and return it
        return Agent()
    
    # Create default agent
    agent = Agent()
    
    # Register specialized tool agents
    from cogitarelink.cli.vocab_tools import VocabToolAgent
    vocab_agent = VocabToolAgent()
    
    # Copy all vocab tools to the main agent
    for tool_name, tool_info in vocab_agent.tools.tools.items():
        if tool_name not in agent.tools.tools:
            agent.tools.tools[tool_name] = tool_info
    
    # Process CLI arguments
    parser = argparse.ArgumentParser(description="CogitareLink CLI")
    # ... existing argument parsing ...
```

### 2. Tool Categories

Organize tools into clear categories with a new `--category` option:

```
cogitarelink --list-tools --category vocab
cogitarelink --list-tools --category context
cogitarelink --list-tools --category retrieval
cogitarelink --list-tools --category validation
```

### 3. Direct Access to Key Operations

Expose specialized tools for working directly with earth616_ontology:

```
cogitarelink --run-tool register_external_context --args '{"prefix": "earth616", "uri": "https://ontology.crc.nd.edu/earth616/", "context_url": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/contexts/latest/context-base.jsonld"}'

cogitarelink --run-tool validate_with_shapes --args '{"data": {...}, "shapes_url": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/main/release/shapes/shacl/latest/shapes.ttl"}'

cogitarelink --run-tool generate_example_from_shapes --args '{"shapes_url": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/main/release/shapes/shacl/latest/shapes.ttl", "target_class": "Event"}'
```

### 4. JSON-LD Operations Tooling

Create dedicated tools for common JSON-LD operations:

```
cogitarelink --run-tool expand_jsonld --args '{"data": {...}, "context": {...}}'
cogitarelink --run-tool compact_jsonld --args '{"data": {...}, "context": {...}}'
cogitarelink --run-tool normalize_jsonld --args '{"data": {...}, "algorithm": "URDNA2015"}'
```

### 5. Format Conversion

Simplify format conversion operations:

```
cogitarelink --run-tool convert_format --args '{"content": "...", "from_format": "json-ld", "to_format": "turtle"}'
```

## New Tools to Implement

Based on my experience with earth616_ontology, these new tools should be implemented and exposed through the CLI:

### Registry Tools

1. **register_external_context** - Register an external context URL with a prefix
2. **register_ttl_as_vocabulary** - Convert and register a TTL file as a vocabulary
3. **list_vocabulary_terms** - List terms defined in a registered vocabulary
4. **extract_vocabulary_classes** - Extract class definitions from a vocabulary
5. **extract_vocabulary_properties** - Extract property definitions from a vocabulary

### Context Tools

1. **compose_context_for_classes** - Create a context focused on specific classes
2. **analyze_context_structure** - Provide summary analysis of a context structure
3. **detect_json_schema** - Generate a JSON Schema based on a JSON-LD context
4. **context_diff** - Compare two contexts and identify differences

### Validation Tools

1. **validate_with_shapes** - Validate data against SHACL shapes
2. **extract_shape_constraints** - Extract constraints from SHACL shapes
3. **generate_example_from_shapes** - Generate example data based on shapes
4. **suggest_shapes_for_data** - Suggest potential SHACL shapes based on existing data

### Entity Tools

1. **create_entity** - Create an entity with a specific context
2. **normalize_entity** - Normalize an entity's representation
3. **hash_entity** - Generate a deterministic hash for an entity
4. **extract_entity_graph** - Extract a graph of entities from a document

## Sample Agent Workflow

Here's how an agent would interact with earth616_ontology using the improved CLI:

```
# Step 1: Register the vocabulary
cogitarelink --run-tool register_external_context --args '{
  "prefix": "earth616", 
  "uri": "https://ontology.crc.nd.edu/earth616/", 
  "context_url": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/contexts/latest/context-base.jsonld"
}'

# Step 2: Analyze the vocabulary structure
cogitarelink --run-tool extract_vocabulary_classes --args '{
  "prefix": "earth616"
}'

# Step 3: Create a sample entity
cogitarelink --run-tool create_entity --args '{
  "type": "Event",
  "prefix": "earth616",
  "properties": {
    "name": "Supply Chain Event",
    "startTime": "2023-01-01T00:00:00Z",
    "description": "Test event"
  }
}'

# Step 4: Validate against SHACL shapes
cogitarelink --run-tool validate_with_shapes --args '{
  "data": <entity from previous step>,
  "shapes_url": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/main/release/shapes/shacl/latest/shapes.ttl"
}'

# Step 5: Convert to turtle format
cogitarelink --run-tool convert_format --args '{
  "content": <entity from step 3>,
  "from_format": "json-ld",
  "to_format": "turtle"
}'
```

## Implementation Recommendations

1. **Tool Registration System**: Modify `Agent` to recursively include tools from specialized agents.

2. **Stateful Agent Context**: Enhance `AgentContext` to persist vocabulary registrations and context compositions across tool invocations.

3. **Unified Output Format**: Standardize tool outputs with consistent fields like `success`, `result`, `error`, and `message`.

4. **Progress Feedback**: For long-running operations, implement progress feedback mechanisms.

5. **Error Recovery**: Add capabilities for agents to recover from errors (retry mechanisms, fallbacks).

6. **Caching Improvements**: Enhance caching for network-dependent operations to improve reliability.

## Potential Challenges

1. **JSON Argument Size Limits**: CLI arguments may have size limits that make passing large contexts difficult.
   - Solution: Add `--args-file` option to read arguments from a file.

2. **Process Isolation**: Each tool invocation runs in a separate process, losing in-memory state.
   - Solution: Enhance disk caching for agent state persistence.

3. **Error Handling**: Agents need clear error information to make recovery decisions.
   - Solution: Standardize error formats and provide actionable recovery hints.

4. **Documentation Discovery**: Agents need to discover tool capabilities at runtime.
   - Solution: Add a tool that returns detailed documentation for each tool.

## Testing Approach

The earth616_ontology provides an excellent test case for this refactoring:

1. **Feature Coverage**: Ensure all operations needed for working with earth616_ontology are covered by tools.

2. **Agent Workflows**: Test end-to-end workflows that an agent would perform with earth616_ontology.

3. **Error Cases**: Test error handling when dealing with malformed inputs or network failures.

4. **Performance Benchmarks**: Measure performance differences between direct library use and CLI tool use.

## Conclusion

By refactoring the Cogitarelink CLI to better support agent-based interactions, we can enable powerful semantic data capabilities without requiring agents to write custom Python code. The earth616_ontology serves as both a user story and test case for this refactoring, ensuring that the resulting system meets real-world requirements for working with complex ontologies and JSON-LD contexts.

The proposed changes maintain the core architecture of Cogitarelink while making its capabilities more accessible to non-human agents, ultimately creating a more flexible and powerful system for semantic data operations.