# Context-Materialization Layer Implementation Plan

This document outlines the implementation approach for adding a "semantic paging" system to Cogitarelink, based on the architecture proposed in `plans/composer.md`. The implementation will enhance Cogitarelink's existing components with token-aware context management and optimized serialization for LLM interactions.

## 1. Overview

The Context-Materialization layer will add four key components:

1. **Retriever**: Find relevant entities using multiple search strategies
2. **Materialiser**: Convert entities to token-efficient text
3. **ContextWindow**: Manage token usage and evict content when necessary
4. **Committer**: Process LLM-generated structured content

These components will integrate with existing Cogitarelink systems (GraphManager, ContextProcessor, vocab tools) to create a cohesive "semantic paging" solution.

## 2. Implementation Phases

### Phase 1: Core Interfaces and Foundation

1. **Define Protocol Interfaces**
   - Create `agent/interfaces.py` with Protocols for all core components
   - Implement tokenizer interface with adapters for tiktoken and Anthropic

2. **Implement ContextWindow**
   - Create `agent/context.py` with basic token-aware context management
   - Implement FIFO eviction with extension points for smarter strategies
   - Add fragment categorization (code vs. semantic data vs. instructions)

3. **Setup Project Structure**
   - Create `agent/` directory with proper imports
   - Set up optional dependencies in pyproject.toml
   - Configure entry points for plugins

### Phase 2: Retrieval and Materialization

1. **Implement Basic Retriever**
   - Create `agent/retrieval/graph.py` using GraphManager.query
   - Add filesystem-based symbol search for code entities
   - Add optional vector search with sentence-transformers

2. **Implement Materialiser**
   - Create `agent/materialiser.py` with token-aware serialization
   - Add format-specific renderers (code, JSON-LD, text)
   - Integrate with composer.compose for optimized contexts

3. **Add Combined Retrieval**
   - Create retrieval scorer that combines results from multiple sources
   - Implement relevance ranking based on combined scores
   - Add pagination for large result sets

### Phase 3: Knowledge Navigation and Interaction

1. **Implement Knowledge Index**
   - Create tools to generate knowledge overviews for LLMs
   - Build schema summaries for available vocabularies
   - Implement query translation between natural language and retrieval operations

2. **Add LLM Navigation Helpers**
   - Create prompt templates for knowledge exploration
   - Add guided knowledge addition capabilities
   - Implement bidirectional knowledge flow patterns

3. **Build Automatic Schema Tools**
   - Create entity type schema extractors
   - Implement property suggestion system
   - Add validation guidance for entity creation

### Phase 4: Committer and Integration

1. **Implement Committer**
   - Create `agent/commit/jsonld.py` for handling JSON-LD outputs
   - Create `agent/commit/patch.py` for code changes
   - Add SHACL validation integration for entity validation

2. **Create Framework Adapters**
   - Add `agent/adapters/openai_llm.py` for OpenAI integration
   - Add `agent/adapters/anthropic_llm.py` for Claude integration
   - Create default prompting templates for semantic workflows

3. **Build CLI Integration**
   - Extend AgentCLI to use new components
   - Add commands for working with semantic paging
   - Add visualization of context window state

## 3. Cache Integration

To ensure efficient operation, the Context-Materialization layer needs to be tightly integrated with Cogitarelink's caching systems.

### 3.1 Multi-level Caching Strategy

```python
# agent/cache_integration.py

from cogitarelink.core.cache import InMemoryCache, DiskCache
from typing import Dict, Any, Optional, Union, List

# Cache for materialized content
_material_cache = InMemoryCache(maxsize=128)

# Cache for retrieval results
_query_cache = InMemoryCache(maxsize=64)

# Entity-to-query mapping for cache invalidation
_entity_query_map: Dict[str, List[str]] = {}

class CacheCoordinator:
    """Coordinate caches across the semantic paging system."""
    
    def __init__(self, use_disk_cache: bool = False):
        self.use_disk_cache = use_disk_cache
        if use_disk_cache:
            from pathlib import Path
            cache_dir = Path.home() / ".cogitarelink" / "semantic_cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.disk_cache = DiskCache(str(cache_dir))
        
    def cache_materialization(self, entity_id: str, style: str, token_budget: int, 
                              content: str) -> None:
        """Cache a materialized representation of an entity."""
        key = f"material:{entity_id}:{style}:{token_budget}"
        _material_cache.set(key, content)
        
        # Also store in disk cache if enabled
        if self.use_disk_cache:
            self.disk_cache.set(key, content)
    
    def get_materialization(self, entity_id: str, style: str, token_budget: int) -> Optional[str]:
        """Get a cached materialized representation."""
        key = f"material:{entity_id}:{style}:{token_budget}"
        
        # Try memory cache first
        result = _material_cache.get(key)
        if result is not None:
            return result
            
        # Try disk cache if enabled
        if self.use_disk_cache:
            return self.disk_cache.get(key)
            
        return None
        
    def cache_query_result(self, query_hash: str, entity_ids: List[str], ttl: int = 300) -> None:
        """Cache query results with entity tracking for invalidation."""
        _query_cache.set(f"query:{query_hash}", entity_ids, ttl=ttl)
        
        # Track which queries reference which entities
        for entity_id in entity_ids:
            if entity_id not in _entity_query_map:
                _entity_query_map[entity_id] = []
            _entity_query_map[entity_id].append(query_hash)
    
    def get_query_result(self, query_hash: str) -> Optional[List[str]]:
        """Get cached query results."""
        return _query_cache.get(f"query:{query_hash}")
        
    def invalidate_entity(self, entity_id: str) -> None:
        """Invalidate all caches related to an entity."""
        # Invalidate materializations
        for style in ["json-ld", "code", "text"]:
            for budget in [1000, 2000, 4000, 8000]:  # Common token budgets
                key = f"material:{entity_id}:{style}:{budget}"
                _material_cache.invalidate(key)
                if self.use_disk_cache:
                    self.disk_cache.invalidate(key)
        
        # Invalidate queries that reference this entity
        for query_hash in _entity_query_map.get(entity_id, []):
            _query_cache.invalidate(f"query:{query_hash}")
            
        # Clean up the entity-query map
        if entity_id in _entity_query_map:
            del _entity_query_map[entity_id]
    
    def warm_cache_for_entities(self, entity_ids: List[str], 
                                materialiser, styles: List[str] = None,
                                token_budgets: List[int] = None) -> None:
        """Pre-compute materializations for frequent entities."""
        styles = styles or ["json-ld", "code", "text"]
        token_budgets = token_budgets or [2000]
        
        for entity_id in entity_ids:
            for style in styles:
                for budget in token_budgets:
                    # Skip if already cached
                    if self.get_materialization(entity_id, style, budget) is not None:
                        continue
                    
                    # Materialize and cache
                    try:
                        from cogitarelink.core.entity import Entity
                        # This would need proper entity retrieval logic
                        entity = Entity(id=entity_id, vocab=["schema"], content={})  
                        content = materialiser._serialize_entity(entity, style, budget)
                        self.cache_materialization(entity_id, style, budget, content)
                    except Exception:
                        # Skip on any error
                        continue
```

### 3.2 Integration with GraphManager and Materialiser

```python
# Update Materialiser class to use caching

def _serialize_jsonld(self, objects: List[Any]) -> str:
    """Serialize entities as compact JSON-LD with caching."""
    from cogitarelink.core.entity import Entity
    import json
    
    # Filter for Entity objects
    entities = [obj for obj in objects if isinstance(obj, Entity)]
    
    if not entities:
        return ""
        
    # Check cache for single entity case
    if len(entities) == 1 and entities[0].id:
        cached = self.cache_coordinator.get_materialization(
            entities[0].id, "json-ld", self.token_budget
        )
        if cached:
            return cached
    
    # Proceed with normal serialization
    # ... [existing serialization code] ...
    
    # Cache the result for single entity
    if len(entities) == 1 and entities[0].id:
        self.cache_coordinator.cache_materialization(
            entities[0].id, "json-ld", self.token_budget, result
        )
    
    return result
```

### 3.3 Committer Cache Management

```python
# Update Committer to invalidate caches

def _process_jsonld(self, content: str, block_index: int, **context) -> Dict[str, Any]:
    """Process JSON-LD with cache invalidation."""
    # ... [existing processing code] ...
    
    # After successful entity ingestion
    if entity_id:
        # Invalidate all caches related to this entity
        from agent.cache_integration import CacheCoordinator
        cache_coordinator = CacheCoordinator()
        cache_coordinator.invalidate_entity(entity_id)
        
        # Also invalidate any related entities
        # For example, if this entity references others
        related_entities = self._extract_referenced_entities(entity)
        for related_id in related_entities:
            cache_coordinator.invalidate_entity(related_id)
    
    return result
```

## 4. Knowledge Navigation for LLMs

A critical aspect of the system is enabling LLMs to effectively navigate the knowledge graph and understand the JSON-LD structure.

### 4.1 Knowledge Index Generation

```python
# agent/knowledge_navigation.py

from typing import Dict, List, Any, Optional
from cogitarelink.core.graph import GraphManager

class KnowledgeNavigator:
    """Tools for LLMs to navigate and interact with the knowledge graph."""
    
    def __init__(self, graph: GraphManager):
        self.graph = graph
        
    def generate_knowledge_index(self) -> str:
        """Create a navigable index of knowledge in the graph."""
        # Count entities by type
        type_counts = {}
        for s, p, o in self.graph.query(
            None, 
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", 
            None
        ):
            type_name = o.split("/")[-1] if "/" in o else o
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
        # Get sample entities for each type
        samples = {}
        for type_name in type_counts:
            entities = []
            # Find entities of this type
            for s, _, _ in self.graph.query(
                None, 
                "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", 
                type_name
            ):
                entities.append(s)
                if len(entities) >= 3:  # Limit to 3 examples
                    break
                    
            samples[type_name] = entities
            
        # Format as a markdown index
        index = "# Knowledge Graph Index\n\n"
        index += "## Available Entity Types\n\n"
        
        for type_name, count in type_counts.items():
            index += f"- **{type_name}**: {count} entities\n"
            index += "  - Example IDs:\n"
            for entity_id in samples.get(type_name, []):
                index += f"    - `{entity_id}`\n"
                
        index += "\n## Query Examples\n\n"
        index += "To retrieve information about specific entities, you can ask:\n"
        index += "- \"Tell me about entity X\"\n"
        index += "- \"What properties does entity Y have?\"\n"
        index += "- \"Find all entities of type Z\"\n"
        
        return index
        
    def generate_schema_summary(self) -> str:
        """Create a summary of the schema structure."""
        # Extract schema information from vocabulary
        from cogitarelink.vocab.registry import registry
        
        schema = "# Knowledge Schema\n\n"
        
        for prefix, entry in registry._v.items():
            schema += f"## {prefix}\n\n"
            schema += f"Base URI: {entry.uris.get('primary')}\n\n"
            
            # If context is available, extract key terms
            if hasattr(entry.context, 'inline') and entry.context.inline:
                schema += "### Key Terms\n\n"
                for term, definition in entry.context.inline.get("@context", {}).items():
                    if not term.startswith("@"):
                        schema += f"- **{term}**: "
                        if isinstance(definition, str):
                            schema += f"`{definition}`\n"
                        else:
                            schema += f"Complex term\n"
                            
        return schema
    
    def interpret_knowledge_query(self, query: str) -> Dict[str, Any]:
        """Convert natural language query to retrieval operations."""
        # Pattern matching for common query types
        import re
        
        # Entity lookup pattern
        entity_match = re.search(r"(?:about|details for|information on)\s+(?:entity\s+)?[`']?([^'`\s]+)[`']?", query, re.I)
        if entity_match:
            entity_id = entity_match.group(1)
            return {"operation": "entity_lookup", "entity_id": entity_id}
            
        # Type query pattern
        type_match = re.search(r"(?:all|find|list)\s+(?:entities of type|instances of)\s+([A-Za-z]+)", query, re.I)
        if type_match:
            type_name = type_match.group(1)
            return {"operation": "type_query", "type": type_name}
        
        # Property pattern
        property_match = re.search(r"(?:what|list|show)\s+(?:are the |the )?properties (?:of|for)\s+([A-Za-z0-9]+)", query, re.I)
        if property_match:
            entity_id = property_match.group(1)
            return {"operation": "property_list", "entity_id": entity_id}
        
        # If no pattern matches, try semantic search
        return {"operation": "semantic_search", "query": query}
        
    def build_knowledge_navigation_prompt(self, query: str, materialiser) -> str:
        """Build a prompt to help LLM navigate knowledge."""
        prompt = "# Knowledge Navigation\n\n"
        prompt += "You have access to a knowledge graph with the following structure:\n\n"
        
        # Add summarized schema
        prompt += self.generate_schema_summary()
        
        prompt += "\n\n# Available Knowledge\n\n"
        # Add index of available knowledge
        prompt += self.generate_knowledge_index()
        
        prompt += "\n\n# Query Examples\n\n"
        prompt += "Example 1: 'Tell me about entity X'\n"
        prompt += "This retrieves details about a specific entity.\n\n"
        
        prompt += "Example 2: 'List all entities of type Person'\n"
        prompt += "This finds all entities of a specific type.\n\n"
        
        prompt += "Example 3: 'What properties does entity Y have?'\n"
        prompt += "This lists all properties of a specific entity.\n\n"
        
        prompt += f"\n\n# User Query\n\n{query}\n\n"
        
        # Interpret the query and add specific context
        interpretation = self.interpret_knowledge_query(query)
        
        if interpretation["operation"] == "entity_lookup":
            entity_id = interpretation["entity_id"]
            prompt += f"I'll look up entity with ID: {entity_id}\n\n"
            
            # Query for the entity
            entity_triples = self.graph.query(entity_id, None, None)
            if entity_triples:
                # Convert to entity and materialize
                entity = self._triples_to_entity(entity_id, entity_triples)
                if entity:
                    entity_text = materialiser.serialise([entity], style="json-ld")
                    prompt += "# Entity Details\n\n```json-ld\n"
                    prompt += entity_text
                    prompt += "\n```\n"
                else:
                    prompt += f"Entity found but couldn't be materialized: {entity_id}\n"
            else:
                prompt += f"No entity found with ID {entity_id}\n"
                
        elif interpretation["operation"] == "type_query":
            type_name = interpretation["type"]
            prompt += f"I'll find entities of type: {type_name}\n\n"
            
            # Construct type URI based on common patterns
            possible_type_uris = [
                f"http://schema.org/{type_name}",
                f"http://xmlns.com/foaf/0.1/{type_name}",
                type_name  # Raw type name as fallback
            ]
            
            # Try each possible URI
            entities_found = []
            for type_uri in possible_type_uris:
                for s, _, _ in self.graph.query(None, "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", type_uri):
                    entities_found.append(s)
                    
            if entities_found:
                prompt += f"# Entities of type {type_name}\n\n"
                for i, entity_id in enumerate(entities_found[:10]):  # Limit to 10
                    prompt += f"{i+1}. `{entity_id}`\n"
                    
                if len(entities_found) > 10:
                    prompt += f"\n... and {len(entities_found) - 10} more entities\n"
            else:
                prompt += f"No entities found of type {type_name}\n"
        
        # Similar implementations for other operations
                
        return prompt
        
    def _triples_to_entity(self, entity_id, triples):
        """Convert a set of triples to an Entity object."""
        from cogitarelink.core.entity import Entity
        
        # Extract properties
        properties = {}
        for _, p, o in triples:
            # Extract property name from URI
            prop_name = p.split('/')[-1] if '/' in p else p
            properties[prop_name] = o
            
        # Try to detect vocabulary
        vocab_prefixes = ["schema"]  # Default to schema.org
        
        # Look for type information that might indicate vocabulary
        type_value = properties.get('type') or properties.get('@type')
        if type_value and ':' in type_value:
            prefix = type_value.split(':')[0]
            if prefix:
                vocab_prefixes = [prefix] + vocab_prefixes
                
        # Create the entity
        try:
            return Entity(id=entity_id, vocab=vocab_prefixes, content=properties)
        except Exception:
            return None
```

### 4.2 Guided Knowledge Addition

```python
class KnowledgeContributor:
    """Tools for LLMs to add or modify information in the knowledge graph."""
    
    def __init__(self, graph: GraphManager):
        self.graph = graph
        
    def get_type_schema(self, entity_type: str) -> Dict[str, Any]:
        """Get a schema for a specific entity type."""
        # Try to find the schema from various sources
        
        # 1. Check if we have SHACL shapes for this type
        shapes = self._find_shacl_shapes(entity_type)
        if shapes:
            return self._shapes_to_schema(shapes, entity_type)
            
        # 2. Check vocabulary registry for type definition
        from cogitarelink.vocab.registry import registry
        for prefix, entry in registry._v.items():
            if hasattr(entry.context, 'inline') and entry.context.inline:
                ctx = entry.context.inline.get("@context", {})
                if entity_type in ctx:
                    # Found type definition
                    return self._vocab_to_schema(ctx, entity_type)
                    
        # 3. Fallback: Create a basic schema from existing entities
        existing_schema = self._infer_schema_from_instances(entity_type)
        if existing_schema:
            return existing_schema
            
        # 4. Ultimate fallback: Generic schema
        return {
            "@type": entity_type,
            "name": {"type": "string", "required": True},
            "description": {"type": "string"},
            "@id": {"type": "string", "format": "uri"}
        }
        
    def build_knowledge_addition_prompt(self, entity_type: str) -> str:
        """Build a prompt to guide knowledge addition."""
        prompt = f"# Adding New {entity_type} Information\n\n"
        
        # Get schema for this type
        type_schema = self.get_type_schema(entity_type)
        
        prompt += "Please format the new information according to this schema:\n\n"
        prompt += "```json\n"
        prompt += json.dumps(type_schema, indent=2)
        prompt += "\n```\n\n"
        
        prompt += "Required properties are marked with *. Please provide these minimum fields.\n\n"
        
        prompt += "Format your response as a JSON-LD block with the proper @context:\n\n"
        prompt += "```json-ld\n"
        prompt += "{\n"
        prompt += '  "@context": {\n'
        prompt += '    "@vocab": "http://schema.org/"\n'
        prompt += "  },\n"
        prompt += f'  "@type": "{entity_type}",\n'
        prompt += '  "name": "Example Name",\n'
        prompt += '  "description": "Example description"\n'
        prompt += "}\n"
        prompt += "```\n"
        
        return prompt
        
    def _find_shacl_shapes(self, entity_type: str) -> List[Dict[str, Any]]:
        """Find SHACL shapes for a given entity type."""
        # This would require SHACL integration
        # Placeholder implementation
        return []
        
    def _shapes_to_schema(self, shapes: List[Dict[str, Any]], entity_type: str) -> Dict[str, Any]:
        """Convert SHACL shapes to a schema."""
        # Placeholder implementation
        return {}
        
    def _vocab_to_schema(self, context: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """Create schema from vocabulary context."""
        # Placeholder implementation
        return {}
        
    def _infer_schema_from_instances(self, entity_type: str) -> Dict[str, Any]:
        """Infer schema by examining existing entities."""
        # Find instances of this type
        instances = []
        type_uris = [
            f"http://schema.org/{entity_type}",
            f"http://xmlns.com/foaf/0.1/{entity_type}",
            entity_type
        ]
        
        for type_uri in type_uris:
            for s, _, _ in self.graph.query(
                None, "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", type_uri
            ):
                # Get all properties for this entity
                entity_data = {}
                for _, p, o in self.graph.query(s, None, None):
                    prop = p.split('/')[-1] if '/' in p else p
                    entity_data[prop] = o
                
                if entity_data:
                    instances.append(entity_data)
                    
        if not instances:
            return {}
            
        # Analyze property frequencies
        properties = {}
        total = len(instances)
        
        for instance in instances:
            for prop, value in instance.items():
                if prop not in properties:
                    properties[prop] = {
                        "count": 0,
                        "types": set(),
                        "sample": None
                    }
                    
                properties[prop]["count"] += 1
                properties[prop]["types"].add(type(value).__name__)
                if properties[prop]["sample"] is None:
                    properties[prop]["sample"] = value
                    
        # Create schema
        schema = {"@type": entity_type}
        
        for prop, data in properties.items():
            # Skip RDF/special properties
            if prop.startswith('@') or prop in ['type', 'rdf:type']:
                continue
                
            # Determine if required (present in >75% of instances)
            required = (data["count"] / total) > 0.75
            
            # Determine type
            if "str" in data["types"] or "string" in data["types"]:
                prop_type = "string"
            elif "int" in data["types"]:
                prop_type = "integer"
            elif "float" in data["types"] or "double" in data["types"]:
                prop_type = "number"
            elif "bool" in data["types"]:
                prop_type = "boolean"
            elif "dict" in data["types"] or "Dict" in data["types"]:
                prop_type = "object"
            elif "list" in data["types"] or "List" in data["types"]:
                prop_type = "array"
            else:
                prop_type = "string"  # Default
                
            schema[prop] = {
                "type": prop_type,
                "required": required,
                "example": str(data["sample"])
            }
            
        return schema
```

## 5. Key Components Details

### 5.1 ContextWindow

```python
# agent/context.py

from typing import List, Dict, Any, Optional
from .interfaces import Tokeniser

class Fragment:
    """A fragment of content in the context window with metadata."""
    def __init__(self, text: str, token_count: int, 
                 category: str = "general", 
                 importance: float = 1.0,
                 source_id: Optional[str] = None):
        self.text = text
        self.token_count = token_count
        self.category = category  # "code", "data", "instruction", "general"
        self.importance = importance  # Higher = less likely to be evicted
        self.source_id = source_id  # Optional ID linking to source entity
        self.created_at = time.time()
        
    def summary(self, max_tokens: int = 100) -> str:
        """Generate a shorter summary if needed."""
        if self.token_count <= max_tokens:
            return self.text
        # TODO: Implement text summarization logic
        return self.text[:max_tokens * 4] + "..."  # Simple truncation

class ContextWindow:
    """Token-aware context window management."""
    def __init__(self, max_tokens: int = 12000, tokeniser: Optional[Tokeniser] = None):
        self.max_tokens = max_tokens
        self.fragments: List[Fragment] = []
        self.tokens_used = 0
        self.tokeniser = tokeniser or SimpleTokeniser()
        
    def add(self, text: str, category: str = "general", 
            importance: float = 1.0, source_id: Optional[str] = None) -> bool:
        """Add content to the context window, returning success status."""
        token_count = self.tokeniser.count(text)
        
        # Check if this would exceed the token limit
        if token_count > self.max_tokens:
            # Content is too large even on its own
            return False
            
        # Try to evict if needed
        if self.tokens_used + token_count > self.max_tokens:
            if not self._evict(token_count):
                # Couldn't free enough space
                return False
                
        # Add the fragment
        fragment = Fragment(text, token_count, category, importance, source_id)
        self.fragments.append(fragment)
        self.tokens_used += token_count
        return True
        
    def _evict(self, needed_tokens: int) -> bool:
        """
        Evict fragments to free up space, returning success status.
        Uses importance and age to determine eviction priority.
        """
        if not self.fragments:
            return False
            
        # Sort fragments by importance (ascending) and age (oldest first)
        eviction_candidates = sorted(
            self.fragments,
            key=lambda f: (f.importance, -f.created_at)
        )
        
        # Try to free enough tokens
        freed_tokens = 0
        fragments_to_remove = []
        
        for fragment in eviction_candidates:
            fragments_to_remove.append(fragment)
            freed_tokens += fragment.token_count
            
            if freed_tokens >= needed_tokens:
                break
                
        # If we can't free enough tokens, fail
        if freed_tokens < needed_tokens:
            return False
            
        # Remove the fragments
        for fragment in fragments_to_remove:
            self.fragments.remove(fragment)
            self.tokens_used -= fragment.token_count
            
        return True
        
    def render(self) -> str:
        """Render all fragments to a single string."""
        return "\n\n".join(fragment.text for fragment in self.fragments)
        
    def categorized_render(self) -> Dict[str, str]:
        """Render fragments grouped by category."""
        result = {}
        by_category = {}
        
        for fragment in self.fragments:
            if fragment.category not in by_category:
                by_category[fragment.category] = []
            by_category[fragment.category].append(fragment.text)
            
        for category, texts in by_category.items():
            result[category] = "\n\n".join(texts)
            
        return result
        
    def token_stats(self) -> Dict[str, Any]:
        """Get statistics about token usage."""
        category_tokens = {}
        
        for fragment in self.fragments:
            if fragment.category not in category_tokens:
                category_tokens[fragment.category] = 0
            category_tokens[fragment.category] += fragment.token_count
            
        return {
            "total_tokens": self.tokens_used,
            "max_tokens": self.max_tokens,
            "remaining_tokens": self.max_tokens - self.tokens_used,
            "fragment_count": len(self.fragments),
            "category_tokens": category_tokens
        }
```

### 5.2 Materialiser

```python
# agent/materialiser.py

from typing import Any, Dict, List, Optional, Union
from cogitarelink.core.entity import Entity
from cogitarelink.vocab.composer import composer
from .interfaces import Materialiser as MaterialiserProtocol
from .cache_integration import CacheCoordinator

class Materialiser(MaterialiserProtocol):
    """
    Convert entities to token-efficient text representations.
    """
    def __init__(self, token_budget: int = 2000, tokeniser = None, 
                cache_coordinator: Optional[CacheCoordinator] = None):
        self.token_budget = token_budget
        self.tokeniser = tokeniser or SimpleTokeniser()
        self.cache_coordinator = cache_coordinator or CacheCoordinator()
        
    def serialise(self, objects: List[Any], style: str = "json-ld") -> str:
        """Convert a list of objects to a string representation."""
        if not objects:
            return ""
            
        if style == "json-ld":
            return self._serialize_jsonld(objects)
        elif style == "code":
            return self._serialize_code(objects)
        elif style == "text":
            return self._serialize_text(objects)
        else:
            raise ValueError(f"Unknown style: {style}")
            
    def _serialize_jsonld(self, objects: List[Any]) -> str:
        """Serialize entities as compact JSON-LD with caching."""
        from cogitarelink.core.entity import Entity
        import json
        
        # Filter for Entity objects
        entities = [obj for obj in objects if isinstance(obj, Entity)]
        
        if not entities:
            return ""
            
        # Check cache for single entity case
        if len(entities) == 1 and entities[0].id:
            cached = self.cache_coordinator.get_materialization(
                entities[0].id, "json-ld", self.token_budget
            )
            if cached:
                return cached
            
        # Get all vocabulary prefixes from entities
        all_prefixes = set()
        for entity in entities:
            all_prefixes.update(entity.vocab)
            
        # Compose a shared context
        try:
            ctx_result = composer.compose(list(all_prefixes))
            shared_ctx = ctx_result.get("@context", {})
        except Exception:
            # Fallback to individual contexts
            shared_ctx = None
            
        # Serialize each entity
        serialized = []
        
        for entity in entities:
            if shared_ctx:
                # Use shared context to minimize duplication
                entity_json = entity.as_json.copy()
                entity_json.pop("@context", None)
                entity_json["@context"] = "..."  # Placeholder to save tokens
            else:
                entity_json = entity.as_json
                
            # Compact representation with sorted keys
            serialized.append(json.dumps(entity_json, sort_keys=True, indent=2))
            
        # Add shared context at the beginning if used
        if shared_ctx:
            ctx_str = "Shared @context (used by all entities):\n"
            ctx_str += json.dumps({"@context": shared_ctx}, indent=2)
            serialized.insert(0, ctx_str)
            
        # Check if we need to truncate
        result = "\n\n".join(serialized)
        
        # If over budget, try to reduce further
        if self.tokeniser.count(result) > self.token_budget:
            # Simplified to fit token budget
            result = self._truncate_to_budget(result)
            
        # Cache the result for single entity
        if len(entities) == 1 and entities[0].id:
            self.cache_coordinator.cache_materialization(
                entities[0].id, "json-ld", self.token_budget, result
            )
            
        return result
        
    def _serialize_code(self, objects: List[Any]) -> str:
        """Serialize code objects (functions, classes, etc.)"""
        # ... Implementation of code serialization
        # Try to show signatures and docstrings while collapsing bodies
        pass
        
    def _serialize_text(self, objects: List[Any]) -> str:
        """Serialize objects as plain text summaries."""
        # Implementation for natural language summaries
        pass
        
    def _truncate_to_budget(self, text: str) -> str:
        """Truncate text to fit within token budget."""
        if self.tokeniser.count(text) <= self.token_budget:
            return text
            
        # For now, use simple truncation with note
        truncated = text[:self.token_budget * 4]  # Approximate chars per token
        return truncated + "\n\n[Content truncated to fit token budget. Request full entity if needed.]"
```

### 5.3 Retriever with Cache

```python
# agent/retrieval/graph.py

from typing import List, Any, Dict, Optional
from cogitarelink.core.graph import GraphManager
from ..interfaces import Retriever as RetrieverProtocol
from ..cache_integration import CacheCoordinator
import hashlib
import json

class GraphRetriever(RetrieverProtocol):
    """Retrieve entities from the graph using various strategies."""
    
    def __init__(self, graph: GraphManager, cache_coordinator: Optional[CacheCoordinator] = None):
        self.graph = graph
        self.cache_coordinator = cache_coordinator or CacheCoordinator()
        
    def fetch(self, query: str, k: int = 10, **kwargs) -> List[Any]:
        """
        Fetch entities matching the query with caching.
        
        Args:
            query: The search query
            k: Maximum number of results
            **kwargs: Additional parameters:
                - subject: Optional subject filter
                - predicate: Optional predicate filter
                - object: Optional object filter
                - expand: Whether to expand entity children
                - bypass_cache: Whether to bypass the cache
        """
        # Generate a cache key based on query and parameters
        query_params = {
            "query": query,
            "k": k,
            **{key: value for key, value in kwargs.items() if key != "bypass_cache"}
        }
        query_hash = hashlib.sha256(
            json.dumps(query_params, sort_keys=True).encode()
        ).hexdigest()
        
        # Check cache unless bypassing
        if not kwargs.get("bypass_cache", False):
            cached_ids = self.cache_coordinator.get_query_result(query_hash)
            if cached_ids:
                # Convert IDs back to entities
                entities = []
                for entity_id in cached_ids:
                    entity = self._get_entity_by_id(entity_id)
                    if entity:
                        entities.append(entity)
                return entities
        
        # Extract optional filters
        subject = kwargs.get('subject')
        predicate = kwargs.get('predicate')
        object = kwargs.get('object')
        expand = kwargs.get('expand', True)
        
        # Query the graph
        triples = self.graph.query(subject, predicate, object)
        
        # Group by subject to collect entity information
        entities_by_id = {}
        
        for s, p, o in triples:
            if s not in entities_by_id:
                entities_by_id[s] = {'@id': s, 'properties': {}}
                
            # Add property
            prop_key = p.split('/')[-1]  # Simple predicate name extraction
            entities_by_id[s]['properties'][prop_key] = o
            
        # Convert to Entity objects
        from cogitarelink.core.entity import Entity
        
        entities = []
        entity_ids = []
        
        for entity_id, data in entities_by_id.items():
            # Try to construct an Entity
            try:
                # This is a simplification - actual implementation would need
                # to determine vocabulary and structure content properly
                entity = Entity(
                    id=entity_id,
                    vocab=["schema"],  # Default vocabulary
                    content=data['properties']
                )
                entities.append(entity)
                entity_ids.append(entity_id)
            except Exception:
                # Skip entities that can't be constructed
                continue
                
        # Sort by relevance (would normally use a more sophisticated scoring)
        entities = entities[:k]
        entity_ids = entity_ids[:k]
        
        # Cache the result
        self.cache_coordinator.cache_query_result(query_hash, entity_ids)
        
        return entities
        
    def _get_entity_by_id(self, entity_id: str) -> Optional[Any]:
        """Retrieve a single entity by ID."""
        from cogitarelink.core.entity import Entity
        
        # Get all triples for this entity
        triples = self.graph.query(entity_id, None, None)
        if not triples:
            return None
            
        # Convert to properties
        properties = {}
        for _, p, o in triples:
            prop_key = p.split('/')[-1]  # Simple predicate name extraction
            properties[prop_key] = o
            
        # Try to create an Entity
        try:
            return Entity(
                id=entity_id,
                vocab=["schema"],  # Default vocabulary
                content=properties
            )
        except Exception:
            return None
```

### 5.4 Committer with Cache Management

```python
# agent/commit/jsonld.py

import re
import json
from typing import Dict, Any, List, Set
from cogitarelink.core.graph import GraphManager
from cogitarelink.core.entity import Entity
from cogitarelink.reason.prov import wrap_patch_with_prov
from ..cache_integration import CacheCoordinator

class JsonLDCommitter:
    """Process JSON-LD content from LLM output and commit to graph."""
    
    def __init__(self, graph: GraphManager, cache_coordinator: Optional[CacheCoordinator] = None):
        self.graph = graph
        self.cache_coordinator = cache_coordinator or CacheCoordinator()
        self.jsonld_pattern = re.compile(r"```(?:json-ld|jsonld)\n(.*?)```", re.DOTALL)
        
    def ingest(self, llm_output: str, **context) -> Dict[str, Any]:
        """
        Extract and process JSON-LD from LLM output.
        
        Args:
            llm_output: Text output from the LLM
            **context: Additional context like source information
            
        Returns:
            Result with success status and details
        """
        # Extract JSON-LD blocks
        matches = self.jsonld_pattern.findall(llm_output)
        
        if not matches:
            return {
                "success": False,
                "error": "No JSON-LD content found",
                "matches": 0
            }
            
        # Process each JSON-LD block
        results = []
        
        for i, match in enumerate(matches):
            result = self._process_jsonld(match, i, **context)
            results.append(result)
            
        # Overall success if at least one block succeeded
        success = any(result["success"] for result in results)
        
        return {
            "success": success,
            "blocks_processed": len(results),
            "blocks_succeeded": sum(1 for r in results if r["success"]),
            "results": results
        }
        
    def _process_jsonld(self, content: str, block_index: int, **context) -> Dict[str, Any]:
        """Process a single JSON-LD block with cache invalidation."""
        # Try to parse the JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON parsing error: {str(e)}",
                "block_index": block_index
            }
            
        # Validate as JSON-LD
        if not isinstance(data, dict) or "@context" not in data:
            # Try to detect vocabulary and add context
            try:
                from cogitarelink.cli.vocab_tools import registry_tools
                detect_vocab = registry_tools()["detect_vocabularies"]
                vocab_result = detect_vocab(data)
                
                if vocab_result.get("success") and vocab_result.get("count") > 0:
                    # Use detected vocabularies
                    prefixes = list(vocab_result.get("detected", {}).keys())
                    
                    # Compose context
                    from cogitarelink.vocab.composer import composer
                    ctx_result = composer.compose(prefixes)
                    
                    # Add context to data
                    data = {"@context": ctx_result["@context"], **data}
                else:
                    # Default to schema.org
                    from cogitarelink.vocab.composer import composer
                    ctx_result = composer.compose(["schema"])
                    data = {"@context": ctx_result["@context"], **data}
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Not valid JSON-LD and couldn't add context: {str(e)}",
                    "block_index": block_index
                }
                
        # Create an Entity from the data
        try:
            # Extract vocabularies from context
            prefixes = []
            ctx = data.get("@context", {})
            
            if isinstance(ctx, dict):
                # Look for vocabulary URLs in context
                from cogitarelink.vocab.registry import registry
                for prefix, uri in ctx.items():
                    if isinstance(uri, str) and "://" in uri:
                        # Try to map to a known prefix
                        normalized = registry._norm(uri)
                        if normalized in registry._alias:
                            prefixes.append(registry._alias[normalized])
                            
            # Default to schema if no prefixes detected
            if not prefixes:
                prefixes = ["schema"]
                
            # Create the entity
            entity = Entity(
                vocab=prefixes,
                content=data
            )
            
            # Extract linked entities before adding to graph
            referenced_entities = self._extract_referenced_entities(entity)
            
            # Apply provenance wrapping
            source = context.get("source", "llm://assistant")
            agent = context.get("agent", "https://example.org/agents/LLM")
            
            with wrap_patch_with_prov(self.graph, source=source, agent=agent):
                self.graph.ingest_entity(entity)
                
            # Invalidate caches for this entity and referenced entities
            self.cache_coordinator.invalidate_entity(entity.id)
            for ref_id in referenced_entities:
                self.cache_coordinator.invalidate_entity(ref_id)
                
            return {
                "success": True,
                "entity_id": entity.id,
                "block_index": block_index,
                "prefixes": prefixes
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Entity creation failed: {str(e)}",
                "block_index": block_index
            }
            
    def _extract_referenced_entities(self, entity: Entity) -> Set[str]:
        """Extract IDs of entities referenced by this entity."""
        referenced = set()
        
        def extract_refs(obj):
            if isinstance(obj, dict):
                # Check for entity references
                if "@id" in obj and isinstance(obj["@id"], str):
                    referenced.add(obj["@id"])
                    
                # Recursively check all values
                for v in obj.values():
                    extract_refs(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_refs(item)
        
        # Check the entity content
        extract_refs(entity.content)
        
        return referenced
```

## 6. LLM Integration and Example Workflow

To demonstrate how this system would work with Claude or other LLM systems, here's an end-to-end example:

```python
def process_query_with_semantic_paging(query, graph, llm_client):
    """Process a user query using the semantic paging system."""
    # Set up components
    retriever = GraphRetriever(graph)
    materialiser = Materialiser(token_budget=4000)
    ctx_window = ContextWindow(max_tokens=12000)
    committer = JsonLDCommitter(graph)
    navigator = KnowledgeNavigator(graph)
    
    # Initial setup - add knowledge navigation tools
    knowledge_index = navigator.generate_knowledge_index()
    ctx_window.add(knowledge_index, category="index", importance=0.8)
    
    # Step 1: Interpret the query
    interpretation = navigator.interpret_knowledge_query(query)
    operation = interpretation["operation"]
    
    # Step 2: Retrieve relevant information
    if operation == "entity_lookup":
        entity_id = interpretation["entity_id"]
        entities = [retriever._get_entity_by_id(entity_id)]
    elif operation == "type_query":
        type_name = interpretation["type"]
        entities = retriever.fetch(query, k=10, 
                                 predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#type", 
                                 object=type_name)
    else:
        # General search
        entities = retriever.fetch(query, k=8)
    
    # Step 3: Materialize the entities
    if entities:
        content = materialiser.serialise(entities, style="json-ld")
        ctx_window.add(content, category="data", importance=1.0)
    
    # Step 4: Add context-specific instructions
    if operation == "entity_lookup":
        instructions = f"""
        You are examining information about the entity {entity_id}.
        If you want to add or update information, please format it as valid JSON-LD.
        """
    elif operation == "type_query":
        instructions = f"""
        You are examining entities of type {type_name}.
        If you want to add a new entity of this type, please format it as valid JSON-LD.
        """
    else:
        instructions = """
        You are examining entities related to the user's query.
        If you want to add or update information, please format it as valid JSON-LD.
        """
        
    ctx_window.add(instructions, category="instruction", importance=0.9)
    
    # Step 5: Generate prompt and call LLM
    prompt = ctx_window.render() + f"\n\nUser Query: {query}\n"
    
    # Call the LLM
    response = llm_client.generate(prompt)
    
    # Step 6: Process LLM response
    result = committer.ingest(response, source="llm")
    
    return {
        "original_query": query,
        "interpretation": interpretation,
        "entities_found": len(entities) if entities else 0,
        "llm_response": response,
        "commit_result": result
    }
```

## 7. Testing with Claude Code

To test the Context-Materialization layer using Claude Code as a surrogate agent, we can implement a dedicated testing suite that simulates LLM interactions.

### 7.1 Test Structure

1. **Mock LLM Interface**
   - Create a Claude Code simulator that processes prompts and generates responses
   - Use prompt templates that match Claude's actual behavior
   - Add ability to record/replay interactions for reproducible tests

2. **Test Scenarios**
   - Knowledge retrieval: Test ability to find and format relevant information
   - Knowledge committing: Test extraction and validation of LLM-generated content
   - Context window management: Test eviction strategies under various constraints

3. **Integration Test Flow**
   - Load test datasets into GraphManager
   - Set up test prompts with specific information needs
   - Process through the full retrieval → materialisation → context window pipeline
   - Generate sample "LLM outputs" with structured content to test committer
   - Validate both the process and resulting graph state

### 7.2 Example Integration Test

```python
def test_end_to_end_workflow():
    """Test the complete semantic paging workflow."""
    # Set up test components
    graph = GraphManager()
    retriever = GraphRetriever(graph)
    materialiser = Materialiser(token_budget=1000)
    ctx_window = ContextWindow(max_tokens=4000)
    committer = JsonLDCommitter(graph)
    navigator = KnowledgeNavigator(graph)
    
    # Load test data
    load_test_entities(graph)
    
    # Test query
    query = "How does GraphManager.query work?"
    
    # 1. Generate knowledge index
    knowledge_index = navigator.generate_knowledge_index()
    ctx_window.add(knowledge_index, category="index", importance=0.8)
    
    # 2. Fetch relevant entities
    entities = retriever.fetch(query, k=5)
    assert len(entities) > 0, "Should find relevant entities"
    
    # 3. Materialize content within token budget
    content = materialiser.serialise(entities, style="code")
    assert len(content) > 0, "Should generate materialized content"
    
    # 4. Add to context window
    success = ctx_window.add(content, category="code")
    assert success, "Should fit in context window"
    
    # Get context window stats
    stats = ctx_window.token_stats()
    assert stats["total_tokens"] > 0, "Should count tokens"
    assert stats["total_tokens"] <= stats["max_tokens"], "Should respect token budget"
    
    # 5. Simulate Claude response with JSON-LD
    claude_response = generate_test_llm_response()
    
    # 6. Process the response
    result = committer.ingest(claude_response, source="test://claude")
    assert result["success"], "Should successfully process response"
    assert result["blocks_processed"] > 0, "Should find JSON-LD blocks"
    
    # 7. Verify the graph was updated
    for block_result in result["results"]:
        if block_result["success"]:
            entity_id = block_result["entity_id"]
            triples = graph.query(entity_id, None, None)
            assert len(triples) > 0, f"Entity {entity_id} should be in graph"
            
            # Also check caches were invalidated
            cached = materialiser.cache_coordinator.get_materialization(
                entity_id, "json-ld", materialiser.token_budget
            )
            assert cached is None, "Cache should be invalidated"
```

### 7.3 Claude Code Integration

To test with actual Claude Code:

1. **Create a Claude Code Tool**
   - Implement a custom tool that uses the Anthropic API
   - Configure with proper model parameters and prompt templates
   - Add ability to record interactions for test reproducibility

2. **Test Script Structure**
   ```python
   from anthropic import Anthropic
   
   def test_with_claude_code():
       """Test semantic paging with actual Claude Code."""
       # Set up components
       graph = GraphManager()
       retriever = GraphRetriever(graph)
       materialiser = Materialiser(token_budget=3000)
       ctx_window = ContextWindow(max_tokens=12000)
       committer = JsonLDCommitter(graph)
       navigator = KnowledgeNavigator(graph)
       
       # Set up Anthropic client
       client = Anthropic()
       
       # Load test entities
       load_test_entities(graph)
       
       # Process user query
       query = "Explain how GraphManager.query works and give me a JSON-LD example of its output"
       
       # Generate knowledge navigation index
       knowledge_index = navigator.generate_knowledge_index()
       ctx_window.add(knowledge_index, category="index", importance=0.8)
       
       # Retrieve and materialize context
       entities = retriever.fetch(query, k=8)
       context = materialiser.serialise(entities, style="code")
       ctx_window.add(context, category="code")
       
       # Generate system instructions for Claude
       system = """
       You are an AI assistant helping with code explanations.
       When explaining concepts, please include a JSON-LD example in a code block.
       Use ```json-ld to mark JSON-LD blocks.
       """
       
       # Build the prompt with context window
       prompt = ctx_window.render() + f"\n\nUser: {query}"
       
       # Call Claude
       response = client.messages.create(
           model="claude-3-opus-20240229",
           max_tokens=2000,
           system=system,
           messages=[{"role": "user", "content": prompt}]
       )
       
       # Process response
       claude_message = response.content[0].text
       result = committer.ingest(claude_message, source="claude-code-test")
       
       # Validate results
       assert result["success"], "Should extract valid JSON-LD"
       
       # Return both for manual inspection
       return {
           "claude_response": claude_message,
           "committer_result": result
       }
   ```

## 8. Implementation Roadmap

### 8.1 Implementation Sequence

1. **Phase 1: Foundation (Core Components)**
   - Define Protocol interfaces in `agent/interfaces.py`
   - Implement ContextWindow with token tracking and fragment categorization
   - Create CacheCoordinator to manage multi-level caching
   - Build tokenizer adapters for Claude and other LLMs
   - Write tests for each core component in isolation

2. **Phase 2: Retrieval and Materialization**
   - Implement GraphRetriever integration with GraphManager
   - Create Materialiser with format-specific serializers
   - Add token-aware serialization with budget enforcement
   - Implement knowledge navigation and index generation
   - Test retrieval and materialization with different entity types

3. **Phase 3: Committer and Knowledge Flow**
   - Build JsonLDCommitter with pattern extraction and validation
   - Create knowledge schema tools for entity validation
   - Implement bidirectional knowledge flow patterns
   - Test committing with varied LLM output patterns

4. **Phase 4: Integration and Testing**
   - Integrate all components into a complete pipeline
   - Create CLI extensions for easy access to semantic paging
   - Build a comprehensive test suite with Claude Code integration
   - Add benchmark tests to measure performance

### 8.2 Deliverables

1. **Code Components**
   - Interface Protocols (Retriever, Materialiser, etc.)
   - Implementation classes for all components
   - Framework adapters for LLM integration
   - CLI extensions for agent-optimized interactions

2. **Documentation**
   - Architecture documentation
   - Component reference documentation
   - Example workflows
   - Integration guide for LLM developers

3. **Tests**
   - Unit tests for each component
   - Integration tests for the full pipeline
   - Performance benchmarks
   - Claude Code simulation tests

4. **Examples**
   - Example notebooks showing workflows
   - Sample applications
   - Code generation demonstrations
   - Knowledge extraction demonstrations

## 9. Conclusion

The proposed implementation adds a token-aware "semantic paging" system to Cogitarelink that integrates cleanly with the existing architecture. By building on GraphManager, ContextProcessor, and vocabulary tools, we can create a powerful system for moving information between LLMs and semantic graphs.

Key benefits include:

1. **Token Efficiency**: Optimize representations for LLM context windows
2. **Intelligent Retrieval**: Combine multiple strategies to find relevant information
3. **Structured Output Processing**: Extract and validate LLM-generated content
4. **Framework Agnostic**: Support multiple LLM providers through adapter pattern
5. **Knowledge Navigation**: Help LLMs understand and interact with the knowledge graph
6. **Cache Integration**: Efficiently manage cache at multiple levels with proper invalidation
7. **Bidirectional Knowledge Flow**: Enable LLMs to both consume and contribute semantic data

This implementation will enable LLMs to work effectively with large knowledge graphs, intelligently retrieving relevant information and committing new knowledge with proper provenance tracking.