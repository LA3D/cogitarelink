# Using the Agent-Enabled CLI with Earth616 Ontology

This guide demonstrates how to use the Cogitarelink agent-enabled CLI to work with the earth616 ontology. The CLI has been specifically optimized for agent interactions, providing structured JSON output with guidance at each step.

## Setup

First, make sure you've installed Cogitarelink with development dependencies:

```bash
uv pip install -e ".[dev]"
```

Export the notebook code to Python modules:

```bash
nbdev_export
```

## Working with Earth616 Ontology

The CLI includes specialized tools for working with the earth616 ontology, making it easy to register the ontology, explore its structure, generate examples, and convert between formats.

### 1. List Available Tools

Start by listing all available tools:

```bash
python -m cogitarelink.cli.agent_cli --list-tools
```

The output will be JSON with all tools categorized by their purpose, along with agent guidance on how to proceed.

To see just the earth616-related tools:

```bash
python -m cogitarelink.cli.agent_cli --list-tools --category earth616
```

### 2. Register Earth616 Ontology

Register the earth616 ontology with a single command:

```bash
python -m cogitarelink.cli.agent_cli --run-tool register_earth616
```

This tool:
1. Retrieves the earth616 context from GitHub
2. Registers it with the vocabulary registry
3. Sets up earth616_shapes_url for validation
4. Returns success with guidance on next steps

Sample output:
```json
{
  "success": true,
  "message": "Successfully registered earth616 ontology with prefix 'earth616'",
  "context_size": 12345,
  "agent_guidance": {
    "description": "The earth616 ontology is now registered in the system.",
    "next_steps": [
      "Get vocabulary information: cogitarelink --run-tool get_vocabulary_info --args '{\"prefix\":\"earth616\"}'",
      "Compose a context: cogitarelink --run-tool compose_context --args '{\"prefixes\":[\"earth616\"]}'",
      "Generate an example: cogitarelink --run-tool generate_earth616_example"
    ]
  }
}
```

### 3. Get Vocabulary Information

Examine the registered vocabulary:

```bash
python -m cogitarelink.cli.agent_cli --run-tool get_vocabulary_info --args '{"prefix":"earth616"}'
```

### 4. Generate Example Entities

Generate example entities using the earth616 ontology:

```bash
python -m cogitarelink.cli.agent_cli --run-tool generate_earth616_example
```

By default, this generates an Event. You can specify other entity types:

```bash
python -m cogitarelink.cli.agent_cli --run-tool generate_earth616_example --args '{"entity_type":"Organization"}'
```

The tool supports these entity types:
- Event
- Place
- Person
- Organization
- Product

Sample output:
```json
{
  "success": true,
  "example": {
    "@context": {...},
    "@type": "Event",
    "@id": "urn:example:event:1234",
    "name": "Example Event",
    "description": "A sample Event using the Earth616 ontology context",
    "startTime": "2023-01-01T00:00:00Z",
    "endTime": "2023-01-02T00:00:00Z",
    "location": {...},
    "participant": [...]
  },
  "agent_guidance": {
    "description": "Generated an example Event using earth616 ontology.",
    "next_steps": [
      "Convert to other formats: cogitarelink --run-tool convert_format --args '{\"content\": <example>, \"from_format\": \"json-ld\", \"to_format\": \"turtle\"}'",
      "Generate examples of other types: cogitarelink --run-tool generate_earth616_example --args '{\"entity_type\": \"Organization\"}'"
    ],
    "available_types": ["Event", "Place", "Person", "Organization", "Product"]
  }
}
```

### 5. Convert Between Formats

Convert your example to Turtle format:

```bash
# First, save the example to a file
echo '{"content": {...example JSON...}, "from_format": "json-ld", "to_format": "turtle"}' > convert_args.json

# Then convert using the file
python -m cogitarelink.cli.agent_cli --run-tool convert_format --args-file convert_args.json
```

The `--args-file` option is useful for large JSON inputs that would be cumbersome to include directly on the command line.

## Working with JSON-LD Contexts

The CLI includes tools for working with JSON-LD contexts:

### Compose a Context

```bash
python -m cogitarelink.cli.agent_cli --run-tool compose_context --args '{"prefixes":["earth616"], "support_nest": true}'
```

### Analyze Context Compatibility

```bash
python -m cogitarelink.cli.agent_cli --run-tool analyze_context_compatibility --args '{"prefix_a":"earth616", "prefix_b":"schema"}'
```

## Agent Guidance

All responses include an `agent_guidance` section that provides:

1. Description of the result
2. Next steps with example commands
3. Additional context-specific guidance

This makes it easy for agents to follow their nose through complex workflows without needing to understand the full API.

## Error Handling

When errors occur, the CLI provides structured error information with suggestions for resolution:

```json
{
  "success": false,
  "error": "Earth616 vocabulary not found: Vocabulary 'earth616' not found",
  "agent_guidance": {
    "description": "The earth616 vocabulary is not registered.",
    "suggestions": [
      "Register earth616 first: cogitarelink --run-tool register_earth616"
    ]
  }
}
```

## Using the CLI from Another Agent

When integrating with another agent:

1. Parse the JSON response to extract the result and agent guidance
2. Follow the suggested next steps in `agent_guidance.next_steps`
3. For errors, use the suggestions in `agent_guidance.suggestions`
4. Use `--args-file` for large JSON payloads

The CLI's consistent structure makes it reliable for automated parsing and navigation.

## Extending the Tools

If you need to add new tools for earth616 or other ontologies, modify the `10_agent_cli.ipynb` notebook to add new methods to the `AgentCLI` class, then export using `nbdev_export`.

For example, to add a new tool for validating earth616 data against SHACL shapes, you would add a method like:

```python
@self.tools.register(name="validate_earth616", 
                   description="Validate data against earth616 SHACL shapes")
def validate_earth616(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate data against earth616 SHACL shapes."""
    # Implementation here
    # ...
```

This extensible architecture allows you to continually improve the agent experience with new tools and capabilities.