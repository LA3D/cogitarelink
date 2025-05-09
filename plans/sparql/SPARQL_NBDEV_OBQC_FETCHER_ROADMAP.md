# Roadmap: nbdev-based SPARQL Tools Integration with OBQC & LODRetriever

This document describes a phased plan for implementing SPARQL and Linked Data tools within CogitareLink using nbdev. We reuse existing OBQC query validation and the built-in Linked Data retriever (LODRetriever) rather than hand-crafting a new fetcher. All source lives in notebooks; the Python package is generated via `nbdev_build_lib`.

## 1. Notebook scaffold
- Create or update **63_sparql_tools.ipynb** with sections:
  1. Core SPARQL functions (`sparql_query`, `describe_resource`)
  2. Discovery (`sparql_discover`, VoID/Service-Desc/Introspection)
  3. Transformation (`sparql_json_to_jsonld`, context extraction)
  4. Tool specifications (JSON-schema for each tool)
  5. OBQC validator tools (`validate_query_against_ontology`, `check_query_patterns`, `generate_query_fixes`, `refine_query_with_ontology`)

## 2. SPARQL query & ingestion
- In the SPARQL core section define:
  - `sparql_query(endpoint_url, query, query_type, result_format, store_result, graph_id)`
    • Send HTTP GET with appropriate Accept header
    • Parse SELECT/ASK results or CONSTRUCT/DESCRIBE via rdflib
    • Serialize to N-Quads and call `GraphManager.ingest_nquads()`
    • Attach provenance metadata for stored graphs
  - `describe_resource`, a thin DESCRIBE wrapper

## 3. Discovery & transform
- In Discovery section implement `sparql_discover()` with:
  - VoID endpoint lookup (`/.well-known/void`)
  - SPARQL Service Description DESCRIBE
  - Lightweight introspection (SELECT DISTINCT ?p)
  - Namespace/prefix extraction logic
- In Transform section implement:
  - `sparql_json_to_jsonld()` to convert SELECT/ASK JSON→JSON-LD
  - Context extraction utilities for JSON-LD

## 4. OBQC validator integration
- Reuse existing OBQC logic in **63_sparql_tools.ipynb**:
  - `validate_query_against_ontology(query, ontology_ttl)` calls `cogitarelink.reason.obqc.check_query`
  - `check_query_patterns(query)` for unbound variables, missing LIMIT, etc.
  - `generate_query_fixes(query, validation_result)` to propose corrected patterns
  - `refine_query_with_ontology(query, ontology_ttl)` for iterative repair
- Export these as agent tools with JSON-schema specs

## 5. Linked-Data fetch (`ld_fetch`) via existing retriever
- Instead of building custom HTTP fetch, wrap `LODRetriever` from `cogitarelink.integration.retriever`:
  1. Call `retriever.retrieve(uri)`
  2. On success, take `result['data']` (JSON-LD), parse via rdflib, serialize to N-Quads
  3. Call `GraphManager.ingest_nquads(nquads, graph_id)`
  4. Return metadata (`success`, `graph_id`, `triples`)
- Provide a JSON-schema spec for `ld_fetch`

## 6. Agent/CLI registration
- In **10_agent_cli.ipynb** (or new **64_register_sparql.ipynb**):
  - Import all SPARQL & OBQC tools plus `ld_fetch`
  - Call `agent.register_tool()` for each with its spec
  - Include a markdown cell: guidance for when to call OBQC on query failure, how to apply fixes

## 7. Testing strategy
- Create **tests/test_sparql_tools.ipynb** with:
  - Unit tests for transform and OBQC functions
  - E2E tests: failing SELECT → OBQC suggestion → fixed SELECT → successful ingestion
  - `ld_fetch` against a known JSON-LD resource
- Run via `nbdev_test_nbs`

## 8. Documentation & build
- Document patterns, examples (Black Cat, Follow-Your-Nose) inline in notebooks
- Build with:
  ```bash
  nbdev_install_hooks
  nbdev_test_nbs
  nbdev_build_lib
  nbdev_build_docs
  ```

## 9. Dependencies & configuration
- Ensure `rdflib`, `httpx`, `bs4`, and their dependencies are in `pyproject.toml`
- Expose SPARQL timeouts and LODRetriever cache settings via `settings.ini` or a config cell

With this roadmap, all SPARQL, validation, and Linked-Data fetching capabilities live in notebooks, and are published automatically into the package via nbdev.