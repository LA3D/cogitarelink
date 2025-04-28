# CogitareLink Migration Documentation

This document outlines the migration from older memory-related components to the new architecture.

## Overview of Legacy Components

### memory.py
The original semantic memory system built on RDF triple stores with the following capabilities:
- Triple/quad storage with both in-memory and RDFLib backends
- Entity storage and retrieval with indexing by ID and type
- JSON-LD processing and normalization
- Query capabilities over graph structures

### memorytools.py
Tools for connecting the memory system to LLM frameworks:
- Tool tracing and debugging facilities
- Memory-aware chat creation
- Entity exploration tools for traversing relationships

### vmemory.py
Vectorized memory extensions:
- Vector embeddings for semantic search
- Hybrid search combining graph and vector approaches
- LLM-based operations on memory contents

### vocabtools.py
Vocabulary management utilities:
- Registry of common vocabularies with URIs and metadata
- Collision strategies for vocabulary combinations
- Document loader that handles vocabulary expansion
- URL transformation utilities

### retriever.py
Linked Open Data retrieval with agent capabilities:
- URI analysis and access strategy determination
- HTML analysis for embedded structured data
- Navigation through linked data resources
- Entity extraction and normalization
- Wikidata-specific utilities

## New Architecture

The functionality has been reorganized into the following components:

### Core Components

#### core/entity.py
- JSON-LD entity representation
- Immutable view of JSON-LD resources
- Child entity extraction
- Normalization and hashing

#### core/graph.py
- RDF triple/quad storage
- Support for both in-memory and RDFLib backends
- Parent-child relationship tracking
- Named graph management

#### core/processor.py
- Entity processing pipeline
- Graph document handling
- Entity relationships and navigation
- Vocabulary tracking

#### core/context.py
- JSON-LD context processing
- Expansion, compaction, and normalization
- Registry-aware document loading
- Context validation

#### core/cache.py
- Lightweight caching system
- Memory and disk backends
- Namespace-scoped memoization

#### core/debug.py
- Logging utilities

### Vocabulary Management

#### vocab/registry.py
- Registry of vocabulary definitions
- Prefix and URI mapping
- Context payload access

#### vocab/collision.py
- Vocabulary collision resolution
- Strategy determination for vocabulary combinations
- Safety checks for protected terms

#### vocab/composer.py
- Context composition from multiple vocabularies
- Implementation of collision strategies
- JSON-LD 1.1 feature support

### Verification

#### verify/signer.py
- Ed25519 signing of normalized documents
- Key generation and management
- Verification of signatures

#### verify/validator.py
- SHACL validation of entities
- Integration with pyshacl

## Migration Paths

### From `memory.py` to New Architecture

| Old Component | New Component | Notes |
|---------------|---------------|-------|
| `SemanticMemory` | `core/graph.py` + `core/processor.py` | Split into graph storage and entity processing |
| `add()` | `EntityProcessor.add()` | Entity creation and storage |
| `add_jsonld()` | `EntityProcessor.add()` | Simplified interface |
| `query_by_id()` | `EntityProcessor.get_by_id()` | Entity retrieval by ID |
| `query_by_type()` | Graph queries | Use graph patterns for type filtering |
| `normalize()` | `ContextProcessor.normalize()` | Now in context module |
| `expand()` | `ContextProcessor.expand()` | Now in context module |

### From `memorytools.py` to New Architecture

| Old Component | New Component | Notes |
|---------------|---------------|-------|
| `create_traced_tool()` | External LLM integration | Tool tracing moved to framework-specific code |
| `create_memory_tracer()` | External LLM integration | Tracing moved to framework-specific code |
| `create_memory_chat()` | External LLM integration | Chat creation moved to framework-specific code |
| `create_memory_exploration_tools()` | Graph API + Entity API | Use core APIs directly in tool implementations |

### From `vocabtools.py` to New Architecture

| Old Component | New Component | Notes |
|---------------|---------------|-------|
| `VocabularyManager` | `vocab/registry.py` | Registry management |
| `detect_vocabularies_in_context()` | `vocab/registry.py` | Now uses registry lookups |
| `register_vocab_aware_loader()` | `core/context.py` | Document loader registration |
| `apply_collision_strategy()` | `vocab/collision.py` | Collision handling |

### From `retriever.py` to Refactored Version

| Old Component | Refactored Component | Notes |
|---------------|----------------------|-------|
| `URIAnalyzer` | Non-LLM pattern matching | Replace dspy with pattern-based recognition |
| `HTMLAnalyzer` | BeautifulSoup parsing | Remove LLM dependency, use explicit patterns |
| `LODNavigator` | `LODRetriever` | Framework-agnostic retrieval |
| `search_wikidata()` | Keep and reuse | Non-LLM dependent utility |
| `json_parse()` | Keep and reuse | Non-LLM dependent utility |
| `rdf_to_jsonld()` | Keep and reuse | Non-LLM dependent utility |

## Code That Should Be Retained

The following components from the old system should be retained:

- `utils.py` - Development utilities
- Core retrieval utilities from `retriever.py`:
  - `json_parse()` - JSON parsing with error recovery
  - `rdf_to_jsonld()` - RDF format conversion
  - `search_wikidata()` - Wikidata API client

## Recommended Migration Strategy

1. Keep legacy modules in `backup/` directory for reference
2. For existing code using old APIs:
   - Use the migration table to map old functions to new ones
   - Create adapters if needed for backward compatibility
3. For new code:
   - Use the new architecture directly
   - Implement framework-specific integrations separately

## Testing Migration

To verify that functionality has been properly migrated:

1. Create test notebooks that exercise both old and new APIs
2. Compare results for identical inputs
3. Document any behavioral differences

## Example Workflow Migration

### Old Workflow

```python
from cogitarelink.memory import SemanticMemory
from cogitarelink.vocabtools import register_vocab_aware_loader

# Register vocab-aware loader
register_vocab_aware_loader()

# Create memory
memory = SemanticMemory()

# Add entity
entity = memory.add({
    "@context": "https://schema.org/",
    "@type": "Person",
    "name": "John Doe"
})

# Query
result = memory.query_by_type("Person")
```

### New Workflow

```python
from cogitarelink.core.context import ContextProcessor
from cogitarelink.core.processor import EntityProcessor
from cogitarelink.core.graph import GraphManager

# Create components
ctx_proc = ContextProcessor()  # Loader already registered
graph = GraphManager()
processor = EntityProcessor(ctx_proc, graph)

# Add entity
entity = processor.add({
    "@type": "Person",
    "name": "John Doe"
}, vocab=["schema"])

# Query
results = [processor.get_by_id(eid) for eid in 
           graph.query(pred="http://www.w3.org/1999/02/22-rdf-syntax-ns#type", 
                      obj="http://schema.org/Person")]
```