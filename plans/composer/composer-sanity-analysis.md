<!-- Auto-generated analysis comparing plans/composer.md and plans/composer-implementation.md to the current codebase -->
# Sanity Check Analysis: Composer Plans vs Codebase

This document compares the high‑level design sketches in `plans/composer.md` and `plans/composer-implementation.md` against the actual files and structure in the `cogitarelink/` package.

## 1. Missing `agent/` subpackage

**Plan reference:**
```text
cogitarelink/
  agent/
    context_window.py    # working‑context controller
    retrieval.py         # hybrid graph + symbol + embedding search
    materialiser.py      # token‑budgeted serialisation of entities
    committer.py         # parses LLM output and writes back
  integration/
    code_indexer.py      # optional: tree‑sitter / ripgrep symbol index
```
【F:plans/composer.md†L9-L18】

**Reality:** The `cogitarelink/agent/` directory does not exist in the repository.

## 2. Missing `core/tokenizer.py` helper

**Plan reference:**
```python
from cogitarelink.core.tokenizer import count_tokens  # thin wrapper around tiktoken/anthropic
```
【F:plans/composer.md†L33-L35】

**Reality:** No `tokenizer.py` or `count_tokens` function is present under `cogitarelink/core/`.

## 3. Missing `integration/code_indexer.py`

**Plan reference:**
```text
cogitarelink/
  integration/
    retriever.py         # hybrid graph + symbol + embedding search (cogitarelink/integration/retriever.py)
    code_indexer.py      # optional: tree‑sitter / ripgrep symbol index
```
【F:plans/composer.md†L16-L18】

**Reality:** The `cogitarelink/integration/` directory contains `retriever.py`, but `code_indexer.py` is still missing.

## 4. Parts that match existing code

| Plan reference                                                                                                        | Actual location & lines                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Vocabulary composer** “Materialiser calls `composer.compose(…)` to squeeze context size…”                          | 【F:plans/composer.md†L156-L156】【F:cogitarelink/vocab/composer.py†L24-L31】                                                                                     |
| **Provenance helper** `wrap_patch_with_prov`                                                                           | 【F:plans/composer.md†L88-L92】【F:cogitarelink/reason/prov.py†L15-L23】                                                                                          |
| **Entity wrapper** `cogitarelink.core.entity.Entity`                                                                   | 【F:plans/composer.md†L87-L90】【F:cogitarelink/core/entity.py†L49-L57】                                                                                         |
| **Caching primitives** `InMemoryCache`, `DiskCache`                                                                     | 【F:plans/composer-implementation.md†L94-L96】【F:cogitarelink/core/cache.py†L86-L96】【F:cogitarelink/core/cache.py†L108-L116】                                     |
| **GraphManager queries** “...graph neighbourhoods to bring in just enough related facts...”                            | 【F:plans/composer.md†L157-L157】【F:cogitarelink/core/graph.py†L132-L133】                                                                                      |

## 5. Missing commit helpers (`apply_unified_diff`, `reindex_codebase`)

**Plan reference:**
```python
    def _apply_patch(self, patch: str):
        apply_unified_diff(patch)
        reindex_codebase()
```
【F:plans/composer.md†L104-L108】

**Reality:** Neither `apply_unified_diff()` nor `reindex_codebase()` exists anywhere in the repository.

## 6. Missing LLM-adapter scaffolding

**Plan reference (adapter API sketch):**
```python
# adapters/openai_llm.py
...
    def __init__(..., **kw):
        import tiktoken; self._tok = tiktoken.encoding_for_model(model)
```
【F:plans/composer.md†L296-L304】

**Plan reference (optional dependencies):**
```toml
[project.optional-dependencies]
openai    = ["openai>=1.16.0","tiktoken"]
anthropic = ["anthropic"]
```
【F:plans/composer.md†L325-L330】

**Reality:** No `agent/adapters/` (or top-level `adapters/`) directory or those adapter files are present.

---

## Summary

> Most of the core “semantic paging” building blocks (vocabulary composer, provenance wrapper, Entity, cache, GraphManager) are already implemented.  However, the entire proposed “agent” layer—including `agent/` modules, tokenizer helper, code indexer, commit helpers, and LLM adapters—is not scaffolded in the codebase.

You may want to either scaffold those modules to match the plans or prune/update the plan documents to reflect the current code structure.