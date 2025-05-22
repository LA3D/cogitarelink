# JSON-LD Filtering for LLM Context Windows - Executive Summary

## Overview

The composer-json-filter proposal suggests an efficient approach to managing JSON-LD data for LLM context windows, similar to how Claude Code and Codex CLI manage their contexts. Our "back of the envelope" experiments validate the core concepts and demonstrate how they could be implemented in Cogitarelink.

## Key Components Validated

1. **Precise JSON-LD Slicing**
   - Demonstrated that jq-style queries can effectively extract relevant subsets of JSON-LD documents
   - Confirmed that tooling exists (pyjq, jmespath, jsonpath-ng) to implement this in Python

2. **Byte/Line-Based Weight Heuristics**
   - Validated the proposal's approach of using byte count as a proxy for token count
   - Confirmed that line counting is effective for N-Quads format

3. **Format-Specific Optimizations**
   - Compared JSON-LD and N-Quads representations
   - JSON-LD: Smaller files with context sharing, but more complex to slice
   - N-Quads: Line-oriented, easier to truncate by line count, deterministic IDs

4. **Performance Considerations**
   - Avoiding tokenizer calls during packing significantly improves performance
   - Only needs one tokenizer safety check at the end of the process

## Integration Path

The proposed enhancement fits naturally into Cogitarelink's architecture:

1. Add a `materialise()` method to the Composer class that:
   - Takes a query pattern and document
   - Applies weight-based filtering
   - Returns LLM-ready content in the requested format

2. Extend ContextProcessor with:
   - Byte-weight calculation
   - Line budget for N-Quads
   - Format conversion utilities

3. Enhance GraphManager with:
   - Ability to produce JSON-LD slices by ID or pattern
   - Integration with the materialization process

## Recommended Next Steps

1. Implement the core `weight()` function based on JSON string length
2. Add the greedy packing algorithm for selecting objects
3. Implement the JSON-LD to N-Quads conversion with line budgeting
4. Create a public API for LLM-friendly entity materialization
5. Add token counting as a final safety check only

## Conclusion

The experimental results confirm that the proposed approach is technically sound and would effectively solve the token management challenge. The implementation would enable Cogitarelink to efficiently page semantic data in and out of LLM context windows while maintaining the full power of JSON-LD's semantic capabilities.