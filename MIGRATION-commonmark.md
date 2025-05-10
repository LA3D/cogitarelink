

# CogitareLink Migration Documentation

This document outlines the migration from older memory-related
components to the new architecture.

## Overview of Legacy Components

### memory.py

The original semantic memory system built on RDF triple stores with the
following capabilities: - Triple/quad storage with both in-memory and
RDFLib backends - Entity storage and retrieval with indexing by ID and
type - JSON-LD processing and normalization - Query capabilities over
graph structures

### memorytools.py

Tools for connecting the memory system to LLM frameworks: - Tool tracing
and debugging facilities - Memory-aware chat creation - Entity
exploration tools for traversing relationships

### vmemory.py

Vectorized memory extensions: - Vector embeddings for semantic search -
Hybrid search combining graph and vector approaches - LLM-based
operations on memory contents

### vocabtools.py

Vocabulary management utilities: - Registry of common vocabularies with
URIs and metadata - Collision strategies for vocabulary combinations -
Document loader that handles vocabulary expansion - URL transformation
utilities

### retriever.py

Linked Open Data retrieval with agent capabilities: - URI analysis and
access strategy determination - HTML analysis for embedded structured
data - Navigation through linked data resources - Entity extraction and
normalization - Wikidata-specific utilities

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

<table>
<colgroup>
<col style="width: 40%" />
<col style="width: 40%" />
<col style="width: 18%" />
</colgroup>
<thead>
<tr>
<th>Old Component</th>
<th>New Component</th>
<th>Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>SemanticMemory</code></td>
<td><code>core/graph.py</code> + <code>core/processor.py</code></td>
<td>Split into graph storage and entity processing</td>
</tr>
<tr>
<td><code>add()</code></td>
<td><code>EntityProcessor.add()</code></td>
<td>Entity creation and storage</td>
</tr>
<tr>
<td><code>add_jsonld()</code></td>
<td><code>EntityProcessor.add()</code></td>
<td>Simplified interface</td>
</tr>
<tr>
<td><code>query_by_id()</code></td>
<td><code>EntityProcessor.get_by_id()</code></td>
<td>Entity retrieval by ID</td>
</tr>
<tr>
<td><code>query_by_type()</code></td>
<td>Graph queries</td>
<td>Use graph patterns for type filtering</td>
</tr>
<tr>
<td><code>normalize()</code></td>
<td><code>ContextProcessor.normalize()</code></td>
<td>Now in context module</td>
</tr>
<tr>
<td><code>expand()</code></td>
<td><code>ContextProcessor.expand()</code></td>
<td>Now in context module</td>
</tr>
</tbody>
</table>

### From `memorytools.py` to New Architecture

<table>
<colgroup>
<col style="width: 40%" />
<col style="width: 40%" />
<col style="width: 18%" />
</colgroup>
<thead>
<tr>
<th>Old Component</th>
<th>New Component</th>
<th>Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>create_traced_tool()</code></td>
<td>External LLM integration</td>
<td>Tool tracing moved to framework-specific code</td>
</tr>
<tr>
<td><code>create_memory_tracer()</code></td>
<td>External LLM integration</td>
<td>Tracing moved to framework-specific code</td>
</tr>
<tr>
<td><code>create_memory_chat()</code></td>
<td>External LLM integration</td>
<td>Chat creation moved to framework-specific code</td>
</tr>
<tr>
<td><code>create_memory_exploration_tools()</code></td>
<td>Graph API + Entity API</td>
<td>Use core APIs directly in tool implementations</td>
</tr>
</tbody>
</table>

### From `vocabtools.py` to New Architecture

<table>
<colgroup>
<col style="width: 40%" />
<col style="width: 40%" />
<col style="width: 18%" />
</colgroup>
<thead>
<tr>
<th>Old Component</th>
<th>New Component</th>
<th>Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>VocabularyManager</code></td>
<td><code>vocab/registry.py</code></td>
<td>Registry management</td>
</tr>
<tr>
<td><code>detect_vocabularies_in_context()</code></td>
<td><code>vocab/registry.py</code></td>
<td>Now uses registry lookups</td>
</tr>
<tr>
<td><code>register_vocab_aware_loader()</code></td>
<td><code>core/context.py</code></td>
<td>Document loader registration</td>
</tr>
<tr>
<td><code>apply_collision_strategy()</code></td>
<td><code>vocab/collision.py</code></td>
<td>Collision handling</td>
</tr>
</tbody>
</table>

### From `retriever.py` to Refactored Version

<table style="width:100%;">
<colgroup>
<col style="width: 34%" />
<col style="width: 50%" />
<col style="width: 15%" />
</colgroup>
<thead>
<tr>
<th>Old Component</th>
<th>Refactored Component</th>
<th>Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>URIAnalyzer</code></td>
<td>Non-LLM pattern matching</td>
<td>Replace dspy with pattern-based recognition</td>
</tr>
<tr>
<td><code>HTMLAnalyzer</code></td>
<td>BeautifulSoup parsing</td>
<td>Remove LLM dependency, use explicit patterns</td>
</tr>
<tr>
<td><code>LODNavigator</code></td>
<td><code>LODRetriever</code></td>
<td>Framework-agnostic retrieval</td>
</tr>
<tr>
<td><code>search_wikidata()</code></td>
<td>Keep and reuse</td>
<td>Non-LLM dependent utility</td>
</tr>
<tr>
<td><code>json_parse()</code></td>
<td>Keep and reuse</td>
<td>Non-LLM dependent utility</td>
</tr>
<tr>
<td><code>rdf_to_jsonld()</code></td>
<td>Keep and reuse</td>
<td>Non-LLM dependent utility</td>
</tr>
</tbody>
</table>

## Code That Should Be Retained

The following components from the old system should be retained:

- `utils.py` - Development utilities
- Core retrieval utilities from `retriever.py`:
  - `json_parse()` - JSON parsing with error recovery
  - `rdf_to_jsonld()` - RDF format conversion
  - `search_wikidata()` - Wikidata API client

## Recommended Migration Strategy

1.  Keep legacy modules in `backup/` directory for reference
2.  For existing code using old APIs:
    - Use the migration table to map old functions to new ones
    - Create adapters if needed for backward compatibility
3.  For new code:
    - Use the new architecture directly
    - Implement framework-specific integrations separately

## Testing Migration

To verify that functionality has been properly migrated:

1.  Create test notebooks that exercise both old and new APIs
2.  Compare results for identical inputs
3.  Document any behavioral differences

## Example Workflow Migration

### Old Workflow

``` python
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

``` python
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
