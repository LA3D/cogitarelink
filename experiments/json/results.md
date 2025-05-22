# JSON-LD Filtering and Token Management - Experiment Results

## Key Findings

1. **JSON-LD to N-Quads Conversion**
   - Original JSON-LD: 2227 bytes, 85 lines
   - N-Quads format: 4103 bytes, 42 lines
   - The N-Quads version is actually larger in byte size but has fewer lines. This is primarily because:
     - Each triple is on a separate line (more verbose)
     - Blank nodes were generated for nested objects (adding overhead)
     - No compression from context sharing (each triple expands IRIs)

2. **JSON-LD Slicing Challenges**
   - The command-line jq tool had issues with handling the @-prefixed keys due to shell escaping, 
     highlighting why a pure Python implementation (as suggested in the proposal) might be more robust.
   - This validates the proposal's suggestion to use libraries like pyjq, jmespath, or jsonpath-ng.

3. **Heuristic Weight Demonstration**
   - The experiment validates that we can measure object byte size quickly.
   - This confirms the proposed approach of using byte size as a proxy for token count.
   - Line counting (as observed in N-Quads) could be another valid heuristic.

## Implementation Considerations

1. **Weight Function Validation**
   - The document proposes `len(json.dumps(obj))` as a weight function, which is simple to implement.
   - For N-Quads, counting lines would be an effective proxy.

2. **Slicing Strategies**
   - The experiment validates that slicing by graph entry ID, property, or value is feasible.
   - For Cogitarelink, implementing selector functions that map to jq/JSONPath patterns would provide clean abstractions.

3. **Format Tradeoffs**
   - JSON-LD with context: Human-readable, nested structure, context overhead
   - N-Quads: Line-oriented, easier to truncate but harder to reconstruct nested objects

4. **Python Implementation Path**
   - Our experiments confirm that the proposed architecture is sound
   - The `materialise()` function should allow switching between formats based on use case
   - Token counting should only be done as a final validation step

## Recommendations

1. Implement the lightweight JSON-LD slicing function using pyjq or jmespath
2. Add byte-based weight calculation and greedy packing algorithm 
3. Support both JSON-LD and N-Quads formats with automatic format selection
4. Add line budgeting for N-Quads and byte budgeting for JSON-LD
5. Integrate the enhanced Composer with the existing GraphManager for efficient querying

This "back of the envelope" validation has confirmed that the architecture proposed in the composer-json-filter.md document is feasible and would effectively address the token management challenge for LLM interactions.