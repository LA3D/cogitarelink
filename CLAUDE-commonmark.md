

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## Project Overview

Cogitarelink (“to think connectedly”) is a Python library for working
with Linked Open Data as semantic memory. It enables processing,
validation, and navigation of JSON-LD 1.1 data with context awareness,
allowing LLMs and agents to have verifiable semantic memory.

The system uses a micro-kernel architecture (~600 LOC) where business
logic lives in data artifacts rather than code. It stores JSON-LD data,
runs SHACL/SPARQL rules to derive facts, caches everything, and records
provenance for every triple it inserts.

## Key Components

- **Core**: debug (logging), cache (LRU/TTL), context, entity, graph
- **Vocab**: registry (prefix → VocabEntry map), composer (merges
  JSON-LD contexts)
- **Reason**: afford (extracts shape/rule hints), prov (provenance
  wrapping), sandbox (runs rules)
- **Tools**: reason_tool (provides OpenAI-function bridge to
  reason_over)
- **Verify**: validator (SHACL validation), signer (cryptographic
  signatures for triples)

The prov (92_prov) module adds provenance tracking to all derived
triples, allowing agents to explain reasoning chains and cite sources.
The validator (90_signer/91_validator) provides cryptographic
verification of semantic data, enabling trustworthy exchanges between
agents.

## Knowledge Artifact Layers

1.  **Context** (\*.context.jsonld) - Term to IRI mappings (keep under
    5KB)
2.  **Ontology** (ontology.ttl/.jsonld) - Class/property definitions
3.  **Shapes/Rules** (shapes.ttl, rules.ttl) - SHACL constraints and
    rules
4.  **Data** (\*.jsonld instances) - Actual instances/events

## Build/Test Commands

- Create environment: `uv venv`
- Install: `uv pip install -e ".[dev]"` (preferred) or
  `pip install -e .`
- Export code from notebooks: `nbdev_export` or `nbdev_prepare`
- Run all tests: `nbdev_test` or `pytest -q`
- Run single test: `pytest tests/test_file.py::test_function -v`
- Install git hooks: `nbdev_install_hooks`

## Code Style Guidelines

- **Format**: Black (88 columns)
- **Imports**: Use `from __future__ import annotations` for type hints
- **Types**: Use type hints everywhere
- **Package Management**: Use uv for dependencies and virtual
  environments
- **Testing**: Use fastcore tests (test_eq, test_fail, flags) with at
  least one test per public function
- **Error handling**: Guard rdflib imports with try/except; expose
  \_HAS_RDFLIB flag
- **Notebooks**: Work in notebooks first, then export to Python modules
- **Notebook exports**: Mark public API cells with `#| export`
- **Documentation**: Use markdown cells to document code, concepts, and
  design decisions
- **Development approach**: Jeremy Howard style incremental, tested
  development
- **Development workflow**: Build small working pieces, test each step,
  refactor, then expand
- **Network requests**: Always set 10s timeout for context fetches
- **Naming**: Use concise variable names; single line if/loop constructs
  on same line
- **Cache keys**: Follow “expand:{hash}”, “norm:{hash}” format
- **References**: LLM reference documents available in llmstxt/
  directory
- **Design principle**: Python should never contain domain business
  logic; the LLM writes SHACL/SPARQL on the fly
