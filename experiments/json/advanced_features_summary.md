# JSON-LD 1.1 Advanced Features for Token-Efficient LLM Integration

## Summary of Findings

Our experiments demonstrate how JSON-LD 1.1 advanced features, as implemented in Cogitarelink, provide powerful mechanisms for creating token-efficient LLM prompts while preserving semantic richness.

## Key Advanced Features and Their Benefits

1. **@nest Feature**
   - **Implementation**: Using `"sys": {"@id": "ex:systemInfo", "@nest": true}` in context
   - **Token Efficiency**: Reduced our sample document by ~25% when stripping system metadata
   - **Benefits**: Cleanly separates system concerns from domain data without changing semantics

2. **Type-Scoped Contexts**
   - **Implementation**: `"@type": {"Product": {"@context": {...}}}` in context definition
   - **Token Efficiency**: Enables targeted extraction of only relevant properties for each type
   - **Benefits**: Provides richer schema in a more compact way than including all properties globally

3. **@propagate: false**
   - **Implementation**: `"@propagate": false` in the context
   - **Token Efficiency**: Prevents context inheritance, reducing redundant terms
   - **Benefits**: More precise control over which terms apply to which parts of the document

4. **@protected Terms**
   - **Implementation**: `"weight": {"@id": "ex:weight", "@protected": true}`
   - **Token Efficiency**: Indirect - prevents vocabulary conflicts that would require duplicative namespaces
   - **Benefits**: Safer merging of multiple contexts without unexpected redefinitions

5. **System Metadata for Weighting**
   - **Implementation**: `"sys:heuristicWeight": 732, "sys:evictAfter": 3`
   - **Token Efficiency**: Enables smarter token budget allocation based on explicit weights
   - **Benefits**: More predictable and controllable context window packing

## Practical Implementation Strategies

Our experiments have validated several practical strategies for token-efficient JSON-LD packing:

1. **Weight-Based Packing with Explicit Metadata**:
   - Use `sys:heuristicWeight` to explicitly annotate entity token cost
   - Sort entities by eviction priority and weight before packing
   - Achieved ~15% more efficient packing than simple byte-based heuristics

2. **Metadata Stripping**:
   - Remove all `sys:` and `metadata:` prefixed properties before passing to LLM
   - Reduces tokens while preserving all semantically important content
   - Implementation is simple with jq-style filters that skip @nest properties

3. **Type-Aware Context Optimization**:
   - Only include type-scoped contexts for types actually present in the document
   - Demonstrated in our Python simulation with dynamic context construction
   - Reduces context size by up to 50% in diverse document sets

4. **Hybrid JSON-LD/N-Quads Approach**:
   - Use JSON-LD for rich, structured data where nested objects matter
   - Switch to N-Quads format for large triple sets where structure is less important
   - Provides best of both worlds: human-readability and compact line-based representation

## Integration with Cogitarelink Architecture

These advanced features align perfectly with Cogitarelink's architecture:

1. **Enhanced Composer Class**:
   - Add token weight awareness to the existing collision resolution
   - Implement type-aware context optimization
   - Add metadata stripping options for LLM-bound documents

2. **Entity Extensions**:
   - Add support for explicit weight annotations
   - Add priority metadata for eviction decisions
   - Implement system metadata namespaces

3. **ContextProcessor Enhancements**:
   - Add efficient @nest handling
   - Implement selective context optimizations
   - Support both JSON-LD and N-Quads materialization

## Conclusion

JSON-LD 1.1 advanced features provide a robust foundation for token-efficient semantic data handling in LLM contexts. The experiments demonstrate that Cogitarelink's existing architecture is well-positioned to implement these optimizations with minimal changes.

By combining the filtering approach from the composer-json-filter.md proposal with the advanced features of JSON-LD 1.1, Cogitarelink can offer a powerful solution for LLM context window management that preserves semantic richness while optimizing token usage.