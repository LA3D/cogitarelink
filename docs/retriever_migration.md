# Retriever Migration Guide

This document outlines how to migrate the Linked Open Data retrieval functionality from the old retriever.py (which used dspy for agentic retrieval) to a framework-agnostic implementation.

## Overview of Original Retriever

The original retriever.py provided these key capabilities:

1. **URI Analysis** (via dspy-based URIAnalyzer)
   - Domain identification
   - URI type detection (entity, property, class, vocabulary)
   - Access pattern recommendations

2. **HTML Analysis** (via dspy-based HTMLAnalyzer)
   - Detection of embedded JSON-LD
   - Link header analysis
   - RDFa and microdata detection

3. **LOD Navigation** (via LODNavigator)
   - Strategy-based access to LOD resources
   - Format conversion
   - Graph extraction

4. **Wikidata Utilities**
   - Entity search
   - Property extraction
   - Entity details

5. **RDF Conversion**
   - Turtle to JSON-LD
   - RDF/XML to JSON-LD
   - Error recovery

## Core Utilities to Preserve

The following utilities from the original retriever.py are not LLM-dependent and should be preserved:

### json_parse
```python
def json_parse(content, uri=None):
    """Parse JSON content with error handling and recovery.
    
    Returns:
        tuple: (parsed_data, error_message)
    """
    # Implementation handles JSON errors
    # Tries recovery strategies
```

### rdf_to_jsonld
```python
def rdf_to_jsonld(content, format="turtle", base_uri=None):
    """Convert RDF content to JSON-LD.
    
    Returns:
        tuple: (jsonld_data, error_message)
    """
    # Handles RDF parsing
    # Converts to JSON-LD
    # Tries fallback formats
```

### search_wikidata
```python
def search_wikidata(query, limit=10, language="en"):
    """Search Wikidata API for entities matching the query string.
    
    Returns:
        list: List of dictionaries containing entity information
    """
    # Performs Wikidata API search
    # Returns structured results
```

## Framework-Agnostic Replacement

The new retriever should maintain the same capabilities but without dspy dependencies. Here's a design approach:

### 1. Pattern-Based URI Analysis

Replace the LLM-based URI analyzer with a rules-based approach:

```python
def analyze_uri(uri):
    """Analyze URI to determine basic characteristics.
    
    Returns:
        dict: URI analysis results
    """
    # Use regex patterns to identify characteristics
    # Check against known URI patterns in registry
    # Return structured analysis
```

### 2. HTML Parser for Linked Data

Replace LLM-based HTML analysis with deterministic parsing:

```python
def analyze_html(html, uri):
    """Analyze HTML to determine how to extract linked data.
    
    Returns:
        dict: Analysis results with extraction method and location
    """
    # Use BeautifulSoup to parse HTML
    # Look for standard patterns (JSON-LD script tags, link headers, etc.)
    # Return structured analysis
```

### 3. LOD Resource Access Patterns

Create a deterministic access strategy selector:

```python
def determine_access_strategy(uri, uri_type=None, source=None):
    """Determine the best strategy to access a LOD resource.
    
    Returns:
        dict: Access strategy details
    """
    # Use registry to find known patterns for the source
    # Apply URL transformations if needed
    # Return structured strategy information
```

### 4. LOD Retriever Class

Define a class that integrates these components:

```python
class LODRetriever:
    """Retriever for Linked Open Data resources."""
    
    def __init__(self, cache=None, registry=None):
        """Initialize the retriever."""
        # Setup components
        
    def retrieve(self, uri):
        """Retrieve a structured data resource from a URI.
        
        Returns:
            dict: Result containing resource data and metadata
        """
        # Analysis phase
        # Strategy selection
        # Resource retrieval
        # Format conversion
        # Return structured result
        
    def get_entity_details(self, entity_id):
        """Get detailed information about an entity.
        
        Returns:
            dict: Structured entity information
        """
        # Entity retrieval
        # Property extraction
        # Return structured data
```

## Integration with LLM Frameworks

The framework-agnostic retriever can be integrated with different LLM frameworks in these ways:

### Tool Definition Example (for Claude/OpenAI)

```python
def lod_retrieve_tool(uri):
    """Retrieve linked data from a URI.
    
    Args:
        uri: The URI to retrieve data from
        
    Returns:
        dict: Retrieved data in JSON-LD format
    """
    retriever = LODRetriever()
    result = retriever.retrieve(uri)
    return result
```

### DSPy Integration Example

```python
class LODRetrieverModule(dspy.Module):
    """DSPy module for LOD retrieval."""
    
    def __init__(self):
        super().__init__()
        self.retriever = LODRetriever()
        
    def forward(self, uri):
        """Retrieve linked data from a URI."""
        return self.retriever.retrieve(uri)
```

### Langchain Integration Example

```python
from langchain.tools import Tool

lod_tool = Tool(
    name="retrieve_lod",
    description="Retrieve linked data from a URI",
    func=lambda uri: LODRetriever().retrieve(uri)
)
```

## Implementation Approach

1. Start by extracting and refactoring the non-LLM dependent utilities
2. Create pattern-based replacements for URI and HTML analysis
3. Build the LODRetriever class using the existing registry and context processor
4. Add framework-specific adaptors as needed

This maintains the core functionality while removing LLM dependencies, making the component more focused and suitable for use in various frameworks.