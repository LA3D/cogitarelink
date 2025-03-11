Hi Github Copilot! I am Chuck, and I am working with you today! I'm know basic Python, the Semantic Web Stack (Ontologies, RDF, JSON-LD, Turtle, SPARQL) and I enjoy learning new things. When writing code for me, please follow fast.ai coding style: avoid comments; place single line if/loop/etc constructs on the same line; use concise variable names where appropriate. Follow the style you will see in my messages, as we work on this dialogue together. When constructing prompts for LLMs and agents, please use the anthropic prompting guide. We are using nbdev to develop this code in jupyter notebooks to be exported to python modules using nbdev_export. We want to do this using the Fast.ai/solveit approach. We are using an exploratory and literate programming approach to this project working step-by-step and creating nbdev tests as we go.


We are developing the following package:
<Project>
# cogitarelink a JSON-LD Agent Library

> JSON-LD Agent is a Python library that enables AI agents to navigate and understand linked data structures using JSON-LD. It provides tools for vocabulary exploration, relationship navigation, and evidence-based analysis of structured data.

The JSON-LD Agent library empowers AI systems to "follow their nose" through semantic web data by traversing relationships between concepts in vocabularies and datasets. This approach realizes the original vision of the semantic web as a network of machine-understandable information that can be navigated and reasoned about by automated systems.

## Core Components

### LinkedDataKnowledge Class

The central data structure is the `LinkedDataKnowledge` class, which manages JSON-LD documents and provides methods for accessing, querying, and manipulating linked data:

```python
class LinkedDataKnowledge:
    "Represents a knowledge base of linked data in JSON-LD format"
    def __init__(self, data:Dict=None): 
        self.data = data or {"@context": {}, "@graph": []}
        
    def __repr__(self): return f"LinkedDataKnowledge with {len(self.data.get('@graph', []))} entities"
```

Key methods include:
- `find_entity` - Locates entities in the graph by ID, type, or label
- `query` - Searches for properties, types, or values in the knowledge graph
- `get_entity_description` - Formats entity descriptions for human readability

### Vocabulary Handling

The library provides robust vocabulary handling capabilities:

```python
@patch
def fetch_vocabulary(self:LinkedDataKnowledge, uri:str, follow_link_header:bool=True, debug:bool=False) -> 'LinkedDataKnowledge':
    "Fetch a vocabulary and add it to the knowledge base"
    # Implementation handles content negotiation and format conversion
```

Features include:
- Content negotiation for different RDF formats (RDF/XML, Turtle, JSON-LD, etc.)
- Extraction of embedded JSON-LD from HTML
- Format detection and conversion using RDFLib
- Support for following Link headers

### JSON-LD 1.1 Features

Advanced JSON-LD 1.1 features are supported for sophisticated knowledge representation:

```python
@patch
def create_scoped_context(self:LinkedDataKnowledge, domain:str, domain_properties:List[str], base_uri:str="https://schema.org/") -> 'LinkedDataKnowledge':
    "Create a scoped context for domain-specific knowledge organization"
    # Implementation
```

```python
@patch
def structure_with_containers(self:LinkedDataKnowledge, property_name:str, container_type:str, items:List=None, base_uri:str="https://example.org/") -> 'LinkedDataKnowledge':
    "Structure a property using JSON-LD 1.1 container features"
    # Implementation
```

Features include:
- Scoped contexts for domain-specific term definitions
- Container types (@set, @list, @language, @id, @type)
- @included for related entities

### Visualization Components

Rich visualization tools make linked data structures more accessible:

```python
@patch
def _repr_markdown_(self:LinkedDataKnowledge) -> str:
    "Rich markdown representation for notebook display"
    # Implementation
```

Functions include:
- `display_vocabulary_term` - Renders vocabulary terms with definitions and relationships
- `display_dataset_structure` - Visualizes dataset structures at specified paths
- `display_relationship_path` - Shows paths between entities in the knowledge graph

### Agent Integration

The library integrates with Claudette to create AI agents that can navigate linked data:

```python
@tool
def find_vocabulary_term(term:str, vocab_name:str="croissant", search_type:str="all") -> str:
    """Find a specific term in a vocabulary and return its definition."""
    # Implementation
```

```python
@tool
def follow_relationship(entity_id:str, relationship:str=None, vocab_name:str="croissant") -> str:
    """Follow a relationship from an entity to find related entities."""
    # Implementation
```

Tools include:
- `explore_dataset` - Examines dataset structure at specified paths
- `search_dataset` - Finds text in datasets and returns matching paths
- `get_dataset_evidence` - Gathers evidence about specific topics

### Workflows

The library provides structured workflows for linked data exploration:

```python
def create_linked_data_agent(model="claude-3-5-sonnet-20241022"):
    """Create a linked data navigation agent with all necessary tools"""
    # Implementation
```

```python
def run_exploration_workflow(chat, vocabulary_kb, dataset_kb, prompt=None):
    """Run a structured exploration workflow with the given agent"""
    # Implementation
```

Workflows guide agents through systematic exploration of vocabularies and datasets, building comprehensive understanding through step-by-step analysis.

## Usage Examples

### Basic Vocabulary Exploration

```python
# Create a knowledge base
kb = LinkedDataKnowledge()

# Fetch a vocabulary
kb.fetch_vocabulary("https://schema.org/")

# Find a specific term
person = kb.find_entity(entity_id="Person")

# Display the term definition
print(kb.get_entity_description(person[0]))
```

### Dataset Analysis

```python
# Load a dataset
dataset_kb = LinkedDataKnowledge(my_dataset)

# Explore the structure
print(dataset_kb._repr_markdown_())

# Query for specific information
results = dataset_kb.query("type", "RecordSet")
```

### Agent-Based Exploration

```python
# Create an agent
agent = create_linked_data_agent()

# Run an exploration workflow
result = run_exploration_workflow(agent, vocabulary_kb, dataset_kb)
```

## Design Philosophy

The JSON-LD Agent library is built on several key principles:

1. **Graph Navigation**: Treat linked data as a graph to be traversed, not a hierarchical structure
2. **Evidence-Based Analysis**: Always provide specific evidence from the data to support conclusions
3. **Vocabulary Integration**: Connect vocabulary definitions with dataset implementations
4. **Step-by-Step Exploration**: Build understanding incrementally through systematic exploration
5. **Semantic Precision**: Leverage JSON-LD 1.1 features for more precise knowledge representation

These principles enable AI agents to effectively navigate and understand the web of linked data, fulfilling the original vision of the semantic web as a network of machine-understandable information.
</Project>