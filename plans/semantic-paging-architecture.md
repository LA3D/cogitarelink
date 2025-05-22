# Semantic Paging Architecture Implementation Plan

This document outlines a comprehensive implementation plan for the semantic paging subsystem described in `plans/composer/composer.md`, integrated with our token-efficient JSON-LD filtering approach.

## 1. Architecture Overview

### Subsystem Layout

```
cogitarelink/
  agent/
    context_window.py    # Working context controller
    retrieval.py         # Hybrid graph + symbol + embedding search
    materialiser.py      # Token-budgeted serialisation of entities (our focus)
    committer.py         # Parses LLM output and writes back
  integration/
    retriever.py         # Hybrid graph + symbol + embedding search
    code_indexer.py      # Optional: tree-sitter / ripgrep symbol index
```

### Key Components

| Layer | Responsibility | Key Abstraction |
|-------|----------------|----------------|
| Retrieval | Find the right nodes (graph triples, code symbols, doc blobs) | `Retriever.fetch(query, k, filters…) → List[Entity]` |
| Materialiser | Convert nodes into tokens of plain text or diff-chunks | `Materialiser.serialise(entities, style="code")` |
| ContextWindow | Build prompts, track token usage, evict when necessary | `ContextWindow.add(fragment)`, `ContextWindow.render()` |
| Committer | Detect structured sections in LLM's reply, validate and write back | `Committer.ingest(text)` |

## 2. Implementation Plan by Component

### Phase 1: Core Token-Efficient Materialiser (Week 1-2)

The Materialiser is the central component of our token-efficient approach and will be implemented first.

#### A. Materialiser Module (`agent/materialiser.py`)

```python
from typing import List, Dict, Any, Optional, Union, Tuple
import json
from cogitarelink.core.entity import Entity
from cogitarelink.vocab.composer import composer
from cogitarelink.core.context import ContextProcessor

class Materialiser:
    """Token-budgeted serialisation of entities for LLM context windows."""
    
    def __init__(self, token_budget: int = 4000):
        self.token_budget = token_budget
        self.ctx_processor = ContextProcessor()
        
    def weight(self, obj: Dict[str, Any], hard_cap: int = 4096) -> int:
        """
        Fast O(size_of_obj) proxy for token cost.
        1 char ≈ ¼ token for English / JSON keys.
        Clamp to hard_cap so one monster object never blocks the queue.
        """
        rough = len(json.dumps(obj, separators=(",", ":")))
        return min(rough, hard_cap)
        
    def serialise(self, 
                 entities: List[Entity], 
                 style: str = "jsonld",
                 max_bytes: int = 20_000,
                 max_chunks: int = 30,
                 compaction: str = "smallest-context") -> str:
        """
        Convert entities into a token-efficient string representation.
        
        Parameters
        ----------
        entities : List of entities to serialize
        style : Format style ("jsonld", "nquads", "code")
        max_bytes : Soft budget for byte length
        max_chunks : Maximum number of entities to include
        compaction : Strategy for handling @context ("smallest-context", "shared", "none")
        
        Returns
        -------
        str : Serialized content ready for LLM context window
        """
        if style == "code":
            return self._serialise_code(entities, max_bytes, max_chunks)
        elif style == "nquads":
            return self._serialise_nquads(entities, max_bytes, max_chunks)
        else:  # default to jsonld
            return self._serialise_jsonld(entities, max_bytes, max_chunks, compaction)
    
    def _serialise_jsonld(self, 
                         entities: List[Entity], 
                         max_bytes: int,
                         max_chunks: int,
                         compaction: str) -> str:
        """Serialize entities as JSON-LD with byte-budget awareness."""
        # Implementation of the core byte-weighted packing algorithm
        picked, total = [], 0
        for entity in entities[:max_chunks]:
            # Get compact representation with efficient context
            entity_json = self._prepare_entity(entity, compaction)
            
            # Calculate weight
            w = self.weight(entity_json)
            
            # Check if we're exceeding budget
            if total + w > max_bytes:
                break
                
            picked.append(entity_json)
            total += w
        
        # Handle context sharing based on compaction strategy
        if compaction == "smallest-context" and picked:
            # Extract shared context to reduce duplication
            shared_context = composer.compose([e.vocab[0] for e in entities if e.vocab])
            result = {
                "@context": shared_context.get("@context", {}),
                "@graph": picked
            }
            serialized = json.dumps(result, indent=2)
        else:
            # Each entity keeps its own context
            serialized = "\n".join(json.dumps(obj, indent=2) for obj in picked)
        
        # Add indication if entities were omitted
        if len(picked) < len(entities):
            omitted = len(entities) - len(picked)
            serialized += f"\n\n// ...{omitted} more entities omitted due to token budget..."
        
        return serialized
    
    def _serialise_nquads(self, entities: List[Entity], max_bytes: int, max_chunks: int) -> str:
        """Serialize entities as N-Quads with line-budget awareness."""
        # Implementation with line-based budgeting
        # ...
    
    def _serialise_code(self, entities: List[Entity], max_bytes: int, max_chunks: int) -> str:
        """Serialize code entities with special handling for signatures, docstrings, etc."""
        # Implementation for code entities
        # ...
    
    def _prepare_entity(self, entity: Entity, compaction: str) -> Dict[str, Any]:
        """Prepare entity for serialization with appropriate context handling."""
        if compaction == "none":
            # Use full entity with context
            return entity.as_json
        
        # Strip system metadata for efficiency
        content = {k: v for k, v in entity.as_json.items() 
                  if not k.startswith("sys:") and not k.startswith("metadata:")}
        
        if compaction == "minimal":
            # Remove @context to be provided separately
            if "@context" in content:
                del content["@context"]
                
        return content
```

### Phase 2: Context Window Management (Week 2-3)

#### A. ContextWindow Module (`agent/context_window.py`)

```python
from typing import List, Dict, Any, Optional, Callable
import json

class ContextWindow:
    """Manages the LLM context window with token tracking and eviction."""
    
    def __init__(self, max_tokens: int = 12_000, tokeniser=None):
        self.max_tokens = max_tokens
        self.fragments: List[Dict[str, Any]] = []
        self.tokens_used = 0
        self.tokeniser = tokeniser or self._default_tokeniser
    
    def add(self, text: str, metadata: Dict[str, Any] = None):
        """
        Add a text fragment to the context window.
        
        Parameters
        ----------
        text : The text fragment to add
        metadata : Optional metadata about the fragment (priority, source, etc.)
        """
        t = self.tokeniser.count(text)
        if self.tokens_used + t > self.max_tokens:
            self._evict(t)
            
        fragment = {
            "text": text,
            "tokens": t,
            "metadata": metadata or {}
        }
        self.fragments.append(fragment)
        self.tokens_used += t
        
        return True  # Successfully added
    
    def _evict(self, needed: int):
        """
        Evict fragments to make room for new content.
        Default is FIFO eviction; can be extended with priority-based policies.
        """
        while self.fragments and self.tokens_used + needed > self.max_tokens:
            # Sort by priority if available, otherwise FIFO
            if all("priority" in f.get("metadata", {}) for f in self.fragments):
                self.fragments.sort(key=lambda f: f.get("metadata", {}).get("priority", 999))
                
            removed = self.fragments.pop(0)
            self.tokens_used -= removed["tokens"]
    
    def render(self) -> str:
        """
        Render the context window content for the LLM prompt.
        """
        return "\n\n".join(f["text"] for f in self.fragments)
    
    def _default_tokeniser(self, text: str) -> int:
        """Simple fallback tokeniser."""
        return len(text.split())
```

### Phase 3: Retrieval System (Week 3-4)

#### A. Retrieval Module (`agent/retrieval.py`)

```python
from typing import List, Dict, Any, Optional
from cogitarelink.core.entity import Entity
from cogitarelink.core.graph import GraphManager

class Retriever:
    """Hybrid retrieval system for finding relevant entities."""
    
    def __init__(self, graph: GraphManager, code_index=None, vector_index=None):
        self.graph = graph
        self.code_index = code_index
        self.vector_index = vector_index
    
    def fetch(self, query: str, k: int = 10, **filters) -> List[Entity]:
        """
        Fetch relevant entities based on the query.
        
        Parameters
        ----------
        query : The user query or keyword
        k : Maximum number of entities to return
        filters : Additional filters (e.g., type, source)
        
        Returns
        -------
        List of relevant entities
        """
        results = []
        
        # Strategy 1: Graph-based retrieval (SPARQL, property traversal)
        graph_results = self._fetch_from_graph(query, k, **filters)
        results.extend(graph_results)
        
        # Strategy 2: Code-symbol lookup (if applicable)
        if self.code_index and "code" in filters.get("sources", []):
            code_results = self._fetch_from_code(query, k, **filters)
            results.extend(code_results)
        
        # Strategy 3: Vector similarity (if available)
        if self.vector_index and len(results) < k:
            vector_results = self._fetch_from_vectors(query, k - len(results), **filters)
            results.extend(vector_results)
        
        # Deduplicate, score, and sort
        unique_results = self._deduplicate_and_score(results, query)
        
        return unique_results[:k]
    
    def _fetch_from_graph(self, query: str, k: int, **filters) -> List[Entity]:
        """Fetch entities from the graph using SPARQL or traversal."""
        # Implementation details...
        
    def _fetch_from_code(self, query: str, k: int, **filters) -> List[Entity]:
        """Fetch code entities from the symbol index."""
        # Implementation details...
        
    def _fetch_from_vectors(self, query: str, k: int, **filters) -> List[Entity]:
        """Fetch entities using vector similarity."""
        # Implementation details...
        
    def _deduplicate_and_score(self, results: List[Entity], query: str) -> List[Entity]:
        """Deduplicate results and score them by relevance."""
        # Implementation details...
```

### Phase 4: Committer System (Week 4-5)

#### A. Committer Module (`agent/committer.py`)

```python
import re, json
from typing import Dict, Any, List
from cogitarelink.core.entity import Entity
from cogitarelink.core.graph import GraphManager
from cogitarelink.reason.prov import wrap_patch_with_prov

class Committer:
    """Parse structured content from LLM output and commit to graph."""
    
    PATCH_RE = re.compile(r"```patch\n(.*?)```", re.S)
    JSONLD_RE = re.compile(r"```jsonld\n(.*?)```", re.S)
    
    def __init__(self, graph: GraphManager):
        self.graph = graph
    
    def ingest(self, llm_output: str):
        """
        Detect and process structured content in LLM output.
        
        Parameters
        ----------
        llm_output : The text output from the LLM
        """
        # Process JSON-LD blocks
        for block in self.JSONLD_RE.findall(llm_output):
            self._store_jsonld(block)
        
        # Process patch blocks (for code modifications)
        for block in self.PATCH_RE.findall(llm_output):
            self._apply_patch(block)
            
        return {
            "jsonld_blocks": len(self.JSONLD_RE.findall(llm_output)),
            "patch_blocks": len(self.PATCH_RE.findall(llm_output))
        }
    
    def _store_jsonld(self, text: str):
        """Store JSON-LD in the graph with provenance."""
        try:
            data = json.loads(text)
            ent = Entity(vocab=["schema"], content=data)
            
            with wrap_patch_with_prov(self.graph,
                                     source="llm://assistant",
                                     agent="https://example.org/agents/LLM"):
                self.graph.ingest_jsonld(ent.as_json, graph_id=ent.id)
        except Exception as e:
            # Handle validation errors or malformed JSON
            pass
    
    def _apply_patch(self, patch: str):
        """Apply code patch."""
        # Implementation details...
```

### Phase 5: Integration and Utilities (Week 5-6)

#### A. Integration Module (`agent/__init__.py`)

```python
"""
Cogitarelink Agent Package

Provides semantic paging capabilities for efficiently moving 
knowledge between durable storage and LLM context windows.
"""

from .context_window import ContextWindow
from .materialiser import Materialiser
from .retrieval import Retriever
from .committer import Committer

__all__ = ['ContextWindow', 'Materialiser', 'Retriever', 'Committer']
```

#### B. Token Utility Module (`agent/token.py`)

```python
"""Token handling utilities."""

class Tokeniser:
    """Base class for token counting."""
    
    def count(self, text: str) -> int:
        """Count tokens in text."""
        # Default implementation
        return len(text.split())

class TiktokenTokeniser(Tokeniser):
    """Tiktoken-based tokeniser for accurate counts."""
    
    def __init__(self, model: str = "gpt-4o"):
        import tiktoken
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count(self, text: str) -> int:
        return len(self.encoding.encode(text))

class AnthropicTokeniser(Tokeniser):
    """Anthropic tokeniser for Claude models."""
    
    def __init__(self):
        try:
            from anthropic import Anthropic
            self.anthropic = Anthropic()
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
    
    def count(self, text: str) -> int:
        return self.anthropic.count_tokens(text)
```

## 3. Integration with Existing Cogitarelink Architecture

### A. Extending the Core Components

1. **Composer Class** (`vocab/composer.py`)
   - Add a `materialise` method that delegates to the new Materialiser
   - Maintain backward compatibility with existing API

2. **GraphManager Class** (`core/graph.py`)
   - Add methods to support the Retriever's query patterns
   - Implement efficient subgraph extraction for token-aware retrieval

3. **Entity Class** (`core/entity.py`)
   - Add system metadata support for token weights and eviction priorities
   - Enhance JSON-LD 1.1 feature support (especially @nest)

### B. CLI Integration

Add new CLI commands for the semantic paging subsystem:

```
cogita agent init                    # Initialize agent components
cogita agent query "search terms"    # Retrieve and materialize entities
cogita agent context add <entity-id> # Add entity to current context window
cogita agent context show            # Display current context window content
cogita agent commit <file>           # Process LLM output and commit changes
```

## 4. Implementation Sequence

### Phase 1: Core Framework (Weeks 1-2)
- Implement Materialiser with token-efficient JSON-LD serialization
- Create ContextWindow for basic window management
- Add weight calculation and packing algorithms
- Implement basic format conversion utilities (JSON-LD ↔ N-Quads)

### Phase 2: Retrieval System (Weeks 2-3)
- Implement graph-based retrieval methods
- Add code symbol lookup (optional)
- Integrate vector similarity search (optional)
- Implement query routing and result ranking

### Phase 3: Committer System (Weeks 3-4)
- Implement JSON-LD block detection and parsing
- Add code patch handling
- Integrate with provenance tracking
- Add validation and error handling

### Phase 4: Advanced Features (Weeks 4-5)
- Implement type-aware context optimization
- Add @nest and other JSON-LD 1.1 features
- Implement efficient context sharing
- Add priority-based eviction policies

### Phase 5: Integration & Testing (Weeks 5-6)
- Create LLM-specific adapters
- Implement CLI commands
- Add comprehensive tests
- Create example workflows and documentation

## 5. API Design and Interfaces

### A. Core Protocols/Interfaces

```python
# agent/interfaces.py
from typing import Protocol, Iterable, Mapping, Any

class Message(Mapping[str, Any]): 
    """Message interface for LLM interactions."""
    pass

class LLM(Protocol):
    """Interface for LLM adapters."""
    def generate(self,
                 messages: list[Message],
                 tools: Mapping[str, "Tool"] | None = None,
                 **kwargs) -> Message: 
        """Generate LLM response."""
        pass

class Tool(Protocol):
    """Interface for LLM tools."""
    name: str
    description: str
    parameters_schema: Mapping[str, Any]

    def __call__(self, **arguments) -> str: 
        """Execute the tool."""
        pass

class Retriever(Protocol):
    """Interface for entity retrieval systems."""
    def fetch(self, query: str, k: int = 10, **kw) -> Iterable[Any]: 
        """Fetch relevant entities."""
        pass

class Materialiser(Protocol):
    """Interface for entity serialization."""
    def serialise(self, objects: Iterable[Any], style: str | None = None) -> str: 
        """Serialize entities for LLM consumption."""
        pass

class Committer(Protocol):
    """Interface for processing LLM output."""
    def ingest(self, llm_output: str, **context) -> None: 
        """Process structured content in LLM output."""
        pass

class Tokeniser(Protocol):
    """Interface for token counting."""
    def count(self, text: str) -> int: 
        """Count tokens in text."""
        pass
```

### B. Example Usage Flow

```python
# Example of the complete semantic paging system in action
from cogitarelink.agent.context_window import ContextWindow
from cogitarelink.agent.materialiser import Materialiser
from cogitarelink.agent.retrieval import Retriever
from cogitarelink.agent.committer import Committer
from cogitarelink.agent.token import TiktokenTokeniser

# Initialize components
tokeniser = TiktokenTokeniser(model="gpt-4o")
context = ContextWindow(max_tokens=12_000, tokeniser=tokeniser)
retriever = Retriever(graph=my_graph)
materialiser = Materialiser(token_budget=4_000)
committer = Committer(graph=my_graph)

# Process user query
def process_query(user_query: str) -> str:
    # 1. Retrieve relevant entities
    entities = retriever.fetch(user_query, k=8)
    
    # 2. Serialize entities with token awareness
    serialized = materialiser.serialise(
        entities, 
        style="jsonld", 
        max_bytes=20_000, 
        compaction="smallest-context"
    )
    
    # 3. Add to context window
    context.add(serialized, metadata={"source": "retrieval", "priority": 1})
    
    # 4. Generate LLM prompt
    prompt = context.render() + f"\n\nUser: {user_query}"
    
    # 5. Call LLM (implementation depends on specific adapter)
    llm_response = call_llm(prompt)
    
    # 6. Process and commit structured content
    committer.ingest(llm_response)
    
    return llm_response
```

## 6. Compatibility and Extension Points

### A. LLM Framework Adapters

The architecture supports multiple LLM frameworks through adapter modules:

```
cogitarelink/agent/adapters/
  openai_llm.py        # OpenAI Chat API adapter
  anthropic_llm.py     # Anthropic Claude adapter
  langchain_llm.py     # LangChain framework adapter
```

### B. Plugin System

Following the composer.md proposal, implement a lightweight plugin system:

```python
# Entry point example
from importlib.metadata import entry_points

def get_plugins(group_name):
    """Load plugins for the specified group."""
    return {ep.name: ep.load() for ep in entry_points(group=f"cogitarelink.{group_name}")}

# Usage
tokenisers = get_plugins("tokenisers")
selected_tokeniser = tokenisers.get("anthropic", tokenisers.get("tiktoken", DefaultTokeniser))
```

### C. Optional Dependencies

Structure the package to handle optional dependencies cleanly:

```python
# In setup.py
extras_require = {
    "openai": ["openai>=1.16.0", "tiktoken"],
    "anthropic": ["anthropic"],
    "vector": ["faiss-cpu", "sentence-transformers"],
    "code": ["tree_sitter_languages", "py-tree-sitter"],
    "langchain": ["langchain"],
}
```

## 7. Testing Strategy

### A. Unit Tests

- Test each component in isolation with mock dependencies
- Verify token calculation accuracy against expected values
- Confirm packing algorithms respect budgets
- Validate serialization formats are correct

### B. Integration Tests

- Test the complete retrieval → materialization → context → commit flow
- Verify system works with different LLM adapters
- Confirm token budgets are respected end-to-end

### C. Benchmark Tests

- Measure serialization speed for different entity sizes
- Compare token estimation accuracy to actual tokenizers
- Evaluate retrieval relevance on standard queries

## 8. Documentation and Examples

### A. Developer Documentation

- Architecture overview with component diagrams
- API reference for each class and method
- Integration examples with different LLM frameworks

### B. Example Workflows

- Minimal agent loop example
- Semantic search and materialization
- Context window management strategies
- Advanced JSON-LD feature usage

## Conclusion

This implementation plan integrates the token-efficient JSON-LD filtering approach into the broader semantic paging architecture outlined in composer.md. The phased approach allows for incremental development while ensuring all components work together cohesively.

The architecture maintains the micro-kernel philosophy of Cogitarelink while adding powerful capabilities for moving knowledge efficiently between durable storage and LLM context windows, supporting both current LLM function-calling patterns and future paradigms.