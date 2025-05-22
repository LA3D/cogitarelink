# JSON-LD Token-Efficient Filtering Implementation Plan

This document outlines the implementation plan for adding token-efficient JSON-LD filtering to Cogitarelink, based on the concepts explored in `composer-json-filter.md` and the experimental validations.

## Overview

Cogitarelink needs to efficiently pack JSON-LD entities into LLM context windows while preserving semantic richness. This requires token-aware filtering, byte-based weight estimation, and advanced JSON-LD 1.1 features.

## Goals

1. Implement byte-weighted entity selection for context windows
2. Support JSON-LD 1.1 advanced features for efficient packing
3. Add format flexibility between JSON-LD and N-Quads
4. Maintain semantic fidelity while optimizing token usage
5. Integrate seamlessly with existing Cogitarelink architecture

## 1. Core Components to Modify

### A. Composer Class (`vocab/composer.py`)

**Current State**: Handles merging multiple vocabularies with collision resolution.

**Changes Needed**:
- Add a new `materialize()` method for token-aware context generation
- Extend `compose()` to support token budget constraints
- Implement selective context optimization based on used types
- Add @nest handling for system metadata
- Support context sharing for multi-entity documents

```python
# Method signature to add
def materialize(
    self, 
    entities: List[Dict], 
    max_bytes: int = 20_000,
    max_chunks: int = 30,
    compaction: str = "smallest-context",
    format: str = "jsonld"
) -> str:
    """Generate LLM-ready content from JSON-LD entities."""
    # Implementation details...
```

### B. ContextProcessor Class (`core/context.py`)

**Current State**: Handles expansion, compaction, and normalization of JSON-LD.

**Changes Needed**:
- Add byte-weight calculation methods
- Implement @nest property handling
- Add format conversion utilities with size constraints
- Support line budgeting for N-Quads
- Add selective context pruning

```python
# Methods to add
def weight(self, obj: Dict) -> int:
    """Calculate byte-weight of object."""
    
def to_nquads(self, obj: Dict, max_lines: int = 800) -> str:
    """Convert to N-Quads with line budget."""
    
def strip_metadata(self, obj: Dict) -> Dict:
    """Remove @nest system metadata."""
```

### C. Entity Class (`core/entity.py`)

**Current State**: Immutable wrapper around JSON-LD dict with context.

**Changes Needed**:
- Add system metadata support
- Implement explicit weight and priority attributes
- Add methods to strip system metadata
- Enhance metadata handling with @nest support

```python
# Properties and methods to add
@property
def weight(self) -> int:
    """Get entity weight (for token estimation)."""
    
@property
def priority(self) -> int:
    """Get eviction priority (lower = keep longer)."""
    
def without_metadata(self) -> Dict:
    """Return entity without system metadata."""
```

### D. GraphManager Class (`core/graph.py`)

**Current State**: Manages triple storage with flexible backends.

**Changes Needed**:
- Add methods to query entities with filtering and weighting
- Support materialization process for context windows
- Add format flexibility (JSON-LD vs N-Quads)
- Implement efficient sub-graph extraction

```python
# Methods to add
def materialize_subgraph(
    self, 
    query,
    format: str = "jsonld", 
    max_bytes: int = 20_000
) -> str:
    """Extract and materialize a subgraph for LLM consumption."""
```

## 2. New Components to Create

### A. TokenManager Module (`core/token.py`)

**Purpose**: Handle token-related calculations and packing algorithms.

**Key Functions**:
- Weight calculation for JSON-LD entities
- Greedy packing algorithm implementation
- Token estimation utilities
- Hard limit safety checks

```python
def weight(obj: Dict, hard_cap: int = 4096) -> int:
    """Calculate byte-weight proxy for token count."""
    
def pack_entities(
    entities: List[Dict], 
    budget: int, 
    priority_fn = None
) -> Tuple[List[Dict], int]:
    """Pack entities into budget using priority function."""

def estimate_tokens(text: str) -> int:
    """Optional safety check with actual tokenizer."""
```

### B. LLMContext Class (`llm/context.py`)

**Purpose**: Manage LLM context windows and track token usage.

**Key Functions**:
- Context window management
- Token tracking
- Multi-turn conversation support
- Entity prioritization

```python
class LLMContext:
    """Manages entities in an LLM context window."""
    
    def __init__(self, max_bytes: int = 20_000):
        """Initialize with byte budget."""
        
    def add(self, entity: Entity, priority: int = None) -> bool:
        """Add entity if budget allows, return success."""
        
    def materialize(self) -> str:
        """Generate context window content."""
        
    def estimate_remaining(self) -> int:
        """Estimate remaining capacity."""
```

### C. JSONFilter Module (`utils/json_filter.py`)

**Purpose**: Implement lightweight JSON-LD filtering.

**Key Functions**:
- Property path selection
- JSONPath or jq-style query support
- Flexible filtering functions

```python
def filter_by_path(obj: Dict, path: str) -> Any:
    """Extract data using JSONPath-like syntax."""
    
def filter_by_type(obj: Dict, type_name: str) -> Dict:
    """Filter based on @type."""
    
def filter_nested(obj: Dict, include_system: bool = False) -> Dict:
    """Filter handling @nest properties."""
```

## 3. Configuration Options to Add

### A. Context Configuration

Add settings for token-efficient context handling:

```python
TOKEN_CONFIG = {
    "max_bytes": 20_000,          # Soft budget
    "max_tokens": 8_000,          # Hard budget
    "format": "jsonld",           # or "nquads" 
    "packing": "weight_based",    # or "priority_based"
    "context_strategy": "minimal" # or "full", "reference"
}
```

### B. System Metadata Namespace

Define standardized system metadata properties using @nest:

```python
SYSTEM_METADATA = {
    "namespace": "sys",
    "properties": {
        "weight": "heuristicWeight",
        "priority": "evictAfter",
        "created": "createdAt",
        "modified": "modifiedAt"
    }
}
```

## 4. Integration Points

### A. CLI Extensions

Add commands to the CLI module for token-efficient exports:

```bash
# Example CLI commands to implement
cogita export --format=jsonld --max-bytes=20000 <entity-id>
cogita pack --budget=8000 --query="type:Product" --format=nquads
```

### B. LLM Integration

Helper functions for LLM prompt construction:

```python
def build_prompt(
    system_prompt: str,
    entities: List[Entity],
    question: str,
    max_bytes: int = 20_000
) -> str:
    """Build LLM prompt with optimal entity packing."""
```

## 5. Testing and Validation

### A. Weight Calculation Tests

Verify that byte-weight calculations accurately estimate token usage:

```python
def test_weight_calculation():
    """Test that byte weights correlate with token counts."""
    # Implement test cases
```

### B. Packing Algorithm Tests

Ensure greedy packing functions work correctly:

```python
def test_greedy_packing():
    """Test packing algorithm respects budget."""
    # Implement test cases
```

### C. Advanced Feature Tests

Validate JSON-LD 1.1 feature handling:

```python
def test_nest_handling():
    """Test @nest property handling."""
    # Implement test cases
```

## Implementation Phases

### Phase 1: Core Weight Functions (Week 1)

1. Implement `weight()` function in new `token.py` module
2. Add system metadata support to Entity class
3. Create basic greedy packing algorithm
4. Add tests for weight calculation
5. Implement byte budget tracking

### Phase 2: Filtering & Materialization (Week 2)

1. Implement `JSONFilter` utilities
2. Add property filtering to ContextProcessor
3. Create new `materialize()` method in Composer
4. Add type-aware context optimization
5. Implement entity retrieval filtering in GraphManager

### Phase 3: Advanced Features (Week 3)

1. Add support for @nest and @protected handling
2. Implement N-Quads serialization with line budgets
3. Add format conversion utilities
4. Create advanced token packing strategies
5. Optimize context sharing for multiple entities

### Phase 4: LLM Integration (Week 4)

1. Create LLMContext class for context window management
2. Add CLI commands for token-efficient exports
3. Implement prompt construction helpers
4. Add multi-turn conversation support
5. Complete documentation and examples

## Compatibility Considerations

- Maintain backward compatibility with existing Cogitarelink APIs
- Add new functionality through extension methods rather than changing core behavior
- Ensure new components work with both JSON-LD and N-Quads formats
- Support optional token counting when needed for safety

## Acceptance Criteria

1. Token estimation accuracy within 10% of actual tokenizer results
2. Packing efficiency improved by at least 20% compared to naive approach
3. N-Quads conversion preserves all semantically relevant triples
4. Type-scoped contexts correctly optimize for used types only
5. System metadata is properly handled with @nest and can be selectively removed
6. All existing tests continue to pass after implementation
7. Clear documentation with examples of token-efficient pattern usage

## Conclusion

This implementation plan provides a roadmap for adding token-efficient JSON-LD filtering to Cogitarelink while preserving its core semantic capabilities. The phased approach allows for incremental testing and validation while maintaining compatibility with existing code.