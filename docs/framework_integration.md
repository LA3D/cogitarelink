# Framework Integration Guide

This guide explains how to integrate CogitareLink with different LLM frameworks.

## Overview

CogitareLink provides core functionality for handling JSON-LD data and Linked Open Data (LOD) retrieval without dependencies on specific LLM frameworks. This guide shows how to integrate these capabilities with popular LLM frameworks.

## General Approach

When integrating CogitareLink with an LLM framework, follow these principles:

1. Keep framework-specific code separate from the core library
2. Use CogitareLink's API to provide structured data to LLMs
3. Convert LLM outputs to appropriate formats for CogitareLink
4. Create wrapper functions/classes that handle the integration

## Integration with Claude/Anthropic (Claude API)

### Tool Definitions

```python
def retrieve_entity_tool(entity_id, vocab=["schema"]):
    """Retrieve an entity from CogitareLink.
    
    Args:
        entity_id: The ID of the entity to retrieve
        vocab: List of vocabulary prefixes to use
        
    Returns:
        dict: The entity data in JSON-LD format
    """
    from cogitarelink.core.processor import EntityProcessor
    
    processor = EntityProcessor()
    entity = processor.get_by_id(entity_id)
    
    if entity:
        return entity.as_json
    else:
        return {"error": f"Entity {entity_id} not found"}

def create_entity_tool(data, vocab=["schema"]):
    """Create a new entity in CogitareLink.
    
    Args:
        data: The entity data to store
        vocab: List of vocabulary prefixes to use
        
    Returns:
        dict: The created entity with its ID
    """
    from cogitarelink.core.processor import EntityProcessor
    
    processor = EntityProcessor()
    entity = processor.add(data, vocab=vocab)
    
    return {
        "id": entity.id,
        "entity": entity.as_json
    }

def retrieve_lod_tool(uri):
    """Retrieve linked data from a URI.
    
    Args:
        uri: The URI to retrieve from
        
    Returns:
        dict: The retrieved data
    """
    from cogitarelink.integration.retriever import LODRetriever
    
    retriever = LODRetriever()
    result = retriever.retrieve(uri)
    
    return result
```

### Tool Registration

```python
from anthropic import Claude

client = Claude(api_key="your_api_key")

tools = [
    {
        "name": "retrieve_entity",
        "description": "Retrieve an entity from the knowledge graph",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The ID of the entity to retrieve"
                },
                "vocab": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of vocabulary prefixes to use"
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "create_entity",
        "description": "Create a new entity in the knowledge graph",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "The entity data to store"
                },
                "vocab": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of vocabulary prefixes to use"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "retrieve_lod",
        "description": "Retrieve linked data from a URI",
        "input_schema": {
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "The URI to retrieve from"
                }
            },
            "required": ["uri"]
        }
    }
]

# Function to handle tool calls
def handle_tool_calls(tool_calls):
    results = []
    for call in tool_calls:
        name = call.name
        arguments = call.arguments
        
        if name == "retrieve_entity":
            result = retrieve_entity_tool(arguments["entity_id"], arguments.get("vocab", ["schema"]))
        elif name == "create_entity":
            result = create_entity_tool(arguments["data"], arguments.get("vocab", ["schema"]))
        elif name == "retrieve_lod":
            result = retrieve_lod_tool(arguments["uri"])
        else:
            result = {"error": f"Unknown tool {name}"}
            
        results.append({
            "tool_call_id": call.id,
            "output": result
        })
        
    return results
```

### Example Usage

```python
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    tools=tools,
    messages=[
        {"role": "user", "content": "Retrieve information about Douglas Adams from Wikidata"}
    ]
)

if response.tool_calls:
    tool_results = handle_tool_calls(response.tool_calls)
    
    follow_up = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": "Retrieve information about Douglas Adams from Wikidata"},
            {"role": "assistant", "content": response.content},
            {"role": "user", "tool_results": tool_results}
        ]
    )
    
    print(follow_up.content)
```

## Integration with LangChain

### Tool Definitions

```python
from langchain.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EntityIdInput(BaseModel):
    entity_id: str = Field(..., description="The ID of the entity to retrieve")
    vocab: Optional[List[str]] = Field(default=["schema"], description="List of vocabulary prefixes to use")

class EntityDataInput(BaseModel):
    data: Dict[str, Any] = Field(..., description="The entity data to store")
    vocab: Optional[List[str]] = Field(default=["schema"], description="List of vocabulary prefixes to use")

class UriInput(BaseModel):
    uri: str = Field(..., description="The URI to retrieve from")

class EntityRetrievalTool(BaseTool):
    name = "retrieve_entity"
    description = "Retrieve an entity from the knowledge graph"
    args_schema = EntityIdInput
    
    def _run(self, entity_id: str, vocab: Optional[List[str]] = ["schema"]):
        from cogitarelink.core.processor import EntityProcessor
        
        processor = EntityProcessor()
        entity = processor.get_by_id(entity_id)
        
        if entity:
            return entity.as_json
        else:
            return {"error": f"Entity {entity_id} not found"}

class EntityCreationTool(BaseTool):
    name = "create_entity"
    description = "Create a new entity in the knowledge graph"
    args_schema = EntityDataInput
    
    def _run(self, data: Dict[str, Any], vocab: Optional[List[str]] = ["schema"]):
        from cogitarelink.core.processor import EntityProcessor
        
        processor = EntityProcessor()
        entity = processor.add(data, vocab=vocab)
        
        return {
            "id": entity.id,
            "entity": entity.as_json
        }

class LODRetrievalTool(BaseTool):
    name = "retrieve_lod"
    description = "Retrieve linked data from a URI"
    args_schema = UriInput
    
    def _run(self, uri: str):
        from cogitarelink.integration.retriever import LODRetriever
        
        retriever = LODRetriever()
        result = retriever.retrieve(uri)
        
        return result
```

### Tool Registration

```python
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)

tools = [
    EntityRetrievalTool(),
    EntityCreationTool(),
    LODRetrievalTool()
]

agent = initialize_agent(
    tools, 
    llm, 
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
```

### Example Usage

```python
agent.run("Retrieve information about Douglas Adams from Wikidata")
```

## Integration with DSPy

### Module Definitions

```python
import dspy
from typing import List, Dict, Any

class EntityRetriever(dspy.Module):
    def __init__(self):
        super().__init__()
        from cogitarelink.core.processor import EntityProcessor
        self.processor = EntityProcessor()
    
    def forward(self, entity_id, vocab=["schema"]):
        entity = self.processor.get_by_id(entity_id)
        if entity:
            return entity.as_json
        else:
            return {"error": f"Entity {entity_id} not found"}

class EntityCreator(dspy.Module):
    def __init__(self):
        super().__init__()
        from cogitarelink.core.processor import EntityProcessor
        self.processor = EntityProcessor()
    
    def forward(self, data, vocab=["schema"]):
        entity = self.processor.add(data, vocab=vocab)
        return {
            "id": entity.id,
            "entity": entity.as_json
        }

class LODRetrieverModule(dspy.Module):
    def __init__(self):
        super().__init__()
        from cogitarelink.integration.retriever import LODRetriever
        self.retriever = LODRetriever()
    
    def forward(self, uri):
        result = self.retriever.retrieve(uri)
        return result
```

### Signature Definitions

```python
class EntityRetrievalSignature(dspy.Signature):
    """Retrieve an entity from the knowledge graph."""
    entity_id = dspy.InputField(desc="The ID of the entity to retrieve")
    vocab = dspy.InputField(desc="List of vocabulary prefixes to use (optional)")
    entity = dspy.OutputField(desc="The retrieved entity data")

class EntityCreationSignature(dspy.Signature):
    """Create a new entity in the knowledge graph."""
    data = dspy.InputField(desc="The entity data to store")
    vocab = dspy.InputField(desc="List of vocabulary prefixes to use (optional)")
    result = dspy.OutputField(desc="The created entity with its ID")

class LODRetrievalSignature(dspy.Signature):
    """Retrieve linked data from a URI."""
    uri = dspy.InputField(desc="The URI to retrieve from")
    result = dspy.OutputField(desc="The retrieved data")
```

### Predictor Definition

```python
class KnowledgeGraphAssistant(dspy.Module):
    def __init__(self):
        super().__init__()
        self.entity_retriever = dspy.TypedPredictor(EntityRetriever(), EntityRetrievalSignature)
        self.entity_creator = dspy.TypedPredictor(EntityCreator(), EntityCreationSignature)
        self.lod_retriever = dspy.TypedPredictor(LODRetrieverModule(), LODRetrievalSignature)
        self.generate_response = dspy.ChainOfThought(dspy.Signature(
            query = dspy.InputField(desc="The user's query"),
            retrieved_data = dspy.InputField(desc="Any data retrieved from tools"),
            response = dspy.OutputField(desc="Response to the user's query")
        ))
    
    def forward(self, query):
        # Example of sequentially using tools based on query
        if "wikidata" in query.lower():
            # Extract entity from query
            entity_name = query.split("about ")[-1].split(" from")[0]
            
            # Use LOD retriever
            lod_result = self.lod_retriever(uri=f"http://www.wikidata.org/entity/{entity_name}")
            
            # Generate response
            response = self.generate_response(
                query=query,
                retrieved_data=lod_result.result
            )
            
            return response.response
        
        # Other logic for different query types...
        return "I couldn't determine how to handle that query."
```

### Example Usage

```python
assistant = KnowledgeGraphAssistant()
response = assistant("Retrieve information about Douglas Adams from Wikidata")
print(response)
```

## Custom Tool Building Pattern

For any LLM framework, you can follow this general pattern to build custom tools:

1. **Identify the CogitareLink Function**: Determine which CogitareLink function provides the capability you need.

2. **Create a Wrapper Function**: Write a wrapper that:
   - Takes inputs in a format expected by the LLM framework
   - Calls the CogitareLink function
   - Formats the output as expected by the LLM framework

3. **Add Error Handling**: Ensure your wrapper handles errors gracefully:
   - Check for missing or invalid inputs
   - Handle exceptions from CogitareLink functions
   - Return informative error messages

4. **Document the Tool**: Provide clear documentation:
   - Input format and required fields
   - Output format
   - Example usage
   - Any limitations

5. **Register with Framework**: Follow the framework-specific registration process.

### Example Pattern

```python
def cogitarelink_tool_template(input_param1, input_param2=None):
    """Tool description for LLM.
    
    Args:
        input_param1: Description of first parameter
        input_param2: Description of second parameter (optional)
        
    Returns:
        dict: Description of return value
    """
    try:
        # Import CogitareLink components
        from cogitarelink.some_module import some_function
        
        # Pre-process inputs if needed
        processed_input = some_preprocessing(input_param1)
        
        # Call CogitareLink function
        result = some_function(processed_input, input_param2)
        
        # Post-process output if needed
        formatted_result = some_postprocessing(result)
        
        return formatted_result
        
    except Exception as e:
        # Handle errors
        return {
            "error": str(e),
            "input_param1": input_param1,
            "input_param2": input_param2
        }
```

## Best Practices

1. **Keep Dependencies Separate**: Don't add framework-specific dependencies to CogitareLink core.

2. **Use Standard Data Formats**: Pass data between CogitareLink and LLMs using standard formats (JSON, strings).

3. **Handle State Carefully**: LLM frameworks have different state management approaches - design your integration accordingly.

4. **Provide Clear Documentation**: Ensure the LLM understands how to use your tools by providing clear descriptions.

5. **Input Validation**: Validate inputs before passing them to CogitareLink functions.

6. **Error Handling**: Gracefully handle and report errors in a way the LLM can understand and respond to.

7. **Cached Results**: Consider caching frequent operations to improve performance.

8. **Testing**: Create integration tests that validate both the LLM interaction and CogitareLink functionality.

## Framework-Specific Resources

- **Anthropic Claude**: [Claude documentation on tools](https://docs.anthropic.com/claude/docs/tools-overview)
- **LangChain**: [LangChain tools documentation](https://python.langchain.com/docs/modules/agents/tools/)
- **DSPy**: [DSPy documentation on modules](https://github.com/stanfordnlp/dspy)