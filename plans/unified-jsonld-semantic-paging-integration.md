# Unified JSON-LD + Semantic Paging Integration Plan

This document describes a unified implementation plan that synthesizes the
JSON‑LD Token‑Efficient Filtering and Semantic Paging Architecture proposals
into a single, cohesive design for CogitareLink. The goals are to:

1. Consolidate duplicated token‑weight, context‑window, and JSON‑LD logic into
   shared core modules.
2. Maintain a clear separation between low‑level JSON‑LD enhancements and
   high‑level agent components.
3. Leverage existing CLI and code structure rather than introduce parallel
   command trees.
4. Drive all new code via nbdev notebooks with jupytext for automatic export,
   testing, and documentation.

## 1 Goals

- Single authoritative token and weight estimation API.
- Unified ContextWindow/LLMContext abiding a shared Protocol.
- Reusable Materialiser façade for budgeted JSON‑LD serialization.
- Agent‑layer components with clear interfaces (Materialiser, ContextWindow,
  Retriever, Committer, Tokenizer adapters).
- Extension of existing `cogitarelink/cli/agent_cli.py` rather than parallel CLI.
- nbdev‑driven workflow for notebooks, export, tests, and docs.

## 2 Proposed Structure

### 2.1 Core JSON‑LD Enhancements (cogitarelink/core)

- **core/token.py**: weight estimation, token counting, and packing utilities.
- **context.py**: add `strip_metadata()`, delegate token logic to `core/token`,
  remove bespoke N‑Quads conversions in favor of standard `normalize(...,
  format="application/n-quads")`.
- **entity.py**: add `without_metadata()`, `weight`/`priority` properties
  delegating to `core/token`.
- **graph.py**: add `materialize_subgraph()` for budgeted subgraph extraction.

### 2.2 Agent‑Layer Components (cogitarelink/agent)

- **interfaces.py**: Protocol definitions for Materialiser, ContextWindow,
  Retriever, Committer.
- **materialiser.py**: budgeted JSON‑LD serializer façade calling Composer and
  `core/token` logic.
- **context_window.py**: `LLMContext` implementing the ContextWindow Protocol,
  eviction and packing powered by `core/token`.
- **retrieval.py**: hybrid graph/symbol/embedding Retriever implementing the
  Retriever Protocol.
- **committer.py**: parse LLM output (`jsonld`, `patch`) implementing the
  Committer Protocol.
- **token.py**: adapters for external tokenizers (tiktoken, anthropic)
  delegating to `core/token`.

Extend the existing CLI in `cli/agent_cli.py` to wire up these components under
`cogita agent ...` rather than introducing a parallel command tree.

## 3 Migration Plan

1. Create new notebooks `10_jsonld_core.ipynb` and `11_agent_components.ipynb`
   with `#| export` markers for all new core and agent-layer code.
2. In `10_jsonld_core.ipynb`, implement `core/token.py`, context.py,
   entity.py, graph.py enhancements. Sync with jupytext and run `nbdev_export`.
3. In `11_agent_components.ipynb`, implement `agent/interfaces.py`,
   materialiser.py, context_window.py, token.py, retrieval.py,
   committer.py. Sync and `nbdev_export`.
4. Update the CLI notebook (`10_agent_cli.ipynb`) to extend commands and wire up
   new components. Sync and `nbdev_export`.
5. Run `pytest -q --disable-warnings`, `nbdev_test_nbs`, and update any tests or
   documentation as needed.

## 4 File Layout

```text
cogitarelink/
  core/
    token.py
    context.py
    entity.py
    graph.py
  agent/
    __init__.py
    interfaces.py
    materialiser.py
    context_window.py
    retrieval.py
    committer.py
    token.py
  cli/
    agent_cli.py
```

## 5 nbdev & Jupytext Workflow

All code changes must follow the nbdev development workflow:

1. Edit or create notebooks with `%`-formatted Python and `#| export` cells.
2. `jupytext --sync path/to/notebook.ipynb`
3. `nbdev_export`
4. `pytest -q --disable-warnings` & `nbdev_test_nbs`
5. `pre-commit run --all-files`

## 6 Reference Experiments

The following prototypes and scripts in `experiments/` validate key aspects of this plan:

- **JSON-LD Filtering & Heuristic Packing** (`experiments/jq-json-filter-experiments.md`):
  Demonstrates jq-based JSON-LD slicing and byte-weight measurements.
- **Weight & Packing Simulation** (`experiments/advanced_packing_simulation.py`):
  Prototype of heuristic `extract_weight()`, priority evictions, and greedy packing.
- **Composer Sketch** (`experiments/composer_sketch.py`):
  Conceptual implementation of `slice_jsonld()`, `jsonld_to_nquads()`, and
  content materialization strategies.
- **Sample Data & Formats** (`experiments/sample-jsonld.json`,
  `experiments/sample.nq`, `experiments/advanced.nt`):
  Sample JSON-LD and N-Quads inputs used during experimentation.
- **Additional JQ Filters** (`experiments/*.jq`):
  Property-based and attribute-based filters exploring JSON-LD pruning rules.

These experiments confirm that the unified design across `core/token`,
`agent/materialiser`, and `agent/context_window` captures all required behaviors
and performance considerations.