# JSON-LD 1.1 Advanced Features for Efficient LLM Context Management

This experiment explores how JSON-LD 1.1 advanced features, as implemented in Cogitarelink, can be leveraged for more efficient context window management in LLMs.

## Advanced Features Used

Our `jsonld-advanced-features.json` file demonstrates these JSON-LD 1.1 features:

1. **@version 1.1**: Enabling JSON-LD 1.1 features explicitly
2. **@protected terms**: Preventing term redefinition conflicts
3. **@nest**: Grouping metadata without affecting the data model
4. **@propagate: false**: Preventing context inheritance
5. **Type-scoped contexts**: Different properties available based on @type
6. **@vocab-scoped values**: Using vocabulary terms as values
7. **@graph partitioning**: Multi-entity documents

## Experiment 1: Impact of @nest on LLM Context Size

The `@nest` feature allows separating metadata from core data without changing the semantic model. This helps with filtering for LLMs.

```bash
# Extract just the core data, excluding nested metadata
jq '.["@graph"][] | del(.["sys:createdAt"], .["sys:heuristicWeight"], .["sys:evictAfter"], .["metadata:sources"], .["metadata:lastUpdated"], .["metadata:verified"], .["metadata:sentiment"])' jsonld-advanced-features.json
```

### Benefits for LLMs:
- Can separate paging/weight metadata from semantic content
- Allows different filtering strategies for system vs. domain data
- Makes it easier for LLMs to focus on core data

## Experiment 2: Type-Scoped Contexts for Targeted Extraction

Type-scoped contexts allow different properties to be available based on entity type:

```bash
# Extract only Product-specific fields (including type-scoped ones)
jq '.["@graph"][] | select(.["@type"] == "Product") | {id: .["@id"], name, price, sku, productId, category}' jsonld-advanced-features.json
```

### Benefits for LLMs:
- Allows type-specific extraction without modifying the schema
- Reduces context bloat by only including relevant properties
- Enables more precise targeting when filtering

## Experiment 3: Protected Terms and Graph Partitioning

Protected terms and graph partitioning help manage vocabulary conflicts:

```bash
# First convert to N-Quads
riot --syntax=jsonld --output=nquads jsonld-advanced-features.json > advanced.nq

# Filter by graph name (once expanded, @graph items become separate named graphs)
grep "http://example.org/product/1" advanced.nq
```

### Benefits for LLMs:
- Safely combine multiple vocabularies without conflicts
- Add private properties with @nest that won't affect standard processing
- Use @protected to ensure critical terms aren't redefined

## Experiment 4: Generating Context-Weighted JSON-LD

This experiment demonstrates how to extract entities with their weights for context-aware packing:

```bash
# Extract entities with their system metadata for weight-based decisions
jq '.["@graph"][] | {id: .["@id"], type: .["@type"], weight: .["sys:heuristicWeight"], evictAfter: .["sys:evictAfter"]}' jsonld-advanced-features.json
```

Using this approach, we could implement the materialization function from the proposal:

```python
def materialize_weighted(processor, entities, budget=20000):
    # Sort by weight
    entities_with_weights = [(e, e.get("sys:heuristicWeight", 1000)) 
                           for e in entities]
    
    # Sort by priority (optional)
    entities_with_weights.sort(key=lambda x: (x[0].get("sys:evictAfter", 999), x[1]))
    
    # Greedy pack
    selected = []
    total_weight = 0
    
    for entity, weight in entities_with_weights:
        if total_weight + weight <= budget:
            selected.append(entity)
            total_weight += weight
        else:
            break
            
    return selected
```

## Experiment 5: Efficient @context Management

The context itself can consume significant tokens. This experiment demonstrates context reuse:

```bash
# Extract just the @context
jq '.["@context"]' jsonld-advanced-features.json > context.json

# Extract just the data without contexts
jq '.["@graph"]' jsonld-advanced-features.json > data.json
```

With separate context and data, we can:
1. Send the context once at the beginning of a conversation
2. Reference it by URL or ID in subsequent messages 
3. Only include minimal context on entities when needed

### Implementation in Cogitarelink:
```python
def build_efficient_context_window(entity_ids, processor, include_full_context=False):
    # Start with the minimal context reference or full context
    if include_full_context:
        window = {"@context": processor.context.as_dict()}
    else:
        window = {"@context": "http://example.org/contexts/standard"}
    
    # Add entities with minimal or no context
    window["@graph"] = []
    
    # Get entities and add to window
    for eid in entity_ids:
        entity = processor.get_entity(eid)
        # Strip context to avoid duplication
        entity_data = {k:v for k,v in entity.items() if k != "@context"}
        window["@graph"].append(entity_data)
    
    return window
```

## Advanced Feature Impact on Context Management

| Feature | Token Impact | Filtering Benefit |
|---------|--------------|-------------------|
| @nest | Reduces by isolating metadata | Easy removal of system metadata |
| Type-scoped contexts | Consolidates similar entities | Type-specific property extraction |
| @protected | Prevents duplication | Safer merging of multiple contexts |
| @propagate: false | Reduces context bloat | Prevents unwanted inheritance |
| @graph | Separates entities | Entity-level filtering and packing |

## Conclusion

JSON-LD 1.1 advanced features provide powerful mechanisms for efficient context management:

1. **Separation of Concerns**: @nest isolates metadata from domain data
2. **Type-specific Properties**: Type-scoped contexts allow precise extraction
3. **Conflict Management**: @protected and graph partitioning help manage vocabulary conflicts
4. **Efficient Packing**: System metadata like weights can guide LLM context composition
5. **Context Reuse**: Context sharing reduces token usage across multiple entities

These features align perfectly with the composer-json-filter proposal, enabling semantically rich but token-efficient LLM prompts.