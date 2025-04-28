# CogitareLink Architecture

This document provides an overview of the CogitareLink architecture, explaining the components and their interactions.

## Core Principles

CogitareLink is built around these principles:

1. **Vocabulary-First Approach**: JSON-LD vocabularies drive the system
2. **Immutability**: Entities are immutable to ensure data integrity
3. **Graph-Based Storage**: Knowledge is stored as RDF triples/quads
4. **Framework Independence**: Core functionality is independent of LLM frameworks
5. **Standard Formats**: JSON-LD and RDF as primary interchange formats

## Component Architecture

![Architecture Diagram](architecture.png)

### Core Layer

The foundation of CogitareLink providing data structures and operations.

#### Entity (`core/entity.py`)

Represents an immutable JSON-LD resource with:
- Vocabulary-aware context
- Normalized representation
- Child entity tracking
- Content integrity (SHA-256 hashing)

```python
entity = Entity(
    vocab=["schema"],
    content={"name": "John Doe", "@type": "Person"}
)
```

#### Graph (`core/graph.py`)

Stores and queries RDF triples/quads with:
- Multiple backend options (in-memory or RDFLib)
- Parent-child relationship tracking
- Named graph management
- Efficient querying

```python
graph = GraphManager()
graph.ingest_nquads(entity.normalized)
```

#### Processor (`core/processor.py`)

Manages entity processing with:
- Entity creation and storage
- Relationship tracking
- Entity retrieval by ID/type
- Special handling for specific vocabularies

```python
processor = EntityProcessor(ctx_proc, graph)
entity = processor.add(data, vocab=["schema"])
```

#### Context (`core/context.py`)

Handles JSON-LD context operations:
- Expansion, compaction, normalization
- Registry-aware document loading
- Scoped context handling
- Protected term validation

```python
ctx_proc = ContextProcessor()
expanded = ctx_proc.expand(data)
```

#### Cache (`core/cache.py`)

Provides caching capabilities:
- Memory and disk backends
- Namespace-scoped caching
- TTL support
- Memoization helper

```python
cache = InMemoryCache(maxsize=256)
@cache.memoize("http")
def fetch(url): ...
```

### Vocabulary Layer

Manages the vocabularies that define the semantics of the data.

#### Registry (`vocab/registry.py`)

Provides vocabulary information:
- Prefix and URI mapping
- Context payload access
- Version management
- Feature detection

```python
entry = registry["schema"]
context = entry.context_payload()
```

#### Collision (`vocab/collision.py`)

Handles vocabulary combinations:
- Strategy determination
- Protected term detection
- Safety checks
- Collision resolution

```python
resolver = Resolver()
plan = resolver.decide(["vc", "schema"])
```

#### Composer (`vocab/composer.py`)

Creates combined contexts:
- Multi-vocabulary composition
- Collision strategy implementation
- JSON-LD 1.1 features (scoping, protection)
- Context validation

```python
composed = composer.compose(["schema", "dc"])
```

### Verification Layer

Provides security and validation for entities.

#### Signer (`verify/signer.py`)

Handles cryptographic operations:
- Ed25519 key generation
- Normalized document signing
- Signature verification

```python
signature = sign(entity.normalized, private_key)
valid = verify(entity.normalized, signature, public_key)
```

#### Validator (`verify/validator.py`)

Performs constraint validation:
- SHACL shapes application
- Validation reporting
- Entity conformance checking

```python
valid = validate_entity(entity, shapes_graph)
```

### Integration Layer

Provides adapters to different frameworks.

#### Retriever (refactored from old retriever.py)

Framework-agnostic linked data retrieval:
- URI analysis
- Access strategy determination
- Format conversion
- Entity extraction

```python
retriever = LODRetriever()
result = retriever.retrieve(uri)
```

## Data Flow

1. **Creation**: Entities are created with vocabulary context
2. **Processing**: Entities are processed and stored in the graph
3. **Querying**: Graph is queried to retrieve related entities
4. **Verification**: Entities can be signed and validated
5. **Retrieval**: External data can be retrieved and converted to entities

## Usage Patterns

### Basic Entity Creation and Storage

```python
from cogitarelink.core.context import ContextProcessor
from cogitarelink.core.processor import EntityProcessor
from cogitarelink.core.graph import GraphManager

# Setup
ctx_proc = ContextProcessor()
graph = GraphManager()
processor = EntityProcessor(ctx_proc, graph)

# Create entity
entity = processor.add({
    "@type": "Person",
    "name": "John Doe"
}, vocab=["schema"])

# Retrieve entity
result = processor.get_by_id(entity.id)
```

### Working with Verified Credentials

```python
# Create a verifiable credential
vc = processor.add({
    "@type": "VerifiableCredential",
    "issuer": {"@id": "https://example.org/issuer"},
    "credentialSubject": {
        "@type": "Person",
        "name": "Jane Doe"
    }
}, vocab=["vc", "schema"])

# Sign the credential
from cogitarelink.verify.signer import sign
signature = sign(vc.normalized, private_key)

# Add proof to credential
signed_vc = processor.add({
    **vc.content,
    "proof": {
        "type": "Ed25519Signature2020",
        "created": "2023-06-18T21:19:10Z",
        "verificationMethod": "https://example.org/keys/1",
        "proofValue": signature
    }
}, vocab=["vc", "schema"])
```

### Retrieving Linked Data

```python
from cogitarelink.integration.retriever import LODRetriever

# Create retriever
retriever = LODRetriever()

# Retrieve data
result = retriever.retrieve("http://www.wikidata.org/entity/Q42")

# Convert to entity
entity = processor.add(result["data"], vocab=["schema"])
```

## Extension Points

CogitareLink provides several extension points:

1. **Custom Vocabularies**: Add new vocabulary entries to the registry
2. **New Graph Backends**: Implement the GraphBackend protocol
3. **Custom Cache Backends**: Extend the BaseCache class
4. **Integration Adapters**: Create new framework-specific modules

## Best Practices

1. Always use vocabulary-aware context creation
2. Maintain immutability of entities
3. Use the entity processor for all entity management
4. Prefer standard vocabularies when possible
5. Create framework-specific integrations outside the core library