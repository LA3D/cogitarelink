# Code Review: Cogitarelink

Date: 2025-05-03

## Overview

This document summarizes a high-level code review of the `cogitarelink` codebase. Key focus areas:
- Avoiding overimplementation where existing libraries suffice.
- Leveraging standard RDF/JSON-LD/SHACL libraries (rdflib, pyld, pyshacl) effectively.

## Areas of Overimplementation

- **Manual N-Quads Parsing**: The `InMemoryGraph.add_nquads` method splits lines on whitespace to parse triples/quads. This reimplements parsing logic that `rdflib` already provides robustly (including literal escaping and datatype handling).
- **Custom Parent-Child Tracking**: Both `GraphManager` and `EntityProcessor` maintain manual maps for parent–child and graph entries. Equivalent relationships could be navigated via SPARQL queries over an RDF graph.
- **HTML JSON-LD Extraction**: Code in `integration/retriever.py` and `cli/vocab_tools.py` manually parses HTML with BeautifulSoup to extract `<script type="application/ld+json">`. Libraries like `extruct` specialize in embedded JSON-LD extraction and edge cases.
- **Reified Temporal Models**: The `core/temporal.py` module defines Pydantic models (`TimeInstant`, `TimeInterval`, reification classes) and builds RDF graphs by hand. In many cases, direct use of `rdflib` with reusable building blocks or helper libraries (e.g., `Owlready2`) could simplify this.
- **Inlined SHACL Rules**: SHACL rules are embedded as multi-line Turtle strings in `create_temporal_rules()`. Maintaining shapes in separate `.ttl` or `.shacl` files and loading them programmatically improves readability and reuse.

## Missing Leverage of Standard Libraries

- **RDF Parsing & Storage**: Fallback to a simplistic in-memory set store rather than defaulting to `rdflib`’s `Graph` or `Dataset` for all backends.
- **JSON-LD Processing**: While `ContextProcessor` uses `pyld`, other modules reimplement context merges or normalization that `pyld` or higher-level wrappers could handle.
- **SHACL Validation**: Multiple entry points (`tools/temporal.py`, `reason/sandbox.py`, `verify/validator.py`) invoke `pyshacl.validate` directly with ad-hoc parameters. A unified validation helper would reduce duplication.
- **Context Loading & Caching**: The custom document loader wraps `httpx` and a registry fallback. Consider using `pyld`’s built-in loader hooks or a caching HTTP library to streamline this logic.

## Recommendations

1. **Consolidate RDF Handling**: Standardize on `rdflib` for parsing, querying, and in-memory storage. Remove or simplify `InMemoryGraph` to leverage `rdflib`’s memory backends.
2. **Externalize SHACL Shapes**: Move all SHACL shapes and SPARQL rules into dedicated `.ttl` files. Load them once in a shared validation utility.
3. **Use JSON-LD Extraction Libraries**: Swap manual HTML traversal for a specialized library (e.g., `extruct`) in retriever and CLI components.
4. **Centralize Utilities**: Create shared helpers for JSON-LD expansion/normalization, SHACL validation, and RDF graph manipulation to remove cross-module duplication.

## Next Steps

- Audit usage of `GraphManager` and migrate critical paths to `rdflib` exclusively.
- Bundle SHACL rules into a version-controlled directory (`shapes/temporal.ttl`, etc.) and update validation calls accordingly.
- Survey JSON-LD context merging across modules; unify under `ContextProcessor` and retire ad-hoc merges.
- Introduce integration tests for fallback behavior (e.g., without `rdflib` installed) to ensure InMemoryGraph correctness or consider deprecating it.
  
## Prioritized Punch List

1. Consolidate RDF handling: migrate all graph storage and queries to `rdflib`, deprecate or remove the custom `InMemoryGraph` backend.
2. Externalize SHACL shapes: extract SPARQL rules and SHACL shapes into dedicated `shapes/` files and load them via a shared validation utility.
3. Centralize JSON-LD processing: unify context composition, expansion, compaction, and normalization under `ContextProcessor`, retiring ad-hoc merges.
4. Replace manual HTML JSON-LD extraction: adopt a specialized extraction library (e.g., `extruct`) in retriever and CLI components.
5. Extract shared utilities: create a common `utils` module for RDF graph operations, SHACL validation, and JSON-LD handling to eliminate duplication.
6. Add integration tests: cover core workflows including RDF parsing, JSON-LD context loading, SHACL validation, and fallback scenarios.
7. Document migration and deprecation: provide clear guidelines for retiring legacy components (InMemoryGraph, ad-hoc extractors) and migrating existing code.