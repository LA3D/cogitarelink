# Data Agent Tools: Cogitarelink Integration Architecture

## Overview

This document outlines a tools-based approach for data agents that fully integrates with Cogitarelink's existing architecture. Based on examining the library's caching, registry, collision handling, and retrieval systems, the tools are designed to extend rather than replace existing functionality, ensuring seamless integration with the library's core design principles.

## Core Design Principles

1. **Extend Existing Architecture**: Build on top of Cogitarelink's registry, caching, and retrieval systems
2. **Respect Class Hierarchy**: Use the established class patterns and inheritance structure
3. **Leverage Existing Caching**: Utilize the InMemoryCache/DiskCache system with namespaced memoization
4. **Adopt Collision Strategies**: Use the existing collision resolution framework
5. **Match Functional Style**: Follow the functional approach with singleton pattern where appropriate

## Tool Categories

### 1. Registry Extension Tools

These tools extend the existing vocabulary registry system in `vocab/registry.py`:

```python
@tool
def explore_registry(filter_tags: List[str] = None) -> Dict[str, Dict]:
    """
    Explore available vocabularies in the registry with optional filtering.
    
    Parameters:
        filter_tags: Optional tags to filter vocabularies
        
    Returns:
        Dictionary of vocabulary entries matching the filter
    """
    from cogitarelink.vocab.registry import registry
    
    result = {}
    for prefix, entry in registry._v.items():
        if filter_tags and not any(tag in entry.tags for tag in filter_tags):
            continue
        result[prefix] = {
            "prefix": entry.prefix,
            "uri": entry.uris.get("primary"),
            "versions": entry.versions.dict(),
            "features": list(entry.features)
        }
    return result

@tool
def add_temp_vocabulary(prefix: str, uri: str, context_url: str = None, 
                       inline_context: Dict = None, ttl_url: str = None) -> Dict:
    """
    Add a temporary vocabulary to the registry for the current session.
    
    Parameters:
        prefix: Short prefix for the vocabulary
        uri: Primary URI for the vocabulary
        context_url: Optional JSON-LD context URL
        inline_context: Optional inline context definition
        ttl_url: Optional TTL file URL to derive context from
        
    Returns:
        Dictionary with operation result
    """
    from cogitarelink.vocab.registry import registry, VocabEntry, ContextBlock, Versions
    from pydantic import AnyUrl
    
    # Create context block (requires exactly one source)
    context = {}
    if context_url:
        context["url"] = AnyUrl(context_url)
    elif inline_context:
        context["inline"] = inline_context
    elif ttl_url:
        context["derives_from"] = AnyUrl(ttl_url)
    else:
        return {"success": False, "error": "Must provide one of: context_url, inline_context, or ttl_url"}
    
    # Create the vocab entry
    entry = VocabEntry(
        prefix=prefix,
        uris={"primary": AnyUrl(uri), "alternates": []},
        context=ContextBlock(**context),
        versions=Versions(current="1.0", supported=["1.0"]),
        features=set(["temp_vocabulary"])
    )
    
    # Add to registry (this modifies the singleton instance)
    registry._v[prefix] = entry
    
    # Update alias map
    registry._alias[registry._norm(uri)] = prefix
    
    return {
        "success": True,
        "prefix": prefix,
        "uri": uri,
        "message": "Temporary vocabulary added to registry"
    }
```

### 2. Context Composition Tools

These tools extend the context composer system in `vocab/composer.py`:

```python
@tool
def compose_context(prefixes: List[str], support_nest: bool = False, 
                  propagate: bool = True) -> Dict:
    """
    Compose a JSON-LD context from multiple vocabulary prefixes.
    
    Parameters:
        prefixes: List of vocabulary prefixes, ordered by priority
        support_nest: Whether to add @nest support
        propagate: Whether to allow context propagation
        
    Returns:
        Composed context object ready to use in a JSON-LD document
    """
    from cogitarelink.vocab.composer import composer
    
    try:
        result = composer.compose(prefixes, support_nest, propagate)
        return {
            "success": True,
            "context": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@tool
def analyze_context_compatibility(prefix_a: str, prefix_b: str) -> Dict:
    """
    Analyze compatibility between two vocabularies.
    
    Parameters:
        prefix_a: First vocabulary prefix
        prefix_b: Second vocabulary prefix
        
    Returns:
        Compatibility analysis with recommended strategy
    """
    from cogitarelink.vocab.collision import resolver, _prot_overlap
    
    # Get the resolution plan
    plan = resolver.choose(prefix_a, prefix_b)
    
    # Check for protected term overlap
    a_has, b_has, overlap = _prot_overlap(prefix_a, prefix_b)
    
    return {
        "success": True,
        "strategy": plan.strategy.value,
        "details": plan.details,
        "protected_terms": {
            f"{prefix_a}_has_protected": a_has,
            f"{prefix_b}_has_protected": b_has,
            "has_overlap": overlap
        }
    }
```

### 3. Robust Retrieval Tools

These tools extend the `integration/retriever.py` system:

```python
@tool
def retrieve_vocabulary_resource(uri: str, format_hint: str = None) -> Dict:
    """
    Retrieve a vocabulary resource with automatic format detection.
    
    Parameters:
        uri: URI of the resource to retrieve
        format_hint: Optional hint about the expected format
        
    Returns:
        Retrieved resource converted to JSON-LD
    """
    from cogitarelink.integration.retriever import LODRetriever
    
    retriever = LODRetriever()
    result = retriever.retrieve(uri)
    
    # Add format-specific metadata if successful
    if result.get("success", False):
        # Add information about the resource format
        if format_hint and format_hint != result.get("format"):
            result["format_requested"] = format_hint
    
    return result

@tool
def extract_embedded_jsonld(html_content: str, base_url: str = None) -> Dict:
    """
    Extract JSON-LD content embedded in HTML.
    
    Parameters:
        html_content: HTML content to analyze
        base_url: Base URL for resolving relative URIs
        
    Returns:
        Extracted JSON-LD data if found
    """
    from bs4 import BeautifulSoup
    from cogitarelink.integration.retriever import json_parse
    
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        jsonld_scripts = soup.select("script[type='application/ld+json']")
        
        if not jsonld_scripts:
            return {
                "success": False,
                "error": "No JSON-LD script tags found in HTML"
            }
        
        results = []
        for script in jsonld_scripts:
            json_ld, error = json_parse(script.string, uri=base_url)
            if json_ld:
                results.append(json_ld)
        
        return {
            "success": bool(results),
            "data": results,
            "count": len(results),
            "error": None if results else "Failed to parse embedded JSON-LD"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"HTML parsing error: {str(e)}"
        }
```

### 4. Cache-Aware Tools

These tools leverage the caching system in `core/cache.py`:

```python
@tool
def cached_context_fetch(prefix: str, max_age: int = 86400) -> Dict:
    """
    Fetch a vocabulary context with time-based caching.
    
    Parameters:
        prefix: Vocabulary prefix to fetch
        max_age: Maximum age of cached content in seconds
        
    Returns:
        Cached or freshly retrieved context
    """
    from cogitarelink.core.cache import InMemoryCache
    from cogitarelink.vocab.registry import registry
    import time
    
    # Use cache with namespace
    cache = InMemoryCache(maxsize=32)
    cache_key = f"context:{prefix}"
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        context, timestamp = cached
        age = time.time() - timestamp
        
        if age < max_age:
            return {
                "success": True,
                "context": context,
                "source": "cache",
                "age_seconds": int(age)
            }
    
    # Not in cache or too old, fetch fresh
    try:
        entry = registry[prefix]
        context = entry.context_payload()
        
        # Store in cache with timestamp
        cache.set(cache_key, (context, time.time()))
        
        return {
            "success": True,
            "context": context,
            "source": "fresh",
            "age_seconds": 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch context: {str(e)}"
        }

@tool
def multi_vocabulary_fetch(prefixes: List[str], strategy: str = "parallel") -> Dict:
    """
    Fetch multiple vocabularies efficiently using batching.
    
    Parameters:
        prefixes: List of vocabulary prefixes to fetch
        strategy: Fetch strategy (parallel or sequential)
        
    Returns:
        Dictionary of fetched vocabularies with metadata
    """
    from cogitarelink.vocab.registry import registry
    import concurrent.futures
    
    def fetch_one(prefix):
        try:
            entry = registry[prefix]
            context = entry.context_payload()
            return {
                "success": True,
                "prefix": prefix,
                "context": context
            }
        except Exception as e:
            return {
                "success": False,
                "prefix": prefix,
                "error": str(e)
            }
    
    results = {}
    
    if strategy == "parallel" and len(prefixes) > 1:
        # Use thread pool for parallel fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(prefixes), 5)) as executor:
            future_to_prefix = {executor.submit(fetch_one, p): p for p in prefixes}
            for future in concurrent.futures.as_completed(future_to_prefix):
                result = future.result()
                results[result["prefix"]] = result
    else:
        # Sequential fetching
        for prefix in prefixes:
            results[prefix] = fetch_one(prefix)
    
    return {
        "success": True,
        "results": results,
        "count": len(results),
        "strategy": strategy
    }
```

### 5. Wikidata Integration Tools

These tools integrate with Wikidata:

```python
@tool
def wikidata_search(query: str, limit: int = 10, language: str = "en") -> Dict:
    """
    Search for entities in Wikidata matching a query.
    
    Parameters:
        query: Search text
        limit: Maximum number of results
        language: Language code for labels
        
    Returns:
        List of matching Wikidata entities
    """
    from cogitarelink.integration.retriever import search_wikidata
    
    results = search_wikidata(query, limit, language)
    
    return {
        "success": not any("error" in item for item in results),
        "results": results,
        "count": len(results),
        "query": query
    }

@tool
def wikidata_entity_details(entity_id: str) -> Dict:
    """
    Get detailed information about a Wikidata entity.
    
    Parameters:
        entity_id: Wikidata entity ID (Q-number)
        
    Returns:
        Detailed entity information
    """
    from cogitarelink.integration.retriever import LODRetriever
    
    retriever = LODRetriever()
    return retriever.get_entity_details(entity_id)

@tool
def align_property_to_wikidata(property_name: str, 
                              description: str = None) -> Dict:
    """
    Find the closest matching Wikidata property for a dataset field.
    
    Parameters:
        property_name: Name of the property to align
        description: Optional property description
        
    Returns:
        Wikidata alignment suggestions
    """
    from cogitarelink.integration.retriever import search_wikidata
    
    # Search for property by name
    query = property_name
    if description:
        # Add first sentence of description to improve search
        first_sentence = description.split('.')[0] if '.' in description else description
        query = f"{property_name} {first_sentence}"
    
    results = search_wikidata(query, limit=5)
    
    # Basic confidence scoring
    scored_results = []
    for item in results:
        if "error" in item:
            continue
            
        # Simple confidence scoring based on label similarity
        confidence = 0.0
        if item.get("label", "").lower() == property_name.lower():
            confidence = 0.9
        elif property_name.lower() in item.get("label", "").lower():
            confidence = 0.7
        elif any(property_name.lower() in word.lower() for word in item.get("label", "").split()):
            confidence = 0.5
        else:
            confidence = 0.3
            
        # Boost confidence if description matches
        if description and description.lower() in item.get("description", "").lower():
            confidence = min(confidence + 0.2, 1.0)
            
        item["confidence"] = round(confidence, 2)
        scored_results.append(item)
    
    # Sort by confidence
    scored_results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    return {
        "success": True,
        "property": property_name,
        "matches": scored_results,
        "best_match": scored_results[0] if scored_results else None
    }
```

## Example Workflows

### 1. Robust Croissant Schema Resolution

This workflow demonstrates resolving and using the Croissant schema despite URI availability issues:

```python
# Task: Resolve and use Croissant vocabulary context for dataset metadata

# 1. First try normal context resolution through the registry
vocab_result = cached_context_fetch("croissant")

if not vocab_result.get("success", False):
    # 2. Try to resolve using the TTL file since we know it's available
    ttl_resource = retrieve_vocabulary_resource(
        "https://raw.githubusercontent.com/mlcommons/croissant/main/docs/croissant.ttl",
        format_hint="turtle"
    )
    
    if ttl_resource.get("success", False):
        # 3. Extract a context from the TTL data
        from cogitarelink.integration.retriever import rdf_to_jsonld
        derived_context, _ = rdf_to_jsonld(
            ttl_resource.get("content", ""),
            format="turtle", 
            base_uri="http://mlcommons.org/croissant/"
        )
        
        # 4. Add as temporary vocabulary to the registry
        add_temp_vocabulary(
            prefix="croissant",
            uri="http://mlcommons.org/croissant/",
            inline_context=derived_context.get("@context", {})
        )
        
        # 5. Fetch again from registry (should now succeed)
        vocab_result = cached_context_fetch("croissant")

# Use the context to create a Croissant dataset
if vocab_result.get("success", False):
    # Create a dataset with the croissant context
    context = vocab_result.get("context", {})
    
    dataset = {
        "@context": context,
        "@type": "Dataset",
        "name": "Sample Dataset",
        "description": "A demonstration dataset",
        "recordSet": {
            "@type": "RecordSet",
            "name": "main",
            "field": [
                {"@type": "Property", "name": "id", "dataType": "string"},
                {"@type": "Property", "name": "value", "dataType": "float"}
            ]
        }
    }
    
    # Additional operations with the dataset...
```

### 2. Multi-Vocabulary Dataset Description

This workflow demonstrates creating a dataset description using multiple vocabularies:

```python
# Task: Create a dataset description using Schema.org, Croissant, and Dublin Core

# 1. First check compatibility between vocabularies
schema_croissant = analyze_context_compatibility("schema", "croissant")
schema_dc = analyze_context_compatibility("schema", "dc")

# 2. Compose a context with these vocabularies
context_result = compose_context(
    prefixes=["schema", "croissant", "dc"],
    support_nest=True
)

if context_result.get("success", False):
    # 3. Create a dataset using the composed context
    dataset = {
        "@context": context_result.get("context", {}).get("@context"),
        "@type": "Dataset",
        # Schema.org properties
        "name": "Climate Data 2023",
        "description": "Global temperature recordings for 2023",
        "url": "https://example.org/climate-data-2023",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        # Dublin Core properties
        "dc:creator": "Climate Research Institute",
        "dc:created": "2023-12-31",
        "dc:subject": "Climate Science",
        # Croissant specific properties
        "recordSet": {
            "@type": "RecordSet",
            "name": "temperature_readings",
            "field": [
                {
                    "@type": "Property",
                    "name": "date",
                    "dataType": "date"
                },
                {
                    "@type": "Property",
                    "name": "location",
                    "dataType": "string"
                },
                {
                    "@type": "Property",
                    "name": "temperature",
                    "dataType": "float",
                    "unit": "celsius"
                }
            ]
        }
    }
    
    # 4. Align dataset properties with Wikidata
    wikidata_mappings = {}
    for field in dataset["recordSet"]["field"]:
        alignment = align_property_to_wikidata(
            field["name"],
            field.get("description", "")
        )
        if alignment.get("success") and alignment.get("best_match"):
            best_match = alignment["best_match"]
            wikidata_mappings[field["name"]] = {
                "wikidata_id": best_match.get("id"),
                "wikidata_uri": best_match.get("uri"),
                "label": best_match.get("label"),
                "confidence": best_match.get("confidence")
            }
            # Add Wikidata reference if confidence is high enough
            if best_match.get("confidence", 0) > 0.7:
                field["sameAs"] = best_match.get("uri")
    
    # Additional operations with the enriched dataset...
```

### 3. Vocabulary Detection and Adaptation

This workflow demonstrates analyzing a document to detect vocabularies and adapt it:

```python
# Task: Analyze a JSON-LD document to detect vocabularies and adapt it if needed

# Sample document to analyze
document = {
    "@context": "https://schema.org/",
    "@type": "Dataset",
    "name": "Example Dataset",
    "description": "An example dataset for demonstration",
    "url": "https://example.org/dataset",
    "distribution": {
        "@type": "DataDownload",
        "contentUrl": "https://example.org/dataset.csv",
        "encodingFormat": "text/csv"
    }
}

# 1. First explore the registry to see available vocabularies
available_vocabs = explore_registry()

# 2. Analyze the document context to detect vocabularies
from cogitarelink.vocab.registry import detect_vocabularies
detected_vocabs = detect_vocabularies(document["@context"])

# 3. See if we need to add Croissant vocabulary
if "croissant" not in detected_vocabs and "dataset" in document.get("@type", "").lower():
    # We're dealing with a dataset, might want to add Croissant
    
    # 4. Get compatibility between schema and croissant
    compat = analyze_context_compatibility("schema", "croissant")
    
    # 5. Create a new context that includes both
    new_context = compose_context(
        prefixes=["schema", "croissant"],
        support_nest=True
    )
    
    if new_context.get("success", False):
        # 6. Add Croissant-specific properties
        enhanced_doc = document.copy()
        enhanced_doc["@context"] = new_context.get("context", {}).get("@context")
        
        # Add recordSet if it doesn't exist
        if "recordSet" not in enhanced_doc:
            # Try to infer structure from distribution
            distribution = enhanced_doc.get("distribution", {})
            encoding_format = distribution.get("encodingFormat", "")
            
            record_set = {
                "@type": "RecordSet",
                "name": "main",
                "field": []
            }
            
            # Try to detect fields or suggest placeholder
            if "csv" in encoding_format.lower():
                record_set["field"] = [
                    {"@type": "Property", "name": "field1", "dataType": "string"},
                    {"@type": "Property", "name": "field2", "dataType": "string"}
                ]
                record_set["note"] = "Fields automatically generated - please update with actual schema"
            
            enhanced_doc["recordSet"] = record_set
        
        # 7. Document is now enhanced with Croissant
        document = enhanced_doc

# Additional operations with the document...
```

## Implementation Strategy

To implement these tools effectively within Cogitarelink's architecture:

### 1. Direct Integration

1. **Extend Existing Classes**: Create agent tools as extensions of existing classes
   ```python
   class VocabRegistryAgent:
       """Agent extensions for the vocabulary registry."""
       def __init__(self, registry_instance=None):
           from cogitarelink.vocab.registry import registry
           self.registry = registry_instance or registry
   ```

2. **Respect Singleton Pattern**: Use the singleton instances where available
   ```python
   from cogitarelink.vocab.registry import registry
   from cogitarelink.vocab.composer import composer
   from cogitarelink.vocab.collision import resolver
   ```

### 2. Namespaced Caching

Leverage the existing caching system with proper namespacing:

```python
from cogitarelink.core.cache import InMemoryCache

# Create a cache instance for agent operations
_agent_cache = InMemoryCache(maxsize=128)

@_agent_cache.memoize("wikidata")
def cached_wikidata_search(query):
    # Implementation that benefits from caching
```

### 3. Progressive Error Handling

Implement a cascade of fallback mechanisms:

```python
def robust_context_resolution(prefix):
    """Resolve a context with fallback mechanisms."""
    # First try registry
    try:
        from cogitarelink.vocab.registry import registry
        entry = registry[prefix]
        return entry.context_payload()
    except Exception as primary_error:
        # Log the primary error
        
        # Try derivation from TTL
        try:
            # TTL derivation logic
        except Exception as secondary_error:
            # Log secondary error
            
            # Try constructing minimal context
            # ...
```

### 4. Vocabulary Integration Tests

Create tests to ensure the tools work with the existing infrastructure:

```python
def test_agent_registry_integration():
    """Test that agent tools properly integrate with the registry."""
    # Test registry exploration
    explore_result = explore_registry()
    assert "schema" in explore_result
    
    # Test temporary vocabulary addition
    temp_result = add_temp_vocabulary("test", "http://example.org/test")
    assert temp_result["success"]
    
    # Verify it was added to the registry
    from cogitarelink.vocab.registry import registry
    assert "test" in registry._v
```

## Conclusion

By designing agent tools that fully integrate with Cogitarelink's architecture, we create a seamless experience for both developers and AI agents working with the library. The tools leverage the existing patterns for registry management, context composition, collision handling, and data retrieval, ensuring that they behave consistently with the rest of the library.

This approach enables AI agents to work effectively with vocabularies like Croissant, handling the complex reality of semantic data integration while maintaining the design principles that make Cogitarelink robust and maintainable.

The tools are specifically designed to handle edge cases like unavailable vocabulary endpoints, providing multiple fallback paths that maintain semantic integrity. This makes them particularly valuable for production environments where reliability is essential.