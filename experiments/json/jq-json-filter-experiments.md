# JSON-LD Filtering and Heuristic Packing Experiments

This document explores the proposed approaches from `composer-json-filter.md` using existing command-line tools (jq and Jena) to demonstrate the concepts without writing new code.

## 1. Slicing JSON-LD with jq (Property Based)

The proposed approach suggests using jq-style filters to extract precise slices of JSON-LD documents. Let's experiment with different filtering patterns:

### 1.1 Extract a specific entity from @graph by ID

```bash
# Extract a specific product from the graph array
jq '.["@graph"][] | select(.["@id"]=="http://example.org/product/1")' sample-jsonld.json
```

### 1.2 Get only certain fields from all products 

```bash
# Extract minimal product info (id, name, price)
jq '.["@graph"][] | {id: .["@id"], name, price}' sample-jsonld.json
```

### 1.3 Filter by attribute value

```bash
# Find products that are "In Stock"
jq '.["@graph"][] | select(.availability == "In Stock")' sample-jsonld.json
```

## 2. Measuring Object Weight (Token Proxy)

The proposal suggests using `len(json.dumps(obj))` as a fast proxy for token count. We can demonstrate this with jq:

```bash
# Calculate byte-length of each object in the graph
jq '.["@graph"][] | {id: .["@id"], byte_size: (. | tostring | length)}' sample-jsonld.json
```

## 3. Heuristic Packing and Truncation

The proposal describes a greedy packing algorithm that adds entities until reaching a soft byte budget.

```bash
# Simulate truncation by taking only first 2 products (arbitrary cutoff)
jq '{
  "@context": .["@context"],
  "@graph": [.["@graph"][0], .["@graph"][1]],
  "_metadata": {
    "original_count": (.["@graph"] | length),
    "truncated_count": 2,
    "truncated_note": "...additional entities omitted..." 
  }
}' sample-jsonld.json
```

## 4. Converting to More Compact N-Quads Format

For even more compact representation, the proposal suggests using N-Quads. We can use Jena's riot tool to convert and then analyze the results:

```bash
# Convert JSON-LD to N-Quads
riot --syntax=jsonld --output=nquads sample-jsonld.json > sample.nq
 
# Count number of quads
wc -l sample.nq

# Calculate byte size of both formats
ls -l sample-jsonld.json sample.nq | awk '{print $5, $9}'
```

## 5. Extracting Targeted Subgraphs with Both Formats

The proposal suggests property-scoped and @nest approaches to isolate parts of the document:

```bash
# Extract just product specs
jq '.["@graph"][] | {id: .["@id"], specs}' sample-jsonld.json

# Extract reviews with nested structure
jq '.["@graph"][] | select(.reviews != null) | {product: .name, reviews}' sample-jsonld.json
```

## 6. Size-aware Packing Simulation

To demonstrate the core idea of byte-weighted selection:

```bash
# For each entity, calculate its size and determine if it fits in budget
jq '.["@graph"] | 
  # Set a mock byte budget
  20000 as $budget |
  # Start with an empty result and 0 used bytes  
  reduce .[] as $item (
    {"selected": [], "bytes_used": 0, "items_selected": 0}; 
    # Calculate this item's size in bytes
    ($item | tostring | length) as $size |
    # If we have room for it, add it
    if (.bytes_used + $size <= $budget) then
      .selected += [$item] | 
      .bytes_used += $size | 
      .items_selected += 1
    else . end
  )' sample-jsonld.json
```

## 7. Practical Implications

These experiments demonstrate the key ideas from the proposal:
1. Precise JSON-LD slicing is possible with jq filters
2. Byte-counting provides a fast, tokenizer-free proxy for LLM context limits
3. Greedy packing based on byte size is feasible
4. N-Quads provides a more compact representation for the same semantic data
5. Selective context inclusion can further optimize token usage

The actual implementation would integrate these concepts into the existing Cogitarelink architecture, particularly enhancing the Composer, ContextProcessor, and Entity classes.