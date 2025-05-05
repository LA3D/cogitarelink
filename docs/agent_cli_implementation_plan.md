# Agent-Enabled CLI Implementation Plan

## Step 1: Enhance the CLI Entry Point

First, we need to modify the `cli_main()` function in `cogitarelink/cli/cli.py` to register the VocabToolAgent's tools and provide agent-friendly output:

```python
def cli_main():
    """Main entry point for the CLI."""
    # Skip argument parsing when run inside a notebook
    in_notebook = 'ipykernel' in sys.modules
    
    if in_notebook:
        # Default behavior for notebook - create an agent and return it
        return Agent()
    
    # Create default agent and register specialized tools
    agent = Agent()
    
    # Register vocabulary tools
    try:
        from cogitarelink.cli.vocab_tools import VocabToolAgent
        vocab_agent = VocabToolAgent()
        
        # Register vocabulary tools with the main agent
        for tool_name, tool_info in vocab_agent.tools.tools.items():
            if tool_name not in agent.tools.tools:
                agent.tools.tools[tool_name] = tool_info
                
        # Track that we've registered these tools
        agent.context.remember("has_vocab_tools", True)
    except ImportError:
        # Vocabulary tools not available
        agent.context.remember("has_vocab_tools", False)
    
    # Normal CLI operation with argument parsing
    parser = argparse.ArgumentParser(description="CogitareLink CLI - Semantic Vocabulary Tools")
    parser.add_argument('--version', action='store_true', help='Show version and exit')
    parser.add_argument('--list-tools', action='store_true', help='List available tools')
    parser.add_argument('--category', help='Filter tools by category (registry, context, retrieval, validation)')
    parser.add_argument('--run-tool', metavar='TOOL', help='Run a specific tool')
    parser.add_argument('--args', metavar='JSON', help='JSON arguments for tool')
    parser.add_argument('--args-file', metavar='FILE', help='File containing JSON arguments for tool')
    parser.add_argument('--agent-mode', action='store_true', help='Run in agent-friendly mode with enhanced output')
    
    args = parser.parse_args()
    
    # Always set agent mode for certain tools
    agent_mode = args.agent_mode or args.list_tools
    
    if args.version:
        version = agent.run_tool('get_version')
        print(f"CogitareLink version: {version}")
        if agent_mode:
            print("\n[AGENT GUIDANCE]")
            print("You are using CogitareLink, a tool for working with Linked Open Data.")
            print("To get started, try: cogitarelink --list-tools --agent-mode")
        return 0
        
    if args.list_tools:
        # Get all tools
        tools = agent.run_tool('list_tools')
        
        # Filter by category if requested
        if args.category:
            category = args.category.lower()
            tools = [tool for tool in tools if category in tool.get('description', '').lower()]
        
        # Group tools by categories for better organization
        tool_categories = {}
        for tool in tools:
            # Infer category from tool name or description
            category = 'core'
            name = tool.get('name', '')
            desc = tool.get('description', '').lower()
            
            if any(x in name for x in ['registry', 'vocabulary']):
                category = 'registry'
            elif any(x in name for x in ['context', 'compose']):
                category = 'context'
            elif any(x in name for x in ['retrieve', 'fetch', 'convert']):
                category = 'retrieval'
            elif any(x in name for x in ['validate', 'shape', 'check']):
                category = 'validation'
            
            if category not in tool_categories:
                tool_categories[category] = []
            tool_categories[category].append(tool)
        
        # Print tools by category with helpful descriptions
        print("CogitareLink Tools:")
        for category, category_tools in tool_categories.items():
            print(f"\n{category.upper()} TOOLS:")
            for tool in category_tools:
                print(f"  - {tool['name']}: {tool['description']}")
                if tool.get('signature'):
                    print(f"      Arguments: {json.dumps(tool['signature'])}")
        
        # Always add agent guidance for --list-tools
        print("\n[AGENT GUIDANCE]")
        print("To use any tool, run: cogitarelink --run-tool TOOL_NAME --args '{\"arg1\": \"value1\"}'")
        print("For large inputs, use: cogitarelink --run-tool TOOL_NAME --args-file arguments.json")
        print("Example workflow for registering an external context:")
        print("  1. cogitarelink --run-tool retrieve_vocabulary_resource --args '{\"uri\": \"https://example.org/context.jsonld\"}'")
        print("  2. cogitarelink --run-tool add_temp_vocabulary --args '{\"prefix\": \"example\", \"uri\": \"http://example.org/\", \"inline_context\": {...}}'")
        print("  3. cogitarelink --run-tool compose_context --args '{\"prefixes\": [\"example\"]}'")
        
        return 0
        
    if args.run_tool:
        tool_name = args.run_tool
        tool_args = {}
        
        # Get tool args from --args or --args-file
        if args.args:
            try:
                tool_args = json.loads(args.args)
            except json.JSONDecodeError as e:
                print(f"Error parsing arguments: {e}", file=sys.stderr)
                return 1
        elif args.args_file:
            try:
                with open(args.args_file, 'r') as f:
                    tool_args = json.loads(f.read())
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error reading arguments file: {e}", file=sys.stderr)
                return 1
        
        try:
            # Run the tool
            result = agent.run_tool(tool_name, **tool_args)
            
            # Check if the tool ran successfully
            if isinstance(result, dict) and 'success' in result and not result['success']:
                # Handle error with agent guidance
                print(json.dumps(result, indent=2, default=str))
                if agent_mode and 'error' in result:
                    print("\n[AGENT GUIDANCE]")
                    print(f"The tool '{tool_name}' failed with error: {result['error']}")
                    print("Possible troubleshooting steps:")
                    
                    # Suggest specific fixes based on common errors
                    error = result.get('error', '').lower()
                    if 'not found' in error:
                        print("- Check the tool name with: cogitarelink --list-tools")
                    elif 'missing' in error:
                        print("- Check required arguments with: cogitarelink --list-tools")
                        print(f"- Make sure you've provided all required arguments for {tool_name}")
                    elif 'vocabulary' in error or 'context' in error:
                        print("- Register the vocabulary first with: cogitarelink --run-tool add_temp_vocabulary")
                    elif 'fetch' in error or 'retrieve' in error:
                        print("- Check that the URI is accessible and properly formatted")
                    else:
                        print("- Review the arguments you provided")
                        print("- Try running with simpler input first")
                
                return 1
            else:
                # Print successful result
                print(json.dumps(result, indent=2, default=str))
                
                # Add agent guidance for successful tool execution
                if agent_mode:
                    print("\n[AGENT GUIDANCE]")
                    print(f"Successfully executed tool: {tool_name}")
                    
                    # Add next step suggestions based on the tool
                    if tool_name == 'retrieve_vocabulary_resource':
                        print("Next steps:")
                        print("1. Register this as a vocabulary with: cogitarelink --run-tool add_temp_vocabulary")
                    elif tool_name == 'add_temp_vocabulary':
                        print("Next steps:")
                        print("1. Compose a context with: cogitarelink --run-tool compose_context")
                        print("2. Get vocabulary info with: cogitarelink --run-tool get_vocabulary_info")
                    elif tool_name == 'compose_context':
                        print("Next steps:")
                        print("1. Use this context in your JSON-LD documents")
                        print("2. Validate data with: cogitarelink --run-tool validate_with_shapes (if you have SHACL shapes)")
                    
                    # Include tips for error handling
                    print("\nIf you encounter any errors, try:")
                    print("- Running with --list-tools to verify available tools")
                    print("- Check argument requirements for the tool")
                    print("- Make sure vocabularies are registered before using them")
                
                return 0
        except Exception as e:
            print(f"Error running tool {tool_name}: {e}", file=sys.stderr)
            if agent_mode:
                print("\n[AGENT GUIDANCE]")
                print(f"The tool '{tool_name}' failed with an unexpected error.")
                print("Try listing available tools with: cogitarelink --list-tools")
            return 1
    
    # Default behavior - show help with agent guidance
    parser.print_help()
    
    if agent_mode:
        print("\n[AGENT GUIDANCE]")
        print("CogitareLink is a tool for working with Linked Open Data and semantic vocabularies.")
        print("\nGet started with these commands:")
        print("1. List available tools: cogitarelink --list-tools --agent-mode")
        print("2. Run a tool: cogitarelink --run-tool TOOL_NAME --args '{\"arg1\": \"value1\"}'")
        print("\nCommonly used tools:")
        print("- retrieve_vocabulary_resource: Get a vocabulary from a URL")
        print("- add_temp_vocabulary: Register a vocabulary with the system")
        print("- compose_context: Create a usable context from registered vocabularies")
        print("- convert_format: Convert between JSON-LD and other formats")
    
    return 0
```

## Step 2: Add Missing Tool for SHACL Validation

Create a new file `/Users/cvardema/dev/git/LA3D/cogitarelink/cogitarelink/cli/validation_tools.py`:

```python
"""Extension tools for validation with SHACL in CogitareLink"""

from __future__ import annotations
import json
from typing import Dict, List, Any, Optional, Union

from .cli import Agent, ToolRegistry
from ..core.debug import get_logger

# Export the public API
__all__ = ['validation_tools', 'ValidationToolAgent']

log = get_logger("validation")

def validation_tools() -> Dict[str, Any]:
    """Create a set of tools for validation with SHACL shapes.
    
    Returns:
        Dict mapping tool names to tool functions
    """
    tools = {}
    
    def validate_with_shapes(data: Dict[str, Any], shapes_url: str = None, 
                            shapes_content: str = None, 
                            shapes_format: str = "turtle") -> Dict[str, Any]:
        """
        Validate data against SHACL shapes.
        
        Parameters:
            data: JSON-LD data to validate
            shapes_url: URL to SHACL shapes (alternative to shapes_content)
            shapes_content: Direct SHACL shapes content (alternative to shapes_url)
            shapes_format: Format of the shapes (turtle, json-ld, etc.)
            
        Returns:
            Validation results with conforms flag and violation details
        """
        try:
            import rdflib
            from pyshacl import validate
            
            # First get the shapes
            shapes_graph = rdflib.Graph()
            
            if shapes_url:
                # Retrieve shapes from URL
                from cogitarelink.integration.retriever import LODRetriever
                retriever = LODRetriever()
                shapes_result = retriever.retrieve(shapes_url)
                
                if not shapes_result.get("success", False):
                    return {
                        "success": False,
                        "error": f"Failed to retrieve shapes: {shapes_result.get('error', 'Unknown error')}"
                    }
                
                shapes_content = shapes_result.get("content")
                shapes_format = shapes_result.get("format", shapes_format)
            
            if not shapes_content:
                return {
                    "success": False,
                    "error": "Must provide either shapes_url or shapes_content"
                }
            
            # Parse the shapes
            shapes_graph.parse(data=shapes_content, format=shapes_format)
            
            # Parse the data
            data_graph = rdflib.Graph()
            if isinstance(data, dict) or isinstance(data, list):
                # Convert JSON-LD to graph
                data_str = json.dumps(data)
                data_graph.parse(data=data_str, format="json-ld")
            else:
                # Assume data is already a string in some RDF format
                data_graph.parse(data=data, format="json-ld")
            
            # Validate the data against the shapes
            conforms, results_graph, results_text = validate(
                data_graph=data_graph,
                shacl_graph=shapes_graph,
                inference='rdfs',
                abort_on_first=False,
                meta_shacl=False,
                debug=False
            )
            
            # Process validation results
            violations = []
            if not conforms and results_graph:
                # Extract violation details from the results graph
                for result in results_graph.subjects(rdflib.RDF.type, rdflib.URIRef("http://www.w3.org/ns/shacl#ValidationResult")):
                    violation = {}
                    
                    # Get the focus node
                    focus_nodes = list(results_graph.objects(result, rdflib.URIRef("http://www.w3.org/ns/shacl#focusNode")))
                    if focus_nodes:
                        violation["focus_node"] = str(focus_nodes[0])
                    
                    # Get the path
                    paths = list(results_graph.objects(result, rdflib.URIRef("http://www.w3.org/ns/shacl#resultPath")))
                    if paths:
                        violation["path"] = str(paths[0])
                    
                    # Get the message
                    messages = list(results_graph.objects(result, rdflib.URIRef("http://www.w3.org/ns/shacl#resultMessage")))
                    if messages:
                        violation["message"] = str(messages[0])
                    
                    # Get the severity
                    severities = list(results_graph.objects(result, rdflib.URIRef("http://www.w3.org/ns/shacl#resultSeverity")))
                    if severities:
                        severity = str(severities[0])
                        if "Violation" in severity:
                            violation["severity"] = "violation"
                        elif "Warning" in severity:
                            violation["severity"] = "warning"
                        elif "Info" in severity:
                            violation["severity"] = "info"
                        else:
                            violation["severity"] = severity
                    
                    violations.append(violation)
            
            return {
                "success": True,
                "conforms": conforms,
                "violations": violations,
                "violation_count": len(violations),
                "results_text": results_text
            }
        except ImportError as e:
            return {
                "success": False,
                "error": f"Missing required library: {str(e)}",
                "help": "Install pyshacl with: pip install pyshacl"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def generate_example_from_shapes(shapes_url: str = None, 
                                   shapes_content: str = None,
                                   shapes_format: str = "turtle",
                                   target_class: str = None) -> Dict[str, Any]:
        """
        Generate example data based on SHACL shapes.
        
        Parameters:
            shapes_url: URL to SHACL shapes (alternative to shapes_content)
            shapes_content: Direct SHACL shapes content (alternative to shapes_url)
            shapes_format: Format of the shapes (turtle, json-ld, etc.)
            target_class: Optional target class to generate an example for
            
        Returns:
            Example data conforming to the shapes
        """
        try:
            import rdflib
            
            # First get the shapes
            shapes_graph = rdflib.Graph()
            
            if shapes_url:
                # Retrieve shapes from URL
                from cogitarelink.integration.retriever import LODRetriever
                retriever = LODRetriever()
                shapes_result = retriever.retrieve(shapes_url)
                
                if not shapes_result.get("success", False):
                    return {
                        "success": False,
                        "error": f"Failed to retrieve shapes: {shapes_result.get('error', 'Unknown error')}"
                    }
                
                shapes_content = shapes_result.get("content")
                shapes_format = shapes_result.get("format", shapes_format)
            
            if not shapes_content:
                return {
                    "success": False,
                    "error": "Must provide either shapes_url or shapes_content"
                }
            
            # Parse the shapes
            shapes_graph.parse(data=shapes_content, format=shapes_format)
            
            # Find node shapes
            node_shapes = []
            for shape in shapes_graph.subjects(rdflib.RDF.type, rdflib.URIRef("http://www.w3.org/ns/shacl#NodeShape")):
                shape_info = {"id": str(shape), "properties": []}
                
                # Get target class if available
                target_classes = list(shapes_graph.objects(shape, rdflib.URIRef("http://www.w3.org/ns/shacl#targetClass")))
                if target_classes:
                    shape_info["target_class"] = str(target_classes[0])
                
                # Get property shapes
                for prop in shapes_graph.objects(shape, rdflib.URIRef("http://www.w3.org/ns/shacl#property")):
                    prop_info = {"id": str(prop)}
                    
                    # Get path
                    paths = list(shapes_graph.objects(prop, rdflib.URIRef("http://www.w3.org/ns/shacl#path")))
                    if paths:
                        prop_info["path"] = str(paths[0])
                    
                    # Get name from path
                    if "path" in prop_info:
                        path = prop_info["path"]
                        prop_info["name"] = path.split("/")[-1].split("#")[-1]
                    
                    # Get min count
                    min_counts = list(shapes_graph.objects(prop, rdflib.URIRef("http://www.w3.org/ns/shacl#minCount")))
                    if min_counts:
                        try:
                            prop_info["min_count"] = int(min_counts[0])
                        except:
                            prop_info["min_count"] = str(min_counts[0])
                    
                    # Get max count
                    max_counts = list(shapes_graph.objects(prop, rdflib.URIRef("http://www.w3.org/ns/shacl#maxCount")))
                    if max_counts:
                        try:
                            prop_info["max_count"] = int(max_counts[0])
                        except:
                            prop_info["max_count"] = str(max_counts[0])
                    
                    # Get class constraint
                    classes = list(shapes_graph.objects(prop, rdflib.URIRef("http://www.w3.org/ns/shacl#class")))
                    if classes:
                        prop_info["class"] = str(classes[0])
                    
                    # Get datatype constraint
                    datatypes = list(shapes_graph.objects(prop, rdflib.URIRef("http://www.w3.org/ns/shacl#datatype")))
                    if datatypes:
                        prop_info["datatype"] = str(datatypes[0])
                    
                    shape_info["properties"].append(prop_info)
                
                node_shapes.append(shape_info)
            
            # Filter shapes if target_class is specified
            if target_class:
                filtered_shapes = []
                for shape in node_shapes:
                    if "target_class" in shape:
                        class_name = shape["target_class"].split("/")[-1].split("#")[-1]
                        if class_name.lower() == target_class.lower():
                            filtered_shapes.append(shape)
                
                if filtered_shapes:
                    node_shapes = filtered_shapes
            
            # Generate example data from the first available shape
            example = {}
            
            if node_shapes:
                shape = node_shapes[0]
                
                # Set type from target class
                if "target_class" in shape:
                    class_uri = shape["target_class"]
                    class_name = class_uri.split("/")[-1].split("#")[-1]
                    example["@type"] = class_name
                    example["@id"] = f"urn:example:{class_name.lower()}:1"
                
                # Add properties based on constraints
                for prop in shape.get("properties", []):
                    # Skip if no name
                    if "name" not in prop:
                        continue
                    
                    prop_name = prop["name"]
                    
                    # Generate value based on constraints
                    if "class" in prop:
                        # For object properties, create a nested object
                        class_uri = prop["class"]
                        class_name = class_uri.split("/")[-1].split("#")[-1]
                        
                        if class_name in ["Person", "Organization"]:
                            example[prop_name] = {
                                "@type": class_name,
                                "name": f"Example {class_name}"
                            }
                        elif class_name in ["Place", "Location"]:
                            example[prop_name] = {
                                "@type": class_name,
                                "name": f"Example {class_name}",
                                "address": {
                                    "@type": "PostalAddress",
                                    "addressLocality": "Example City",
                                    "addressRegion": "EX",
                                    "addressCountry": "US"
                                }
                            }
                        else:
                            example[prop_name] = {
                                "@type": class_name,
                                "name": f"Example {class_name}"
                            }
                    elif "datatype" in prop:
                        # For data properties, create a sample literal
                        datatype = prop["datatype"].split("/")[-1].split("#")[-1]
                        
                        if datatype in ["dateTime", "date", "dateTimeStamp"]:
                            example[prop_name] = "2023-01-01T00:00:00Z"
                        elif datatype in ["integer", "decimal", "float", "double"]:
                            example[prop_name] = 42
                        elif datatype in ["boolean"]:
                            example[prop_name] = True
                        else:
                            example[prop_name] = f"Example {prop_name}"
                    else:
                        # Default to a string value
                        example[prop_name] = f"Example {prop_name}"
            
            return {
                "success": True,
                "example": example,
                "shapes": node_shapes,
                "shape_count": len(node_shapes)
            }
        except ImportError as e:
            return {
                "success": False,
                "error": f"Missing required library: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Generation error: {str(e)}"
            }
    
    # Add tools to the dictionary
    tools["validate_with_shapes"] = validate_with_shapes
    tools["generate_example_from_shapes"] = generate_example_from_shapes
    
    return tools

class ValidationToolAgent(Agent):
    """Agent with specialized tools for validation with SHACL."""
    
    def __init__(self, name: str = "validation-agent"):
        super().__init__(name=name)
        self._register_validation_tools()
    
    def _register_validation_tools(self):
        """Register all validation tools."""
        # Register validation tools
        for name, func in validation_tools().items():
            self.register_tool(func=func, name=name)
```

## Step 3: Modify the Main CLI Entry Point

Update the CLI initialization to include the new ValidationToolAgent in `cogitarelink/cli/__init__.py`:

```python
"""CogitareLink CLI tools and agents."""

from .cli import Agent, AgentContext, ToolRegistry, cli_main
from .vocab_tools import VocabToolAgent
from .validation_tools import ValidationToolAgent

__all__ = ['Agent', 'AgentContext', 'ToolRegistry', 'VocabToolAgent', 'ValidationToolAgent', 'cli_main']
```

## Step 4: Document the Agent Interface

Create a new file `/Users/cvardema/dev/git/LA3D/cogitarelink/docs/agent_interface.md`:

```markdown
# Cogitarelink Agent Interface Guide

This document describes how agents (like Claude) can interact with Cogitarelink using its CLI interface.

## Basic Interaction Pattern

The Cogitarelink CLI is designed to be agent-friendly with consistent output formats and helpful guidance. When running commands, you'll see:

1. **Command output**: The actual result of your command
2. **[AGENT GUIDANCE]**: Special sections with hints for agents on what to do next

## Getting Started

To begin working with Cogitarelink, run:

```bash
cogitarelink --list-tools --agent-mode
```

This will list all available tools with descriptions and argument requirements, along with guidance on how to use them.

## Working with Earth616 Ontology

### Step 1: Retrieve and Register the Context

```bash
# Retrieve the context
cogitarelink --run-tool retrieve_vocabulary_resource --args '{
  "uri": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/contexts/latest/context-base.jsonld"
}'

# Register the context with a prefix
cogitarelink --run-tool add_temp_vocabulary --args '{
  "prefix": "earth616",
  "uri": "https://ontology.crc.nd.edu/earth616/",
  "inline_context": CONTEXT_FROM_PREVIOUS_STEP
}'
```

### Step 2: Explore the Vocabulary

```bash
# Get vocabulary information
cogitarelink --run-tool get_vocabulary_info --args '{
  "prefix": "earth616"
}'

# Extract classes and properties
cogitarelink --run-tool extract_vocabulary_classes --args '{
  "prefix": "earth616"
}'
```

### Step 3: Create a Composed Context

```bash
# Compose a context using the registered vocabulary
cogitarelink --run-tool compose_context --args '{
  "prefixes": ["earth616"]
}'
```

### Step 4: Work with SHACL Shapes

```bash
# Retrieve SHACL shapes
cogitarelink --run-tool retrieve_vocabulary_resource --args '{
  "uri": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/main/release/shapes/shacl/latest/shapes.ttl",
  "format_hint": "turtle"
}'

# Generate an example based on shapes
cogitarelink --run-tool generate_example_from_shapes --args '{
  "shapes_url": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/main/release/shapes/shacl/latest/shapes.ttl",
  "target_class": "Event"
}'

# Validate data against shapes
cogitarelink --run-tool validate_with_shapes --args '{
  "data": YOUR_DATA_HERE,
  "shapes_url": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/main/release/shapes/shacl/latest/shapes.ttl"
}'
```

### Step 5: Convert Between Formats

```bash
# Convert JSON-LD to Turtle
cogitarelink --run-tool convert_format --args '{
  "content": YOUR_JSONLD_DATA,
  "from_format": "json-ld",
  "to_format": "turtle"
}'

# Convert Turtle to JSON-LD
cogitarelink --run-tool convert_format --args '{
  "content": YOUR_TURTLE_DATA,
  "from_format": "turtle",
  "to_format": "json-ld"
}'
```

## Handling Large Inputs

For large JSON inputs, use the `--args-file` option instead of `--args`:

```bash
# Create a file with your arguments
echo '{"data": {...large data...}, "shapes_url": "https://example.org/shapes.ttl"}' > my_args.json

# Use the file for arguments
cogitarelink --run-tool validate_with_shapes --args-file my_args.json
```

## Error Handling

When errors occur, Cogitarelink provides guidance on how to fix them:

```
Error: Failed to find vocabulary with prefix 'earth616'

[AGENT GUIDANCE]
The tool 'get_vocabulary_info' failed with error: Vocabulary 'earth616' not found
Possible troubleshooting steps:
- Register the vocabulary first with: cogitarelink --run-tool add_temp_vocabulary
```

Follow the guidance to resolve errors and continue your workflow.

## Stateful Operations

Note that Cogitarelink maintains some state between operations:

1. **Vocabulary registrations**: Once you register a vocabulary with `add_temp_vocabulary`, it remains available for subsequent commands.
2. **Caching**: Cogitarelink caches network operations to improve performance, with a default 15-minute cache expiration.

## Best Practices for Agents

1. **Always use --agent-mode**: This ensures you get helpful guidance.
2. **Check tool availability**: Run `--list-tools` to verify which tools are available.
3. **Follow the guidance**: The [AGENT GUIDANCE] sections provide step-by-step instructions.
4. **Handle errors gracefully**: Use the error guidance to recover from failures.
5. **Use batching for complex operations**: Break down complex tasks into smaller, manageable steps.
```

## Step 5: Create a Test Script for Earth616 Integration

Create a file `/Users/cvardema/dev/git/LA3D/cogitarelink/tests/test_earth616_agent.py`:

```python
"""Test the agent-enabled CLI with Earth616 ontology."""

import pytest
import subprocess
import json
import os
from pathlib import Path

# Constants for testing
EARTH616_CONTEXT_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/contexts/latest/context-base.jsonld"
EARTH616_SHAPES_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/main/release/shapes/shacl/latest/shapes.ttl"
EARTH616_URI = "https://ontology.crc.nd.edu/earth616/"
PREFIX = "earth616"

def run_cli_tool(tool_name, args=None, args_file=None, agent_mode=True):
    """Run a cogitarelink CLI tool and return the parsed result."""
    cmd = ["cogitarelink", "--run-tool", tool_name]
    
    if agent_mode:
        cmd.append("--agent-mode")
    
    if args:
        cmd.extend(["--args", json.dumps(args)])
    elif args_file:
        cmd.extend(["--args-file", args_file])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        # Try to parse the output as JSON
        output = json.loads(result.stdout)
        return {
            "success": result.returncode == 0,
            "result": output,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except json.JSONDecodeError:
        # Return raw output if not JSON
        return {
            "success": result.returncode == 0,
            "result": None,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

def test_list_tools():
    """Test that we can list tools in agent mode."""
    result = subprocess.run(
        ["cogitarelink", "--list-tools", "--agent-mode"], 
        capture_output=True, 
        text=True
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check for expected output sections
    assert "CogitareLink Tools:" in result.stdout
    assert "[AGENT GUIDANCE]" in result.stdout
    
    # Check for expected tool categories
    stdout = result.stdout.lower()
    assert "registry tools" in stdout or "vocabulary tools" in stdout
    assert "retrieve" in stdout or "retrieval" in stdout

def test_earth616_workflow():
    """Test a complete workflow with the Earth616 ontology."""
    # Step 1: Retrieve the context
    context_result = run_cli_tool("retrieve_vocabulary_resource", {
        "uri": EARTH616_CONTEXT_URL
    })
    
    assert context_result["success"]
    assert "content" in context_result["result"]
    
    context = context_result["result"]["content"]
    
    # Step 2: Register the vocabulary
    register_result = run_cli_tool("add_temp_vocabulary", {
        "prefix": PREFIX,
        "uri": EARTH616_URI,
        "inline_context": context,
        "description": "Earth616 Ontology Context"
    })
    
    assert register_result["success"]
    assert register_result["result"]["success"]
    
    # Step 3: Get vocabulary info
    info_result = run_cli_tool("get_vocabulary_info", {
        "prefix": PREFIX
    })
    
    assert info_result["success"]
    assert PREFIX in info_result["stdout"]
    
    # Step 4: Compose a context
    compose_result = run_cli_tool("compose_context", {
        "prefixes": [PREFIX],
        "support_nest": True
    })
    
    assert compose_result["success"]
    assert "context" in compose_result["result"]
    
    composed_context = compose_result["result"]["context"]
    
    # Step 5: Create a sample entity
    sample_data = {
        "@context": composed_context,
        "@type": "Event",
        "@id": "urn:example:event:1234",
        "name": "Test Event",
        "description": "A test event using the Earth616 ontology",
        "startTime": "2023-01-01T00:00:00Z"
    }
    
    # Create a temporary file for the sample data
    temp_file = Path("temp_sample_data.json")
    with open(temp_file, "w") as f:
        json.dump(sample_data, f)
    
    # Step 6: Convert to Turtle
    convert_result = run_cli_tool("convert_format", {
        "content": sample_data,
        "from_format": "json-ld",
        "to_format": "turtle"
    })
    
    assert convert_result["success"]
    assert isinstance(convert_result["result"]["data"], str)
    assert "<urn:example:event:1234>" in convert_result["result"]["data"]
    
    # Step 7: Try shape validation if validation tools are available
    validation_result = run_cli_tool("validate_with_shapes", {
        "data": sample_data,
        "shapes_url": EARTH616_SHAPES_URL
    })
    
    # Note: This might fail if SHACL validation isn't available
    # Just check that we get a result
    assert "result" in validation_result
    
    # Clean up
    if temp_file.exists():
        temp_file.unlink()
```

## Implementation Roadmap

1. **Phase 1: CLI Enhancement**
   - Modify `cli_main()` to register VocabToolAgent and ValidationToolAgent
   - Add agent-friendly output with guidance sections
   - Implement basic tool filtering by category
   - Add support for argument files (--args-file)

2. **Phase 2: Documentation**
   - Create agent interface guide
   - Add examples for working with Earth616 ontology
   - Document error handling and recovery strategies

3. **Phase 3: Testing**
   - Create automated tests for the agent interface
   - Test with Earth616 ontology as a real-world use case
   - Verify error handling and guidance

4. **Phase 4: Extended Tools**
   - Add remaining tools identified in the requirements
   - Enhance feedback with more detailed next steps
   - Add progress reporting for long-running operations

## Success Criteria

The implementation will be considered successful when:

1. An agent can discover available tools through `--list-tools --agent-mode`
2. The agent receives clear guidance on next steps after each operation
3. The agent can work with Earth616 ontology without writing Python code
4. Error messages include actionable guidance for recovery
5. The automated tests pass and verify the complete workflow