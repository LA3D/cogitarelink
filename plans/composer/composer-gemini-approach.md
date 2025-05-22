# CogitareLink Agentic Control Restructuring: A Gemini-Guided Approach

(As of May 20, 2025)

## 1. Introduction

This document outlines the agreed-upon strategy for restructuring the `cogitarelink` Python package to support robust agentic control. It synthesizes a discussion between Chuck (the user) and Gemini (the AI assistant) regarding two proposed approaches for integrating an agent layer, as detailed in `composer.md` and `composer-claude-approach.md`.

The goal is to enable `cogitarelink` to effectively "give any LLM a verified semantic memory" by allowing agents to store, load, verify, and reason over JSON-LD documents, manage context windows, and interact with tools.

## 2. Context: Initial Brief and Proposed Architectures

The development of `cogitarelink` is guided by the "Agentic-Coder Brief," which specifies:
- Project elevator pitch: "Give any LLM a verified semantic memory."
- Tooling: `nbdev`, `fastcore`, `pyld`, `httpx`, `pydantic`, `rdflib` (optional), `fastapi` (later).
- Directory structure and core modules (notebooks 00-08, 90-91).
- Milestone M0: Complete notebooks 00-08 (except stubs), ensuring `nbdev_test --flags fast` passes.

Two primary approaches for the agentic/composer layer were considered:

*   **`composer.md` (Semantic Paging Subsystem):**
    *   Proposes an additive approach, introducing new `agent/` and `integration/` layers.
    *   These new layers would consume functionalities from the core CogitareLink modules (00-08).
    *   Emphasizes `typing.Protocol` for interfaces and optional dependencies for adapters.
    *   Less disruptive to the M0 milestone and existing module specifications.

*   **`composer-claude-approach.md` (Claude Code-Inspired Approach):**
    *   Suggests a more significant and immediate refactoring of the existing core modules (00-08).
    *   Involves embedding token awareness, tool registries, and other LLM-centric concerns directly into core modules from the outset.
    *   Potentially alters the scope of M0 deliverables for the core notebooks.

## 3. Chosen Path: Iterative Development Starting with `composer.md`

After a sanity check against the "Agentic-Coder Brief" and the M0 milestone, the decision is to proceed with the approach outlined in **`composer.md`** first.

**Rationale:**

*   **Alignment with M0:** This approach is more consistent with achieving the M0 milestone as currently defined, allowing foundational modules (00-08) to be completed as specified.
*   **Modularity and "Micro-Kernel" Preservation:** It better preserves the idea of CogitareLink as a "semantic memory micro-kernel" by keeping agent-specific logic in a separate, additive layer.
*   **Reduced Disruption:** It is less disruptive to the existing plan and codebase structure for the initial milestones.
*   **Iterative Development:** It allows for an iterative build-out, establishing the core semantic layer first, then adding the agent interaction layer on top.

The more extensive refactoring suggested by `composer-claude-approach.md` remains a valuable consideration for subsequent milestones, once the core M0 functionality is stable and validated.

## 4. How `composer.md` Facilitates the "Claude-Style" Refactoring

The `composer.md` approach ("semantic paging subsystem") can effectively pave the way for the more comprehensive "Claude-style" refactoring by:

1.  **Defining Robust, Generic Interfaces:** Establishing `agent/interfaces.py` with abstract `Protocol`-based interfaces (`LLM`, `Tool`, `Retriever`, `Materialiser`, `Committer`, `Tokeniser`) will create stable contracts.
2.  **Isolating Token Management:** Implementing `ContextWindow` with clear token counting (via a `Tokeniser` interface) and budget management will provide a reference implementation.
3.  **Developing a Flexible `Materialiser`:** The `Materialiser`'s logic for using `cogitarelink.vocab.composer` for context compaction and managing output size will inform the evolution of `vocab/composer.py`.
4.  **Establishing Basic Plug-in/Adapter Patterns:** Implementing the proposed plug-in system for retrievers and adapters for LLMs sets up a pattern for optional dependencies and dynamic loading.
5.  **Maintaining Initial Separation of Concerns:** Developing agent-specific logic in new `agent/` and `integration/` directories allows core modules to stabilize, making it easier to later identify functionalities for deeper integration.
6.  **Focusing on Clear Data Flows:** Refining interactions at the agent layer will provide insights for how core components might be refactored to support these flows more directly.

## 5. Impact on Existing Notebooks

The primary impact of implementing the `composer.md` system will be on:

*   **`10_agent_cli.ipynb`**: This notebook's planned functionality for agent logic and its CLI will be largely superseded or guided by the new, structured components from `composer.md` (e.g., `ContextWindow`, `Materialiser`, `Retriever`, `Committer`). `10_agent_cli.ipynb` will likely be refactored to orchestrate these new components.

The core notebooks (`00_debug.ipynb` through `08_processor.ipynb`, `90_signer.ipynb`, `91_validator.ipynb`) are foundational and are intended to be *used by* this new agent system, not replaced by it.

## 6. Conclusion

The strategy is to first implement the agentic layer as described in `composer.md`. This provides a modular and less disruptive path to achieving initial agent capabilities while aligning with the M0 milestone. The components, interfaces, and learnings from this phase will then inform and facilitate a potential, more extensive refactoring of `cogitarelink`'s core, as envisioned in `composer-claude-approach.md`, at a later stage of development.
